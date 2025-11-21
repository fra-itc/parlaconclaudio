"""
FastAPI Application for Real-Time STT Orchestrator
Main API server with WebSocket support, health checks, and CORS configuration.
"""

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .websocket_gateway import websocket_manager, MessageType


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models for API
class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    connections: int = Field(..., description="Number of active WebSocket connections")
    timestamp: str = Field(..., description="Current timestamp")


class InfoResponse(BaseModel):
    """API information response."""
    name: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    description: str = Field(..., description="API description")
    endpoints: Dict[str, str] = Field(..., description="Available endpoints")


class ConnectionInfo(BaseModel):
    """WebSocket connection information."""
    client_id: str = Field(..., description="Client identifier")
    connected_at: str = Field(..., description="Connection timestamp")
    message_count: int = Field(..., description="Number of messages sent")
    last_activity: str = Field(..., description="Last activity timestamp")


# Application metadata
APP_NAME = "Real-Time STT Orchestrator API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "WebSocket-based API for real-time speech-to-text orchestration"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.info("WebSocket gateway initialized")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await websocket_manager.cleanup()
    logger.info("Application shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Health check endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint",
    description="Check if the API is running and get system status"
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: Current health status and metrics
    """
    from datetime import datetime

    return HealthResponse(
        status="healthy",
        version=APP_VERSION,
        connections=websocket_manager.get_connection_count(),
        timestamp=datetime.utcnow().isoformat()
    )


# API information endpoint
@app.get(
    "/",
    response_model=InfoResponse,
    tags=["Info"],
    summary="API information",
    description="Get API metadata and available endpoints"
)
async def root() -> InfoResponse:
    """
    Get API information.

    Returns:
        InfoResponse: API metadata and endpoints
    """
    return InfoResponse(
        name=APP_NAME,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
        endpoints={
            "health": "/health",
            "websocket": "/ws",
            "connections": "/connections",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    )


# WebSocket connections info endpoint
@app.get(
    "/connections",
    tags=["WebSocket"],
    summary="Get WebSocket connections",
    description="Get information about active WebSocket connections"
)
async def get_connections() -> Dict[str, Any]:
    """
    Get information about active WebSocket connections.

    Returns:
        Dict: Connection count and client information
    """
    return {
        "total_connections": websocket_manager.get_connection_count(),
        "clients": websocket_manager.get_all_clients_info()
    }


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = None):
    """
    WebSocket endpoint for real-time communication.

    Args:
        websocket: WebSocket connection
        client_id: Optional client identifier (auto-generated if not provided)
    """
    # Generate client ID if not provided
    if not client_id:
        client_id = str(uuid.uuid4())

    logger.info(f"New WebSocket connection request from client: {client_id}")

    try:
        # Connect the client
        await websocket_manager.connect(websocket, client_id)

        # Send welcome message
        await websocket_manager.send_personal_message(
            message={
                "type": MessageType.STATUS,
                "status": "ready",
                "message": "Connected to Real-Time STT Orchestrator",
                "client_id": client_id
            },
            client_id=client_id
        )

        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()

                # Handle the message
                await websocket_manager.handle_client_message(client_id, data)

            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected normally")
                break

            except Exception as e:
                logger.error(f"Error in WebSocket loop for client {client_id}: {e}")
                await websocket_manager.broadcast_error(
                    error_message="Internal server error",
                    error_code="INTERNAL_ERROR"
                )
                break

    except Exception as e:
        logger.error(f"Error connecting client {client_id}: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass

    finally:
        # Ensure disconnection
        await websocket_manager.disconnect(client_id)


# Broadcast endpoint (for testing/admin purposes)
@app.post(
    "/broadcast",
    tags=["WebSocket"],
    summary="Broadcast message",
    description="Broadcast a message to all connected WebSocket clients (admin/testing only)"
)
async def broadcast_message(
    message: str,
    message_type: str = "status"
) -> Dict[str, Any]:
    """
    Broadcast a message to all connected clients.

    Args:
        message: Message to broadcast
        message_type: Type of message (status, error, etc.)

    Returns:
        Dict: Broadcast result with recipient count
    """
    count = await websocket_manager.broadcast({
        "type": message_type,
        "message": message,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    })

    return {
        "status": "success",
        "recipients": count,
        "message": message
    }


# Transcription broadcast endpoint
@app.post(
    "/transcribe",
    tags=["Transcription"],
    summary="Broadcast transcription",
    description="Broadcast a transcription result to all connected clients"
)
async def broadcast_transcription(
    text: str,
    is_final: bool = False,
    confidence: Optional[float] = None
) -> Dict[str, Any]:
    """
    Broadcast a transcription result to all connected clients.

    Args:
        text: Transcription text
        is_final: Whether this is a final or partial transcription
        confidence: Confidence score (0.0 to 1.0)

    Returns:
        Dict: Broadcast result with recipient count
    """
    if confidence is not None and not 0.0 <= confidence <= 1.0:
        raise HTTPException(
            status_code=400,
            detail="Confidence must be between 0.0 and 1.0"
        )

    count = await websocket_manager.broadcast_transcription(
        text=text,
        is_final=is_final,
        confidence=confidence
    )

    return {
        "status": "success",
        "recipients": count,
        "text": text,
        "is_final": is_final,
        "confidence": confidence
    }


# Error handler for WebSocket errors
@app.exception_handler(WebSocketDisconnect)
async def websocket_disconnect_handler(request, exc):
    """Handle WebSocket disconnections gracefully."""
    logger.info("WebSocket disconnected")
    return None


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc)
        }
    )


def main():
    """
    Main entry point to run the FastAPI application.
    """
    import uvicorn

    # Server configuration
    config = {
        "app": "src.agents.orchestrator.fastapi_app:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True,  # Enable auto-reload in development
        "log_level": "info",
        "access_log": True,
        "ws_ping_interval": 20.0,  # WebSocket ping interval
        "ws_ping_timeout": 20.0,   # WebSocket ping timeout
    }

    logger.info(f"Starting server on {config['host']}:{config['port']}")
    logger.info(f"WebSocket endpoint: ws://{config['host']}:{config['port']}/ws")
    logger.info(f"API docs: http://{config['host']}:{config['port']}/docs")

    # Run the server
    uvicorn.run(**config)


if __name__ == "__main__":
    main()
