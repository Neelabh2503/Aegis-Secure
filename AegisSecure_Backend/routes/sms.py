# routes/sms.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import jwt
import os
from dotenv import load_dotenv


from .auth import get_current_user

router = APIRouter()

# Pydantic Models

class SmsMessage(BaseModel):
    """Model for a single SMS message coming from the Flutter app."""
    address: str
    body: str
    date_ms: int # Date in milliseconds
    type: str # 'inbox' or 'sent'

class SmsSyncRequest(BaseModel):
    """Model for the list of SMS messages sent in the request body."""
    messages: List[SmsMessage]

#  Endpoint to receive and process SMS data

@router.post("/sync")
async def sync_sms(
    request: SmsSyncRequest,

    current_user: dict = Depends(get_current_user)
):
    """
    Receives a batch of SMS messages from the client, validates them,
    and returns a success message. Placeholder for actual processing (e.g., saving to DB, analysis).
    """
    user_id = current_user.get("user_id")
    message_count = len(request.messages)


    # In a real app
    # 1. Save these messages to a dedicated 'sms_collection' in MongoDB.
    # 2. messages already synced?
    # 3. Queue them for analysis (e.g., check for phishing/spam).


    print(f"SMS SYNC SUCCESS: Received {message_count} messages for user {user_id}")

    return {
        "status": "success",
        "message": f"Successfully processed {message_count} messages.",
        "user_id": user_id
    }

# The full path this route creates is: (prefix) + /sync
#  Must make sure , main.py file includes the prefix '/sms'
