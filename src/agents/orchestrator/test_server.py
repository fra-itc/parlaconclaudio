"""
Test script for FastAPI + WebSocket gateway
Runs the server on port 8001 for testing purposes
"""

import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.info("Starting test server on port 8001...")

    uvicorn.run(
        "src.agents.orchestrator.fastapi_app:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info",
        access_log=True,
        ws_ping_interval=20.0,
        ws_ping_timeout=20.0,
    )
