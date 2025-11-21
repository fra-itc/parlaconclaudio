# Real-Time STT Orchestrator Architecture

## Overview

Sistema end-to-end per trascrizione real-time con architettura multi-agente basata su ORCHIDEA v1.3

## Core Components

### 1. Audio Capture Layer

- **Windows**: WASAPI + Virtual Audio Cable
- **macOS**: CoreAudio + BlackHole driver
- **Linux**: PulseAudio + module-loopback

### 2. STT Pipeline (RTX 5080)

- **Primary Model**: Whisper Large V3 (FP16 optimized)
- **Fallback**: FasterWhisper with CTranslate2
- **Chunking**: 30ms frames, 500ms buffer
- **VAD**: Silero VAD v4

### 3. NLP Insights Engine

- **Local LLM**: Mistral-7B-Instruct (4-bit quantized)
- **Topic Extraction**: KeyBERT + Sentence-BERT
- **Speaker Diarization**: PyAnnote Audio

### 4. Summary Generator

- **Model**: Llama-3.2-8B (RTX optimized)
- **Context Window**: 32K tokens
- **Output**: Structured JSON + Markdown

## Agent Architecture

### Orchestrator Team (Claude Opus)

- **Master Orchestrator**: Workflow coordination
- **Quality Gate Controller**: HAS level management
- **Metrics Collector**: ORCHIDEA telemetry

### Development Teams

- **Audio Squad** (Sonnet): Audio capture, processing
- **ML Squad** (Sonnet): Model optimization, inference
- **Frontend Squad** (Sonnet): UI/UX implementation
- **DB Squad** (Opus architect + Sonnet workers): Data persistence

### Support Teams

- **Testing Team** (Haiku): Unit/integration tests
- **Git Team** (Haiku): Version control, CI/CD
- **Documentation Team** (Sonnet): Spec maintenance
