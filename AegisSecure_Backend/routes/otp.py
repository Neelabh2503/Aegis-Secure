import os
import asyncio
import random
import datetime
import base64
from email.mime.text import MIMEText

import httpx
from dotenv import load_dotenv
load_dotenv()

from database import auth_db


OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", "10"))
otp_col = auth_db.otps

SMTP_EMAIL = os.getenv("SMTP_EMAIL")  
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN") 
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

async def get_access_token_from_refresh(refresh_token: str) -> str:

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


async def send_gmail_email(access_token: str, to_email: str, subject: str, body: str):
    message = MIMEText(body, "html")
    message["to"] = to_email
    message["from"] = SMTP_EMAIL
    message["subject"] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json={"raw": raw_message}
        )
        if resp.status_code != 200:
            raise Exception(f"Failed to send email: {resp.text}")
        return resp.json()


def generate_otp() -> str:
    """6-digit OTP as string"""
    return str(random.randint(100000, 999999)).zfill(6)


async def send_otp_email_async(to_email: str, otp: str) -> bool:
    """Send OTP email via Gmail API."""
    html_body = f"""
    <html>
      <body style='font-family: Arial, sans-serif;'>
        <h2>AegisSecure — Verification Code</h2>
        <p>Your verification code is:</p>
        <h1 style='letter-spacing:6px'>{otp}</h1>
        <p>This code will expire in {OTP_EXPIRE_MINUTES} minutes.</p>
      </body>
    </html>
    """

    try:
        access_token = await get_access_token_from_refresh(REFRESH_TOKEN)
        if not access_token:
            print("[DEBUG] Failed to get access token")
            return False
        await send_gmail_email(access_token, to_email, "AegisSecure OTP", html_body)
        print(f"[DEBUG] OTP sent via Gmail API to {to_email}")
        return True
    except Exception as e:
        print("❌ Failed to send OTP via Gmail API:", e)
        # print(f"[DEV OTP] {to_email} -> {otp}")
        return False


async def store_otp(email: str, otp: str):
    """Store OTP in DB and remove previous ones"""
    await otp_col.delete_many({"email": email})
    doc = {
        "email": email,
        "otp": otp,
        "created_at": datetime.datetime.utcnow(),
        "expires_at": datetime.datetime.utcnow() + datetime.timedelta(minutes=OTP_EXPIRE_MINUTES),
        "verified": False,
    }
    await otp_col.insert_one(doc)


async def verify_otp_in_db(email: str, otp: str) -> bool:
    email = email.lower()
    otp = str(otp).zfill(6)
    doc = await otp_col.find_one({
        "email": email,
        "otp": otp,
        "verified": False,
        "expires_at": {"$gt": datetime.datetime.utcnow()}
    })
    if doc:
        await otp_col.update_one({"_id": doc["_id"]}, {"$set": {"verified": True}})
        return True
    return False


async def ensure_otp_indexes():
    """Create indexes for OTP collection"""
    await otp_col.create_index("email")
    await otp_col.create_index("expires_at", expireAfterSeconds=0)
