# RTSTT Monitoring Stack

Production-ready monitoring solution for the RTSTT Integration Platform using Prometheus and Grafana.

## Overview

This monitoring stack provides comprehensive observability for all RTSTT services:

- **Prometheus**: Time-series database for metrics collection
- **Grafana**: Visualization and dashboarding
- **Redis Exporter**: Metrics from Redis message queue
- **Custom Metrics**: Application-specific business metrics

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Backend   │────▶│ Prometheus  │────▶│   Grafana   │
│   :8000     │     │   :9090     │     │   :3001     │
└─────────────┘     └─────────────┘     └─────────────┘
       │                    ▲                    │
       │                    │                    │
┌─────────────┐     ┌─────────────┐            │
│ STT Engine  │────▶│   Redis     │            │
│   :50051    │     │  Exporter   │            │
└─────────────┘     │   :9121     │            │
       │            └─────────────┘            │
       │                                        │
┌─────────────┐                                │
│ NLP Service │                                │
│   :50052    │                                │
└─────────────┘                                ▼
       │                              Dashboard Viewer
┌─────────────┐
│  Summary    │
│   :50053    │
└─────────────┘
```

## Components

### 1. Prometheus (Port 9090)

**Configuration**: `infrastructure/monitoring/prometheus.yml`

Scrapes metrics from:
- Backend API (FastAPI): `backend:8000/metrics`
- STT Engine: `stt-engine:50051/metrics`
- NLP Service: `nlp-service:50052/metrics`
- Summary Service: `summary-service:50053/metrics`
- Redis Exporter: `redis-exporter:9121/metrics`

**Scrape interval**: 15 seconds
**Retention**: 30 days

### 2. Grafana (Port 3001)

**Default Credentials**:
- Username: `admin`
- Password: `admin`

**Auto-provisioned**:
- Prometheus datasource
- RTSTT Production Dashboard

**Access**: http://localhost:3001

### 3. Redis Exporter (Port 9121)

Exports Redis metrics:
- Connected clients
- Memory usage
- Commands processed
- Pub/Sub channels and patterns
- Keyspace statistics

### 4. Metrics Instrumentation

**File**: `src/agents/orchestrator/metrics.py`

Provides:
- FastAPI middleware for automatic HTTP tracking
- Custom metrics for WebSocket, Redis, gRPC
- Helper functions for business metrics

## Metrics Collected

### HTTP Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests by endpoint, method, status |
| `http_request_duration_seconds` | Histogram | Request latency distribution |
| `http_request_size_bytes` | Summary | Request payload size |
| `http_response_size_bytes` | Summary | Response payload size |
| `http_requests_in_progress` | Gauge | Current active requests |

### WebSocket Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `websocket_connections_active` | Gauge | Active WebSocket connections |
| `websocket_connections_total` | Counter | Total WebSocket connections |
| `websocket_messages_sent_total` | Counter | Messages sent to clients |
| `websocket_messages_received_total` | Counter | Messages received from clients |
| `websocket_connection_duration_seconds` | Histogram | Connection duration |

### Redis Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `redis_messages_published_total` | Counter | Messages published to channels |
| `redis_messages_received_total` | Counter | Messages received from channels |
| `redis_operation_duration_seconds` | Histogram | Redis operation latency |
| `redis_active_subscriptions` | Gauge | Active channel subscriptions |
| `redis_up` | Gauge | Redis health status (1=up, 0=down) |
| `redis_connected_clients` | Gauge | Connected clients count |

### gRPC Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `grpc_requests_total` | Counter | gRPC requests by service, method, status |
| `grpc_request_duration_seconds` | Histogram | gRPC request latency |

### Business Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `transcription_sessions_active` | Gauge | Active transcription sessions |
| `transcription_sessions_total` | Counter | Total sessions by status |
| `audio_chunks_processed_total` | Counter | Audio chunks processed |
| `transcription_results_total` | Counter | Transcription results (interim/final) |

## Dashboard Panels

The Grafana dashboard includes:

1. **HTTP Request Latency (p95/p99)**: Response time percentiles
2. **HTTP Request Throughput**: Requests per second
3. **HTTP Error Rate (5xx)**: Server error percentage
4. **HTTP Requests by Status Code**: Status code distribution
5. **Active WebSocket Connections**: Real-time connection count
6. **WebSocket Message Rate**: Messages sent/received
7. **Redis Pub/Sub Message Rate**: Redis message throughput
8. **Redis Operation Latency (p95)**: Redis performance
9. **gRPC Request Rate**: gRPC calls per second
10. **gRPC Request Latency (p95)**: gRPC performance
11. **gRPC Error Rate**: gRPC failure rate
12. **Active Transcription Sessions**: Business metric
13. **Redis Connected Clients**: Connection distribution
14. **Redis Health Status**: Service availability

## Quick Start

### 1. Start Monitoring Stack

```bash
# Start all services including monitoring
docker-compose up -d

# Start only monitoring services
docker-compose up -d prometheus grafana redis-exporter
```

### 2. Access Dashboards

- **Grafana UI**: http://localhost:3001
  - Login: `admin` / `admin`
  - Navigate to: Dashboards → RTSTT → RTSTT Integration Platform

- **Prometheus UI**: http://localhost:9090
  - Query metrics directly
  - View targets: http://localhost:9090/targets

- **Redis Exporter**: http://localhost:9121/metrics
  - Raw Redis metrics

### 3. Integration with FastAPI

```python
from fastapi import FastAPI
from src.agents.orchestrator.metrics import setup_metrics

app = FastAPI()

# Enable automatic metrics collection
setup_metrics(app)

# Metrics endpoint available at: /metrics
```

### 4. Manual Metric Tracking

```python
from src.agents.orchestrator.metrics import (
    track_websocket_connection,
    track_websocket_message,
    track_redis_message,
    track_transcription_session,
)

# Track WebSocket lifecycle
track_websocket_connection(endpoint="/ws/transcribe", connected=True)
track_websocket_message(endpoint="/ws/transcribe", message_type="audio", sent=False)

# Track Redis pub/sub
track_redis_message(channel="transcription_requests", published=True)

# Track business metrics
track_transcription_session(session_id="sess_123", status="started")
```

## Health Checks

### Check Prometheus Targets

```bash
curl http://localhost:9090/api/v1/targets
```

All targets should show status "up".

### Check Metrics Endpoint

```bash
# Backend metrics
curl http://localhost:8000/metrics

# Redis metrics
curl http://localhost:9121/metrics
```

### Check Grafana

```bash
# Health check
curl http://localhost:3001/api/health

# List datasources
curl -u admin:admin http://localhost:3001/api/datasources
```

## Troubleshooting

### Prometheus Not Scraping

1. Check target status: http://localhost:9090/targets
2. Verify service is exposing `/metrics` endpoint
3. Check network connectivity: `docker-compose exec prometheus ping backend`

### Grafana Dashboard Not Loading

1. Verify Prometheus datasource: Grafana → Configuration → Data Sources
2. Check provisioning: `docker-compose exec grafana ls /etc/grafana/provisioning/dashboards`
3. Restart Grafana: `docker-compose restart grafana`

### Missing Metrics

1. Verify metrics.py is imported in FastAPI app
2. Check Prometheus scrape config
3. Ensure service is running and accessible

### High Cardinality Warning

If you see warnings about high cardinality:
- Avoid using user IDs or session IDs as label values
- Use aggregation in queries
- Limit the number of unique label combinations

## Best Practices

### 1. Metric Naming

- Use snake_case: `http_requests_total`
- Include units in name: `_seconds`, `_bytes`, `_total`
- Be descriptive but concise

### 2. Label Usage

- Keep cardinality low (< 1000 unique combinations)
- Use labels for dimensions: `endpoint`, `method`, `status_code`
- Avoid high-cardinality labels: user IDs, timestamps

### 3. Query Performance

- Use recording rules for expensive queries
- Limit time range for high-resolution data
- Use appropriate step interval in Grafana

### 4. Alerting (Future)

Recommended alerts to implement:

- High error rate (> 5%)
- High latency (p95 > 2s)
- Low availability (< 99%)
- High memory usage (> 80%)
- Redis connection failures

## Configuration Files

```
infrastructure/monitoring/
├── prometheus.yml                          # Prometheus configuration
├── grafana/
│   ├── dashboards/
│   │   └── rtstt-dashboard.json           # Main dashboard
│   └── provisioning/
│       ├── datasources/
│       │   └── prometheus.yml             # Auto-configure Prometheus
│       └── dashboards/
│           └── dashboard.yml              # Auto-import dashboards
└── README.md                               # This file
```

## Maintenance

### Update Retention

Edit `docker-compose.yml`:

```yaml
prometheus:
  command:
    - '--storage.tsdb.retention.time=30d'  # Change retention period
```

### Backup Grafana

```bash
# Export dashboards
docker-compose exec grafana grafana-cli admin export-dashboard

# Backup data volume
docker run --rm -v rtstt_grafana_data:/data -v $(pwd):/backup alpine tar czf /backup/grafana-backup.tar.gz /data
```

### Update Dashboard

1. Edit dashboard in Grafana UI
2. Export as JSON: Dashboard → Share → Export
3. Save to `infrastructure/monitoring/grafana/dashboards/rtstt-dashboard.json`
4. Restart Grafana to reload

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Redis Exporter](https://github.com/oliver006/redis_exporter)
- [Prometheus Client Python](https://github.com/prometheus/client_python)

## Support

For issues or questions:
- Check logs: `docker-compose logs prometheus grafana`
- Review Prometheus targets: http://localhost:9090/targets
- Verify Grafana datasource connectivity
