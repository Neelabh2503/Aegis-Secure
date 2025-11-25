import os,time,re
from jose import jwt


from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer


from database import messages_col, accounts_col,avatars_col
from utils.user_info_utils import get_current_user_id


router = APIRouter()
JWT_SECRET = os.getenv("JWT_SECRET", "your_secret_key")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


#route to fetch the state-token
@router.get("/gmail/state-token")
def get_state_token(user_id: str):
    payload = {
        "user_id": user_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 300  
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"state": token}


#This route fetches all the emails of the current user form the DB
@router.get("/emails")
async def get_emails(
    user_id: str = Depends(get_current_user_id),
    account: str | None = None,
):
    try:
        query = {"user_id": user_id}
        if account:
            query["gmail_email"] = account  

        emails_cursor = messages_col.find(query, {"_id": 0})
        emails = await emails_cursor.to_list(length=None)

        for e in emails:
            if "timestamp" in e:
                e["timestamp"] = int(e["timestamp"])
            elif "date" in e:
                e["timestamp"] = int(e.pop("date", 0))
            else:
                e["timestamp"] = 0

        for e in emails:
            sender_field = e.get("from", "")
            match = re.search(r"<(.+?)>", sender_field)
            sender_email = match.group(1) if match else sender_field
            avatar_doc = await avatars_col.find_one({"email": sender_email})
            e["char_color"] = avatar_doc.get("char_color") if avatar_doc else "#90A4AE"
        emails_sorted = sorted(emails, key=lambda e: e.get("timestamp", 0), reverse=True)
        return emails_sorted

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#To get the name,gmail_email of the current user
@router.get("/user/me")
async def get_current_user(user_id: str):
    user = await accounts_col.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"name": user.get("name", "User"), "gmail_email": user.get("gmail_email")}


#to get the connected/linked accounts of the current user
@router.get("/gmail/accounts")
async def get_connected_accounts(user_id: str = Depends(get_current_user_id)):
    try:
        accounts_cursor = accounts_col.find(
            {"user_id": user_id},
            {"_id": 0, "gmail_email": 1, "connected_at": 1}
        )
        accounts = await accounts_cursor.to_list(length=None)
        return {"accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

#to delete a particular account of the current user
@router.post("/accounts/delete")
async def delete_connected_account(
    payload: dict,
    user_id: str = Depends(get_current_user_id)
):
    gmail_email = payload.get("gmail_email")
    if not gmail_email:
        raise HTTPException(status_code=400, detail="Missing gmail_email")

    result = await accounts_col.delete_one(
        {"user_id": user_id, "gmail_email": gmail_email}
    )
    msg_result = await messages_col.delete_many(
        {"user_id": user_id, "gmail_email": gmail_email}
    )

    if result.deleted_count == 0 or msg_result==0:
        raise HTTPException(status_code=404, detail="Account not found")

    return {"message": "Account deleted successfully"}
