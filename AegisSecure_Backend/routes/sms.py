from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import jwt
import os
from dotenv import load_dotenv
from .auth import get_current_user

router = APIRouter()

class SmsMessage(BaseModel):
    address: str
    body: str
    date_ms: int 
    type: str

class SmsSyncRequest(BaseModel):

    messages: List[SmsMessage]


@router.post("/sync")
async def sync_sms(
    request: SmsSyncRequest,

    current_user: dict = Depends(get_current_user)
):
    
    user_id = current_user.get("user_id")
    message_count = len(request.messages)

    print(f"SMS SYNC SUCCESS: Received {message_count} messages for user {user_id}")

    return {
        "status": "success",
        "message": f"Successfully processed {message_count} messages.",
        "user_id": user_id
    }

