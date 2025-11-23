# RTSTT Parallel Deployment Verification & Testing Orchestration

**Terminal Role**: Orchestrator Terminal
**Framework**: ORCHIDEA v1.3
**HAS Level**: H3 (Human-Supervised)
**Execution Mode**: Parallel with GPU Safety
**Estimated Duration**: 45-60 minutes
**Last Updated**: 2025-11-22

---

## Mission Statement

Execute comprehensive parallel deployment verification, health checks, and testing for the RTSTT (Real-Time Speech-to-Text Orchestrator) system. Coordinate multiple specialized agents to validate all system components while respecting GPU memory constraints and service dependencies.

---

## System Context

### Architecture Overview
- **Repository**: `/home/frisco/projects/RTSTT`
- **Services**: 7 Docker containers (Redis, Backend, STT, NLP, Summary, Prometheus, Grafana)
- **ML Models**: Whisper Large V3, Llama-3.2-8B (8-bit), FLAN-T5
- **GPU**: RTX 5080 Blackwell (validated), CUDA 12.8, PyTorch 2.7.0+cu128
- **Frontend**: Electron + React desktop application
- **Testing**: 92+ unit tests, integration tests, benchmarks

### Performance Targets
- End-to-end latency: <100ms (P95)
- Word Error Rate: <5%
- GPU memory: <14GB operational
- Test coverage: >95%
- Audio capture latency: <10ms

### Critical Constraints
- **GPU Memory**: Sequential ML model loading (prevent OOM)
- **Service Dependencies**: Redis must start before backend/ML services
- **Windows-Specific**: WASAPI tests require Windows 11 hardware
- **Model Downloads**: First run requires ~15GB model downloads

---

## Orchestration Strategy

### Execution Principles

1. **Maximize Parallelization**: Launch independent tasks concurrently
2. **Respect Dependencies**: Sequential execution where required (GPU, service startup)
3. **Fail-Fast**: Stop phase on critical failures, continue on warnings
4. **Resource-Aware**: Monitor GPU memory, prevent OOM conditions
5. **Comprehensive Logging**: Capture all outputs for post-mortem analysis

### Agent Coordination

- **Total Agents**: 21 specialized agents across 5 phases
- **Concurrent Max**: 5 agents (Phase 1), limited by GPU in later phases
- **Communication**: Shared status via stdout/files, no inter-agent messaging
- **Timeout**: 10 minutes per agent, 2 hours overall

---

## PHASE 1: Pre-Deployment Validation

**Objective**: Verify environment readiness before Docker deployment
**Duration**: ~5 minutes
**Parallelization**: 5 concurrent agents
**Failure Mode**: ABORT deployment if any critical check fails

### Agent 1.1: Environment Infrastructure Check

**Tasks**:
```bash
# Docker daemon status
docker --version
docker ps > /dev/null 2>&1 && echo "✅ Docker running" || echo "❌ Docker not running"

# NVIDIA driver and CUDA
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
nvcc --version | grep "release"

# Python environment
python --version
pip list | grep -E "(torch|transformers|faster-whisper)"

# Node.js for Electron
node --version
npm --version
```

**Success Criteria**:
- Docker daemon running
- NVIDIA driver ≥560.94 (RTX 5080 support)
- CUDA 12.8 available
- Python 3.11+
- PyTorch 2.7.0+cu128 installed
- Node.js 18+ and npm available

**Report Format**:
```
ENVIRONMENT CHECK REPORT
========================
Docker: [VERSION] - [STATUS]
NVIDIA Driver: [VERSION] - [STATUS]
CUDA: [VERSION] - [STATUS]
Python: [VERSION] - [STATUS]
PyTorch: [VERSION]+[CUDA] - [STATUS]
Node.js: [VERSION] - [STATUS]

STATUS: [PASS/FAIL]
BLOCKERS: [List any critical issues]
```

---

### Agent 1.2: Configuration Validation

**Tasks**:
```bash
# Check .env.local exists
test -f .env.local && echo "✅ .env.local found" || echo "❌ .env.local missing"

# Validate critical environment variables (without exposing values)
grep -q "HF_TOKEN=" .env.local && echo "✅ HF_TOKEN set" || echo "⚠️  HF_TOKEN missing"
grep -q "REDIS_HOST=" .env.local && echo "✅ REDIS_HOST set" || echo "⚠️  REDIS_HOST missing"
grep -q "BACKEND_PORT=" .env.local && echo "✅ BACKEND_PORT set" || echo "⚠️  BACKEND_PORT missing"

# Check Redis configuration
grep "maxmemory" infrastructure/monitoring/redis.conf || echo "⚠️  Redis maxmemory not configured"

# GPU memory availability
nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits
```

**Success Criteria**:
- `.env.local` file exists
- HF_TOKEN configured (required for Llama, PyAnnote)
- Redis configuration valid
- ≥16GB GPU memory free

**Report Format**:
```
CONFIGURATION VALIDATION REPORT
================================
.env.local: [FOUND/MISSING]
HF_TOKEN: [SET/MISSING]
REDIS_HOST: [SET/MISSING]
BACKEND_PORT: [SET/MISSING]
GPU Memory Free: [XX.X] GB

STATUS: [PASS/FAIL/WARNING]
WARNINGS: [List non-critical issues]
```

---

### Agent 1.3: Model Availability Check

**Tasks**:
```bash
# Check Whisper Large V3
test -d models/whisper/large-v3 && echo "✅ Whisper Large V3 found" || echo "❌ Whisper Large V3 missing"

# Check Llama model
test -d models/transformers/llama-3.2-8b-instruct && echo "✅ Llama-3.2-8B found" || echo "⚠️  Llama-3.2-8B missing"

# Check FLAN-T5 (fallback summarizer)
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('google/flan-t5-base'); print('✅ FLAN-T5 accessible')" 2>/dev/null || echo "⚠️  FLAN-T5 not cached"

# Check Silero VAD
test -f models/silero_vad.onnx && echo "✅ Silero VAD found" || echo "⚠️  Silero VAD missing"

# Disk space check
df -h . | tail -1 | awk '{print "Disk free:", $4}'
```

**Success Criteria**:
- Whisper Large V3 model files present (critical)
- At least one summarization model available (Llama or FLAN-T5)
- Silero VAD model present
- ≥20GB disk space free

**Report Format**:
```
MODEL AVAILABILITY REPORT
==========================
Whisper Large V3: [FOUND/MISSING] - [SIZE]
Llama-3.2-8B: [FOUND/MISSING] - [SIZE]
FLAN-T5-base: [CACHED/NOT_CACHED]
Silero VAD: [FOUND/MISSING]
Disk Space Free: [XX.X] GB

STATUS: [PASS/FAIL]
CRITICAL_MISSING: [List critical missing models]
WARNINGS: [List optional missing models]
```

---

### Agent 1.4: Code Quality Scan

**Tasks**:
```bash
# Type checking with mypy
echo "Running mypy type checks..."
mypy src/ --ignore-missing-imports --no-error-summary 2>&1 | head -20

# Linting with flake8
echo "Running flake8 linting..."
flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics

# Check test coverage configuration
grep "cov-report" pyproject.toml && echo "✅ Coverage configured"

# Count total tests
find tests/ -name "test_*.py" -type f | wc -l
```

**Success Criteria**:
- No critical mypy errors (allow warnings)
- No flake8 syntax errors (E9, F63, F7, F82)
- Test coverage configured in pyproject.toml
- ≥10 test files present

**Report Format**:
```
CODE QUALITY SCAN REPORT
=========================
MyPy Errors: [COUNT]
Flake8 Syntax Errors: [COUNT]
Test Files: [COUNT]
Coverage Config: [FOUND/MISSING]

STATUS: [PASS/FAIL]
CRITICAL_ISSUES: [List blocking issues]
WARNINGS: [List non-blocking issues]
```

---

### Agent 1.5: Documentation Completeness Review

**Tasks**:
```bash
# Check main documentation files
test -f README.md && echo "✅ README.md exists" || echo "❌ README.md missing"
test -f docs/ARCHITECTURE.md && echo "✅ ARCHITECTURE.md exists" || echo "⚠️  ARCHITECTURE.md missing"
test -f docs/API.md && echo "✅ API.md exists" || echo "⚠️  API.md missing"

# Check orchestration documentation
test -f KB/orchestrator.agent.md && echo "✅ Orchestrator spec exists" || echo "❌ Orchestrator spec missing"

# Check deployment guides
find orchestration/ -name "*deploy*.md" -type f | wc -l

# README content validation
grep -q "Installation" README.md && echo "✅ Installation section found"
grep -q "Usage" README.md && echo "✅ Usage section found"
grep -q "Architecture" README.md && echo "✅ Architecture section found"
```

**Success Criteria**:
- README.md exists with key sections
- KB/orchestrator.agent.md exists
- At least 1 deployment guide present

**Report Format**:
```
DOCUMENTATION REVIEW REPORT
============================
README.md: [FOUND/MISSING]
ARCHITECTURE.md: [FOUND/MISSING]
API.md: [FOUND/MISSING]
Orchestrator Spec: [FOUND/MISSING]
Deployment Guides: [COUNT]

README Sections:
- Installation: [FOUND/MISSING]
- Usage: [FOUND/MISSING]
- Architecture: [FOUND/MISSING]

STATUS: [PASS/FAIL]
MISSING: [List missing critical docs]
```

---

### Phase 1 Checkpoint

**Orchestrator Action**: Collect all 5 agent reports

**Decision Logic**:
```
IF all critical checks PASS:
    → Proceed to Phase 2 (Docker Deployment)
ELSE IF only warnings:
    → Prompt user: "Continue with warnings? (Y/n)"
ELSE:
    → ABORT: "Critical pre-deployment checks failed. Fix issues before deployment."
```

**Output**: Phase 1 Summary Report
```
PHASE 1: PRE-DEPLOYMENT VALIDATION SUMMARY
===========================================
Agent 1.1 (Environment): [PASS/FAIL]
Agent 1.2 (Configuration): [PASS/FAIL/WARNING]
Agent 1.3 (Models): [PASS/FAIL]
Agent 1.4 (Code Quality): [PASS/FAIL/WARNING]
Agent 1.5 (Documentation): [PASS/FAIL/WARNING]

OVERALL: [READY/NOT_READY/PROCEED_WITH_WARNINGS]
PROCEED TO PHASE 2: [YES/NO]
```

---

## PHASE 2: Docker Deployment with Parallel Monitoring

**Objective**: Start all Docker services with real-time monitoring
**Duration**: ~3-5 minutes
**Parallelization**: 1 main thread + 4 monitoring agents
**Failure Mode**: Rollback on container startup failures

### Main Thread: Sequential Service Startup

**Execution Strategy**: Respect service dependencies

```bash
# Step 1: Start Redis (dependency for all services)
echo "=== Starting Redis ==="
docker-compose up -d redis
sleep 10  # Allow Redis to initialize

# Verify Redis is healthy
docker-compose ps redis | grep -q "(healthy)" || {
    echo "❌ Redis failed to start"
    docker-compose logs redis
    exit 1
}

# Step 2: Start ML services (GPU-dependent)
echo "=== Starting ML Services (STT, NLP, Summary) ==="
docker-compose up -d stt-engine nlp-service summary-service

# Wait for model loading (critical - models are large)
echo "⏳ Waiting 120 seconds for model loading..."
sleep 120

# Step 3: Start backend and monitoring
echo "=== Starting Backend and Monitoring ==="
docker-compose up -d backend prometheus grafana

# Final wait for full initialization
echo "⏳ Waiting 30 seconds for service stabilization..."
sleep 30

echo "✅ All services started"
```

**Critical Timing**:
- Redis: 10 seconds initialization
- ML services: 120 seconds model loading (Whisper: ~3GB, Llama: ~8GB)
- Backend/Monitoring: 30 seconds stabilization

---

### Agent 2.1: Container Status Monitor

**Tasks**: Real-time container health tracking

```bash
# Poll every 5 seconds for 3 minutes
for i in {1..36}; do
    echo "=== Container Status Check $i/36 ==="
    docker-compose ps

    # Check for unhealthy or exited containers
    UNHEALTHY=$(docker-compose ps | grep -E "(unhealthy|exited)" | wc -l)
    if [ "$UNHEALTHY" -gt 0 ]; then
        echo "⚠️  Detected unhealthy/exited containers!"
        docker-compose ps | grep -E "(unhealthy|exited)"
    fi

    sleep 5
done
```

**Alert Triggers**:
- Any container in "exited" state
- Any container showing "unhealthy" status
- Container restart loops (>3 restarts)

**Report Format**:
```
CONTAINER STATUS MONITORING REPORT
===================================
Monitoring Duration: 3 minutes
Polling Interval: 5 seconds

Service Status Timeline:
[TIMESTAMP] redis: starting → running → healthy
[TIMESTAMP] stt-engine: starting → running (loading models...) → healthy
[TIMESTAMP] nlp-service: starting → running (loading models...) → healthy
[TIMESTAMP] summary-service: starting → running (loading models...) → healthy
[TIMESTAMP] backend: starting → running → healthy
[TIMESTAMP] prometheus: starting → running → healthy
[TIMESTAMP] grafana: starting → running → healthy

ALERTS: [List any unhealthy states detected]
STATUS: [ALL_HEALTHY/ISSUES_DETECTED]
```

---

### Agent 2.2: GPU Memory Monitor

**Tasks**: Track GPU memory allocation by service

```bash
# Baseline GPU memory before services
echo "=== Baseline GPU Memory ==="
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# Monitor every 5 seconds
for i in {1..36}; do
    echo "=== GPU Memory Check $i/36 ==="
    nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader

    # Extract memory usage (in MiB)
    MEMORY_USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)

    # Alert if >15GB used (danger zone for RTX 5080 24GB)
    if [ "$MEMORY_USED" -gt 15360 ]; then
        echo "⚠️  HIGH GPU MEMORY USAGE: ${MEMORY_USED} MiB"
        nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
    fi

    sleep 5
done
```

**Alert Triggers**:
- GPU memory >15GB (approaching OOM risk)
- Sudden memory spikes (>2GB increase in 5 seconds)
- GPU utilization >90% sustained

**Report Format**:
```
GPU MEMORY MONITORING REPORT
=============================
GPU Model: [RTX 5080]
Total Memory: [24 GB]

Memory Usage Timeline:
[TIMESTAMP] Baseline: [X.X GB]
[TIMESTAMP] After Redis: [X.X GB] (+0.0 GB)
[TIMESTAMP] After STT: [X.X GB] (+3.2 GB)
[TIMESTAMP] After NLP: [X.X GB] (+1.8 GB)
[TIMESTAMP] After Summary: [X.X GB] (+4.5 GB)
[TIMESTAMP] Final Stable: [X.X GB]

Peak Memory: [X.X GB]
Process Breakdown:
- stt-engine: [X.X GB]
- nlp-service: [X.X GB]
- summary-service: [X.X GB]

ALERTS: [List any high memory warnings]
STATUS: [SAFE/WARNING/CRITICAL]
```

---

### Agent 2.3: Log Analyzer

**Tasks**: Real-time log analysis for errors and warnings

```bash
# Stream logs from all services
docker-compose logs -f --tail=0 2>&1 | while read -r line; do
    # Extract service name and message
    echo "$line"

    # Detect ERROR patterns
    if echo "$line" | grep -qi "error"; then
        echo "🔴 ERROR DETECTED: $line" >> deployment-errors.log
    fi

    # Detect WARNING patterns
    if echo "$line" | grep -qi "warning"; then
        echo "🟡 WARNING DETECTED: $line" >> deployment-warnings.log
    fi

    # Detect successful initializations
    if echo "$line" | grep -qi "server started\|ready to accept connections\|application startup complete"; then
        echo "✅ SERVICE READY: $line" >> deployment-success.log
    fi
done
```

**Critical Patterns to Detect**:
- **Errors**: "ERROR", "CRITICAL", "FATAL", "Exception", "Traceback"
- **Warnings**: "WARNING", "WARN", "deprecated"
- **Success**: "started", "ready", "listening on", "healthy"

**Report Format**:
```
LOG ANALYSIS REPORT
====================
Monitoring Duration: 3 minutes

ERROR Summary:
- [SERVICE] [TIMESTAMP]: [ERROR MESSAGE]
  ... (up to 10 most recent errors)

WARNING Summary:
- [SERVICE] [TIMESTAMP]: [WARNING MESSAGE]
  ... (up to 5 most recent warnings)

SUCCESS Events:
- [SERVICE] [TIMESTAMP]: Server started
- [SERVICE] [TIMESTAMP]: Model loaded
- [SERVICE] [TIMESTAMP]: Health check passed

CRITICAL_ERRORS: [COUNT]
WARNINGS: [COUNT]
STATUS: [CLEAN/WARNINGS/ERRORS]
```

---

### Agent 2.4: Network Port Monitor

**Tasks**: Validate service port availability and listeners

```bash
# Check expected ports
PORTS=(6379 8000 50051 50052 50053 9090 3001)
PORT_NAMES=("Redis" "Backend" "STT-gRPC" "NLP-gRPC" "Summary-gRPC" "Prometheus" "Grafana")

for i in ${!PORTS[@]}; do
    PORT=${PORTS[$i]}
    NAME=${PORT_NAMES[$i]}

    echo "=== Checking port $PORT ($NAME) ==="

    # Check if port is listening
    if netstat -tuln | grep -q ":$PORT "; then
        echo "✅ Port $PORT ($NAME) is listening"

        # Try to connect (if HTTP)
        if [ "$PORT" -eq 8000 ] || [ "$PORT" -eq 9090 ] || [ "$PORT" -eq 3001 ]; then
            curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:$PORT/ || echo "⚠️  Port open but not responding"
        fi
    else
        echo "❌ Port $PORT ($NAME) is NOT listening"
    fi

    sleep 2
done
```

**Alert Triggers**:
- Expected port not listening after 3 minutes
- Port listening but service not responding
- Port conflicts (already in use by another process)

**Report Format**:
```
NETWORK PORT MONITORING REPORT
===============================
Expected Ports: 7

Port Status:
- 6379 (Redis): [LISTENING/NOT_LISTENING] - [STATUS]
- 8000 (Backend): [LISTENING/NOT_LISTENING] - HTTP [STATUS_CODE]
- 50051 (STT-gRPC): [LISTENING/NOT_LISTENING] - [STATUS]
- 50052 (NLP-gRPC): [LISTENING/NOT_LISTENING] - [STATUS]
- 50053 (Summary-gRPC): [LISTENING/NOT_LISTENING] - [STATUS]
- 9090 (Prometheus): [LISTENING/NOT_LISTENING] - HTTP [STATUS_CODE]
- 3001 (Grafana): [LISTENING/NOT_LISTENING] - HTTP [STATUS_CODE]

ISSUES: [List any ports not listening or not responding]
STATUS: [ALL_READY/PARTIAL/FAILED]
```

---

### Phase 2 Checkpoint

**Orchestrator Action**: Collect main thread status + 4 monitoring reports

**Decision Logic**:
```
IF all containers healthy AND no critical errors AND all ports listening:
    → Proceed to Phase 3 (Health Checks)
ELSE IF containers healthy but warnings present:
    → Prompt user: "Services started with warnings. Continue? (Y/n)"
ELSE:
    → ROLLBACK: docker-compose down
    → Capture all logs to deployment-failure.log
    → Report failure and exit
```

**Output**: Phase 2 Summary Report
```
PHASE 2: DOCKER DEPLOYMENT SUMMARY
====================================
Deployment Time: [X minutes Y seconds]

Container Status:
- redis: [healthy/unhealthy]
- backend: [healthy/unhealthy]
- stt-engine: [healthy/unhealthy]
- nlp-service: [healthy/unhealthy]
- summary-service: [healthy/unhealthy]
- prometheus: [healthy/unhealthy]
- grafana: [healthy/unhealthy]

GPU Memory: [X.X GB / 24 GB] ([XX%])
Critical Errors: [COUNT]
Warnings: [COUNT]
Ports Listening: [7/7]

OVERALL: [SUCCESS/PARTIAL/FAILED]
PROCEED TO PHASE 3: [YES/NO]
```

---

## PHASE 3: Health Check Validation

**Objective**: Verify all service APIs are functional
**Duration**: ~2 minutes
**Parallelization**: 4 concurrent agents
**Failure Mode**: Continue with partial failures, report all issues

### Agent 3.1: Automated Health Check Script

**Tasks**: Execute comprehensive health check script

```bash
# Run the main health check script
python scripts/health_check.py --verbose --timeout 30 --json > health-report.json

# Parse and display results
cat health-report.json | python -m json.tool

# Extract key metrics
echo "=== Health Check Summary ==="
cat health-report.json | jq -r '
    .services[] |
    "\(.name): \(.status) - Response: \(.response_time_ms)ms"
'

# Check overall status
OVERALL=$(cat health-report.json | jq -r '.overall_status')
if [ "$OVERALL" = "healthy" ]; then
    echo "✅ All services healthy"
else
    echo "❌ Some services unhealthy"
    cat health-report.json | jq '.services[] | select(.status != "healthy")'
fi
```

**Checks Performed** (by health_check.py):
- Docker daemon accessible
- All 7 containers running
- Backend /health endpoint (HTTP 200)
- Backend /health/ready endpoint (HTTP 200)
- Redis PING command
- GPU memory <16GB

**Report Format**:
```
AUTOMATED HEALTH CHECK REPORT
==============================
Script: scripts/health_check.py
Execution Time: [X.X] seconds

Service Health:
- Docker Daemon: [healthy/unhealthy]
- Redis Container: [running/stopped] - [healthy/unhealthy]
- Backend Container: [running/stopped] - [healthy/unhealthy]
- STT Engine Container: [running/stopped] - [healthy/unhealthy]
- NLP Service Container: [running/stopped] - [healthy/unhealthy]
- Summary Service Container: [running/stopped] - [healthy/unhealthy]
- Prometheus Container: [running/stopped] - [healthy/unhealthy]
- Grafana Container: [running/stopped] - [healthy/unhealthy]

API Endpoints:
- GET /health: [STATUS_CODE] - [RESPONSE_TIME]ms
- GET /health/ready: [STATUS_CODE] - [RESPONSE_TIME]ms
- Redis PING: [PONG/FAILED]

GPU Status:
- Memory Used: [X.X] GB
- Memory Free: [X.X] GB

OVERALL: [HEALTHY/UNHEALTHY]
ISSUES: [List any unhealthy components]
```

---

### Agent 3.2: gRPC Service Validation

**Tasks**: Test gRPC service availability

```bash
# Check if grpc_health_probe is available
if command -v grpc_health_probe &> /dev/null; then
    echo "=== Testing gRPC Services with grpc_health_probe ==="

    # STT Engine (port 50051)
    grpc_health_probe -addr=localhost:50051 -connect-timeout 5000ms && \
        echo "✅ STT Engine gRPC service healthy" || \
        echo "❌ STT Engine gRPC service unhealthy"

    # NLP Service (port 50052)
    grpc_health_probe -addr=localhost:50052 -connect-timeout 5000ms && \
        echo "✅ NLP Service gRPC service healthy" || \
        echo "❌ NLP Service gRPC service unhealthy"

    # Summary Service (port 50053)
    grpc_health_probe -addr=localhost:50053 -connect-timeout 5000ms && \
        echo "✅ Summary Service gRPC service healthy" || \
        echo "❌ Summary Service gRPC service unhealthy"
else
    echo "⚠️  grpc_health_probe not available, using netstat instead"

    # Fallback: Check if ports are listening
    netstat -tuln | grep ":50051" && echo "✅ STT Engine port listening" || echo "❌ STT Engine port not listening"
    netstat -tuln | grep ":50052" && echo "✅ NLP Service port listening" || echo "❌ NLP Service port not listening"
    netstat -tuln | grep ":50053" && echo "✅ Summary Service port listening" || echo "❌ Summary Service port not listening"
fi
```

**Validation Levels**:
1. **Optimal**: grpc_health_probe returns healthy
2. **Fallback**: Port listening (does not validate service functionality)

**Report Format**:
```
gRPC SERVICE VALIDATION REPORT
===============================
Tool: [grpc_health_probe/netstat]

STT Engine (port 50051):
- Status: [healthy/unhealthy/port_listening]
- Response Time: [X]ms (if available)

NLP Service (port 50052):
- Status: [healthy/unhealthy/port_listening]
- Response Time: [X]ms (if available)

Summary Service (port 50053):
- Status: [healthy/unhealthy/port_listening]
- Response Time: [X]ms (if available)

OVERALL: [ALL_HEALTHY/PARTIAL/FAILED]
RECOMMENDATION: [Install grpc_health_probe for better validation] (if using fallback)
```

---

### Agent 3.3: REST API Smoke Tests

**Tasks**: Test critical REST API endpoints

```bash
# Backend base health
echo "=== Testing Backend /health ==="
curl -s -w "\nHTTP Status: %{http_code}\nResponse Time: %{time_total}s\n" \
    http://localhost:8000/health | tee health-response.json

# Backend readiness
echo "=== Testing Backend /health/ready ==="
curl -s -w "\nHTTP Status: %{http_code}\nResponse Time: %{time_total}s\n" \
    http://localhost:8000/health/ready

# Audio devices endpoint
echo "=== Testing GET /api/v1/audio/devices ==="
curl -s -w "\nHTTP Status: %{http_code}\n" \
    http://localhost:8000/api/v1/audio/devices | python -m json.tool

# Create session endpoint
echo "=== Testing POST /api/v1/sessions ==="
curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"device_id": "default"}' \
    -w "\nHTTP Status: %{http_code}\n" \
    http://localhost:8000/api/v1/sessions | python -m json.tool

# Metrics endpoint
echo "=== Testing GET /metrics ==="
curl -s http://localhost:8000/metrics | head -20

# WebSocket endpoint (connection test only)
echo "=== Testing WebSocket Endpoint ==="
# Note: Full WebSocket test requires a client, just verify endpoint exists
curl -s -I http://localhost:8000/ws | grep -i "upgrade"
```

**Success Criteria**:
- /health returns 200 with {"status": "healthy"}
- /health/ready returns 200
- /api/v1/audio/devices returns 200 with device list
- /api/v1/sessions returns 201 with session object
- /metrics returns 200 with Prometheus metrics
- /ws returns upgrade headers for WebSocket

**Report Format**:
```
REST API SMOKE TESTS REPORT
============================

Endpoint Test Results:
- GET /health: [STATUS_CODE] - [RESPONSE_TIME]s
  Response: [JSON_PAYLOAD]

- GET /health/ready: [STATUS_CODE] - [RESPONSE_TIME]s

- GET /api/v1/audio/devices: [STATUS_CODE]
  Devices Found: [COUNT]

- POST /api/v1/sessions: [STATUS_CODE]
  Session ID: [SESSION_ID]

- GET /metrics: [STATUS_CODE]
  Metrics Count: [COUNT]

- WebSocket /ws: [UPGRADE_SUPPORTED]

PASSED: [X/6]
FAILED: [List failed endpoints]
STATUS: [ALL_PASS/PARTIAL/FAILED]
```

---

### Agent 3.4: Monitoring Stack Validation

**Tasks**: Verify Prometheus and Grafana functionality

```bash
# Prometheus health
echo "=== Testing Prometheus ==="
curl -s http://localhost:9090/-/healthy && echo "✅ Prometheus healthy" || echo "❌ Prometheus unhealthy"

# Prometheus targets
echo "=== Checking Prometheus Targets ==="
curl -s http://localhost:9090/api/v1/targets | jq -r '
    .data.activeTargets[] |
    "\(.job): \(.health) - \(.lastError // "no errors")"
'

# Prometheus query test
echo "=== Testing Prometheus Query ==="
curl -s "http://localhost:9090/api/v1/query?query=up" | jq '.data.result[] | {job: .metric.job, value: .value[1]}'

# Grafana health
echo "=== Testing Grafana ==="
curl -s http://localhost:3001/api/health | python -m json.tool

# Grafana datasources
echo "=== Checking Grafana Datasources ==="
curl -s -u admin:admin http://localhost:3001/api/datasources | jq -r '.[] | "\(.name): \(.type) - UID: \(.uid)"'

# Grafana dashboards
echo "=== Checking Grafana Dashboards ==="
curl -s -u admin:admin http://localhost:3001/api/search?type=dash-db | jq -r '.[] | "\(.title) - UID: \(.uid)"'
```

**Success Criteria**:
- Prometheus /-/healthy returns 200
- All Prometheus targets in "up" state
- Prometheus query returns data
- Grafana /api/health returns healthy status
- At least 1 datasource configured (Prometheus)
- At least 1 dashboard provisioned

**Report Format**:
```
MONITORING STACK VALIDATION REPORT
====================================

Prometheus (port 9090):
- Health Check: [healthy/unhealthy]
- Scrape Targets:
  - [job_name]: [up/down] - [last_error]
  ...
- Query Test: [SUCCESS/FAILED]

Grafana (port 3001):
- Health Check: [healthy/unhealthy]
- Datasources:
  - [name]: [type] - UID: [uid]
  ...
- Dashboards:
  - [title] - UID: [uid]
  ...

PROMETHEUS: [HEALTHY/UNHEALTHY]
GRAFANA: [HEALTHY/UNHEALTHY]
OVERALL: [FULLY_OPERATIONAL/PARTIAL/FAILED]
```

---

### Phase 3 Checkpoint

**Orchestrator Action**: Collect all 4 health check reports

**Decision Logic**:
```
IF all health checks pass:
    → Proceed to Phase 4 (Testing)
ELSE IF critical services healthy (backend, STT, Redis) but monitoring partial:
    → Prompt user: "Core services healthy, monitoring partial. Continue testing? (Y/n)"
ELSE:
    → WARN: "Health checks failed. Testing may be unreliable."
    → Prompt user: "Attempt testing anyway? (y/N)"
```

**Output**: Phase 3 Summary Report
```
PHASE 3: HEALTH CHECK VALIDATION SUMMARY
==========================================
Agent 3.1 (Automated Script): [HEALTHY/UNHEALTHY]
Agent 3.2 (gRPC Services): [ALL_HEALTHY/PARTIAL/FAILED]
Agent 3.3 (REST API): [X/6 PASSED]
Agent 3.4 (Monitoring): [FULLY_OPERATIONAL/PARTIAL/FAILED]

Critical Services:
- Backend API: [HEALTHY/UNHEALTHY]
- STT Engine: [HEALTHY/UNHEALTHY]
- NLP Service: [HEALTHY/UNHEALTHY]
- Redis: [HEALTHY/UNHEALTHY]

OVERALL: [READY_FOR_TESTING/PARTIAL/NOT_READY]
PROCEED TO PHASE 4: [YES/NO]
```

---

## PHASE 4: Test Suite Execution

**Objective**: Run comprehensive test suites in parallel
**Duration**: ~10-15 minutes
**Parallelization**: 4 concurrent test runners
**Failure Mode**: Continue all tests, report failures at end

### Agent 4.1: Audio Module Unit Tests

**Tasks**: Test audio capture, buffering, and VAD

```bash
# Run audio-related unit tests with coverage
pytest tests/unit/test_audio_format.py \
       tests/unit/test_circular_buffer.py \
       tests/unit/test_vad.py \
       -v \
       --cov=src/core/audio_capture \
       --cov-report=term-missing \
       --cov-report=html:htmlcov/audio \
       --tb=short \
       -x  # Stop on first failure (optional)

# Capture results
AUDIO_EXIT_CODE=$?

# Generate summary
pytest tests/unit/test_audio_format.py \
       tests/unit/test_circular_buffer.py \
       tests/unit/test_vad.py \
       --collect-only -q | tail -1
```

**Tests Covered**:
- `test_audio_format.py`: Audio format validation, sample rate conversion
- `test_circular_buffer.py`: Thread-safe circular buffer operations
- `test_vad.py`: Voice Activity Detection accuracy

**Success Criteria**:
- All tests pass (exit code 0)
- Coverage ≥80% for audio_capture module
- No critical failures in thread-safety tests

**Report Format**:
```
AUDIO MODULE UNIT TESTS REPORT
================================
Test Files: 3
Total Tests: [COUNT]

Results:
- test_audio_format.py: [PASSED/FAILED] - [X/Y tests]
- test_circular_buffer.py: [PASSED/FAILED] - [X/Y tests]
- test_vad.py: [PASSED/FAILED] - [X/Y tests]

Coverage:
- src/core/audio_capture: [XX%]
- Missing lines: [LINE_NUMBERS]

Duration: [X.X] seconds
Exit Code: [0/1]

FAILURES: [List any failed tests with error messages]
STATUS: [ALL_PASS/PARTIAL/FAILED]
```

---

### Agent 4.2: WASAPI Tests (Windows-Specific)

**Tasks**: Test Windows Audio Session API integration

```bash
# WASAPI tests require Windows 11 hardware
# Check if running on Windows
if [ -f "/proc/version" ] && grep -qi "microsoft" /proc/version; then
    echo "⚠️  Running in WSL - WASAPI tests may not work without hardware access"
fi

# Attempt WASAPI tests
pytest tests/unit/test_wasapi_capture.py \
       tests/unit/test_wasapi_devices.py \
       -v \
       --tb=short \
       -x  # Stop on first failure

WASAPI_EXIT_CODE=$?

# If tests are skipped due to missing hardware, report as warning
if [ $WASAPI_EXIT_CODE -eq 5 ]; then
    echo "⚠️  WASAPI tests skipped - no Windows audio hardware available"
elif [ $WASAPI_EXIT_CODE -eq 0 ]; then
    echo "✅ WASAPI tests passed"
else
    echo "❌ WASAPI tests failed"
fi
```

**Tests Covered**:
- `test_wasapi_capture.py`: Audio capture latency (<10ms target)
- `test_wasapi_devices.py`: Device enumeration, default device selection

**Success Criteria**:
- Tests pass on Windows 11 hardware
- Acceptable to skip in WSL/Linux environments
- Latency <10ms if hardware available

**Report Format**:
```
WASAPI TESTS REPORT
====================
Platform: [Windows/WSL/Linux]
Hardware Available: [YES/NO]

Results:
- test_wasapi_capture.py: [PASSED/FAILED/SKIPPED] - [X/Y tests]
- test_wasapi_devices.py: [PASSED/FAILED/SKIPPED] - [X/Y tests]

Performance Metrics (if run):
- Average Latency: [X.X]ms
- Max Latency: [X.X]ms
- Target: <10ms

Duration: [X.X] seconds
Exit Code: [0/1/5]

STATUS: [PASS/SKIPPED/FAILED]
SKIPPED_REASON: [No Windows hardware / Running in WSL]
```

---

### Agent 4.3: Integration Tests

**Tasks**: Test service integration points

```bash
# Run integration tests for audio service and Redis
pytest tests/integration/test_audio_service.py \
       tests/test_redis_streams.py \
       -v \
       --tb=short \
       --timeout=60

INTEGRATION_EXIT_CODE=$?

# These tests require Docker services to be running
# Verify prerequisites
docker-compose ps redis | grep -q "(healthy)" || echo "⚠️  Redis not healthy - integration tests may fail"
```

**Tests Covered**:
- `test_audio_service.py`: Audio service initialization, capture workflow
- `test_redis_streams.py`: Redis stream operations, message publishing/consuming

**Success Criteria**:
- All tests pass with Docker services running
- Redis connection successful
- Stream operations complete within timeout

**Report Format**:
```
INTEGRATION TESTS REPORT
=========================
Prerequisites:
- Redis Container: [running/stopped]
- Backend Container: [running/stopped]

Test Files: 2
Total Tests: [COUNT]

Results:
- test_audio_service.py: [PASSED/FAILED] - [X/Y tests]
- test_redis_streams.py: [PASSED/FAILED] - [X/Y tests]

Performance:
- Redis Latency: [X]ms (avg)
- Stream Throughput: [X] msg/s

Duration: [X.X] seconds
Exit Code: [0/1]

FAILURES: [List any failed tests]
STATUS: [ALL_PASS/PARTIAL/FAILED]
```

---

### Agent 4.4: ML Service Integration Tests

**Tasks**: Test NLP and Summary service integration

```bash
# Check if ML services are healthy before testing
echo "=== Checking ML Service Prerequisites ==="
curl -s http://localhost:8000/health | grep -q "healthy" || {
    echo "❌ Backend not healthy - skipping ML service tests"
    exit 5
}

# Run ML service integration tests
pytest tests/test_nlp_service_integration.py \
       tests/test_summary_service_integration.py \
       -v \
       --tb=short \
       --timeout=120 \
       -x  # Stop on first failure (these are slow)

ML_EXIT_CODE=$?

# If tests pass, report metrics
if [ $ML_EXIT_CODE -eq 0 ]; then
    echo "✅ ML service integration tests passed"
fi
```

**Tests Covered**:
- `test_nlp_service_integration.py`: Keyword extraction, diarization, semantic analysis
- `test_summary_service_integration.py`: Text summarization quality

**Success Criteria**:
- Services respond to gRPC requests
- NLP extracts keywords accurately
- Summary service generates coherent summaries
- No GPU OOM errors

**GPU Safety Note**: These tests load models but should use already-running services (no new model loading)

**Report Format**:
```
ML SERVICE INTEGRATION TESTS REPORT
====================================
Prerequisites:
- NLP Service: [healthy/unhealthy]
- Summary Service: [healthy/unhealthy]

Test Files: 2
Total Tests: [COUNT]

Results:
- test_nlp_service_integration.py: [PASSED/FAILED] - [X/Y tests]
  - Keyword extraction: [PASS/FAIL]
  - Speaker diarization: [PASS/FAIL]
  - Semantic analysis: [PASS/FAIL]

- test_summary_service_integration.py: [PASSED/FAILED] - [X/Y tests]
  - Summary quality: [PASS/FAIL]
  - Summary length: [PASS/FAIL]

GPU Status:
- Memory Before: [X.X] GB
- Memory After: [X.X] GB
- Peak Usage: [X.X] GB

Duration: [X.X] seconds
Exit Code: [0/1/5]

FAILURES: [List any failed tests]
STATUS: [ALL_PASS/PARTIAL/FAILED/SKIPPED]
```

---

### Phase 4 Checkpoint

**Orchestrator Action**: Collect all 4 test runner reports

**Decision Logic**:
```
Total tests run: [SUM of all agents]
Total passed: [COUNT]
Total failed: [COUNT]
Total skipped: [COUNT]

Coverage: [Overall coverage %]

IF total_failed == 0:
    → "All tests passed!"
    → Proceed to Phase 5 (Dashboard Verification)
ELSE IF critical tests passed (audio, integration):
    → "Some tests failed but core functionality intact"
    → Prompt user: "Continue to dashboard verification? (Y/n)"
ELSE:
    → "Critical tests failed"
    → Prompt user: "Critical failures detected. Continue anyway? (y/N)"
```

**Output**: Phase 4 Summary Report
```
PHASE 4: TEST SUITE EXECUTION SUMMARY
=======================================
Agent 4.1 (Audio Tests): [PASSED/FAILED] - [X/Y tests]
Agent 4.2 (WASAPI Tests): [PASSED/SKIPPED/FAILED] - [X/Y tests]
Agent 4.3 (Integration Tests): [PASSED/FAILED] - [X/Y tests]
Agent 4.4 (ML Service Tests): [PASSED/FAILED/SKIPPED] - [X/Y tests]

Overall Statistics:
- Total Tests: [COUNT]
- Passed: [COUNT] ([XX%])
- Failed: [COUNT] ([XX%])
- Skipped: [COUNT] ([XX%])

Coverage:
- src/core/audio_capture: [XX%]
- Overall: [XX%]

Duration: [X] minutes [Y] seconds

CRITICAL_FAILURES: [List critical test failures]
PROCEED TO PHASE 5: [YES/NO]
```

---

## PHASE 5: Dashboard and RTSTT System Verification

**Objective**: Verify dashboard accessibility and end-to-end RTSTT functionality
**Duration**: ~5 minutes
**Parallelization**: 3 concurrent agents
**Failure Mode**: Report issues but allow manual verification

### Agent 5.1: Dashboard Access Verification

**Tasks**: Open and verify monitoring dashboards

```bash
# Detect browser (Linux)
if command -v xdg-open &> /dev/null; then
    BROWSER="xdg-open"
elif command -v firefox &> /dev/null; then
    BROWSER="firefox"
elif command -v google-chrome &> /dev/null; then
    BROWSER="google-chrome"
else
    BROWSER="echo 'No browser found. Please open manually:'"
fi

# Open Prometheus
echo "=== Opening Prometheus Dashboard ==="
$BROWSER http://localhost:9090 &
sleep 2

# Open Grafana
echo "=== Opening Grafana Dashboard ==="
$BROWSER http://localhost:3001 &
sleep 2

# Open API Documentation
echo "=== Opening API Documentation ==="
$BROWSER http://localhost:8000/docs &
sleep 2

# Verify URLs are accessible
echo "=== Verifying Dashboard URLs ==="
curl -s -o /dev/null -w "Prometheus: %{http_code}\n" http://localhost:9090/
curl -s -o /dev/null -w "Grafana: %{http_code}\n" http://localhost:3001/
curl -s -o /dev/null -w "API Docs: %{http_code}\n" http://localhost:8000/docs
```

**Manual Verification Checklist**:
- [ ] Prometheus UI loads
- [ ] Grafana login page appears (admin/admin)
- [ ] API documentation (Swagger UI) displays

**Report Format**:
```
DASHBOARD ACCESS VERIFICATION REPORT
=====================================
Browser Detected: [BROWSER_NAME]

Dashboard URLs:
- Prometheus: http://localhost:9090 - HTTP [STATUS_CODE]
- Grafana: http://localhost:3001 - HTTP [STATUS_CODE]
- API Docs: http://localhost:8000/docs - HTTP [STATUS_CODE]
- ReDoc: http://localhost:8000/redoc - HTTP [STATUS_CODE]

Browser Tabs Opened: [COUNT]

STATUS: [ACCESSIBLE/PARTIAL/FAILED]
MANUAL_VERIFICATION_REQUIRED: [YES/NO]
```

---

### Agent 5.2: Grafana Dashboard Provisioning Verification

**Tasks**: Verify Grafana datasources and dashboards

```bash
# Login to Grafana API
GRAFANA_URL="http://localhost:3001"
GRAFANA_USER="admin"
GRAFANA_PASS="admin"

# Check datasources
echo "=== Verifying Grafana Datasources ==="
curl -s -u $GRAFANA_USER:$GRAFANA_PASS $GRAFANA_URL/api/datasources | \
    jq -r '.[] | "✅ Datasource: \(.name) (\(.type)) - UID: \(.uid)"'

# Check dashboards
echo "=== Verifying Grafana Dashboards ==="
curl -s -u $GRAFANA_USER:$GRAFANA_PASS $GRAFANA_URL/api/search?type=dash-db | \
    jq -r '.[] | "✅ Dashboard: \(.title) - UID: \(.uid)"'

# Test a sample query against Prometheus datasource
echo "=== Testing Prometheus Datasource Query ==="
# Get first datasource UID
DS_UID=$(curl -s -u $GRAFANA_USER:$GRAFANA_PASS $GRAFANA_URL/api/datasources | jq -r '.[0].uid')

curl -s -u $GRAFANA_USER:$GRAFANA_PASS \
    -X POST \
    -H "Content-Type: application/json" \
    -d "{\"queries\":[{\"datasource\":{\"uid\":\"$DS_UID\"},\"expr\":\"up\",\"refId\":\"A\"}]}" \
    $GRAFANA_URL/api/ds/query | \
    jq '.results.A.frames[0].data.values' && \
    echo "✅ Datasource query successful" || \
    echo "❌ Datasource query failed"
```

**Expected Provisioned Dashboards**:
- System Overview Dashboard
- STT Performance Dashboard
- ORCHIDEA Metrics Dashboard
- Redis Streams Dashboard

**Report Format**:
```
GRAFANA PROVISIONING VERIFICATION REPORT
==========================================
Grafana URL: http://localhost:3001
Credentials: admin / admin

Datasources:
- [NAME] ([TYPE]) - UID: [UID] - [STATUS]
...

Dashboards:
- [TITLE] - UID: [UID] - [STATUS]
...

Query Test:
- Prometheus Datasource: [QUERY_SUCCESSFUL/FAILED]

Expected Dashboards: [4]
Found Dashboards: [COUNT]

STATUS: [FULLY_PROVISIONED/PARTIAL/FAILED]
MISSING: [List any missing expected dashboards]
```

---

### Agent 5.3: Prometheus Metrics Validation

**Tasks**: Verify Prometheus is collecting RTSTT metrics

```bash
# Check Prometheus targets
echo "=== Checking Prometheus Scrape Targets ==="
curl -s http://localhost:9090/api/v1/targets | \
    jq -r '.data.activeTargets[] |
           "\(.job): \(.health) - Last scrape: \(.lastScrape) - \(.lastError // "no errors")"'

# Query RTSTT-specific metrics
echo "=== Querying RTSTT Metrics ==="

# Audio latency metric
curl -s "http://localhost:9090/api/v1/query?query=audio_capture_latency_ms" | \
    jq -r '.data.result[] | "\(.metric.__name__): \(.value[1])"'

# STT throughput metric
curl -s "http://localhost:9090/api/v1/query?query=stt_throughput" | \
    jq -r '.data.result[] | "\(.metric.__name__): \(.value[1])"'

# GPU memory metric
curl -s "http://localhost:9090/api/v1/query?query=gpu_memory_used_gb" | \
    jq -r '.data.result[] | "\(.metric.__name__): \(.value[1])"'

# Redis queue length
curl -s "http://localhost:9090/api/v1/query?query=redis_queue_length" | \
    jq -r '.data.result[] | "\(.metric.__name__): \(.value[1])"'

# Count total metrics
echo "=== Total Metrics Available ==="
curl -s "http://localhost:9090/api/v1/label/__name__/values" | \
    jq '.data | length'
```

**Expected RTSTT Metrics**:
- `audio_capture_latency_ms`
- `stt_throughput`
- `gpu_memory_used_gb`
- `redis_queue_length`
- `orchidea_puii_alignment_score`

**Report Format**:
```
PROMETHEUS METRICS VALIDATION REPORT
======================================
Prometheus URL: http://localhost:9090

Scrape Targets:
- [JOB_NAME]: [up/down] - Last scrape: [TIMESTAMP] - [ERROR]
...

RTSTT-Specific Metrics:
- audio_capture_latency_ms: [VALUE/NOT_FOUND]
- stt_throughput: [VALUE/NOT_FOUND]
- gpu_memory_used_gb: [VALUE/NOT_FOUND]
- redis_queue_length: [VALUE/NOT_FOUND]
- orchidea_puii_alignment_score: [VALUE/NOT_FOUND]

Total Metrics: [COUNT]
Expected RTSTT Metrics: [5]
Found RTSTT Metrics: [COUNT]

STATUS: [ALL_METRICS_PRESENT/PARTIAL/MISSING]
MISSING: [List any missing expected metrics]
```

---

### Phase 5 Checkpoint

**Orchestrator Action**: Collect all 3 dashboard verification reports

**Decision Logic**:
```
IF dashboards accessible AND Grafana provisioned AND metrics collecting:
    → "Dashboard verification complete!"
    → Generate final comprehensive report
ELSE IF dashboards accessible but metrics partial:
    → "Dashboards accessible, some metrics missing"
    → Prompt user: "Proceed with manual verification? (Y/n)"
ELSE:
    → "Dashboard verification incomplete"
    → Prompt user: "Manual verification required. Mark as complete? (y/N)"
```

**Output**: Phase 5 Summary Report
```
PHASE 5: DASHBOARD VERIFICATION SUMMARY
=========================================
Agent 5.1 (Access): [ACCESSIBLE/PARTIAL/FAILED]
Agent 5.2 (Grafana Provisioning): [FULLY_PROVISIONED/PARTIAL/FAILED]
Agent 5.3 (Prometheus Metrics): [ALL_METRICS_PRESENT/PARTIAL/MISSING]

Dashboard URLs:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)
- API Docs: http://localhost:8000/docs

Grafana Dashboards: [X/4 found]
Prometheus Metrics: [X/5 found]

OVERALL: [FULLY_OPERATIONAL/PARTIAL/MANUAL_VERIFICATION_REQUIRED]
```

---

## FINAL COMPREHENSIVE REPORT

**Orchestrator Action**: Generate master report combining all phases

### Success Criteria Checklist

- [ ] **Phase 1**: All pre-deployment checks passed
- [ ] **Phase 2**: 7/7 Docker containers healthy
- [ ] **Phase 2**: GPU memory <14GB
- [ ] **Phase 3**: Backend API responding (200 OK)
- [ ] **Phase 3**: gRPC services responding
- [ ] **Phase 3**: Monitoring stack operational
- [ ] **Phase 4**: ≥90% tests passed
- [ ] **Phase 4**: Critical tests passed (audio, integration)
- [ ] **Phase 5**: Dashboards accessible
- [ ] **Phase 5**: Grafana provisioned with datasources
- [ ] **Phase 5**: Prometheus collecting metrics

### Master Report Template

```markdown
# RTSTT Deployment Verification & Testing Report

**Date**: [TIMESTAMP]
**Duration**: [TOTAL_TIME]
**Overall Status**: [SUCCESS/PARTIAL_SUCCESS/FAILED]

---

## Executive Summary

[2-3 sentence summary of deployment outcome]

**Key Metrics**:
- Docker Containers: [7/7 healthy]
- GPU Memory: [X.X GB / 24 GB] ([XX%])
- Tests Passed: [XX/YY] ([ZZ%])
- Dashboards Operational: [X/3]

---

## Phase 1: Pre-Deployment Validation

**Status**: [PASS/FAIL/WARNING]
**Duration**: [X min Y sec]

| Check | Status | Details |
|-------|--------|---------|
| Environment | [✅/❌] | Docker [VERSION], CUDA [VERSION] |
| Configuration | [✅/❌/⚠️ ] | .env.local [FOUND], HF_TOKEN [SET] |
| Models | [✅/❌] | Whisper [FOUND], Llama [FOUND] |
| Code Quality | [✅/❌/⚠️ ] | MyPy [X errors], Flake8 [Y errors] |
| Documentation | [✅/❌/⚠️ ] | README [FOUND], API docs [FOUND] |

**Issues**: [List any warnings or failures]

---

## Phase 2: Docker Deployment

**Status**: [SUCCESS/PARTIAL/FAILED]
**Duration**: [X min Y sec]

| Container | Status | Health | GPU Memory |
|-----------|--------|--------|------------|
| redis | [running] | [healthy] | - |
| backend | [running] | [healthy] | - |
| stt-engine | [running] | [healthy] | [X.X GB] |
| nlp-service | [running] | [healthy] | [X.X GB] |
| summary-service | [running] | [healthy] | [X.X GB] |
| prometheus | [running] | [healthy] | - |
| grafana | [running] | [healthy] | - |

**Total GPU Memory**: [X.X GB / 24 GB] ([XX%])
**Critical Errors**: [COUNT]
**Warnings**: [COUNT]

**Deployment Timeline**:
- [TIMESTAMP] Redis started
- [TIMESTAMP] ML services started
- [TIMESTAMP] Backend started
- [TIMESTAMP] All services healthy

**Issues**: [List any errors or warnings from logs]

---

## Phase 3: Health Check Validation

**Status**: [HEALTHY/PARTIAL/UNHEALTHY]
**Duration**: [X min Y sec]

| Component | Status | Response Time | Details |
|-----------|--------|---------------|---------|
| Health Script | [✅/❌] | - | [Overall status] |
| STT gRPC | [✅/❌] | [X ms] | Port 50051 |
| NLP gRPC | [✅/❌] | [X ms] | Port 50052 |
| Summary gRPC | [✅/❌] | [X ms] | Port 50053 |
| Backend /health | [✅/❌] | [X ms] | HTTP 200 |
| Backend /ready | [✅/❌] | [X ms] | HTTP 200 |
| Prometheus | [✅/❌] | [X ms] | HTTP 200 |
| Grafana | [✅/❌] | [X ms] | HTTP 200 |

**API Smoke Tests**: [X/6 passed]
**Monitoring Stack**: [OPERATIONAL/PARTIAL/FAILED]

**Issues**: [List any unhealthy services]

---

## Phase 4: Test Suite Execution

**Status**: [ALL_PASS/PARTIAL/FAILED]
**Duration**: [X min Y sec]

| Test Suite | Passed | Failed | Skipped | Coverage | Duration |
|------------|--------|--------|---------|----------|----------|
| Audio Tests | [X] | [Y] | [Z] | [XX%] | [X.X s] |
| WASAPI Tests | [X] | [Y] | [Z] | - | [X.X s] |
| Integration Tests | [X] | [Y] | [Z] | - | [X.X s] |
| ML Service Tests | [X] | [Y] | [Z] | - | [X.X s] |

**Overall**:
- Total Tests: [COUNT]
- Passed: [COUNT] ([XX%])
- Failed: [COUNT] ([XX%])
- Skipped: [COUNT] ([XX%])
- Overall Coverage: [XX%]

**Failed Tests**: [List failed tests with error summaries]

---

## Phase 5: Dashboard Verification

**Status**: [FULLY_OPERATIONAL/PARTIAL/FAILED]
**Duration**: [X min Y sec]

| Dashboard | Status | URL | Details |
|-----------|--------|-----|---------|
| Prometheus | [✅/❌] | http://localhost:9090 | [Targets: X/Y up] |
| Grafana | [✅/❌] | http://localhost:3001 | [Dashboards: X/4] |
| API Docs | [✅/❌] | http://localhost:8000/docs | [HTTP STATUS] |

**Grafana Dashboards**: [X/4 provisioned]
- [ ] System Overview Dashboard
- [ ] STT Performance Dashboard
- [ ] ORCHIDEA Metrics Dashboard
- [ ] Redis Streams Dashboard

**Prometheus Metrics**: [X/5 found]
- [ ] audio_capture_latency_ms
- [ ] stt_throughput
- [ ] gpu_memory_used_gb
- [ ] redis_queue_length
- [ ] orchidea_puii_alignment_score

**Issues**: [List any missing dashboards or metrics]

---

## RTSTT System Status

**Deployment**: [FULLY_OPERATIONAL/PARTIAL/FAILED]
**Readiness**: [PRODUCTION_READY/TESTING_READY/NOT_READY]

### Critical Services Status
- Audio Capture: [READY/NOT_READY]
- STT Engine: [READY/NOT_READY]
- NLP Insights: [READY/NOT_READY]
- Summarization: [READY/NOT_READY]
- WebSocket Gateway: [READY/NOT_READY]

### Performance Validation
- End-to-end Latency: [TESTED/NOT_TESTED] - [X ms] (target: <100ms)
- GPU Memory Usage: [X.X GB] (target: <14GB) - [✅/❌]
- Test Coverage: [XX%] (target: >95%) - [✅/❌]

---

## Next Steps

### If Deployment Successful
1. ✅ Start Electron desktop application: `npm run dev` (in src/ui/desktop/)
2. ✅ Test WebSocket connection to ws://localhost:8000/ws
3. ✅ Test real-time transcription with live audio
4. ✅ Review Grafana dashboards for system metrics
5. ✅ Run benchmark suite: `python benchmarks/audio_latency_benchmark.py`

### If Partial Success
1. Review warnings in [PHASE_NAME]
2. Address failed tests: [LIST_FAILED_TESTS]
3. Verify missing metrics: [LIST_MISSING_METRICS]
4. Re-run health checks after fixes

### If Deployment Failed
1. Review logs: `docker-compose logs > deployment-failure.log`
2. Check GPU state: `nvidia-smi > gpu-state.log`
3. Fix critical issues: [LIST_CRITICAL_ISSUES]
4. Rollback: `docker-compose down`
5. Re-run deployment after fixes

---

## Rollback Procedure

If issues arise:

```bash
# Capture diagnostic information
docker-compose logs > logs/deployment-$(date +%Y%m%d-%H%M%S).log
nvidia-smi > logs/gpu-state-$(date +%Y%m%d-%H%M%S).log
python scripts/health_check.py --json > logs/health-report-$(date +%Y%m%d-%H%M%S).json

# Stop all services
docker-compose down

# Clean up (if needed)
docker-compose down -v  # Remove volumes
docker system prune -f  # Clean dangling images

# Review logs and fix issues before redeployment
```

---

## Appendix

### Command Reference

**Start Services**:
```bash
docker-compose up -d
```

**Check Status**:
```bash
docker-compose ps
python scripts/health_check.py
```

**View Logs**:
```bash
docker-compose logs -f [service_name]
```

**Run Tests**:
```bash
pytest tests/ -v
```

**Monitor GPU**:
```bash
watch -n 1 nvidia-smi
```

### Dashboard Access

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin / admin)
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Support

- **Documentation**: /docs/
- **Issues**: /KB/troubleshooting.md
- **Orchestrator Spec**: /KB/orchestrator.agent.md

---

**Report Generated**: [TIMESTAMP]
**Orchestrator**: ORCHIDEA v1.3
**Terminal**: Parallel Deploy Test Terminal
```

---

## Execution Instructions for Claude Code

To execute this orchestration workflow:

1. **Read this document**: `cat /home/frisco/projects/RTSTT/orchestration/parallel-deploy-test-terminal.md`

2. **Initialize Todo List**: Create 21 todos (5 per Phase 1-4, 3 for Phase 5, 1 for final report)

3. **Execute Phases Sequentially**: Run each phase to completion before proceeding

4. **Parallelize Within Phases**:
   - Phase 1: Launch all 5 agents concurrently
   - Phase 2: Main thread sequential, 4 monitors concurrent
   - Phase 3: Launch all 4 agents concurrently
   - Phase 4: Launch all 4 test runners concurrently
   - Phase 5: Launch all 3 agents concurrently

5. **Collect Reports**: After each phase, aggregate all agent reports

6. **Decision Gates**: Apply decision logic at each checkpoint

7. **Generate Final Report**: Compile master report with all results

8. **Mark Todos**: Update todo status as each agent completes

---

**End of Orchestration Specification**
