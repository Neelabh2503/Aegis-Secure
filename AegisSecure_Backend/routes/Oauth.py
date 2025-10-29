from fastapi import APIRouter, HTTPException, Request
import httpx
from database import messages_col, accounts_col
import os
from jose import jwt
from dotenv import load_dotenv
from .notifications import get_spam_prediction
from datetime import datetime
from websocket_manager import broadcast_new_email
import base64, json

load_dotenv()
router = APIRouter()


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
JWT_SECRET = os.getenv("JWT_SECRET")

if not JWT_SECRET:
    raise Exception("JWT_SECRET is not set in .env")


async def get_access_token_from_refresh(refresh_token: str):
    """Get a new Google access token using the refresh token."""
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


@router.get("/gmail/refresh")
async def refresh_access_token(user_id: str, gmail_email: str):
    user_data = await accounts_col.find_one({"user_id": user_id, "gmail_email": gmail_email})
    if not user_data or "refresh_token" not in user_data:
        raise HTTPException(status_code=400, detail="No refresh token found")

    refresh_token = user_data["refresh_token"]
    access_token = await get_access_token_from_refresh(refresh_token)
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to refresh access token")

    return {"access_token": access_token}


@router.get("/google/callback")
async def google_callback(code: str, state: str = None):
    if not state:
        raise HTTPException(status_code=400, detail="Missing user state token")
    
    # Decode JWT to get user_id
    try:
        payload = jwt.decode(state, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid JWT token")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JWT token: {e}")

    async with httpx.AsyncClient() as client:
        # Get access & refresh tokens
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code"
            }
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")


        profile_resp = await client.get(
            "https://www.googleapis.com/gmail/v1/users/me/profile",
            headers={"Authorization": f"Bearer {access_token}"})
        gmail_email = profile_resp.json().get("emailAddress")

    
        if refresh_token:
            await accounts_col.update_one(
                {"user_id": user_id, "gmail_email": gmail_email},
                {"$set": {"refresh_token": refresh_token}},
                upsert=True)
        else:
            await accounts_col.update_one(
                {"user_id": user_id, "gmail_email": gmail_email},
                {
                    "$setOnInsert": {"connected_at": datetime.utcnow()},
                },
                upsert=True,
            )


        messages_resp = await client.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=10",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        messages_list = messages_resp.json().get("messages", [])
        emails = []

        for msg in messages_list:
            msg_id = msg["id"]
            msg_resp = await client.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=full",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            msg_data = msg_resp.json()
            subject = next((h["value"] for h in msg_data["payload"]["headers"] if h["name"] == "Subject"), "")
            sender = next((h["value"] for h in msg_data["payload"]["headers"] if h["name"] == "From"), "")
            snippet = msg_data.get("snippet", "")
            combined_text = f"{subject} {snippet}"
            spam_prediction = await get_spam_prediction(combined_text)

            emails.append({
                "gmail_id": msg_id,
                "gmail_email": gmail_email,
                "user_id": user_id,
                "subject": next((h["value"] for h in msg_data["payload"]["headers"] if h["name"]=="Subject"), ""),
                "from": next((h["value"] for h in msg_data["payload"]["headers"] if h["name"]=="From"), ""),
                "snippet": msg_data.get("snippet", ""),
                "timestamp": int(msg_data["internalDate"]),
                "spam_prediction": spam_prediction, 
            })

        
        for email in emails:
            await messages_col.update_one(
                {"user_id": user_id, "gmail_email": gmail_email, "gmail_id": email["gmail_id"]},
                {"$set": email},
                upsert=True
            )

        topic_name = "projects/emailfetchingcheckandlearn/topics/AegisSecureMails"
        watch_resp = await client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/watch",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"topicName": topic_name, "labelIds": ["INBOX"]}
        )
        watch_data = watch_resp.json()
        if "historyId" in watch_data:
            await messages_col.update_one(
                {"user_id": user_id, "gmail_email": gmail_email},
                {"$set": {"last_history_id": watch_data["historyId"]}}
            )

    return {
        "status": "success",
        "fetched": len(emails),
        "gmail_email": gmail_email,
        "watch_status": "started"
    }