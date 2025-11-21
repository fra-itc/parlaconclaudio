# gRPC Connection Pool

This module provides robust gRPC connection pooling with automatic reconnection and load balancing.

## Features

- **Connection Pooling**: Multiple connections per service for better throughput
- **Load Balancing**: Round-robin distribution across healthy connections
- **Auto-Reconnection**: Automatic reconnection on connection failures
- **Health Monitoring**: Background health checks with automatic recovery
- **Metrics Collection**: Per-connection and per-pool metrics
- **Async Support**: Full async/await support for high performance

## Architecture

```
GrpcPoolManager
├── GrpcConnectionPool (STT Service)
│   ├── GrpcConnection #0
│   ├── GrpcConnection #1
│   └── GrpcConnection #2
├── GrpcConnectionPool (NLP Service)
│   ├── GrpcConnection #0
│   └── GrpcConnection #1
└── GrpcConnectionPool (Summary Service)
    ├── GrpcConnection #0
    └── GrpcConnection #1
```

## Usage

### Basic Setup

```python
from src.shared.protocols.grpc_pool import (
    ServiceType,
    ServiceConfig,
    initialize_grpc_pools,
    get_pool_manager
)

# Configure services
service_configs = {
    ServiceType.STT: ServiceConfig(
        host="localhost",
        port=50051,
        pool_size=3,
        max_retries=3,
        timeout=30.0
    ),
    ServiceType.NLP: ServiceConfig(
        host="localhost",
        port=50052,
        pool_size=2
    ),
    ServiceType.SUMMARY: ServiceConfig(
        host="localhost",
        port=50053,
        pool_size=2
    )
}

# Initialize pools
await initialize_grpc_pools(service_configs)
```

### Making gRPC Calls

```python
from src.shared.protocols.grpc_pool import get_pool_manager, ServiceType

pool_manager = get_pool_manager()

# Get connection from pool
async with pool_manager.get_connection(ServiceType.STT) as conn:
    # Get underlying gRPC channel
    channel = conn.get_channel()

    # Create stub and make call
    stub = stt_pb2_grpc.STTServiceStub(channel)
    response = await stub.Transcribe(request)

    # Connection automatically returned to pool
```

### Monitoring and Metrics

```python
# Get metrics for all pools
metrics = pool_manager.get_all_metrics()
print(f"STT Pool: {metrics['stt']}")
print(f"NLP Pool: {metrics['nlp']}")

# Check health of all services
health = await pool_manager.health_check()
print(f"STT Healthy: {health['stt']}")
print(f"NLP Healthy: {health['nlp']}")

# Get per-pool metrics
pool = pool_manager.pools[ServiceType.STT]
metrics = pool.get_metrics()
print(f"Total Requests: {metrics['total_requests']}")
print(f"Success Rate: {metrics['success_rate'] * 100:.2f}%")
print(f"Avg Response Time: {metrics['avg_response_time_ms']:.2f}ms")
```

### Connection Lifecycle

The pool automatically manages connection lifecycle:

1. **Initialization**: Connections are established on pool startup
2. **Health Checks**: Background task monitors connection health every 30s
3. **Auto-Reconnection**: Failed connections are automatically reconnected
4. **Load Balancing**: Requests are distributed round-robin across healthy connections
5. **Shutdown**: All connections are gracefully closed on application shutdown

### Configuration Options

```python
@dataclass
class ServiceConfig:
    host: str                    # Service hostname
    port: int                    # Service port
    pool_size: int = 3          # Number of connections in pool
    max_retries: int = 3        # Max reconnection attempts
    retry_delay: float = 1.0    # Delay between retries (seconds)
    timeout: float = 30.0       # Connection timeout (seconds)
    keepalive_time_ms: int = 10000      # gRPC keepalive interval
    keepalive_timeout_ms: int = 5000    # gRPC keepalive timeout
    max_connection_idle_ms: int = 300000  # Max idle time (5 minutes)
    enable_retries: bool = True         # Enable gRPC retries
    compression: bool = True            # Enable gzip compression
```

### FastAPI Integration

See `example_app.py` for a complete FastAPI integration example.

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await initialize_grpc_pools(service_configs)
    yield
    # Shutdown
    await close_grpc_pools()

app = FastAPI(lifespan=lifespan)
```

## Error Handling

The pool handles various error scenarios:

- **Connection Timeout**: Returns `ConnectionState.TRANSIENT_FAILURE`
- **Connection Lost**: Triggers automatic reconnection
- **All Connections Down**: Returns first connection and lets caller handle
- **Service Unavailable**: Exponential backoff on reconnection

## Thread Safety

All pool operations are thread-safe using asyncio locks:
- Connection acquisition
- Health checks
- Reconnection logic
- Metrics updates

## Performance Considerations

- **Pool Size**: 2-5 connections per service is typical
- **Keepalive**: Prevents connection drops during idle periods
- **Compression**: Reduces bandwidth, adds CPU overhead
- **Metrics**: Cached for 10 seconds to reduce overhead

## Testing

```bash
# Run with mock services
python -m pytest tests/test_grpc_pool.py

# Integration test with real services
python -m pytest tests/integration/test_grpc_integration.py
```

## Logging

The module logs to `src.shared.protocols.grpc_pool`:

```python
import logging
logging.getLogger('src.shared.protocols.grpc_pool').setLevel(logging.INFO)
```

Log events include:
- Connection establishment/closure
- Health check failures
- Reconnection attempts
- Pool initialization/shutdown
