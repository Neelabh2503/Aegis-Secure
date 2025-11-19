from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import asyncio

from config import settings
from database import avatars_col
from websocket_manager import connect, disconnect, active_connections, broadcast_new_email
from routes import auth, gmail, Oauth, notifications, otp, sms, analysis
from middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlerMiddleware
)
from errors import AegisException, handle_exception
from logger import logger, log_startup_message, log_shutdown_message
from db_utils import db_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown events."""
    # Startup
    log_startup_message()
    
    # Validate configuration
    config_errors = settings.validate()
    if config_errors:
        logger.error("Configuration errors found:")
        for error in config_errors:
            logger.error(f"  - {error}")
        logger.warning("Some features may not work correctly!")
    else:
        logger.info("✅ Configuration validated successfully")
    
    # Connect to database
    try:
        await db_manager.connect()
        logger.info("✅ Database connection established")
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {str(e)}")
    
    # Create database indexes
    try:
        await avatars_col.create_index("email", unique=True)
        logger.info("✅ Database indexes created")
    except Exception as e:
        logger.warning(f"⚠️ Index creation warning: {str(e)}")
    
    # Start background cleanup task
    from routes.notifications import clean_invalid_messages
    cleanup_task = asyncio.create_task(clean_invalid_messages())
    logger.info("✅ Background cleanup task started")
    
    settings.print_config_summary()
    
    yield  # Application runs here
    
    # Shutdown
    log_shutdown_message()
    cleanup_task.cancel()
    await db_manager.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Secure phishing detection and email/SMS analysis API",
    lifespan=lifespan
)

# Add middleware (order matters - first added is outermost)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Exception handlers
@app.exception_handler(AegisException)
async def aegis_exception_handler(request: Request, exc: AegisException):
    """Handle custom AegisException errors."""
    return handle_exception(exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Validation error",
            "details": exc.errors()
        }
    )


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(gmail.router, prefix="/gmail", tags=["Gmail"])
app.include_router(Oauth.router, prefix="/oauth", tags=["OAuth"])
app.include_router(Oauth.router, prefix="/auth", tags=["OAuth"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
app.include_router(sms.router, prefix="/sms", tags=["SMS"])
app.include_router(dashboard.router)


# Health check endpoints
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API status."""
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "AegisSecure Backend is running"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint with database status."""
    db_healthy = await db_manager.ping()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "version": settings.APP_VERSION,
        "database": "connected" if db_healthy else "disconnected",
        "websocket_connections": len(active_connections)
    }


@app.get("/ping", tags=["Health"])
async def ping():
    """Simple ping endpoint for monitoring."""
    return {"ping": "pong"}

@app.websocket("/ws/emails")
async def websocket_endpoint(websocket: WebSocket):
    """Handle real-time email update connections."""
    await connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await disconnect(websocket)

@app.websocket("/ws/sms")
async def websocket_sms_endpoint(websocket: WebSocket):
    """Handle real-time SMS update connections."""
    await connect(websocket)
    try:
        while True:
            await websocket.receive_text()  
    except WebSocketDisconnect:
        await disconnect(websocket)
    except Exception as e:
        print(f"WebSocket SMS error: {e}")
        await disconnect(websocket)

