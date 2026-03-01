"""FastAPI application entry point for BoredGames backend."""

from __future__ import annotations

import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.database import init_db
from backend.routers import auth, explain, games, houserules, moderate, ocr, voice
from backend.websocket.manager import manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI-powered board game moderator powered by Mistral La Plateforme",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup
@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("Database initialized")
    if settings.mistral_api_key:
        logger.info("Mistral API key configured")
    else:
        logger.warning("No Mistral API key found — AI features will fail")


# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(games.router, prefix="/api")
app.include_router(ocr.router, prefix="/api")
app.include_router(explain.router, prefix="/api")
app.include_router(moderate.router, prefix="/api")
app.include_router(houserules.router, prefix="/api")
app.include_router(voice.router, prefix="/api")


# Health check
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "mistral_configured": bool(settings.mistral_api_key),
    }


# WebSocket endpoint for live game sessions
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    disconnected = False
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_personal(
                    websocket,
                    {
                        "type": "error",
                        "content": "Invalid JSON payload",
                    },
                )
                continue

            event_type = message.get("type", "chat")

            if event_type == "chat":
                # Broadcast to all session participants
                await manager.send_to_session(
                    session_id,
                    {"type": "chat", "player": message.get("player", "Unknown"), "content": message.get("content", "")},
                )
            elif event_type == "turn_action":
                # Process through moderation
                await manager.send_to_session(
                    session_id,
                    {"type": "turn_action", "player": message.get("player"), "action": message.get("action")},
                )
            elif event_type == "voice_data":
                # Acknowledge voice data receipt
                await manager.send_personal(
                    websocket,
                    {"type": "voice_ack", "status": "received"},
                )
            else:
                await manager.send_personal(
                    websocket,
                    {
                        "type": "error",
                        "content": f"Unknown event type: {event_type}",
                    },
                )

    except WebSocketDisconnect:
        disconnected = True
    except Exception:
        logger.exception("Unexpected WebSocket error for session %s", session_id)
    finally:
        manager.disconnect(websocket, session_id)
        if disconnected:
            await manager.send_to_session(
                session_id,
                {"type": "system", "content": "A player disconnected"},
            )
