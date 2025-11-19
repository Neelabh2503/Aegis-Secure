from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from datetime import datetime
from dotenv import load_dotenv
from .auth import get_current_user
from database import sms_messages_col
from websocket_manager import broadcast_new_sms
import hashlib
import os
from bson import ObjectId
import asyncio

from routes.notifications import get_spam_prediction

router = APIRouter()
load_dotenv()


class SpamRequest(BaseModel):
    sender: str
    subject: str
    text: str


class SmsMessage(BaseModel):
    address: str
    body: str
    date_ms: int
    type: str

class SmsSyncRequest(BaseModel):
    messages: List[SmsMessage]


def generate_message_hash(address: str, body: str, date_ms: int):
    text = f"{address}-{body}-{date_ms}"
    return hashlib.sha256(text.encode()).hexdigest()

def convert_doc(doc):
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    if isinstance(doc, dict):
        return {k: convert_doc(v) for k, v in doc.items()}
    if isinstance(doc, list):
        return [convert_doc(i) for i in doc]
    return doc

@router.get("/all")
async def get_all_sms(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")

    messages = await sms_messages_col.find({"user_id": user_id}).sort("timestamp", -1).to_list(200)
    safe_messages = [convert_doc(m) for m in messages]

    return {"sms_messages": safe_messages}



@router.post("/sync")
async def sync_sms(request: SmsSyncRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    inserted_count = 0
    for msg in request.messages:
        msg_hash = generate_message_hash(msg.address, msg.body, msg.date_ms)

        existing = await sms_messages_col.find_one({"hash": msg_hash, "user_id": user_id})
        if existing:
            continue

        message_doc = {
            "user_id": user_id,
            "address": msg.address,
            "body": msg.body,
            "timestamp": msg.date_ms,
            "type": msg.type,
            "hash": msg_hash,
            "spam_score": None,
            "spam_reasoning": None,
            "spam_highlighted_text": None,
            "spam_suggestion": None,
            "spam_verdict": None,
            "created_at": datetime.utcnow()
        }

        inserted = await sms_messages_col.insert_one(message_doc)
        message_doc["_id"] = inserted.inserted_id
        inserted_count += 1
    return {
        "status": "success",
        "inserted": inserted_count,
        "user_id": user_id,
    }


async def retry_failed_sms_predictions():
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
                req = SpamRequest(sender=sms["address"], subject="", text=sms["body"])
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
                print(f"Failed retry for SMS {_id}: {e}")
        await asyncio.sleep(60) 
