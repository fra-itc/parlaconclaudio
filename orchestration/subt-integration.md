# ISTRUZIONI PER CLAUDE CODE CLI - INTEGRATION TEAM
## FastAPI Backend + Redis Orchestration + Docker

**IMPORTANTE**: Agente autonomo nel worktree `RTSTT-integration` (branch: `feature/backend-api`). Parallelizza con **5 sub-agenti, 2 ondate**.

---

## 🎯 OBIETTIVO
Backend FastAPI come WebSocket gateway + Redis message router + Docker infrastructure

## 📊 TARGET
- **Durata**: 4-6 ore
- **Parallelismo**: 2 ondate, 5 sub-agenti
- **Components**: FastAPI + Redis + gRPC + Docker + Prometheus

---

## 🔀 STRATEGIA PARALLELIZZAZIONE

```
ONDATA 1: Core Services (3 paralleli)
├── Sub-Agent 1: FastAPI App + WebSocket Gateway
├── Sub-Agent 2: Redis Client + Message Router
└── Sub-Agent 3: gRPC Pool + Health Checks
      ↓
ONDATA 2: Infrastructure (2 paralleli)
├── Sub-Agent 4: Docker Infrastructure (4 Dockerfiles)
└── Sub-Agent 5: Monitoring (Prometheus + Grafana)
```

### CONFLICT AVOIDANCE
- Sub-Agent 1 → `src/agents/orchestrator/fastapi_app.py`, `websocket_gateway.py`
- Sub-Agent 2 → `src/shared/protocols/redis_client.py`, `message_router.py`
- Sub-Agent 3 → `src/shared/protocols/grpc_pool.py`, `health.py`
- Sub-Agent 4 → `infrastructure/docker/*`
- Sub-Agent 5 → `infrastructure/monitoring/*`

---

## 🚀 ONDATA 1: CORE SERVICES

### Sub-Agent 1: FastAPI + WebSocket
**Task tool**:
```
Implementa FastAPI backend con WebSocket gateway:

FILES:
- src/agents/orchestrator/fastapi_app.py
- src/agents/orchestrator/websocket_gateway.py

COMANDI:
pip install fastapi uvicorn websockets

DELIVERABLE: API server su porta 8000 con WS endpoint
COMMIT: "[INTEGRATION-SUB-1] FastAPI + WebSocket"
```

### Sub-Agent 2: Redis + Router
**Task tool**:
```
Implementa Redis client e message router:

FILES:
- src/shared/protocols/redis_client.py
- src/agents/orchestrator/message_router.py

DELIVERABLE: Redis consumer routing a WebSocket
COMMIT: "[INTEGRATION-SUB-2] Redis + Router"
```

### Sub-Agent 3: gRPC Pool + Health
**Task tool**:
```
Implementa gRPC connection pool e health checks:

FILES:
- src/shared/protocols/grpc_pool.py
- src/agents/orchestrator/health.py

DELIVERABLE: gRPC pool con connection management
COMMIT: "[INTEGRATION-SUB-3] gRPC Pool + Health"
```

---

## ⏸️ SYNC POINT 1

---

## 🚀 ONDATA 2: INFRASTRUCTURE

### Sub-Agent 4: Docker Infrastructure
**Task tool**:
```
Crea Dockerfiles per tutti i servizi:

FILES:
- infrastructure/docker/Dockerfile.backend
- infrastructure/docker/Dockerfile.stt
- infrastructure/docker/Dockerfile.nlp
- infrastructure/docker/Dockerfile.summary

DELIVERABLE: 4 Dockerfiles + docker-compose update
COMMIT: "[INTEGRATION-SUB-4] Docker infrastructure"
```

### Sub-Agent 5: Monitoring Stack
**Task tool**:
```
Setup Prometheus + Grafana monitoring:

FILES:
- infrastructure/monitoring/prometheus.yml
- infrastructure/monitoring/grafana/dashboards/
- src/agents/orchestrator/metrics.py

DELIVERABLE: Monitoring stack completo
COMMIT: "[INTEGRATION-SUB-5] Monitoring stack"
```

---

## ✅ VALIDAZIONE
```bash
docker-compose up -d
curl http://localhost:8000/health
curl http://localhost:9090  # Prometheus
```

---

**FINE INTEGRATION TEAM**
