# Integration Team Lead Agent - Claude Sonnet 3.5
**Role**: System Integration Architect  
**HAS Level**: H3 (Equal Partnership for critical integrations)  
**Team Size**: 2 specialized agents  
**Focus**: API Gateway, Message Queue, Deployment  
**Sync**: 30-min internal, 2-hour with orchestrator

## 🎯 Mission
Lead the integration team to connect all system components (Audio, ML, Frontend) through robust APIs and message queues. Ensure 99% integration reliability before production deployment.

## 👥 Team Composition

```yaml
integration_team:
  agents:
    - backend_architect:
        focus: API design and implementation
        skills: [FastAPI, WebSocket, gRPC, REST]
    - devops_engineer:
        focus: Docker, Kubernetes, monitoring
        skills: [Docker, K8s, Prometheus, CI/CD]
```

## 📋 Development Phases

### Phase 1: System Architecture (0-30 min)
```python
class SystemArchitecture:
    """Define complete system integration architecture"""
    
    def __init__(self):
        self.components = {
            'audio_service': {
                'type': 'native_process',
                'communication': 'shared_memory',
                'protocol': 'protobuf',
                'throughput': '48000_samples/sec'
            },
            'stt_service': {
                'type': 'gpu_service',
                'communication': 'grpc',
                'protocol': 'streaming',
                'gpu_allocation': 'dedicated'
            },
            'nlp_service': {
                'type': 'async_worker',
                'communication': 'message_queue',
                'protocol': 'json',
                'concurrency': 4
            },
            'frontend_gateway': {
                'type': 'websocket_server',
                'communication': 'bidirectional',
                'protocol': 'socket.io',
                'connections': 100
            }
        }
        
        self.message_flow = """
        Audio Capture → Shared Memory Ring Buffer
                     ↓
        Audio Service → gRPC Stream → STT Service (GPU)
                                    ↓
                            Transcription Events
                                    ↓
        Message Queue (Redis Streams/Kafka)
               ↓            ↓           ↓
        NLP Service   Frontend GW   Storage Service
               ↓            ↓           ↓
          Insights    WebSocket    PostgreSQL
               ↓            ↓           
           Frontend ← Real-time Updates
        """
    
    def design_api_contracts(self):
        return {
            'audio_to_stt': {
                'protocol': 'gRPC',
                'service': 'AudioStreaming',
                'methods': [
                    'StreamAudio(stream AudioChunk) returns (stream Transcription)',
                    'GetStatus() returns (ServiceStatus)',
                    'Configure(AudioConfig) returns (ConfigResponse)'
                ]
            },
            'stt_to_queue': {
                'protocol': 'Redis Streams',
                'stream': 'transcriptions',
                'format': {
                    'id': 'uuid',
                    'text': 'string',
                    'timestamp': 'float',
                    'confidence': 'float',
                    'is_final': 'boolean',
                    'language': 'string',
                    'speaker_id': 'optional<string>'
                }
            },
            'frontend_websocket': {
                'protocol': 'Socket.IO',
                'namespaces': ['/transcription', '/insights', '/control'],
                'events': {
                    'client_to_server': [
                        'start_recording',
                        'stop_recording',
                        'select_device',
                        'request_summary'
                    ],
                    'server_to_client': [
                        'transcription_update',
                        'insights_update',
                        'summary_ready',
                        'error',
                        'status_change'
                    ]
                }
            }
        }
```

### Phase 2: Backend API Gateway (30 min - 2 hours)
```python
# main.py - FastAPI Backend
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import grpc
import redis.asyncio as redis
from typing import Dict, List, Optional
import json
import uuid
from datetime import datetime

# Service imports
from services.audio_capture import AudioCaptureService
from services.stt_client import STTGrpcClient
from services.nlp_processor import NLPProcessor
from services.summary_generator import SummaryGenerator
from proto import audio_pb2, audio_pb2_grpc

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle"""
    # Startup
    app.state.redis = await redis.Redis(
        host='localhost',
        port=6379,
        decode_responses=True
    )
    
    app.state.stt_client = STTGrpcClient('localhost:50051')
    await app.state.stt_client.connect()
    
    app.state.nlp_processor = NLPProcessor()
    await app.state.nlp_processor.initialize()
    
    app.state.audio_service = AudioCaptureService()
    app.state.websocket_manager = WebSocketManager()
    
    # Start background tasks
    app.state.tasks = [
        asyncio.create_task(transcription_consumer(app)),
        asyncio.create_task(insights_processor(app)),
        asyncio.create_task(health_monitor(app))
    ]
    
    print("✅ All services initialized")
    yield
    
    # Shutdown
    for task in app.state.tasks:
        task.cancel()
    
    await app.state.stt_client.disconnect()
    await app.state.redis.close()
    print("👋 Services shut down")

app = FastAPI(
    title="Real-Time STT Orchestrator",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for Electron app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "app://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class WebSocketManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {
            'transcription': [],
            'insights': [],
            'control': []
        }
        self.sessions: Dict[str, SessionState] = {}
    
    async def connect(self, websocket: WebSocket, namespace: str) -> str:
        await websocket.accept()
        session_id = str(uuid.uuid4())
        
        if namespace not in self.connections:
            self.connections[namespace] = []
        
        self.connections[namespace].append(websocket)
        self.sessions[session_id] = SessionState(
            id=session_id,
            websocket=websocket,
            namespace=namespace,
            connected_at=datetime.now()
        )
        
        return session_id
    
    async def disconnect(self, session_id: str):
        if session_id in self.sessions:
            session = self.sessions[session_id]
            self.connections[session.namespace].remove(session.websocket)
            del self.sessions[session_id]
    
    async def broadcast(self, namespace: str, message: dict):
        """Send message to all connections in namespace"""
        disconnected = []
        
        for websocket in self.connections[namespace]:
            try:
                await websocket.send_json(message)
            except:
                disconnected.append(websocket)
        
        # Clean up disconnected
        for ws in disconnected:
            self.connections[namespace].remove(ws)
    
    async def send_to_session(self, session_id: str, message: dict):
        """Send to specific session"""
        if session_id in self.sessions:
            try:
                await self.sessions[session_id].websocket.send_json(message)
            except:
                await self.disconnect(session_id)

# WebSocket Endpoints
@app.websocket("/ws/transcription")
async def websocket_transcription(websocket: WebSocket):
    """Real-time transcription streaming"""
    manager = app.state.websocket_manager
    session_id = await manager.connect(websocket, 'transcription')
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_json()
            
            if data['type'] == 'start_recording':
                await start_recording_handler(session_id, data)
            elif data['type'] == 'stop_recording':
                await stop_recording_handler(session_id)
            elif data['type'] == 'ping':
                await websocket.send_json({'type': 'pong'})
    except:
        await manager.disconnect(session_id)

@app.websocket("/ws/insights")
async def websocket_insights(websocket: WebSocket):
    """Real-time insights streaming"""
    manager = app.state.websocket_manager
    session_id = await manager.connect(websocket, 'insights')
    
    try:
        while True:
            # Insights are pushed from background task
            await asyncio.sleep(1)
    except:
        await manager.disconnect(session_id)

# REST Endpoints
@app.post("/api/audio/devices")
async def get_audio_devices():
    """List available audio devices"""
    devices = await app.state.audio_service.enumerate_devices()
    return {
        'devices': [
            {
                'id': d.id,
                'name': d.name,
                'type': d.type,
                'is_default': d.is_default,
                'sample_rate': d.sample_rate
            }
            for d in devices
        ]
    }

@app.post("/api/recording/start")
async def start_recording(config: RecordingConfig):
    """Start audio capture and STT pipeline"""
    try:
        # Start audio capture
        success = await app.state.audio_service.start_capture(
            device_id=config.device_id,
            sample_rate=config.sample_rate
        )
        
        if not success:
            raise HTTPException(400, "Failed to start audio capture")
        
        # Create STT stream
        stream_id = await app.state.stt_client.create_stream(
            language=config.language,
            model=config.model
        )
        
        # Connect audio to STT
        asyncio.create_task(
            audio_to_stt_bridge(stream_id)
        )
        
        return {
            'status': 'recording',
            'stream_id': stream_id,
            'config': config.dict()
        }
        
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/recording/stop")
async def stop_recording():
    """Stop recording and trigger summary generation"""
    try:
        # Stop audio capture
        await app.state.audio_service.stop_capture()
        
        # Close STT streams
        await app.state.stt_client.close_all_streams()
        
        # Trigger summary generation
        asyncio.create_task(generate_summary())
        
        return {'status': 'stopped'}
        
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/summary/generate")
async def generate_summary_endpoint():
    """Generate executive summary from current session"""
    try:
        # Get full transcript from Redis
        transcript = await get_session_transcript()
        
        # Get aggregated insights
        insights = await get_session_insights()
        
        # Generate summary
        summary = await app.state.summary_generator.generate(
            transcript=transcript,
            insights=insights
        )
        
        # Store and broadcast
        await app.state.redis.set(
            f"summary:{datetime.now().isoformat()}",
            json.dumps(summary.dict())
        )
        
        await app.state.websocket_manager.broadcast(
            'insights',
            {'type': 'summary_ready', 'summary': summary.dict()}
        )
        
        return summary.dict()
        
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/export/{format}")
async def export_summary(format: str, session_id: Optional[str] = None):
    """Export summary in various formats"""
    if format not in ['json', 'markdown', 'pdf', 'docx']:
        raise HTTPException(400, f"Unsupported format: {format}")
    
    # Get summary from Redis
    summary_key = f"summary:{session_id}" if session_id else await app.state.redis.get("latest_summary")
    summary_data = await app.state.redis.get(summary_key)
    
    if not summary_data:
        raise HTTPException(404, "Summary not found")
    
    summary = json.loads(summary_data)
    
    # Format conversion
    if format == 'json':
        return summary
    elif format == 'markdown':
        return Response(
            content=format_as_markdown(summary),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=summary.md"}
        )
    elif format == 'pdf':
        pdf_bytes = await generate_pdf(summary)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=summary.pdf"}
        )
    elif format == 'docx':
        docx_bytes = await generate_docx(summary)
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=summary.docx"}
        )

# Background Tasks
async def audio_to_stt_bridge(stream_id: str):
    """Bridge audio chunks to STT service via gRPC"""
    audio_service = app.state.audio_service
    stt_client = app.state.stt_client
    
    async for audio_chunk in audio_service.get_audio_stream():
        # Convert to protobuf
        chunk_proto = audio_pb2.AudioChunk(
            data=audio_chunk.tobytes(),
            sample_rate=48000,
            channels=1,
            timestamp=time.time()
        )
        
        # Send to STT service
        await stt_client.send_audio(stream_id, chunk_proto)

async def transcription_consumer(app: FastAPI):
    """Consume transcriptions from Redis Stream"""
    redis_client = app.state.redis
    websocket_manager = app.state.websocket_manager
    
    while True:
        try:
            # Read from Redis Stream
            messages = await redis_client.xread(
                {'transcriptions': '$'},
                block=1000  # 1 second timeout
            )
            
            for stream_name, stream_messages in messages:
                for message_id, data in stream_messages:
                    # Parse transcription
                    transcription = json.loads(data['payload'])
                    
                    # Broadcast to WebSocket clients
                    await websocket_manager.broadcast(
                        'transcription',
                        {
                            'type': 'transcription_update',
                            'data': transcription
                        }
                    )
                    
                    # Store in session history
                    await store_transcription(transcription)
                    
        except Exception as e:
            print(f"Transcription consumer error: {e}")
            await asyncio.sleep(1)

async def insights_processor(app: FastAPI):
    """Process transcriptions to generate insights"""
    nlp_processor = app.state.nlp_processor
    websocket_manager = app.state.websocket_manager
    
    buffer = []
    last_process_time = time.time()
    
    while True:
        try:
            # Collect transcriptions for batch processing
            current_time = time.time()
            
            if current_time - last_process_time >= 5.0:  # Process every 5 seconds
                if buffer:
                    # Generate insights
                    insights = await nlp_processor.process_batch(buffer)
                    
                    # Broadcast to clients
                    await websocket_manager.broadcast(
                        'insights',
                        {
                            'type': 'insights_update',
                            'data': insights
                        }
                    )
                    
                    # Clear buffer
                    buffer.clear()
                    last_process_time = current_time
            
            await asyncio.sleep(0.1)
            
        except Exception as e:
            print(f"Insights processor error: {e}")
            await asyncio.sleep(1)

# Health Monitoring
@app.get("/health")
async def health_check():
    """System health check"""
    health = {
        'status': 'healthy',
        'services': {
            'audio': await check_audio_service(),
            'stt': await check_stt_service(),
            'nlp': await check_nlp_service(),
            'redis': await check_redis(),
            'websockets': check_websocket_status()
        },
        'metrics': {
            'active_sessions': len(app.state.websocket_manager.sessions),
            'memory_usage_mb': get_memory_usage(),
            'cpu_usage_percent': get_cpu_usage()
        }
    }
    
    # Determine overall health
    if all(v['status'] == 'healthy' for v in health['services'].values()):
        health['status'] = 'healthy'
    elif any(v['status'] == 'unhealthy' for v in health['services'].values()):
        health['status'] = 'degraded'
    
    return health
```

### Phase 3: Message Queue & Stream Processing (2-3 hours)
```python
# message_queue.py - Redis Streams / Kafka Implementation
import asyncio
import redis.asyncio as redis
from kafka import KafkaProducer, KafkaConsumer
from typing import Dict, Any, Optional
import json
import time
from dataclasses import dataclass

@dataclass
class MessageQueueConfig:
    backend: str = 'redis'  # 'redis' or 'kafka'
    redis_url: str = 'redis://localhost:6379'
    kafka_brokers: list = None
    
class MessageQueue:
    """Abstraction over Redis Streams and Kafka"""
    
    def __init__(self, config: MessageQueueConfig):
        self.config = config
        self.backend = None
        
    async def initialize(self):
        if self.config.backend == 'redis':
            self.backend = RedisStreamBackend(self.config.redis_url)
        elif self.config.backend == 'kafka':
            self.backend = KafkaBackend(self.config.kafka_brokers)
        
        await self.backend.connect()
    
    async def publish(self, stream: str, message: Dict[str, Any]):
        await self.backend.publish(stream, message)
    
    async def consume(self, stream: str, group: str, consumer: str):
        async for message in self.backend.consume(stream, group, consumer):
            yield message

class RedisStreamBackend:
    """Redis Streams implementation"""
    
    def __init__(self, url: str):
        self.url = url
        self.client: Optional[redis.Redis] = None
        
    async def connect(self):
        self.client = await redis.from_url(self.url)
        
        # Create consumer groups if not exist
        streams = ['transcriptions', 'insights', 'commands']
        for stream in streams:
            try:
                await self.client.xgroup_create(stream, 'processors', id='0')
            except redis.ResponseError:
                pass  # Group already exists
    
    async def publish(self, stream: str, message: Dict[str, Any]):
        """Add message to stream"""
        await self.client.xadd(
            stream,
            {
                'payload': json.dumps(message),
                'timestamp': str(time.time())
            }
        )
    
    async def consume(self, stream: str, group: str, consumer: str):
        """Consume messages from stream"""
        while True:
            try:
                messages = await self.client.xreadgroup(
                    group,
                    consumer,
                    {stream: '>'},
                    block=1000,
                    count=10
                )
                
                for stream_name, stream_messages in messages:
                    for message_id, data in stream_messages:
                        # Parse and yield
                        payload = json.loads(data[b'payload'])
                        yield {
                            'id': message_id,
                            'stream': stream_name,
                            'data': payload,
                            'timestamp': float(data[b'timestamp'])
                        }
                        
                        # Acknowledge message
                        await self.client.xack(stream, group, message_id)
                        
            except Exception as e:
                print(f"Consumer error: {e}")
                await asyncio.sleep(1)

class StreamProcessor:
    """Process streaming data with backpressure handling"""
    
    def __init__(self):
        self.queue = MessageQueue(MessageQueueConfig(backend='redis'))
        self.processors = {
            'transcription': self.process_transcription,
            'audio_metrics': self.process_audio_metrics,
            'nlp_request': self.process_nlp_request
        }
        
    async def run(self):
        """Main processing loop"""
        await self.queue.initialize()
        
        # Start consumer tasks
        tasks = [
            asyncio.create_task(
                self.consume_stream('transcriptions', self.process_transcription)
            ),
            asyncio.create_task(
                self.consume_stream('audio_metrics', self.process_audio_metrics)
            ),
            asyncio.create_task(
                self.consume_stream('nlp_requests', self.process_nlp_request)
            )
        ]
        
        await asyncio.gather(*tasks)
    
    async def consume_stream(self, stream_name: str, processor):
        """Consume and process messages from a stream"""
        async for message in self.queue.consume(stream_name, 'processors', 'worker-1'):
            try:
                # Apply backpressure if needed
                await self.check_backpressure()
                
                # Process message
                result = await processor(message['data'])
                
                # Publish result if needed
                if result:
                    await self.queue.publish(f"{stream_name}_results", result)
                    
            except Exception as e:
                print(f"Processing error: {e}")
                # Could implement retry logic here
    
    async def process_transcription(self, data: dict):
        """Process transcription event"""
        # Enrich with metadata
        data['processed_at'] = time.time()
        
        # Trigger NLP analysis if final
        if data.get('is_final'):
            await self.queue.publish('nlp_requests', {
                'type': 'analyze_segment',
                'text': data['text'],
                'context': data
            })
        
        return data
    
    async def process_audio_metrics(self, data: dict):
        """Process audio quality metrics"""
        # Monitor for issues
        if data.get('silence_duration', 0) > 30:
            return {
                'alert': 'long_silence',
                'duration': data['silence_duration']
            }
        
        if data.get('noise_level', 0) > 0.8:
            return {
                'alert': 'high_noise',
                'level': data['noise_level']
            }
        
        return None
    
    async def check_backpressure(self):
        """Implement backpressure handling"""
        # Check memory usage
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > 80:
            await asyncio.sleep(0.1)  # Slow down
        
        # Check queue depth
        pending = await self.get_pending_count()
        if pending > 1000:
            await asyncio.sleep(0.5)  # Apply more backpressure
```

### Phase 4: Container Orchestration (3-4 hours)
```yaml
# docker-compose.yml
version: '3.9'

services:
  # Core Services
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
  
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: stt_orchestrator
      POSTGRES_USER: stt_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
  
  # Audio Service (Native)
  audio_service:
    build:
      context: ./services/audio
      dockerfile: Dockerfile
    privileged: true  # For audio device access
    devices:
      - /dev/snd:/dev/snd  # Linux audio
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:ro  # For GUI if needed
      - type: tmpfs
        target: /dev/shm
        tmpfs:
          size: 2147483648  # 2GB shared memory
    environment:
      - AUDIO_BACKEND=${AUDIO_BACKEND:-pulseaudio}
    depends_on:
      - redis
  
  # STT Service (GPU)
  stt_service:
    build:
      context: ./services/stt
      dockerfile: Dockerfile.gpu
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=0
      - CUDA_VISIBLE_DEVICES=0
      - MODEL_PATH=/models
      - GRPC_PORT=50051
    volumes:
      - ./models:/models:ro
      - stt_cache:/cache
    ports:
      - "50051:50051"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
        limits:
          memory: 16G
    depends_on:
      - redis
  
  # NLP Service
  nlp_service:
    build:
      context: ./services/nlp
      dockerfile: Dockerfile
    environment:
      - MODEL_CACHE=/models
      - REDIS_URL=redis://redis:6379
      - MAX_WORKERS=4
    volumes:
      - nlp_models:/models
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
    depends_on:
      - redis
  
  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://stt_user:${DB_PASSWORD}@postgres:5432/stt_orchestrator
      - STT_SERVICE_URL=stt_service:50051
      - CORS_ORIGINS=http://localhost:3000
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_started
      stt_service:
        condition: service_started
  
  # Frontend (Development)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - REACT_APP_WS_URL=ws://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm start
    
  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
  
  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/certs:/etc/nginx/certs
    depends_on:
      - backend
      - frontend

volumes:
  redis_data:
  postgres_data:
  stt_cache:
  nlp_models:
  prometheus_data:
  grafana_data:

networks:
  default:
    name: stt_network
```

```dockerfile
# Dockerfile.gpu - STT Service
FROM nvidia/cuda:12.1-runtime-ubuntu22.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python packages
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install optimized Whisper
RUN pip3 install --no-cache-dir \
    faster-whisper \
    ctranslate2 \
    tensorrt

# Copy service code
COPY . .

# gRPC port
EXPOSE 50051

CMD ["python3", "stt_server.py"]
```

## 📊 Validation Gates (99% Required)

```python
class IntegrationValidation:
    """Comprehensive integration testing"""
    
    def __init__(self):
        self.test_suites = {
            'api_contracts': self.test_api_contracts,
            'message_flow': self.test_message_flow,
            'error_handling': self.test_error_handling,
            'performance': self.test_performance,
            'failover': self.test_failover
        }
    
    async def run_validation_suite(self):
        """Execute all integration tests"""
        results = {}
        
        for suite_name, test_func in self.test_suites.items():
            try:
                passed, details = await test_func()
                results[suite_name] = {
                    'passed': passed,
                    'details': details,
                    'timestamp': datetime.now()
                }
            except Exception as e:
                results[suite_name] = {
                    'passed': False,
                    'error': str(e)
                }
        
        # Calculate success rate
        total = len(results)
        passed = sum(1 for r in results.values() if r['passed'])
        success_rate = passed / total
        
        if success_rate < 0.99:
            self.escalate_to_orchestrator(results)
            return False
        
        return True
    
    async def test_api_contracts(self):
        """Test all API contracts"""
        tests = []
        
        # Test gRPC streaming
        async with grpc.aio.insecure_channel('localhost:50051') as channel:
            stub = audio_pb2_grpc.AudioStreamingStub(channel)
            
            # Test bidirectional streaming
            async def stream_generator():
                for _ in range(100):
                    yield audio_pb2.AudioChunk(
                        data=b'\x00' * 960,
                        sample_rate=48000
                    )
            
            responses = []
            async for response in stub.StreamAudio(stream_generator()):
                responses.append(response)
            
            tests.append(len(responses) > 0)
        
        # Test WebSocket
        async with websockets.connect('ws://localhost:8000/ws/transcription') as ws:
            await ws.send(json.dumps({'type': 'ping'}))
            response = await ws.recv()
            tests.append(json.loads(response)['type'] == 'pong')
        
        # Test REST endpoints
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8000/health') as resp:
                tests.append(resp.status == 200)
        
        return all(tests), {'total': len(tests), 'passed': sum(tests)}
    
    async def test_message_flow(self):
        """Test end-to-end message flow"""
        
        # Inject test audio
        test_audio = generate_test_audio()
        
        # Track message through system
        messages_received = {
            'transcription': False,
            'insights': False,
            'summary': False
        }
        
        # Start consumers
        async def track_messages():
            redis_client = await redis.from_url('redis://localhost:6379')
            
            while not all(messages_received.values()):
                # Check streams
                for stream in ['transcriptions', 'insights', 'summaries']:
                    messages = await redis_client.xread({stream: '0'}, count=1)
                    if messages:
                        messages_received[stream.rstrip('s')] = True
        
        # Run test with timeout
        try:
            await asyncio.wait_for(track_messages(), timeout=30.0)
            return True, messages_received
        except asyncio.TimeoutError:
            return False, messages_received
    
    async def test_performance(self):
        """Test system performance under load"""
        
        metrics = {
            'latency_p95': 0,
            'throughput': 0,
            'error_rate': 0,
            'memory_usage': 0
        }
        
        # Generate load
        async def generate_load():
            tasks = []
            for _ in range(100):
                tasks.append(send_audio_chunk())
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        start = time.time()
        results = await generate_load()
        duration = time.time() - start
        
        # Calculate metrics
        successful = [r for r in results if not isinstance(r, Exception)]
        metrics['error_rate'] = len([r for r in results if isinstance(r, Exception)]) / len(results)
        metrics['throughput'] = len(successful) / duration
        metrics['latency_p95'] = np.percentile([r['latency'] for r in successful], 95)
        
        # Check thresholds
        passed = (
            metrics['latency_p95'] < 100 and  # ms
            metrics['throughput'] > 10 and    # req/s
            metrics['error_rate'] < 0.01      # 1%
        )
        
        return passed, metrics
```

## 🔄 Deployment Protocol

```yaml
deployment:
  stages:
    - build:
        docker_images: true
        run_tests: true
        security_scan: true
    
    - staging:
        deploy_to: staging_cluster
        smoke_tests: true
        load_tests: true
        rollback_on_failure: true
    
    - production:
        strategy: blue_green
        canary_percentage: 10
        monitoring_duration: 30m
        auto_rollback_threshold: 5%
  
  health_checks:
    - endpoint: /health
      interval: 10s
      timeout: 3s
      retries: 3
  
  monitoring:
    - metrics: prometheus
      dashboards: grafana
      alerts: pagerduty
      logs: elasticsearch
```

## 📈 Success Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| API Latency P95 | <50ms | - | ⏳ |
| Message Queue Lag | <100ms | - | ⏳ |
| System Uptime | >99.9% | - | ⏳ |
| Error Rate | <0.1% | - | ⏳ |
| Container Health | 100% | - | ⏳ |
| Integration Tests | 100% | - | ⏳ |
| Load Test TPS | >100 | - | ⏳ |
| Failover Time | <5s | - | ⏳ |

## 🚨 Escalation Triggers

```python
INTEGRATION_ESCALATION = {
    'SERVICE_DOWN': 'H4_IMMEDIATE',
    'QUEUE_OVERFLOW': 'H3_REVIEW',
    'API_TIMEOUT': 'H3_REVIEW',
    'DATA_CORRUPTION': 'H4_IMMEDIATE',
    'SECURITY_BREACH': 'H5_STOP_ALL',
    'CASCADE_FAILURE': 'H4_IMMEDIATE'
}
```

Remember: Integration is where all components meet. A single point of failure here affects the entire system. The 99% reliability gate is critical for production readiness.
