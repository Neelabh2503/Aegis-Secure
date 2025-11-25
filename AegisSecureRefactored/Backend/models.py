from pydantic import BaseModel,EmailStr
from typing import List

class RegisterRequest(BaseModel):
    name:str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    verified: bool


class SendOTPRequest(BaseModel):
    email: EmailStr


class UserResponse(BaseModel):
    name: str
    email: str
    user_id: str

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str
    confirm_password: str

class Spam_request(BaseModel):
    sender: str
    subject: str
    text: str


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