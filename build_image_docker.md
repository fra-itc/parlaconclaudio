# Build Docker Images - ML Services (Debian)

## Setup Iniziale

```bash
# Naviga nella cartella del progetto
cd ~/RTSTT  # o la path dove hai clonato

# Verifica GPU
nvidia-smi

# Verifica Docker con GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

---

## 1. Build STT Engine (con dipendenze corrette)

```bash
# Build con DOCKER_BUILDKIT per velocità
DOCKER_BUILDKIT=1 docker-compose build --progress=plain stt-engine

# Oppure build manuale
DOCKER_BUILDKIT=1 docker build \
  -t rtstt_stt-engine:latest \
  -f infrastructure/docker/Dockerfile.stt \
  .
```

**Dipendenze installate:**
- `av==11.*`
- `tokenizers>=0.13,<0.16`
- `more-itertools`
- `numba`
- `tiktoken`
- `openai-whisper==20231117`
- `faster-whisper==0.10.0`

---

## 2. Build NLP Service

```bash
DOCKER_BUILDKIT=1 docker-compose build --progress=plain nlp-service

# Oppure build manuale
DOCKER_BUILDKIT=1 docker build \
  -t rtstt_nlp-service:latest \
  -f infrastructure/docker/Dockerfile.nlp \
  .
```

---

## 3. Build Summary Service

```bash
DOCKER_BUILDKIT=1 docker-compose build --progress=plain summary-service

# Oppure build manuale
DOCKER_BUILDKIT=1 docker build \
  -t rtstt_summary-service:latest \
  -f infrastructure/docker/Dockerfile.summary \
  .
```

---

## 4. Build Tutti e Tre Insieme (opzionale)

```bash
# Build sequenziale di tutti i servizi
DOCKER_BUILDKIT=1 docker-compose build --progress=plain \
  stt-engine nlp-service summary-service
```

---

## 5. Verifica Immagini Create

```bash
# Lista immagini
docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}\t{{.Size}}' | grep rtstt

# Dovrai vedere:
# rtstt_stt-engine       latest    [DATA RECENTE]    ~7.5GB
# rtstt_nlp-service      latest    [DATA RECENTE]    ~10GB
# rtstt_summary-service  latest    [DATA RECENTE]    ~7.2GB
```

---

## 6. Test Dipendenze

### Test STT
```bash
docker run --rm --gpus all --entrypoint '' rtstt_stt-engine:latest \
  python -c "import numpy, tiktoken, whisper; print('✅ STT OK:', numpy.__version__, tiktoken.__version__)"
```

### Test NLP
```bash
docker run --rm --gpus all --entrypoint '' rtstt_nlp-service:latest \
  python -m pip check

# Dovrebbe stampare: "No broken requirements found."
```

### Test Summary
```bash
docker run --rm --gpus all --entrypoint '' rtstt_summary-service:latest \
  python -m pip check

# Dovrebbe stampare: "No broken requirements found."
```

---

## 7. Start Servizi

```bash
# Start solo ML services con GPU
docker-compose up -d stt-engine nlp-service summary-service

# Verifica status
docker-compose ps

# Dovrebbero essere tutti "Up" (non "Restarting")
```

---

## 8. Verifica Logs

```bash
# STT logs
docker-compose logs -f --tail=50 stt-engine

# NLP logs
docker-compose logs -f --tail=50 nlp-service

# Summary logs
docker-compose logs -f --tail=50 summary-service

# Tutti insieme
docker-compose logs -f --tail=50 stt-engine nlp-service summary-service
```

**Cosa cercare nei logs:**
- ✅ `Server started on port 50051/50052/50053`
- ✅ `Model loaded successfully`
- ❌ **NO** `ModuleNotFoundError`
- ❌ **NO** `Restarting` continuo

---

## 9. Test Funzionalità

### Test STT Health
```bash
# Richiede grpc_health_probe installato
docker exec rtstt-stt-engine grpc_health_probe -addr=:50051
```

### Test NLP Health
```bash
docker exec rtstt-nlp-service grpc_health_probe -addr=:50052
```

### Test Summary Health
```bash
docker exec rtstt-summary-service grpc_health_probe -addr=:50053
```

---

## 10. Cleanup (se necessario)

```bash
# Stop servizi
docker-compose down

# Rimuovi immagini vecchie
docker images | grep rtstt | grep -v "$(date +%Y-%m-%d)" | awk '{print $3}' | xargs docker rmi

# Cleanup completo
docker system prune -af
docker volume prune -f
```

---

## Troubleshooting

### Se STT va in Restarting
```bash
# Check logs dettagliati
docker logs rtstt-stt-engine --tail=100

# Test import manuale
docker run --rm --gpus all -it rtstt_stt-engine:latest python
>>> import tiktoken
>>> import whisper
>>> exit()
```

### Se manca tiktoken
```bash
# Rebuild STT dopo aver verificato Dockerfile.stt line 48
DOCKER_BUILDKIT=1 docker-compose build --no-cache --progress=plain stt-engine
```

### Problemi GPU
```bash
# Verifica NVIDIA runtime
docker info | grep -i runtime

# Test GPU in container
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

---

## Performance Tips

- **DOCKER_BUILDKIT=1**: ~30-40% più veloce
- **--progress=plain**: Output dettagliato per debug
- **--no-cache**: Solo se necessario rebuild completo
- **Build parallelo**: Non raccomandato su WSL, OK su Linux nativo

---

## Status Finale Atteso

```bash
$ docker-compose ps
NAME                    STATUS              PORTS
rtstt-stt-engine       Up 2 minutes        0.0.0.0:50051->50051/tcp
rtstt-nlp-service      Up 2 minutes        0.0.0.0:50052->50052/tcp
rtstt-summary-service  Up 2 minutes        0.0.0.0:50053->50053/tcp
```

✅ **Tutto green = deployment riuscito!**
