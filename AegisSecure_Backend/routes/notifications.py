import httpx
import os, json, base64
import asyncio
from database import messages_col, accounts_col
from fastapi import APIRouter, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime, timezone
load_dotenv()
API_CALL_INTERVAL = 6 
router = APIRouter()
lock = asyncio.Lock()  

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
CYBER_SECURE_URI=os.getenv("CYBER_SECURE_API_URI")
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise Exception("Google OAuth credentials are missing in .env")

class Spam_request(BaseModel):
    sender: str
    subject: str
    text: str

async def get_spam_prediction(req:Spam_request):
    try:
        # print("⭐️PREDICTING:")
        async with httpx.AsyncClient() as client:
            sender=req.sender
            subject=req.subject
            body=req.text
            payload = {
                "sender": sender,
                "subject": subject,
                "text": body
            }
            # print(payload)
            resp = await client.post(
                CYBER_SECURE_URI,
                json=payload,
                timeout=30.0
            )
            # print(resp)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                return data
            return {"confidence": data, "reasoning": None}

    except Exception as e:
        return {
            "confidence": "unknown",
            "reasoning": None,
            "highlighted_text": None,
            "suggestion": None,
            "final_decision": "unknown"
        }

async def get_access_token_from_refresh(refresh_token: str):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
        )
        data = resp.json()
        return data.get("access_token")

@router.post("/analyze_text")
async def analyze_text_endpoint(data: dict):
    text = data.get("text", "")
    if not text:
        return {"prediction": "UNKNOWN"} 

    try:
        
        prediction = await get_spam_prediction(text)
        prediction_str = str(prediction).strip().upper() 
        if prediction_str not in ["SPAM", "HAM"]:
            prediction_str = "UNKNOWN"
        return {"prediction": prediction_str}
    except Exception as e:
        print("Error in analyze_text_endpoint:", e)
        return {"prediction": "UNKNOWN"}
    
def extract_body(payload):
    if not payload:
        return None

    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    if body_data and ("text/plain" in mime_type or "text/html" in mime_type):
        try:
            return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")
        except Exception:
            return None

    for part in payload.get("parts", []):
        text = extract_body(part)
        if text:
            return text

    return None

@router.post("/gmail/notifications")
async def gmail_notifications(request: Request):
    try:
        raw_data = await request.json()
        if "message" not in raw_data:
            return {"status": "ignored"}
        msg_str = base64.b64decode(raw_data["message"]["data"]).decode("utf-8")
        msg = json.loads(msg_str)
        email_address = msg.get("emailAddress")
        history_id = int(msg.get("historyId", 0))

        if not email_address:
            return {"status": "error", "message": "Missing emailAddress"}
        user = await accounts_col.find_one({"gmail_email": email_address})
        if not user or "refresh_token" not in user:
            # print(f"No refresh_token for {email_address}")
            return {"status": "ignored"}

        last_saved = int(user.get("last_history_id", 0))
        if history_id <= last_saved:
            # print(f"Ignored duplicate webhook historyId={history_id}")
            return {"status": "duplicate"}

        access_token = await get_access_token_from_refresh(user["refresh_token"])
        if not access_token:
            # print(f"Failed to refresh token for {email_address}")
            return {"status": "error"}

        async with httpx.AsyncClient() as client:
            history_resp = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/history",
                params={"startHistoryId": last_saved + 1},
                headers={"Authorization": f"Bearer {access_token}"}
            )
            history_data = history_resp.json()
            history_list = history_data.get("history", [])
            if not history_list:
                await accounts_col.update_one(
                    {"gmail_email": email_address},
                    {"$set": {"last_history_id": history_id}}
                )
                return {"status": "empty"}

            for record in history_list:
                for msg_event in record.get("messages", []):
                    msg_id = msg_event["id"]
                    exists = await messages_col.find_one({
                        "gmail_id": msg_id,
                        "gmail_email": email_address
                    })
                    if exists:
                        print(f"⏩ Already stored msgId={msg_id}")
                        continue
                    msg_resp = await client.get(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=full",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    msg_data = msg_resp.json()

                    headers = msg_data.get("payload", {}).get("headers", [])
                    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
                    sender = next((h["value"] for h in headers if h["name"] == "From"), "")
                    snippet = msg_data.get("snippet", "")
                    body = extract_body(msg_data.get("payload", {})) or snippet

                    if body:
                        body = body.strip()
                        if len(body) > 2000:
                            body = body[:2000]
                            # print("⭐️Truncating BODY");
                            
                    if not sender:
                        continue

                    if not body:
                        continue

                    await messages_col.update_one(
                        {"gmail_id": msg_id, "gmail_email": email_address},
                        {"$set": {
                            "user_id": user["user_id"],
                            "subject": subject,
                            "from": sender,
                            "snippet": snippet,
                            "body": body,
                            "timestamp": int(msg_data.get("internalDate", datetime.now(timezone.utc).timestamp() * 1000)),
                            "spam_prediction": None,  
                            "spam_reasoning": None,
                            "spam_highlighted_text": None,
                            "spam_suggestion": None,
                            "spam_verdict": None,
                        }},
                        upsert=True
                    )
        await accounts_col.update_one(
            {"gmail_email": email_address},
            {"$set": {"last_history_id": history_id}}
        )

        return {"status": "stored"}

    except Exception as e:
        import traceback
        print("Error in gmail_notifications:", str(e))
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

async def retry_failed_predictions():
    while True:

        msg = await messages_col.find_one_and_update(
            {
                "$or": [
                    {"spam_prediction": {"$exists": False}},
                    {"spam_prediction": None},
                    {"spam_prediction": "unknown"}
                ],
            },
            {"$set": {"processing": True}},
            return_document=False
        )
        if not msg:
            await asyncio.sleep(5)
            continue
        try:
            if not msg.get("from"):
                await messages_col.update_one(
                    {"_id": msg["_id"]},
                    {"$set": {"processing": False}}
                )
                continue
            #print(f"Retrying spam prediction for msgId={msg['gmail_id']}")
            req = Spam_request(
                sender=msg["from"],
                subject=msg["subject"],
                text=msg["body"]
            )
            prediction = await get_spam_prediction(req)

            await messages_col.update_one(
                {"_id": msg["_id"]},
                {
                    "$set": {
                        "spam_prediction": prediction.get("confidence"),
                        "spam_reasoning": prediction.get("reasoning"),
                        "spam_highlighted_text": prediction.get("highlighted_text"),
                        "spam_suggestion": prediction.get("suggestion"),
                        "spam_verdict": prediction.get("final_decision"),
                        "processing": False  
                    }
                }
            )
        except Exception as e:
            await messages_col.update_one(
                {"_id": msg["_id"]},
                {"$set": {"processing": False}}  
            )

async def clean_invalid_messages():
    while True:
        try:
            result = await messages_col.delete_many({
                "$or": [
                    {"from": {"$exists": False}},
                    {"from": ""},
                    {"body": {"$exists": False}},
                    {"body": ""},
                ]
            })
        except Exception as e:
            print("Error in clean_invalid_messages:", e)
        await asyncio.sleep(15) 