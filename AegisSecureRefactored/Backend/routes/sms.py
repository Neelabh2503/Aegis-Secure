import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends

import models
from database import sms_messages_col
from routes.auth import get_current_user

from utils.format_utils import convert_doc,generate_message_hash

from dotenv import load_dotenv
router = APIRouter()
load_dotenv()

@router.get("/all")
async def get_all_sms(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    messages = await sms_messages_col.find({"user_id": user_id}).sort("timestamp", -1).to_list(200)
    safe_messages = [convert_doc(m) for m in messages]
    return {"sms_messages": safe_messages}

@router.post("/sync")
async def sync_sms(request: models.SmsSyncRequest, current_user: dict = Depends(get_current_user)):
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
    
    return {"status": "success", "inserted": inserted_count}
