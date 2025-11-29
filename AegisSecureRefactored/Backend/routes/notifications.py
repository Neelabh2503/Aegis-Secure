import os, json, base64,httpx
import asyncio,traceback
from datetime import datetime, timezone

from database import messages_col, accounts_col
from fastapi import APIRouter, Request
from dotenv import load_dotenv

from utils.access_token_util import get_access_token
from utils.access_token_util import get_access_token as get_access_token_from_refresh
from utils.get_email_utils import extract_body

load_dotenv()
router = APIRouter()
lock = asyncio.Lock()  

API_CALL_INTERVAL = 6 
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
CYBER_SECURE_URI=os.getenv("CYBER_SECURE_API_URI")

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
            return {"status": "ignored"}

        last_saved = int(user.get("last_history_id", 0))
        if history_id <= last_saved:
            return {"status": "duplicate"}

        access_token = await get_access_token(user["refresh_token"])
        if not access_token:
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
                        if len(body) > 3000:
                            body = body[:3000]
                            
                    if not sender:
                        continue
                    if not body:
                        continue

                    user_id_str = user["user_id"]
                    await messages_col.update_one(
                        {"gmail_id": msg_id, "gmail_email": email_address},
                        {"$set": {
                            "user_id": user_id_str,
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
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
