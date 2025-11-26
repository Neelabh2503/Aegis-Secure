import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from config import settings
from database import auth_db, mail_db, sms_db
from utils.SpamPrediction_utils import (
    retry_email_SpamPrediction,
    retry_sms_SpamPrediction
)

from routes import (
    auth,
    gmail,
    Oauth,
    notifications,
    sms,
    dashboard
)

from middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlerMiddleware
)

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Starting Aegis Backend...")

    if os.environ.get("UVICORN_RELOADER") != "true":
        print("Starting spam prediction retry loops...")
        asyncio.create_task(retry_email_SpamPrediction())
        asyncio.create_task(retry_sms_SpamPrediction())

    print("Creating indexes...")
    await auth_db.users.create_index("email", unique=True)
    await auth_db.otps.create_index("email")

    await mail_db.accounts.create_index("user_id")
    await mail_db.accounts.create_index([("user_id", 1), ("gmail_email", 1)],unique=True)

    await mail_db.messages.create_index([("user_id", 1), ("gmail_email", 1), ("timestamp", -1)])
    await mail_db.messages.create_index("gmail_id")
    await mail_db.messages.create_index("from_email")
    await mail_db.messages.create_index("subject")

    await mail_db.avatars.create_index("email")
    await sms_db.sms_messages.create_index([("user_id", 1), ("timestamp", -1)])
    await sms_db.sms_messages.create_index([("user_id", 1), ("hash", 1)],unique=True)
    await sms_db.sms_messages.create_index("address")

    print("All indexes created")

    yield

    print("Shutting down Aegis Backend...")


app = FastAPI(
    title=getattr(settings, "APP_NAME", "Aegis Backend"),
    version=getattr(settings, "APP_VERSION", "1.0.0"),
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "CORS_ORIGINS", ["*"]),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(gmail.router, tags=["Gmail"])
app.include_router(Oauth.router, prefix="/auth", tags=["OAuth"])
app.include_router(notifications.router, tags=["Notifications"])
app.include_router(sms.router, prefix="/sms", tags=["SMS"])
app.include_router(dashboard.router, tags=["Dashboard"])

ws_router = APIRouter()

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "service": getattr(settings, "APP_NAME", "Aegis Backend")
    }