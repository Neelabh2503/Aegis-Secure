import uuid,base64,os,datetime
import jwt

from fastapi import APIRouter, HTTPException,Depends,File, UploadFile, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

import models
from database import users_col ,otps_col

from utils.password_utils import hash_password,verify_password
from utils.otp_utils import generate_otp,store_otp,send_otp,verify_otp_in_db
from utils.jwt_utils import decode_jwt,create_reset_jwt

#Load The env variables and defien router
load_dotenv()
router = APIRouter()
security = HTTPBearer()
RESET_JWT_TTL_MINUTES = int(os.getenv("RESET_JWT_TTL_MINUTES", "15"))
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")  
JWT_ALGORITHM="HS256"


#Routes with prefix auth
@router.post("/register")
async def register_user(req: models.RegisterRequest):
    existing = await users_col.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(req.password)
    user_doc = {
        "name": req.name,
        "email": req.email,
        "password": hashed_password,
        "verified": False,
        "user_id" : str(uuid.uuid4()),
        "avatar_base64": "",
    }
    await users_col.insert_one(user_doc)
    otp_code =generate_otp()
    await store_otp(req.email, otp_code)
    await send_otp(req.email, otp_code)



@router.post("/login", response_model=models.LoginResponse)
async def login_user(req: models.LoginRequest):
    user = await users_col.find_one({"email": req.email})
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    if not verify_password(req.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    payload = {
        "email": user["email"],
        "user_id": str(user["user_id"]),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"token": token,"verified": user.get("verified", False)}


#Routes for OTP send aaand verification during Registeration as well as password change
#Prefix is auth
@router.post("/send-otp")
async def send_otp_router(req: models.SendOTPRequest):
    user = await users_col.find_one({"email": req.email})
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    otp_code = generate_otp()
    await store_otp(req.email, otp_code)
    await send_otp(req.email, otp_code)


@router.post("/verify-otp")
async def verify_otp(req: models.VerifyOTPRequest):
    try:
        is_valid = await verify_otp_in_db(req.email, req.otp)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")

        await users_col.update_one({"email": req.email}, {"$set": {"verified": True}})
        await otps_col.delete_many({"email": req.email})
        return {"message": "OTP verified successfully, user is now verified."}

    except Exception as e:
        print(f"Exception during OTP verify: {e}")
        raise


#Routes with prefix auth and these routes are for fetching user Information
@router.get("/me")
async def get_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    decoded = decode_jwt(token)
    user = await users_col.find_one({"email": decoded["email"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "name": user["name"],
        "email": user["email"],
        "verified": user.get("verified", False),
        "avatar_base64": user.get("avatar_base64", ""),
    }

@router.post("/me/avatar")
async def upload_avatar(credentials: HTTPAuthorizationCredentials = Depends(security), file: UploadFile = File(...)):
    token = credentials.credentials
    decoded = decode_jwt(token)
    user = await users_col.find_one({"email": decoded["email"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    contents = await file.read()
    avatar_base64 = base64.b64encode(contents).decode('utf-8')
    
    await users_col.update_one(
        {"email": decoded["email"]},
        {"$set": {"avatar_base64": avatar_base64}}
    )
    return JSONResponse({"avatar_base64": avatar_base64})




async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = decode_jwt(token)
        email: str = payload.get("email")
        if email is None:
            raise HTTPException(status_code=403, detail="Invalid token payload")

        user = await users_col.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        user["user_id"] = str(user["user_id"])
        return user
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="JWT Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid JWT token")
    



#Routes with auth prefix 
@router.post("/forgot-password")
async def forgot_password(req: models.SendOTPRequest):
    email = req.email.lower()
    user = await users_col.find_one({"email": email})
    if user:
        otp_code =generate_otp()
        await store_otp(email, otp_code)
        await send_otp(email, otp_code)

@router.post("/verify-reset-otp")
async def verify_reset_otp(req: models.VerifyOTPRequest):
    email = req.email.lower()
    is_valid = await verify_otp_in_db(email, req.otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    reset_token = create_reset_jwt(email)
    return {"reset_token": reset_token, "expires_in_minutes": RESET_JWT_TTL_MINUTES}


@router.post("/reset-password")
async def reset_password(data: dict):
    email = data.get("email")
    otp = data.get("otp")
    new_password = data.get("new_password")

    if not all([email, otp, new_password]):
        raise HTTPException(status_code=400, detail="Missing fields")

    otp_doc = await otps_col.find_one({"email": email, "otp": otp})
    if not otp_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    hashed_pw = hash_password(new_password)
    result = await users_col.update_one(
        {"email": email},
        {"$set": {"password": hashed_pw}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    await otps_col.delete_many({"email": email})
    return {"message": "Password updated successfully"}