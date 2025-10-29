from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi import WebSocket
from websocket_manager import connect, disconnect
load_dotenv()

from routes import auth, gmail, Oauth,notifications,otp
from websocket_manager import active_connections  
from websocket_manager import broadcast_new_email
import asyncio

app = FastAPI(title="Mail Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth")
app.include_router(gmail.router)
app.include_router(Oauth.router)
app.include_router(Oauth.router, prefix="/auth")
app.include_router(notifications.router) 
ws_router = APIRouter()


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
@app.get("/")
async def root():
    return {"message": "Mail Backend is running and WebSocket ready!"}