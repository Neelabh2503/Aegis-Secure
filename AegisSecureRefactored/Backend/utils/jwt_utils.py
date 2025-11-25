import os,jwt
from dotenv import load_dotenv
from datetime import datetime

from fastapi import HTTPException

load_dotenv()


JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")  
JWT_ALGORITHM="HS256"
RESET_JWT_TTL_MINUTES = int(os.getenv("RESET_JWT_TTL_MINUTES", "15"))



def create_reset_jwt(email: str) -> str:
    exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=RESET_JWT_TTL_MINUTES)
    payload = {"sub": email, "purpose": "password_reset", "exp": exp}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_reset_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("purpose") != "password_reset":
            raise HTTPException(status_code=401, detail="Invalid token purpose")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Reset token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid reset token")
    

def decode_jwt(token: str):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")