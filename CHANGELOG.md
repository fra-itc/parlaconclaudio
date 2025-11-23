# Changelog

All notable changes to the RTSTT project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added - Wave 3: Cross-Platform Support & Production Features (November 23, 2025)

**Platform Support:**
- Full WSL2 (Windows Subsystem for Linux 2) support with automated setup
- Native Linux deployment capabilities
- Cross-platform audio capture abstraction layer
- Platform auto-detection (Windows, WSL1/2, Linux, macOS)

**Audio Infrastructure:**
- WebSocket audio bridge for WSL2 audio streaming
- PulseAudio driver for native Linux audio capture
- PortAudio universal driver for cross-platform compatibility
- Mock audio driver for hardware-free testing
- Factory pattern for automatic driver selection
- Thread-safe asyncio event loop handling

**Processing Pipeline:**
- Complete STT→NLP→Summary enrichment pipeline
- Keyword extraction from transcriptions
- Automatic text summarization for longer content
- Multi-stage latency tracking (STT: 250-311ms, NLP: <1ms, Summary: <1ms)
- Enriched JSON response format with separate sections
- Graceful fallback if pipeline stages fail

**Deployment & DevOps:**
- Automated WSL2 setup script (setup-wsl2.sh) with dependency installation
- POC deployment orchestration script (deploy-poc.sh) with health monitoring
- Comprehensive deployment guide (DEPLOYMENT.md - 818 lines)
- Docker and NVIDIA GPU auto-configuration
- Service health checks and monitoring
- Optional requirements for audio drivers (requirements-audio.txt)

**Testing & Validation:**
- End-to-end pipeline testing: 253-312ms total latency (48% under 500ms target)
- 100% success rate with 0 errors over 6 test runs
- Mock driver validated with sine wave, noise, and silence patterns
- WebSocket→STT→NLP→Summary full pipeline validation

### Changed

**Architecture:**
- Decoupled audio capture from WASAPI (Windows-only) to cross-platform abstraction
- WebSocket gateway now includes full NLP/Summary enrichment
- Audio bridge service runs on host, streams to containerized backend
- gRPC connection pooling for ML services (STT, NLP, Summary)

**Performance:**
- Total pipeline latency: 253-312ms (STT + NLP + Summary)
- WebSocket audio streaming: 0.28 Mbps throughput
- 2-second audio buffering for optimal network efficiency

**Compatibility:**
- Supports WSL2 without direct audio access (WebSocket bridge pattern)
- Supports native Linux with PulseAudio or PortAudio
- Maintains Windows support (PortAudio fallback until WASAPI refactor)

### Fixed
- cuDNN library path in STT engine for proper GPU acceleration
- Proto file compilation in backend Docker image
- Asyncio event loop threading for WebSocket audio callbacks
- Legacy audio imports made optional to avoid container errors
- Circular import issues in audio factory registration

### Commits (Wave 3)
1. **417f495**: fix: Add cuDNN library path to STT engine LD_LIBRARY_PATH
2. **122b74b**: feat: Implement WebSocket→STT integration for real-time audio processing
3. **1203673**: feat: Add cross-platform audio capture abstraction layer
4. **ae78273**: feat: Implement WebSocket audio bridge for WSL2/Linux support
5. **2459260**: feat: Add comprehensive WSL2/Linux deployment infrastructure
6. **909e80a**: feat: Implement complete STT→NLP→Summary pipeline
7. **0734baf**: feat: Add PulseAudio and PortAudio drivers for real audio capture

### Added - Wave 2: RTX 5080 & GPU Validation (November 22, 2025)

**GPU Support:**
- Full RTX 5080 Blackwell GPU support
- GPU validation suite with comprehensive 7-test framework
- Benchmark infrastructure foundation (metrics DB, test datasets)
- RTX 5080 validation report with detailed performance metrics

### Changed - Wave 2
- **BREAKING**: Upgraded PyTorch from 2.1.0+cu121 to 2.7.0+cu128
- **BREAKING**: Upgraded CUDA runtime from 12.1.0 to 12.8.0
- Upgraded transformers: 4.35.0 → 4.48.0
- Upgraded accelerate: 0.25.0 → 1.2.0
- Upgraded bitsandbytes: 0.41.3 → 0.48.0
- Upgraded sentence-transformers: 2.2.2 → 2.3.0
- Upgraded tokenizers: 0.14.1 → 0.21.0
- Upgraded safetensors: 0.4.1 → 0.4.3
- All Docker images now use nvidia/cuda:12.8.0-runtime-ubuntu22.04
- Restored GPU mode (DEVICE=cuda) for NLP and Summary services

### Fixed - Wave 2
- RTX 5080 CUDA kernel compatibility (PyTorch 2.1.0 lacked sm_120 support)
- Dependency conflicts in NLP and Summary service builds
- tokenizers version compatibility with transformers 4.48.0
- safetensors version compatibility with accelerate 1.2.0

---

## [1.0.0-POC] - 2025-11-21

### Added
- Initial POC release with multi-agent orchestration
- WASAPI audio capture with <10ms latency
- Whisper Large V3 STT engine
- NLP insights (keywords, diarization, sentiment)
- Llama-3.2-8B summarization
- Electron desktop app with React UI
- FastAPI WebSocket gateway
- Redis Streams message queue
- gRPC inter-service communication
- Docker Compose orchestration
- Prometheus + Grafana monitoring
- ORCHIDEA Framework v1.3 integration

### Components Implemented
- Audio capture service (WASAPI)
- STT engine service (Whisper + gRPC)
- NLP insights service (Mistral-7B + gRPC)
- Summary generator service (Llama-3.2-8B + gRPC)
- FastAPI backend (WebSocket + REST)
- Electron desktop app (React + TypeScript)
- Redis message queue
- Monitoring stack (Prometheus + Grafana)

---

## RTX 5080 GPU Support Details (November 22, 2025)

### Validation Results

**All Services: 7/7 Tests Passed ✅**

| Service | GPU | Compute Capability | PyTorch | CUDA | Status |
|---------|-----|-------------------|---------|------|--------|
| STT Engine | RTX 5080 | 12.0 (Blackwell sm_120) | 2.7.0+cu128 | 12.8 | ✅ OPERATIONAL |
| NLP Service | RTX 5080 | 12.0 (Blackwell sm_120) | 2.7.0+cu128 | 12.8 | ✅ OPERATIONAL |
| Summary Service | RTX 5080 | 12.0 (Blackwell sm_120) | 2.7.0+cu128 | 12.8 | ✅ OPERATIONAL |

### Performance Metrics

**Matrix Multiplication Benchmark (2048x2048):**
- STT Engine: 129.82 ms
- NLP Service: 86.45 ms
- Summary Service: 60.36 ms

**GPU Memory:**
- Total Available: 15.9 GB
- Memory Allocation Test: PASSED (1 GB allocated and freed cleanly)
- No memory leaks detected

**Docker Images:**
- STT Engine: 11.6 GB
- NLP Service: 11.2 GB
- Summary Service: 11.0 GB

### Files Modified

**Core Stack:**
- `requirements/ml.txt` - Updated all ML dependencies to CUDA 12.8 compatible versions
- `pyproject.toml` - Changed PyTorch source from cu121 to cu128

**Infrastructure:**
- `infrastructure/docker/Dockerfile.stt` - Updated to CUDA 12.8 base image
- `infrastructure/docker/Dockerfile.nlp` - Updated to CUDA 12.8 base image
- `infrastructure/docker/Dockerfile.summary` - Updated to CUDA 12.8 base image
- `docker-compose.yml` - Restored GPU mode for NLP and Summary services

**New Tools:**
- `benchmarks/quick_gpu_validation.py` - Comprehensive GPU validation suite
- `benchmarks/metrics_db.py` - SQLite metrics database
- `benchmarks/test_datasets.py` - Synthetic test data generator
- `RTX_5080_VALIDATION_REPORT.md` - Full validation report

### Git Commits

1. **7fec0f7**: feat: Add full RTX 5080 GPU support with PyTorch 2.7.0 and CUDA 12.8
2. **b7c4595**: feat: Add GPU validation suite and benchmark infrastructure foundation

### Dependencies Updated

```
PyTorch: 2.1.0+cu121 → 2.7.0+cu128
CUDA Runtime: 12.1.0 → 12.8.0
transformers: 4.35.0 → 4.48.0
accelerate: 0.25.0 → 1.2.0
bitsandbytes: 0.41.3 → 0.48.0
sentence-transformers: 2.2.2 → 2.3.0
tokenizers: 0.14.1 → 0.21.0
safetensors: 0.4.1 → 0.4.3
```

### Breaking Changes

- **Minimum CUDA version**: Now requires CUDA 12.8+ (was 12.1+)
- **PyTorch version**: Now requires PyTorch 2.7.0+ with cu128 variant
- **Docker base images**: All ML services now use nvidia/cuda:12.8.0-runtime-ubuntu22.04
- **GPU requirement**: RTX 5080 or GPU with compute capability 12.0+ (Blackwell architecture)

### Migration Guide

For systems not using RTX 5080 Blackwell:
1. Ensure GPU has CUDA compute capability supported by PyTorch 2.7.0
2. Update CUDA driver to 576.88+ for full CUDA 12.8 support
3. Rebuild all Docker images after pulling changes
4. Verify GPU detection: `docker run --rm --gpus all <image> python -c "import torch; print(torch.cuda.is_available())"`

---

## Future Planned Features

### Benchmarking Suite (Partial Implementation)
- [x] GPU validation framework
- [x] Metrics database schema
- [x] Synthetic test dataset generator
- [ ] Main benchmark orchestrator (ml_benchmark.py)
- [ ] Model comparison tool (model_comparator.py)
- [ ] Hyperparameter tuning (hyperparameter_tuner.py)
- [ ] Load testing framework (load_test.py)
- [ ] Report generator (HTML/Markdown)

### Model Optimization
- [ ] Alternative Whisper models (Distil-Whisper, Medium, Small)
- [ ] Alternative Llama models (3B, 1B variants)
- [ ] Hyperparameter optimization via grid search
- [ ] Concurrent session limits validation
- [ ] Pareto frontier analysis (speed vs quality trade-offs)

---

**Last Updated**: November 22, 2025
