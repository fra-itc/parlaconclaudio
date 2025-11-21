# SUB-PLAN: INTEGRATION TEAM
## FastAPI Backend + Redis Orchestration + Docker Infrastructure

---

**Worktree**: `../RTSTT-integration`
**Branch**: `feature/backend-api`
**Team**: 2 Sonnet Agents (Backend Architect, DevOps Engineer)
**Duration**: 6 hours
**Priority**: CRITICA (integration layer)

---

## 🎯 OBIETTIVO

Implementare il backend FastAPI come WebSocket gateway e orchestratore Redis Streams. Setup Docker infrastructure per tutti i servizi. Gestire routing messaggi tra audio → STT → NLP → Summary → Frontend.

---

## 📦 DELIVERABLES

1. **FastAPI Application** (`src/agents/orchestrator/fastapi_app.py`)
2. **WebSocket Gateway** (`src/agents/orchestrator/websocket_gateway.py`)
3. **Redis Client** (`src/shared/protocols/redis_client.py`)
4. **gRPC Pool** (`src/shared/protocols/grpc_pool.py`)
5. **Message Router** (`src/agents/orchestrator/message_router.py`)
6. **Dockerfiles** (4 services: backend, stt, nlp, summary)
7. **Prometheus Metrics** (`src/agents/orchestrator/metrics.py`)
8. **Health Checks** (`src/agents/orchestrator/health.py`)
9. **Integration Tests** (end-to-end pipeline)

---

## 📋 TASK BREAKDOWN

### TASK 1: FastAPI Backend Core (1.5h)

#### Step 1.1: Application Setup (30min)
```python
# File: src/agents/orchestrator/fastapi_app.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import uvicorn

from .websocket_gateway import WebSocketManager
from .message_router import MessageRouter
from .health import health_check, get_system_info
from ..shared.protocols.redis_client import RedisClient
from ..shared.protocols.grpc_pool import GRPCPool

logger = logging.getLogger(__name__)

# Global instances
ws_manager = WebSocketManager()
message_router = MessageRouter()
redis_client = RedisClient()
grpc_pool = GRPCPool()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting RTSTT Backend...")
    await redis_client.connect()
    await grpc_pool.initialize()
    await message_router.start(redis_client, ws_manager)
    logger.info("Backend ready")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await message_router.stop()
    await grpc_pool.close()
    await redis_client.disconnect()
    logger.info("Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Real-Time STT Orchestrator API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# REST Endpoints
@app.get("/health")
async def health():
    """Health check endpoint"""
    return await health_check(redis_client, grpc_pool)

@app.get("/api/v1/info")
async def info():
    """System information"""
    return await get_system_info()

@app.get("/api/v1/devices")
async def list_devices():
    """List audio devices"""
    # Call audio capture service
    devices = await grpc_pool.audio.list_devices()
    return {"devices": devices}

@app.get("/api/v1/sessions")
async def list_sessions():
    """List transcription sessions"""
    # Query from Redis or database
    return {"sessions": []}

@app.get("/api/v1/sessions/{session_id}/transcript")
async def get_transcript(session_id: str):
    """Get session transcript"""
    # Fetch from storage
    return {"session_id": session_id, "segments": []}

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time communication"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            await ws_manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

def run():
    """Run FastAPI server"""
    uvicorn.run(
        "src.agents.orchestrator.fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
```

---

#### Step 1.2: WebSocket Gateway (1h)
```python
# File: src/agents/orchestrator/websocket_gateway.py

from fastapi import WebSocket
from typing import Dict, Set
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Manage WebSocket connections

    Features:
    - Multiple concurrent connections
    - Session-based routing
    - Message broadcasting
    - Automatic reconnection handling
    """

    def __init__(self):
        # Active connections: {websocket: session_id}
        self.active_connections: Dict[WebSocket, str] = {}

        # Sessions: {session_id: Set[WebSocket]}
        self.sessions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[websocket] = None
        logger.info(f"WebSocket connected: {id(websocket)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        session_id = self.active_connections.get(websocket)
        if session_id and session_id in self.sessions:
            self.sessions[session_id].discard(websocket)
            if not self.sessions[session_id]:
                del self.sessions[session_id]

        self.active_connections.pop(websocket, None)
        logger.info(f"WebSocket disconnected: {id(websocket)}")

    async def handle_message(self, websocket: WebSocket, message: dict):
        """
        Handle incoming message from client

        Message types:
        - transcription_start
        - transcription_stop
        - list_devices
        - ping
        """
        msg_type = message.get("type")
        logger.debug(f"Received message: {msg_type}")

        if msg_type == "transcription_start":
            await self._handle_transcription_start(websocket, message)
        elif msg_type == "transcription_stop":
            await self._handle_transcription_stop(websocket, message)
        elif msg_type == "list_devices":
            await self._handle_list_devices(websocket)
        elif msg_type == "ping":
            await self._send_message(websocket, {
                "type": "pong",
                "timestamp": message.get("timestamp"),
                "server_time": int(time.time() * 1000)
            })
        else:
            logger.warning(f"Unknown message type: {msg_type}")

    async def _handle_transcription_start(self, websocket: WebSocket, message: dict):
        """Start transcription session"""
        payload = message.get("payload", {})
        device_id = payload.get("device_id")
        session_id = f"session-{int(time.time() * 1000)}"

        # Associate websocket with session
        self.active_connections[websocket] = session_id
        if session_id not in self.sessions:
            self.sessions[session_id] = set()
        self.sessions[session_id].add(websocket)

        # Start audio capture (via message to audio service)
        # This would trigger audio service to start publishing to Redis
        logger.info(f"Started session {session_id} for device {device_id}")

        # Send confirmation
        await self._send_message(websocket, {
            "type": "status_update",
            "timestamp": int(time.time() * 1000),
            "payload": {
                "status": "recording",
                "message": f"Session {session_id} started",
                "session_id": session_id
            }
        })

    async def _handle_transcription_stop(self, websocket: WebSocket, message: dict):
        """Stop transcription session"""
        session_id = self.active_connections.get(websocket)
        if not session_id:
            return

        # Stop audio capture
        logger.info(f"Stopped session {session_id}")

        # Send confirmation
        await self._send_message(websocket, {
            "type": "status_update",
            "timestamp": int(time.time() * 1000),
            "payload": {
                "status": "stopped",
                "message": f"Session {session_id} stopped"
            }
        })

    async def _handle_list_devices(self, websocket: WebSocket):
        """List audio devices"""
        # Mock devices (in real implementation, query audio service)
        devices = [
            {
                "device_id": "wasapi-loopback-0",
                "device_name": "System Audio (Loopback)",
                "device_type": "loopback",
                "is_default": True
            }
        ]

        await self._send_message(websocket, {
            "type": "device_list",
            "timestamp": int(time.time() * 1000),
            "payload": {"devices": devices}
        })

    async def broadcast_to_session(self, session_id: str, message: dict):
        """Broadcast message to all connections in a session"""
        if session_id not in self.sessions:
            return

        disconnected = set()
        for websocket in self.sessions[session_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to websocket: {e}")
                disconnected.add(websocket)

        # Remove disconnected websockets
        for ws in disconnected:
            self.disconnect(ws)

    async def _send_message(self, websocket: WebSocket, message: dict):
        """Send message to specific websocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.disconnect(websocket)
```

---

### TASK 2: Redis Client & Message Router (1.5h)

```python
# File: src/shared/protocols/redis_client.py

import redis.asyncio as redis
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class RedisClient:
    """Async Redis client for Streams"""

    def __init__(self, host: str = "localhost", port: int = 6379):
        self.host = host
        self.port = port
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        self.client = await redis.from_url(
            f"redis://{self.host}:{self.port}",
            decode_responses=True
        )
        logger.info(f"Connected to Redis at {self.host}:{self.port}")

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis")

    async def xadd(self, stream: str, fields: dict) -> str:
        """Add message to stream"""
        return await self.client.xadd(stream, fields)

    async def xread(self, streams: dict, count: int = 10, block: int = 1000):
        """Read from streams"""
        return await self.client.xread(streams, count=count, block=block)

    async def xreadgroup(self, group: str, consumer: str,
                        streams: dict, count: int = 10, block: int = 1000):
        """Read from streams as consumer group"""
        return await self.client.xreadgroup(
            groupname=group,
            consumername=consumer,
            streams=streams,
            count=count,
            block=block
        )

    async def xack(self, stream: str, group: str, *ids):
        """Acknowledge processed messages"""
        return await self.client.xack(stream, group, *ids)

    async def xgroup_create(self, stream: str, group: str, id: str = '0',
                           mkstream: bool = True):
        """Create consumer group"""
        try:
            await self.client.xgroup_create(stream, group, id, mkstream=mkstream)
            logger.info(f"Created consumer group: {group} on {stream}")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group {group} already exists")
            else:
                raise
```

```python
# File: src/agents/orchestrator/message_router.py

import asyncio
import logging
from typing import Dict
from ..shared.protocols.redis_client import RedisClient
from .websocket_gateway import WebSocketManager

logger = logging.getLogger(__name__)

class MessageRouter:
    """
    Route messages between Redis Streams and WebSocket clients

    Flow:
    Redis STT out → WebSocket (transcription_update)
    Redis NLP out → WebSocket (nlp_insights)
    Redis Summary out → WebSocket (summary_update)
    """

    def __init__(self):
        self.redis: Optional[RedisClient] = None
        self.ws_manager: Optional[WebSocketManager] = None
        self.tasks = []
        self.running = False

    async def start(self, redis: RedisClient, ws_manager: WebSocketManager):
        """Start message routing"""
        self.redis = redis
        self.ws_manager = ws_manager
        self.running = True

        # Create consumer groups
        await self.redis.xgroup_create('rtstt:prod:stt:out', 'gateway-workers')
        await self.redis.xgroup_create('rtstt:prod:nlp:out', 'gateway-workers')
        await self.redis.xgroup_create('rtstt:prod:summary:out', 'gateway-workers')

        # Start consumer tasks
        self.tasks = [
            asyncio.create_task(self._consume_stt()),
            asyncio.create_task(self._consume_nlp()),
            asyncio.create_task(self._consume_summary())
        ]

        logger.info("Message router started")

    async def stop(self):
        """Stop message routing"""
        self.running = False
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("Message router stopped")

    async def _consume_stt(self):
        """Consume STT transcription messages"""
        consumer_name = "gateway-stt-01"

        while self.running:
            try:
                messages = await self.redis.xreadgroup(
                    group='gateway-workers',
                    consumer=consumer_name,
                    streams={'rtstt:prod:stt:out': '>'},
                    count=10,
                    block=1000
                )

                for stream, stream_messages in messages:
                    for msg_id, fields in stream_messages:
                        await self._handle_stt_message(msg_id, fields)

            except Exception as e:
                logger.error(f"Error in STT consumer: {e}")
                await asyncio.sleep(1)

    async def _handle_stt_message(self, msg_id: str, fields: dict):
        """Handle STT transcription message"""
        session_id = fields.get('session_id')
        text = fields.get('text')
        confidence = float(fields.get('confidence', 0))

        # Build WebSocket message
        ws_message = {
            "type": "transcription_update",
            "timestamp": int(fields.get('timestamp_start_ms', 0)),
            "payload": {
                "text": text,
                "confidence": confidence,
                "is_partial": fields.get('is_partial') == 'true',
                "timestamp_start_ms": int(fields.get('timestamp_start_ms', 0)),
                "timestamp_end_ms": int(fields.get('timestamp_end_ms', 0)),
                "language": fields.get('language', 'unknown')
            }
        }

        # Broadcast to session
        await self.ws_manager.broadcast_to_session(session_id, ws_message)

        # Acknowledge
        await self.redis.xack('rtstt:prod:stt:out', 'gateway-workers', msg_id)

    async def _consume_nlp(self):
        """Consume NLP insights messages"""
        # Similar to _consume_stt
        pass

    async def _consume_summary(self):
        """Consume summary messages"""
        # Similar to _consume_stt
        pass
```

---

### TASK 3: Docker Infrastructure (2h)

```dockerfile
# File: infrastructure/docker/Dockerfile.backend

FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements/base.txt ./requirements/
RUN pip install --no-cache-dir -r requirements/base.txt

# Copy source
COPY src/ ./src/
COPY docs/api/ ./docs/api/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI
CMD ["uvicorn", "src.agents.orchestrator.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# File: infrastructure/docker/Dockerfile.stt

FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Install Python
RUN apt-get update && apt-get install -y \
    python3.10 python3-pip curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements/base.txt requirements/ml.txt ./requirements/
RUN pip3 install --no-cache-dir -r requirements/base.txt -r requirements/ml.txt

# Copy source
COPY src/ ./src/
COPY models/ ./models/

# Expose gRPC port
EXPOSE 50051

# Run STT gRPC server
CMD ["python3", "-m", "src.core.stt_engine.grpc_server"]
```

```yaml
# File: infrastructure/monitoring/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'rtstt-backend'
    static_configs:
      - targets: ['backend:8001']

  - job_name: 'rtstt-stt'
    static_configs:
      - targets: ['stt-engine:8001']

  - job_name: 'rtstt-nlp'
    static_configs:
      - targets: ['nlp-service:8001']

  - job_name: 'rtstt-summary'
    static_configs:
      - targets: ['summary-service:8001']
```

---

### TASK 4: Metrics & Monitoring (1h)

```python
# File: src/agents/orchestrator/metrics.py

from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
transcription_requests = Counter(
    'rtstt_transcription_requests_total',
    'Total transcription requests'
)

transcription_latency = Histogram(
    'rtstt_transcription_latency_seconds',
    'Transcription latency',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

active_sessions = Gauge(
    'rtstt_active_sessions',
    'Number of active sessions'
)

websocket_connections = Gauge(
    'rtstt_websocket_connections',
    'Number of active WebSocket connections'
)

redis_stream_lag = Gauge(
    'rtstt_redis_stream_lag',
    'Redis stream lag',
    ['stream']
)
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] FastAPI server starts on port 8000
- [ ] WebSocket gateway accepts connections
- [ ] Redis consumer routes messages correctly
- [ ] Docker services orchestrated with docker-compose
- [ ] Health checks return status for all services
- [ ] Prometheus metrics exposed
- [ ] End-to-end test: audio → transcription → frontend
- [ ] Latency <100ms for message routing
- [ ] Integration tests pass

---

## 🚀 COMANDI ESECUZIONE

```bash
cd ../RTSTT-integration

# Install dependencies
pip install -r requirements/base.txt

# Start services with Docker
docker-compose up -d

# Run FastAPI backend
python -m src.agents.orchestrator.fastapi_app

# Integration tests
pytest tests/integration/test_e2e_pipeline.py -v

# Check metrics
curl http://localhost:8001/metrics
```

---

**BUON LAVORO, INTEGRATION TEAM! 🔧**
