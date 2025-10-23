# routes/auth.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
import os
from dotenv import load_dotenv
import datetime

load_dotenv()
from database import users_col 

router = APIRouter()
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")  
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str


@router.post("/register")
async def register_user(req: RegisterRequest):
    # Check if email is already registered
    existing = await users_col.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password before storing
    hashed_password = pwd_context.hash(req.password)
    
    # Prepare user document
    user_doc = {
        "name": req.name,
        "email": req.email,
        "password": hashed_password,
        "verified": False,
        "user_id": str(datetime.datetime.now().timestamp())
    }
    
    await users_col.insert_one(user_doc)
    return {"message": "User registered. OTP verification pending."}


@router.post("/login", response_model=LoginResponse)
async def login_user(req: LoginRequest):
    # Find user by email
    user = await users_col.find_one({"email": req.email})
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    # Verify password
    if not pwd_context.verify(req.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    # Create JWT token valid for 12 hours
    payload = {
        "email": user["email"],
        "user_id": str(user["_id"]),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    return {"token": token}
