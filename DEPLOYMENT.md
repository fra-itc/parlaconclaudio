# RTSTT Deployment Guide

Comprehensive deployment guide for Real-Time Speech-to-Text (RTSTT) on WSL2 and Linux platforms.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [WSL2 Deployment](#wsl2-deployment)
- [Native Linux Deployment](#native-linux-deployment)
- [Configuration](#configuration)
- [Running the POC](#running-the-poc)
- [Troubleshooting](#troubleshooting)
- [Performance Tuning](#performance-tuning)

---

## Overview

RTSTT is a real-time speech-to-text system built with a microservices architecture. It supports deployment on:

- **WSL2 (Windows Subsystem for Linux 2)** - Recommended for Windows development
- **Native Linux** - Production deployment on Linux servers
- **Docker Containers** - All ML services run in isolated containers

### Key Features

- **Real-time transcription** with <500ms latency
- **GPU acceleration** via NVIDIA CUDA
- **WebSocket streaming** for live audio
- **Cross-platform audio capture** (WASAPI, PulseAudio, PortAudio)
- **Microservices architecture** (STT, NLP, Summary)

---

## Architecture

### System Components

```
┌──────────────────────────────────────────────────────────────┐
│                     Host Machine (WSL2/Linux)                │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Audio Bridge Service                                  │ │
│  │  - Captures audio from host microphone                 │ │
│  │  - Buffers and streams via WebSocket                   │ │
│  └────────────────┬───────────────────────────────────────┘ │
│                   │ WebSocket (ws://localhost:8000/ws)      │
└───────────────────┼──────────────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────────────┐
│              Docker Container Network                        │
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│  │ Backend      │   │ STT Engine   │   │ NLP Service  │   │
│  │ (FastAPI)    │──▶│ (Whisper)    │──▶│ (Flair)      │   │
│  │ Port: 8000   │   │ gRPC: 50051  │   │ gRPC: 50052  │   │
│  └──────┬───────┘   └──────────────┘   └──────┬───────┘   │
│         │                                      │            │
│         │           ┌──────────────┐          │            │
│         └──────────▶│ Summary Svc  │◀─────────┘            │
│                     │ (T5)         │                        │
│                     │ gRPC: 50053  │                        │
│                     └──────────────┘                        │
│                                                              │
│  ┌──────────────┐                                           │
│  │ Redis Cache  │                                           │
│  │ Port: 6379   │                                           │
│  └──────────────┘                                           │
└──────────────────────────────────────────────────────────────┘
```

### Audio Flow

1. **Capture**: Audio bridge captures from host microphone
2. **Buffer**: Accumulates 2-second chunks to reduce overhead
3. **Stream**: Sends via WebSocket to backend
4. **Process**: Backend forwards to STT engine via gRPC
5. **Transcribe**: STT engine (Whisper) transcribes audio
6. **Analyze**: NLP service analyzes sentiment/entities
7. **Summarize**: Summary service generates summaries
8. **Respond**: Results sent back via WebSocket

### Network Architecture

- **Host Network**: Audio bridge runs on host
- **Docker Network**: All ML services in isolated network
- **WebSocket Bridge**: Connects host to containers
- **gRPC Pools**: Load-balanced connections to ML services

---

## Prerequisites

### Hardware Requirements

**Minimum:**
- CPU: 4 cores, 2.5 GHz
- RAM: 16 GB
- Disk: 20 GB free space
- GPU: Optional, but recommended for performance

**Recommended:**
- CPU: 8+ cores, 3.0+ GHz
- RAM: 32 GB
- Disk: 50 GB SSD
- GPU: NVIDIA RTX 3060+ with 8GB+ VRAM

### Software Requirements

**All Platforms:**
- Docker 24.0+
- Docker Compose 2.20+
- Python 3.10+
- Git

**WSL2 Specific:**
- Windows 10/11 with WSL2 enabled
- Ubuntu 22.04 LTS or newer in WSL2
- NVIDIA drivers in Windows (for GPU)

**Linux Specific:**
- Ubuntu 22.04 LTS or newer
- NVIDIA drivers (for GPU)
- PulseAudio or ALSA (for audio)

---

## WSL2 Deployment

### Why WSL2?

WSL2 provides a complete Linux environment on Windows with:
- Native Docker support
- GPU passthrough via NVIDIA drivers
- Near-native Linux performance
- Easy development workflow

### Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd RTSTT

# 2. Run automated setup
./scripts/setup-wsl2.sh

# 3. Configure secrets
./scripts/setup-secrets.sh

# 4. Deploy and test
./scripts/deploy-poc.sh test
```

### Detailed Steps

#### 1. Verify WSL2

```bash
# Check WSL version
wsl --list --verbose

# Should show WSL version 2
# If not, upgrade:
wsl --set-version Ubuntu 2
```

#### 2. Install Dependencies

The setup script automates this, but manual steps:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Install Python dependencies
sudo apt install python3 python3-pip python3-venv

# Log out and back in for group changes
```

#### 3. Configure GPU (Optional)

```bash
# Verify GPU is accessible
nvidia-smi

# If not working, install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt update
sudo apt install -y nvidia-docker2
sudo service docker restart
```

#### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env

# Key settings:
# - RTSTT_WEBSOCKET_URL=ws://localhost:8000/ws
# - RTSTT_AUDIO_DRIVER=mock (for testing) or wasapi (for real audio)
# - CUDA_VISIBLE_DEVICES=0
```

#### 5. Build and Deploy

```bash
# Build all Docker images
docker-compose build

# Start all services
./scripts/deploy-poc.sh start

# Check status
./scripts/deploy-poc.sh status

# View logs
./scripts/deploy-poc.sh logs backend
```

#### 6. Test Audio Pipeline

```bash
# Test with mock audio (sine wave)
./scripts/deploy-poc.sh test

# Expected output:
# ✓ Connected to backend
# ✓ Audio capture started
# 📝 Transcription: '...' (latency: 250-350ms)
```

### WSL2-Specific Notes

**Audio Limitations:**
- WSL2 cannot directly access Windows audio devices
- Use WebSocket audio bridge to stream from Windows host
- Mock driver available for testing without real audio

**GPU Support:**
- Requires NVIDIA GPU with compute capability 6.0+
- Windows must have NVIDIA drivers installed
- WSL2 automatically shares GPU via /dev/dxg

**File System:**
- Keep project in WSL2 filesystem (/home/...) for best performance
- Avoid Windows filesystem (/mnt/c/...) for Docker volumes

---

## Native Linux Deployment

### Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd RTSTT

# 2. Install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install docker.io docker-compose python3 python3-pip

# 3. Configure Docker
sudo usermod -aG docker $USER
# Log out and back in

# 4. Setup environment
cp .env.example .env
nano .env  # Configure settings

# 5. Build and deploy
docker-compose build
docker-compose up -d

# 6. Test
python -m src.host_audio_bridge.main --driver pulseaudio --test-duration 10
```

### Audio Drivers

Linux supports multiple audio backends:

**PulseAudio (Recommended):**
```bash
# Check if running
pactl info

# Test capture
parecord --channels=1 --rate=16000 test.wav
```

**ALSA (Alternative):**
```bash
# List devices
arecord -L

# Test capture
arecord -d 5 -f S16_LE -r 16000 -c 1 test.wav
```

**PortAudio (Universal):**
```bash
# Install
sudo apt install portaudio19-dev python3-pyaudio

# Use in bridge
python -m src.host_audio_bridge.main --driver portaudio
```

### GPU Setup (NVIDIA)

```bash
# Install NVIDIA drivers
sudo ubuntu-drivers install

# Verify
nvidia-smi

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt update
sudo apt install -y nvidia-docker2
sudo systemctl restart docker

# Test GPU in Docker
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

---

## Configuration

### Environment Variables

Key settings in `.env`:

```bash
# WebSocket Configuration
RTSTT_WEBSOCKET_URL=ws://localhost:8000/ws
RTSTT_RECONNECT_DELAY=5.0
RTSTT_MAX_RECONNECT=0  # 0 = infinite

# Audio Configuration
RTSTT_AUDIO_DRIVER=mock  # mock, wasapi, pulseaudio, alsa, portaudio
RTSTT_SAMPLE_RATE=16000  # Hz
RTSTT_CHANNELS=1         # 1=mono, 2=stereo
RTSTT_CHUNK_SIZE=4096    # frames
RTSTT_BUFFER_SECONDS=2.0 # seconds

# Logging
RTSTT_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# GPU
CUDA_VISIBLE_DEVICES=0  # GPU index, -1 for CPU only

# ML Models
STT_MODEL=openai/whisper-large-v3
NLP_MODEL=flair/sentiment-english
SUMMARY_MODEL=google/flan-t5-base
```

### Docker Compose Configuration

Key services in `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8000:8000"
    environment:
      - BACKEND_PORT=8000
      - REDIS_HOST=redis
      - REDIS_PORT=6379

  stt-engine:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - STT_MODEL=openai/whisper-large-v3

  nlp-service:
    environment:
      - NLP_MODEL=flair/sentiment-english

  summary-service:
    environment:
      - SUMMARY_MODEL=google/flan-t5-base

  redis:
    ports:
      - "6379:6379"
```

---

## Running the POC

### Deployment Script Usage

The `deploy-poc.sh` script provides a complete deployment workflow:

```bash
# Quick test with mock audio (30 seconds)
./scripts/deploy-poc.sh test

# Start services only
./scripts/deploy-poc.sh start

# Start with custom settings
./scripts/deploy-poc.sh start --mode production --driver pulseaudio

# Check status
./scripts/deploy-poc.sh status

# View logs
./scripts/deploy-poc.sh logs              # All services
./scripts/deploy-poc.sh logs backend      # Specific service

# Restart
./scripts/deploy-poc.sh restart

# Stop
./scripts/deploy-poc.sh stop
```

### Manual Deployment

```bash
# Build images
docker-compose build

# Start services in order
docker-compose up -d redis
sleep 5
docker-compose up -d stt-engine
sleep 15
docker-compose up -d nlp-service summary-service
sleep 10
docker-compose up -d backend
sleep 10

# Check health
docker-compose ps
python scripts/health_check.py

# Start audio bridge
python -m src.host_audio_bridge.main \
    --driver mock \
    --test-duration 30 \
    --log-level INFO
```

### Production Mode

```bash
# Start services
./scripts/deploy-poc.sh start --skip-build

# Run audio bridge in production mode (continuous)
python -m src.host_audio_bridge.main \
    --driver pulseaudio \
    --log-level INFO \
    --buffer-seconds 2.0

# Or on Windows with WASAPI
python -m src.host_audio_bridge.main \
    --driver wasapi \
    --log-level INFO
```

---

## Troubleshooting

### Common Issues

#### 1. Docker Permission Denied

**Symptoms:**
```
Got permission denied while trying to connect to the Docker daemon socket
```

**Solution:**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

#### 2. GPU Not Available

**Symptoms:**
```
NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver
```

**WSL2 Solution:**
```bash
# Install NVIDIA drivers in Windows
# Verify in WSL2:
nvidia-smi

# If still failing, check WSL2 version:
wsl --version
# Ensure using WSL2, not WSL1
```

**Linux Solution:**
```bash
# Install drivers
sudo ubuntu-drivers install

# Restart
sudo reboot
```

#### 3. WebSocket Connection Failed

**Symptoms:**
```
Error: WebSocket connection failed
```

**Solution:**
```bash
# Check backend is running
docker-compose ps backend

# Check logs
docker-compose logs backend

# Verify port not in use
sudo netstat -tulpn | grep 8000

# Test connection
curl http://localhost:8000/health
```

#### 4. Audio Capture Error (WSL2)

**Symptoms:**
```
Error: No audio devices found
```

**Solution:**
```bash
# WSL2 cannot access Windows audio directly
# Use mock driver for testing:
python -m src.host_audio_bridge.main --driver mock

# For real audio, need to:
# 1. Run audio bridge on Windows host
# 2. Stream to WSL2 backend via WebSocket
```

#### 5. Audio Capture Error (Linux)

**Symptoms:**
```
Error: PulseAudio connection failed
```

**Solution:**
```bash
# Check PulseAudio is running
pactl info

# Start if needed
pulseaudio --start

# Test capture
parecord --channels=1 --rate=16000 --duration=5 test.wav

# Try alternative driver
python -m src.host_audio_bridge.main --driver alsa
```

#### 6. Out of Memory (GPU)

**Symptoms:**
```
CUDA out of memory
```

**Solution:**
```bash
# Reduce batch size in STT config
# Use smaller model
# Free GPU memory:
nvidia-smi --gpu-reset

# Check GPU usage
nvidia-smi
```

#### 7. Slow Transcription

**Symptoms:**
```
Latency > 1000ms
```

**Solution:**
```bash
# Check GPU is being used
nvidia-smi

# Verify CUDA device
docker exec rtstt-stt-engine python -c "import torch; print(torch.cuda.is_available())"

# Use smaller/faster model
# Adjust buffer size for more frequent processing
```

### Health Check

```bash
# Run comprehensive health check
python scripts/health_check.py

# Check individual services
curl http://localhost:8000/health
docker exec rtstt-stt-engine grpc_health_probe -addr=:50051
docker exec rtstt-nlp-service grpc_health_probe -addr=:50052

# View resource usage
docker stats

# Check logs
docker-compose logs --tail=100 -f
```

### Debug Mode

```bash
# Run with debug logging
export RTSTT_LOG_LEVEL=DEBUG

# Start services with debug output
docker-compose up --build

# Run audio bridge with debug
python -m src.host_audio_bridge.main \
    --driver mock \
    --log-level DEBUG \
    --test-duration 10
```

---

## Performance Tuning

### Latency Optimization

**Target: <500ms end-to-end latency**

1. **Audio Buffer Size**: Smaller = lower latency, more overhead
   ```bash
   # Low latency (more overhead)
   --buffer-seconds 1.0

   # Balanced (recommended)
   --buffer-seconds 2.0

   # High throughput (higher latency)
   --buffer-seconds 5.0
   ```

2. **GPU Utilization**: Ensure GPU is being used
   ```bash
   # Check GPU usage
   nvidia-smi -l 1

   # Verify in container
   docker exec rtstt-stt-engine nvidia-smi
   ```

3. **Model Selection**: Faster models = lower latency
   ```bash
   # Fast (lower accuracy)
   STT_MODEL=openai/whisper-base

   # Balanced
   STT_MODEL=openai/whisper-medium

   # Best (higher latency)
   STT_MODEL=openai/whisper-large-v3
   ```

### Resource Optimization

**Memory:**
```yaml
# docker-compose.yml
services:
  stt-engine:
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
```

**CPU:**
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
```

**Network:**
```bash
# Use host network for lowest latency
docker-compose.yml:
  backend:
    network_mode: host
```

### Monitoring

```bash
# Resource usage
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Logs
docker-compose logs -f --tail=100

# Health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/metrics  # If Prometheus enabled
```

---

## Next Steps

After successful deployment:

1. **Integrate with Frontend**
   - React/MUI dashboard at `src/ui/`
   - WebSocket client for real-time updates

2. **Configure Secrets**
   - API keys for external services
   - Database credentials
   - TLS certificates

3. **Enable HTTPS**
   - Configure nginx reverse proxy
   - Add TLS certificates
   - Update WebSocket URL to wss://

4. **Production Hardening**
   - Enable authentication
   - Configure rate limiting
   - Add monitoring (Prometheus/Grafana)
   - Set up log aggregation

5. **Scale Services**
   - Add load balancer
   - Increase gRPC pool sizes
   - Deploy multiple replicas

---

## Support

**Documentation:**
- [Project README](README.md)
- [API Documentation](docs/API.md)
- [Architecture Guide](docs/ARCHITECTURE.md)

**Issues:**
- GitHub Issues: <repository-url>/issues

**Contributing:**
- See [CONTRIBUTING.md](CONTRIBUTING.md)
