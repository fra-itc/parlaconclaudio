"""
Prometheus Metrics Integration for RTSTT Orchestrator
======================================================

This module provides Prometheus metrics collection and exposition for the RTSTT platform.
It integrates with FastAPI to automatically track HTTP requests, WebSocket connections,
gRPC calls, and Redis pub/sub activity.

Features:
- Automatic HTTP request tracking (latency, count, errors)
- WebSocket connection monitoring
- Redis message queue metrics
- gRPC service health and performance
- Custom business metrics
- FastAPI middleware for automatic instrumentation

Usage:
    from src.agents.orchestrator.metrics import setup_metrics, track_redis_message

    app = FastAPI()
    setup_metrics(app)  # Adds /metrics endpoint and middleware

    # Manual metric tracking
    track_redis_message("transcription_request")

Author: RTSTT Integration Team
Version: 1.0.0
"""

from typing import Callable, Dict, Optional
import time
from functools import wraps

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR


# ============================================================================
# Prometheus Registry
# ============================================================================

# Use the default registry
REGISTRY = CollectorRegistry()


# ============================================================================
# Core HTTP Metrics
# ============================================================================

# Request counter by endpoint, method, and status
http_requests_total = Counter(
    name='http_requests_total',
    documentation='Total number of HTTP requests',
    labelnames=['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)

# Request duration histogram
http_request_duration_seconds = Histogram(
    name='http_request_duration_seconds',
    documentation='HTTP request duration in seconds',
    labelnames=['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=REGISTRY
)

# Request size
http_request_size_bytes = Summary(
    name='http_request_size_bytes',
    documentation='HTTP request size in bytes',
    labelnames=['method', 'endpoint'],
    registry=REGISTRY
)

# Response size
http_response_size_bytes = Summary(
    name='http_response_size_bytes',
    documentation='HTTP response size in bytes',
    labelnames=['method', 'endpoint'],
    registry=REGISTRY
)

# In-flight requests
http_requests_in_progress = Gauge(
    name='http_requests_in_progress',
    documentation='Number of HTTP requests currently being processed',
    labelnames=['method', 'endpoint'],
    registry=REGISTRY
)


# ============================================================================
# WebSocket Metrics
# ============================================================================

# Active WebSocket connections
websocket_connections_active = Gauge(
    name='websocket_connections_active',
    documentation='Number of active WebSocket connections',
    labelnames=['endpoint'],
    registry=REGISTRY
)

# Total WebSocket connections
websocket_connections_total = Counter(
    name='websocket_connections_total',
    documentation='Total number of WebSocket connections',
    labelnames=['endpoint'],
    registry=REGISTRY
)

# WebSocket messages sent
websocket_messages_sent_total = Counter(
    name='websocket_messages_sent_total',
    documentation='Total number of WebSocket messages sent',
    labelnames=['endpoint', 'message_type'],
    registry=REGISTRY
)

# WebSocket messages received
websocket_messages_received_total = Counter(
    name='websocket_messages_received_total',
    documentation='Total number of WebSocket messages received',
    labelnames=['endpoint', 'message_type'],
    registry=REGISTRY
)

# WebSocket connection duration
websocket_connection_duration_seconds = Histogram(
    name='websocket_connection_duration_seconds',
    documentation='WebSocket connection duration in seconds',
    labelnames=['endpoint'],
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600],
    registry=REGISTRY
)


# ============================================================================
# Redis Pub/Sub Metrics
# ============================================================================

# Redis messages published
redis_messages_published_total = Counter(
    name='redis_messages_published_total',
    documentation='Total number of Redis messages published',
    labelnames=['channel'],
    registry=REGISTRY
)

# Redis messages received
redis_messages_received_total = Counter(
    name='redis_messages_received_total',
    documentation='Total number of Redis messages received',
    labelnames=['channel'],
    registry=REGISTRY
)

# Redis operation duration
redis_operation_duration_seconds = Histogram(
    name='redis_operation_duration_seconds',
    documentation='Redis operation duration in seconds',
    labelnames=['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
    registry=REGISTRY
)

# Active Redis subscriptions
redis_active_subscriptions = Gauge(
    name='redis_active_subscriptions',
    documentation='Number of active Redis channel subscriptions',
    registry=REGISTRY
)


# ============================================================================
# gRPC Service Metrics
# ============================================================================

# gRPC requests
grpc_requests_total = Counter(
    name='grpc_requests_total',
    documentation='Total number of gRPC requests',
    labelnames=['service', 'method', 'status'],
    registry=REGISTRY
)

# gRPC request duration
grpc_request_duration_seconds = Histogram(
    name='grpc_request_duration_seconds',
    documentation='gRPC request duration in seconds',
    labelnames=['service', 'method'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
    registry=REGISTRY
)


# ============================================================================
# Business Metrics
# ============================================================================

# Transcription sessions
transcription_sessions_active = Gauge(
    name='transcription_sessions_active',
    documentation='Number of active transcription sessions',
    registry=REGISTRY
)

# Transcription sessions total
transcription_sessions_total = Counter(
    name='transcription_sessions_total',
    documentation='Total number of transcription sessions',
    labelnames=['status'],
    registry=REGISTRY
)

# Audio chunks processed
audio_chunks_processed_total = Counter(
    name='audio_chunks_processed_total',
    documentation='Total number of audio chunks processed',
    labelnames=['session_id'],
    registry=REGISTRY
)

# Transcription results
transcription_results_total = Counter(
    name='transcription_results_total',
    documentation='Total number of transcription results',
    labelnames=['type'],  # interim, final
    registry=REGISTRY
)


# ============================================================================
# Application Info
# ============================================================================

app_info = Info(
    name='rtstt_app',
    documentation='RTSTT Application Information',
    registry=REGISTRY
)

app_info.info({
    'version': '1.0.0',
    'environment': 'production',
    'platform': 'rtstt-integration',
})


# ============================================================================
# FastAPI Middleware
# ============================================================================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic Prometheus metrics collection.

    Tracks:
    - Request count, duration, size
    - Response status, size
    - In-flight requests
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        endpoint = request.url.path

        # Track in-flight requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        # Track request size
        request_size = int(request.headers.get("content-length", 0))
        if request_size > 0:
            http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(request_size)

        # Track request duration
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = HTTP_500_INTERNAL_SERVER_ERROR
            raise exc
        finally:
            # Record metrics
            duration = time.time() - start_time

            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()

            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

        # Track response size
        response_size = int(response.headers.get("content-length", 0))
        if response_size > 0:
            http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(response_size)

        return response


# ============================================================================
# Metrics Endpoint
# ============================================================================

def metrics_endpoint() -> Response:
    """
    Prometheus metrics endpoint.

    Returns:
        Response with metrics in Prometheus format
    """
    return PlainTextResponse(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# Setup Function
# ============================================================================

def setup_metrics(app: FastAPI) -> None:
    """
    Setup Prometheus metrics for FastAPI application.

    Args:
        app: FastAPI application instance

    Usage:
        app = FastAPI()
        setup_metrics(app)
    """
    # Add middleware
    app.add_middleware(PrometheusMiddleware)

    # Add metrics endpoint
    app.add_route("/metrics", metrics_endpoint, methods=["GET"])


# ============================================================================
# Helper Functions
# ============================================================================

def track_websocket_connection(endpoint: str, connected: bool = True) -> None:
    """
    Track WebSocket connection state.

    Args:
        endpoint: WebSocket endpoint
        connected: True if connecting, False if disconnecting
    """
    if connected:
        websocket_connections_active.labels(endpoint=endpoint).inc()
        websocket_connections_total.labels(endpoint=endpoint).inc()
    else:
        websocket_connections_active.labels(endpoint=endpoint).dec()


def track_websocket_message(endpoint: str, message_type: str, sent: bool = True) -> None:
    """
    Track WebSocket message.

    Args:
        endpoint: WebSocket endpoint
        message_type: Type of message (e.g., 'audio', 'transcript', 'control')
        sent: True if sent, False if received
    """
    if sent:
        websocket_messages_sent_total.labels(
            endpoint=endpoint,
            message_type=message_type
        ).inc()
    else:
        websocket_messages_received_total.labels(
            endpoint=endpoint,
            message_type=message_type
        ).inc()


def track_redis_message(channel: str, published: bool = True) -> None:
    """
    Track Redis pub/sub message.

    Args:
        channel: Redis channel name
        published: True if published, False if received
    """
    if published:
        redis_messages_published_total.labels(channel=channel).inc()
    else:
        redis_messages_received_total.labels(channel=channel).inc()


def track_redis_operation(operation: str):
    """
    Decorator to track Redis operation duration.

    Args:
        operation: Operation name (e.g., 'publish', 'subscribe', 'get', 'set')

    Usage:
        @track_redis_operation('publish')
        async def publish_message(channel, message):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                redis_operation_duration_seconds.labels(operation=operation).observe(duration)
        return wrapper
    return decorator


def track_grpc_request(service: str, method: str, status: str = "success") -> None:
    """
    Track gRPC request.

    Args:
        service: Service name (e.g., 'stt-engine', 'nlp-service')
        method: Method name
        status: Request status ('success' or 'error')
    """
    grpc_requests_total.labels(service=service, method=method, status=status).inc()


def track_grpc_duration(service: str, method: str):
    """
    Decorator to track gRPC request duration.

    Args:
        service: Service name
        method: Method name

    Usage:
        @track_grpc_duration('stt-engine', 'transcribe')
        async def call_stt_service():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                track_grpc_request(service, method, "success")
                return result
            except Exception as exc:
                track_grpc_request(service, method, "error")
                raise exc
            finally:
                duration = time.time() - start_time
                grpc_request_duration_seconds.labels(service=service, method=method).observe(duration)
        return wrapper
    return decorator


def track_transcription_session(session_id: str, status: str = "started") -> None:
    """
    Track transcription session lifecycle.

    Args:
        session_id: Session ID
        status: Session status ('started', 'completed', 'failed')
    """
    if status == "started":
        transcription_sessions_active.inc()
        transcription_sessions_total.labels(status="started").inc()
    elif status in ["completed", "failed"]:
        transcription_sessions_active.dec()
        transcription_sessions_total.labels(status=status).inc()


# ============================================================================
# Export Public API
# ============================================================================

__all__ = [
    "setup_metrics",
    "track_websocket_connection",
    "track_websocket_message",
    "track_redis_message",
    "track_redis_operation",
    "track_grpc_request",
    "track_grpc_duration",
    "track_transcription_session",
    # Metrics
    "http_requests_total",
    "http_request_duration_seconds",
    "websocket_connections_active",
    "redis_messages_published_total",
    "grpc_requests_total",
    "transcription_sessions_active",
]
