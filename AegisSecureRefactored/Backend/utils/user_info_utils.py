from jose import JWTError
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from utils.jwt_utils import decode_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user_id(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_jwt(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token missing user_id")
        return user_id
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")