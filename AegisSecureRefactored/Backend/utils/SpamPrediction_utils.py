import os,asyncio,httpx
from fastapi import APIRouter

import models
from database import sms_messages_col,messages_col

from dotenv import load_dotenv
router = APIRouter()
load_dotenv()

CYBER_SECURE_URI=os.getenv("CYBER_SECURE_API_URI")



def format_score(value):
    try:
        num = float(value)
        return f"{num:.2f}"
    except:
        return value
    
async def get_spam_prediction(req:models.Spam_request):
    try:
        async with httpx.AsyncClient() as client:
            sender=req.sender
            subject=req.subject
            body=req.text
            payload = {
                "sender": sender,
                "subject": subject,
                "text": body
            }
            resp = await client.post(
                CYBER_SECURE_URI,
                json=payload,
                timeout=30.0
            )
            resp.raise_for_status()

            data = resp.json()
            if isinstance(data, dict):
                if "confidence" in data:
                    data["confidence"] = format_score(data["confidence"])
                return data
            
            return {"confidence": format_score(data), "reasoning": None}

    except Exception as e:
        return {
            "confidence": "unknown",
            "reasoning": None,
            "highlighted_text": None,
            "suggestion": None,
            "final_decision": "unknown"
        }


async def retry_email_SpamPrediction():
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
            req = models.Spam_request(
                sender=msg["from"],
                subject=msg["subject"],
                text=msg["body"]
            )
            # print("Predicting")
            prediction = await get_spam_prediction(req)
            # print("got")
            # print(prediction)
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


async def retry_sms_SpamPrediction():
    while True:
        cursor = sms_messages_col.find({
            "$or": [
                {"spam_verdict": {"$exists": False}},
                {"spam_verdict": None},
                {"spam_verdict": "unknown"}
            ]
        })

        async for sms in cursor:
            try:
                req = models.SpamRequest(sender=sms["address"], subject="", text=sms["body"])
                prediction = await get_spam_prediction(req)
                await sms_messages_col.update_one(
                    {"_id": sms["_id"], "spam_verdict": {"$in": [None, "unknown"]}},
                    {"$set": {
                        "spam_score": prediction.get("confidence"),
                        "spam_reasoning": prediction.get("reasoning"),
                        "spam_highlighted_text": prediction.get("highlighted_text"),
                        "spam_suggestion": prediction.get("suggestion"),
                        "spam_verdict": prediction.get("final_decision"),
                    }}
                )
            except Exception as e:
                print(f"Failed retry for SMS {sms.get('_id')}: {e}")



#this function is to remove invalid messages which are presen in the DB.
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