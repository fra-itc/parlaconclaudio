# Health Check Module

Comprehensive health monitoring for the Real-Time STT Orchestrator service.

## Features

- **Component Monitoring**: Redis, gRPC services, system resources
- **Kubernetes Probes**: Liveness and readiness endpoints
- **Metrics Collection**: Detailed service metrics
- **Caching**: 10-second cache to reduce check overhead
- **FastAPI Integration**: Ready-to-use router

## Architecture

```
HealthChecker
├── Redis Health Check
│   ├── Connectivity test
│   ├── Response time measurement
│   └── Server info collection
├── gRPC Service Health Checks
│   ├── STT Service
│   ├── NLP Service
│   └── Summary Service
└── Metrics Collection
    ├── gRPC pool metrics
    ├── Redis statistics
    └── System uptime
```

## Endpoints

### GET /health

Comprehensive health check with all components.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-21T20:00:00Z",
  "uptime_seconds": 3600.5,
  "version": "1.0.0",
  "components": {
    "redis": {
      "name": "redis",
      "type": "redis",
      "status": "healthy",
      "message": "Connected",
      "response_time_ms": 2.5,
      "last_check": "2025-11-21T20:00:00Z",
      "metadata": {
        "version": "7.2.0",
        "connected_clients": 5,
        "used_memory_human": "2.5M",
        "uptime_days": 10
      }
    },
    "grpc_stt": {
      "name": "grpc_stt",
      "type": "grpc_stt",
      "status": "healthy",
      "message": "All 3 connections healthy",
      "response_time_ms": 1.2,
      "metadata": {
        "pool_size": 3,
        "healthy_connections": 3,
        "total_requests": 1500,
        "success_rate": 99.8,
        "avg_response_time_ms": 45.2
      }
    }
  },
  "summary": {
    "total_components": 4,
    "healthy": 4,
    "degraded": 0,
    "unhealthy": 0
  }
}
```

### GET /health/ready

Readiness probe for Kubernetes.

**Success Response (200):**
```json
{
  "status": "ready",
  "timestamp": "2025-11-21T20:00:00Z"
}
```

**Not Ready Response (503):**
```json
{
  "status": "not_ready",
  "timestamp": "2025-11-21T20:00:00Z"
}
```

**Readiness Criteria:**
- Redis is healthy
- At least one gRPC service is healthy

### GET /health/live

Liveness probe for Kubernetes.

**Success Response (200):**
```json
{
  "status": "alive",
  "timestamp": "2025-11-21T20:00:00Z"
}
```

**Dead Response (503):**
```json
{
  "status": "dead",
  "timestamp": "2025-11-21T20:00:00Z"
}
```

### GET /health/metrics

Detailed service metrics.

**Response:**
```json
{
  "timestamp": "2025-11-21T20:00:00Z",
  "uptime_seconds": 3600.5,
  "grpc_pools": {
    "stt": {
      "service": "stt",
      "pool_size": 3,
      "healthy_connections": 3,
      "total_requests": 1500,
      "successful_requests": 1497,
      "failed_requests": 3,
      "success_rate": 0.998,
      "total_reconnections": 2,
      "avg_response_time_ms": 45.2
    },
    "nlp": { ... },
    "summary": { ... }
  },
  "redis_stats": {
    "version": "7.2.0",
    "uptime_days": 10,
    "connected_clients": 5,
    "used_memory_bytes": 2621440,
    "used_memory_human": "2.5M",
    "total_commands_processed": 50000,
    "instantaneous_ops_per_sec": 10
  },
  "system_stats": {
    "uptime_seconds": 3600.5,
    "start_time": "2025-11-21T19:00:00Z"
  }
}
```

## Usage

### Basic Setup

```python
from src.agents.orchestrator.health import (
    HealthChecker,
    initialize_health_checker,
    create_health_router
)
from fastapi import FastAPI

# Initialize health checker
health_checker = await initialize_health_checker(
    redis_url="redis://localhost:6379/0"
)

# Create FastAPI app
app = FastAPI()

# Add health check router
health_router = create_health_router(health_checker)
app.include_router(health_router)
```

### FastAPI Lifespan Integration

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    health_checker = await initialize_health_checker()
    app.state.health_checker = health_checker

    yield

    # Shutdown
    await close_health_checker()

app = FastAPI(lifespan=lifespan)

# Add health router after initialization
@app.on_event("startup")
async def setup_routes():
    health_router = create_health_router(app.state.health_checker)
    app.include_router(health_router)
```

### Manual Health Checks

```python
from src.agents.orchestrator.health import get_health_checker

health_checker = get_health_checker()

# Check overall health
health_status = await health_checker.get_health_status()
print(f"Status: {health_status.status}")

# Check readiness
is_ready = await health_checker.get_readiness()
print(f"Ready: {is_ready}")

# Check liveness
is_alive = await health_checker.get_liveness()
print(f"Alive: {is_alive}")

# Get metrics
metrics = await health_checker.get_metrics()
print(f"Metrics: {metrics}")
```

### Component-Specific Checks

```python
# Check Redis
redis_health = await health_checker.check_redis()
print(f"Redis: {redis_health.status}")
print(f"Response Time: {redis_health.response_time_ms}ms")

# Check gRPC service
from src.shared.protocols.grpc_pool import ServiceType

stt_health = await health_checker.check_grpc_service(ServiceType.STT)
print(f"STT Service: {stt_health.status}")
print(f"Message: {stt_health.message}")
```

## Health Status

### Status Values

- **healthy**: All checks pass, component fully operational
- **degraded**: Component partially operational (e.g., some connections down)
- **unhealthy**: Component not operational

### Component Types

- **redis**: Redis cache/message broker
- **grpc_stt**: Speech-to-Text gRPC service
- **grpc_nlp**: NLP Analysis gRPC service
- **grpc_summary**: Summarization gRPC service
- **system**: System resources and uptime

## Kubernetes Integration

### Deployment YAML

```yaml
apiVersion: v1
kind: Service
metadata:
  name: orchestrator
spec:
  selector:
    app: orchestrator
  ports:
    - port: 8000
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orchestrator
  template:
    metadata:
      labels:
        app: orchestrator
    spec:
      containers:
      - name: orchestrator
        image: orchestrator:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
```

## Caching

Health checks are cached for 10 seconds to reduce overhead:

- Component health checks cache results
- Subsequent requests within 10 seconds return cached data
- Reduces load on Redis and gRPC services

```python
# Configure cache TTL
health_checker._cache_ttl = 15.0  # 15 seconds
```

## Error Handling

The module handles various error scenarios gracefully:

- **Redis Unavailable**: Returns unhealthy status with error message
- **gRPC Service Down**: Returns unhealthy status for that service
- **Timeout**: Returns unhealthy status after timeout
- **Partial Failure**: Returns degraded status

## Performance

- **Check Timeout**: 5 seconds (configurable)
- **Cache TTL**: 10 seconds
- **Background Health Checks**: Not blocking
- **Async Operations**: Non-blocking health checks

## Monitoring and Alerting

### Prometheus Integration

The `/health/metrics` endpoint can be scraped by Prometheus:

```yaml
scrape_configs:
  - job_name: 'orchestrator'
    static_configs:
      - targets: ['orchestrator:8000']
    metrics_path: '/health/metrics'
    scrape_interval: 15s
```

### Grafana Dashboard

Example queries:

```promql
# gRPC Success Rate
rate(grpc_successful_requests[5m]) / rate(grpc_total_requests[5m])

# Average Response Time
avg(grpc_avg_response_time_ms)

# Redis Operations per Second
redis_instantaneous_ops_per_sec
```

## Testing

```bash
# Manual test
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/live
curl http://localhost:8000/health/metrics

# Automated tests
pytest tests/test_health.py
```

## Logging

The module logs to `src.agents.orchestrator.health`:

```python
import logging
logging.getLogger('src.agents.orchestrator.health').setLevel(logging.INFO)
```

Log events include:
- Health check initialization
- Component failures
- Redis connection issues
- gRPC service unavailability
