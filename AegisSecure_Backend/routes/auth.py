from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import jwt
import os
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
from typing import Optional
import datetime

from database import users_col, auth_db, otps_col
from routes import otp
from config import settings, StatusMessages
from errors import (
    AuthenticationError, ValidationError, ResourceNotFoundError,
    DuplicateResourceError, TokenError, OTPError
)
from validators import PasswordValidator, EmailValidator, OTPValidator
from logger import logger, log_auth_attempt, log_otp_event, log_user_action

security = HTTPBearer()
router = APIRouter()

# Use settings from config instead of hardcoded values
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class VerifyResetOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str
    confirm_password: str

class UserResponse(BaseModel):
    name: str
    email: str
    user_id: str



def create_reset_jwt(email: str) -> str:
    """Create a short-lived JWT for password reset."""
    exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.RESET_JWT_TTL_MINUTES)
    payload = {"sub": email, "purpose": "password_reset", "exp": exp}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token

def decode_reset_jwt(token: str) -> dict:
    """Decode and validate reset JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("purpose") != "password_reset":
            raise TokenError("Invalid token purpose")
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenError("Reset token expired")
    except jwt.InvalidTokenError:
        raise TokenError("Invalid reset token")

#--⭐️

    
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(req: RegisterRequest):
    """
    Register a new user with email verification.
    Validates password strength and sends OTP for verification.
    """
    try:
        # Normalize email
        email = req.email.lower().strip()
        
        # Validate password strength
        PasswordValidator.validate_or_raise(req.password)
        
        # Check if user already exists
        existing = await users_col.find_one({"email": email})
        if existing:
            log_auth_attempt(email, False, "Email already registered")
            raise DuplicateResourceError("User", details={"email": email})
        
        # Hash password
        hashed_password = pwd_context.hash(req.password)
        
        # Create user document
        user_doc = {
            "name": req.name.strip(),
            "email": email,
            "password": hashed_password,
            "verified": False,
            "user_id": str(datetime.datetime.now().timestamp()),
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }
        
        result = await users_col.insert_one(user_doc)
        logger.info(f"✅ New user registered: {email}")
        
        # Generate and send OTP
        otp_code = otp.generate_otp()
        await otp.store_otp(email, otp_code)
        sent = await otp.send_otp_email_async(email, otp_code)
        
        log_otp_event(email, "generated", success=True)
        
        if sent:
            return {
                "message": StatusMessages.REGISTRATION_SUCCESS,
                "email": email,
                "otp_sent": True
            }
        else:
            # Development mode - include OTP in response
            if settings.DEBUG:
                return {
                    "message": StatusMessages.REGISTRATION_SUCCESS,
                    "email": email,
                    "otp": otp_code,
                    "otp_sent": False
                }
            return {
                "message": StatusMessages.REGISTRATION_SUCCESS,
                "email": email,
                "otp_sent": False
            }
    
    except (DuplicateResourceError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Registration error for {req.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=StatusMessages.INTERNAL_ERROR
        )

@router.post("/login", response_model=LoginResponse)
async def login_user(req: LoginRequest):
    """
    Authenticate user and return JWT token.
    Returns generic error messages to prevent user enumeration.
    """
    try:
        # Normalize email
        email = req.email.lower().strip()
        
        # Find user
        user = await users_col.find_one({"email": email})
        
        # Use generic error message to prevent user enumeration
        if not user:
            log_auth_attempt(email, False, "User not found")
            raise AuthenticationError(StatusMessages.INVALID_CREDENTIALS)
        
        # Verify password
        if not pwd_context.verify(req.password, user["password"]):
            log_auth_attempt(email, False, "Incorrect password")
            raise AuthenticationError(StatusMessages.INVALID_CREDENTIALS)
        
        # Create JWT token
        payload = {
            "email": user["email"],
            "user_id": str(user["_id"]),
            "iat": datetime.datetime.utcnow(),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(
                hours=settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS
            )
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        
        # Log successful login
        log_auth_attempt(email, True)
        log_user_action(str(user["_id"]), "login", {"email": email})
        
        return {
            "token": token,
            "verified": user.get("verified", False)
        }
    
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=StatusMessages.INTERNAL_ERROR
        )

@router.post("/send-otp")
async def send_otp(req: SendOTPRequest):
    """Send OTP to user's email for verification."""
    try:
        email = req.email.lower().strip()
        
        user = await users_col.find_one({"email": email})
        if not user:
            raise ResourceNotFoundError("User")
        
        # Generate and store OTP
        otp_code = otp.generate_otp()
        await otp.store_otp(email, otp_code)
        
        # Send OTP email
        sent = await otp.send_otp_email_async(email, otp_code)
        
        log_otp_event(email, "sent", success=sent)
        
        if sent:
            return {"message": StatusMessages.OTP_SENT}
        else:
            # Development mode - include OTP in response
            if settings.DEBUG:
                return {
                    "message": "OTP generated (dev mode)",
                    "otp": otp_code
                }
            return {"message": StatusMessages.OTP_SENT}
    
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Send OTP error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=StatusMessages.INTERNAL_ERROR
        )

@router.post("/verify-otp")
async def verify_otp_endpoint(req: VerifyOTPRequest):
    """
    Verify OTP and mark user as verified.
    Validates OTP format before checking database.
    """
    try:
        email = req.email.lower().strip()
        
        # Validate OTP format
        OTPValidator.validate_or_raise(req.otp)
        
        # Verify OTP in database
        is_valid = await otp.verify_otp_in_db(email, req.otp)
        
        if not is_valid:
            log_otp_event(email, "verification failed", success=False)
            raise OTPError(StatusMessages.INVALID_OTP)

        # Mark user as verified
        result = await users_col.update_one(
            {"email": email},
            {
                "$set": {
                    "verified": True,
                    "verified_at": datetime.datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            logger.warning(f"User {email} not found during OTP verification")
        
        log_otp_event(email, "verified", success=True)
        logger.info(f"✅ User {email} marked as verified")

        return {"message": StatusMessages.OTP_VERIFIED}

    except (OTPError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=StatusMessages.INTERNAL_ERROR
        )


def decode_jwt(token: str) -> dict:
    """Decode and validate JWT token."""
    try:
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return decoded
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise TokenError("Token expired")
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        raise TokenError("Invalid token")


@router.get("/me")
async def get_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Returns the name and email of the logged-in user."""
    token = credentials.credentials
    decoded = decode_jwt(token)
    user = await users_col.find_one({"email": decoded["email"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "name": user["name"],
        "email": user["email"],
        "verified": user.get("verified", False),
    }



async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get the current authenticated user from JWT token.
    Use this in route dependencies to require authentication.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        email: str = payload.get("email")
        if email is None:
            raise TokenError("Invalid token payload")

        user = await users_col.find_one({"email": email})
        if user is None:
            raise ResourceNotFoundError("User")

        user["user_id"] = str(user["_id"])
        return user
    
    except jwt.ExpiredSignatureError:
        raise TokenError("Token has expired")
    except jwt.InvalidTokenError:
        raise TokenError("Invalid token")
    except (TokenError, ResourceNotFoundError):
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=StatusMessages.INTERNAL_ERROR
        )
    

    
@router.post("/forgot-password")
async def forgot_password(req: SendOTPRequest):
    """Generate OTP and send to user's email if the user exists.
    Returns a generic message regardless of whether the email exists
    (to avoid user enumeration)."""
    email = req.email.lower()
    user = await users_col.find_one({"email": email})
    if user:
        otp_code = otp.generate_otp()
        await otp.store_otp(email, otp_code)
        sent = await otp.send_otp_email_async(email, otp_code)
        if sent:
            return {"message": "If this email is registered, an OTP has been sent."}
        else:
            print(f"[DEV] OTP for {email}: {otp_code}")
            return {"message": "If this email is registered, an OTP has been sent."}
    return {"message": "If this email is registered, an OTP has been sent."}

@router.post("/verify-reset-otp")
async def verify_reset_otp(req: VerifyResetOTPRequest):
    """Verify OTP for password reset. If valid, return a short-lived reset token."""
    email = req.email.lower()
    is_valid = await otp.verify_otp_in_db(email, req.otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    reset_token = create_reset_jwt(email)
    return {"reset_token": reset_token, "expires_in_minutes": settings.RESET_JWT_TTL_MINUTES}


@router.post("/reset-password")
async def reset_password(data: dict):
    """
    Reset password using OTP verification.
    Validates new password strength before updating.
    """
    try:
        email = data.get("email")
        otp_code = data.get("otp")
        new_password = data.get("new_password")

        # Validate required fields
        if not all([email, otp_code, new_password]):
            raise ValidationError("Missing required fields: email, otp, new_password")
        
        # Normalize email
        email = email.lower().strip()
        
        # Validate OTP format
        OTPValidator.validate_or_raise(otp_code)
        
        # Validate new password strength
        PasswordValidator.validate_or_raise(new_password)
        
        # Verify OTP
        otp_doc = await otps_col.find_one({"email": email, "otp": otp_code})
        if not otp_doc:
            log_otp_event(email, "verification failed", success=False)
            raise OTPError(StatusMessages.INVALID_OTP)

        # Hash new password
        hashed_pw = pwd_context.hash(new_password)
        
        # Update password
        result = await users_col.update_one(
            {"email": email},
            {
                "$set": {
                    "password": hashed_pw,
                    "updated_at": datetime.datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise ResourceNotFoundError("User")
        
        # Clean up all OTPs for this email
        await otps_col.delete_many({"email": email})
        
        logger.info(f"✅ Password reset successful for: {email}")
        log_user_action(email, "password_reset", {"email": email})
        
        return {"message": StatusMessages.PASSWORD_RESET_SUCCESS}
    
    except (ValidationError, OTPError, ResourceNotFoundError):
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=StatusMessages.INTERNAL_ERROR
        )