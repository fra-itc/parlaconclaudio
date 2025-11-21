# Services Integration Guide

## Overview

This document describes the orchestration services for NLP Insights and Summary Generation, including Redis stream integration for inter-service communication.

**Author**: ML Team (ONDATA 2)
**Date**: 2025-11-21
**Status**: ✅ Operational

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ML Pipeline Services                          │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│   NLP Service        │         │  Summary Service     │
│  (nlp_service.py)    │         │ (summary_service.py) │
│                      │         │                      │
│  ┌────────────────┐  │         │  ┌────────────────┐  │
│  │ KeywordExtract │  │         │  │ LlamaSummarizer│  │
│  └────────────────┘  │         │  └────────────────┘  │
│  ┌────────────────┐  │         │  ┌────────────────┐  │
│  │ SpeakerDiariz  │  │         │  │ Redis Cache    │  │
│  └────────────────┘  │         │  └────────────────┘  │
│                      │         │                      │
│        ↓             │         │        ↓             │
│  Redis Producer      │         │  Redis Producer      │
└──────────────────────┘         └──────────────────────┘
         ↓                                  ↓
    ┌────────────────────────────────────────────┐
    │         Redis Streams                      │
    │                                            │
    │  • nlp:insights                            │
    │  • summary:output                          │
    │  • summary:cache:*                         │
    └────────────────────────────────────────────┘
                     ↓
         ┌───────────────────────┐
         │  Downstream Services  │
         │  (API, Storage, etc)  │
         └───────────────────────┘
```

---

## NLP Service

### Purpose
Orchestrates NLP insights extraction from transcription text and audio.

### Components
1. **KeywordExtractor**: Extracts meaningful keywords using KeyBERT
2. **SpeakerDiarization**: Identifies speakers in audio (optional)
3. **Redis Producer**: Publishes results to `nlp:insights` stream

### Input
```python
{
    "text": str,              # Transcribed text
    "audio_path": str,        # Path to audio file (optional)
    "session_id": str,        # Unique session ID (optional)
    "metadata": dict          # Custom metadata (optional)
}
```

### Output (Redis Stream: `nlp:insights`)
```json
{
    "session_id": "nlp_session_20251121_210000",
    "timestamp": "2025-11-21T21:00:00.000Z",
    "text_length": 500,
    "keywords": [
        {"keyword": "machine learning", "score": 0.85},
        {"keyword": "neural networks", "score": 0.78}
    ],
    "speakers": {
        "SPEAKER_00": {
            "num_turns": 5,
            "total_time": 45.2,
            "avg_turn_duration": 9.04
        }
    },
    "insights": {
        "num_keywords": 10,
        "top_keywords": ["machine learning", "neural networks"],
        "text_stats": {
            "char_count": 500,
            "word_count": 85,
            "sentence_count": 8
        },
        "speaker_summary": {
            "num_speakers": 2,
            "dominant_speaker": "SPEAKER_00"
        }
    },
    "processing_time_ms": 145.2
}
```

### Usage
```python
from core.nlp_insights.nlp_service import NLPService

# Initialize
service = NLPService(
    diarization_token="your_hf_token",  # Optional
    enable_diarization=True
)

# Process transcription
result = service.process_transcription(
    text="Your transcription text here...",
    audio_path="/path/to/audio.wav",  # Optional
    session_id="meeting_001",
    metadata={"user_id": "user123"}
)

# Get keywords
keywords = result["keywords"]

# Get speaker info (if available)
speakers = result["speakers"]

# Health check
health = service.health_check()

# Get metrics
metrics = service.get_metrics()
```

### Configuration
```python
class NLPServiceConfig:
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_STREAM_KEY = "nlp:insights"
    KEYWORD_TOP_N = 10
    KEYWORD_USE_MMR = True
    KEYWORD_DIVERSITY = 0.6
    SPEAKER_MIN_SPEAKERS = 1
    SPEAKER_MAX_SPEAKERS = 10
    MAX_TEXT_LENGTH = 50000
```

---

## Summary Service

### Purpose
Orchestrates text summarization using Llama-3.2-8B-Instruct with intelligent caching.

### Components
1. **LlamaSummarizer**: Generates abstractive summaries
2. **Redis Cache**: Stores summaries for frequently requested texts
3. **Redis Producer**: Publishes results to `summary:output` stream

### Input
```python
{
    "text": str,              # Text to summarize
    "max_length": int,        # Max summary length (default: 150 words)
    "min_length": int,        # Min summary length (default: 50 words)
    "temperature": float,     # Sampling temperature (default: 0.7)
    "top_p": float,           # Nucleus sampling (default: 0.9)
    "session_id": str,        # Unique session ID (optional)
    "metadata": dict,         # Custom metadata (optional)
    "use_cache": bool         # Use cached results (default: True)
}
```

### Output (Redis Stream: `summary:output`)
```json
{
    "session_id": "summary_session_20251121_210000",
    "timestamp": "2025-11-21T21:00:00.000Z",
    "text_length": 1500,
    "summary_length": 120,
    "summary": "The meeting discussed implementing a new ML pipeline...",
    "cached": false,
    "parameters": {
        "max_length": 150,
        "min_length": 50,
        "temperature": 0.7,
        "top_p": 0.9
    },
    "processing_time_ms": 2345.6
}
```

### Usage
```python
from core.summary_generator.summary_service import SummaryService

# Initialize (may take a few minutes on first run)
service = SummaryService(
    use_quantization=True,  # 8-bit quantization for memory efficiency
    use_gpu=True,           # Use GPU if available
    enable_cache=True       # Enable Redis caching
)

# Generate summary
summary = service.generate_summary(
    text="Your long text here...",
    max_length=150,
    session_id="meeting_001",
    metadata={"user_id": "user123"}
)

# Batch processing
texts = ["text1", "text2", "text3"]
summaries = service.generate_summaries_batch(texts, max_length=100)

# Cache management
cache_stats = service.get_cache_stats()
service.clear_cache()

# Health check
health = service.health_check()

# Get metrics
metrics = service.get_metrics()
```

### Configuration
```python
class SummaryServiceConfig:
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_STREAM_KEY = "summary:output"
    REDIS_CACHE_PREFIX = "summary:cache:"
    DEFAULT_MAX_LENGTH = 150
    DEFAULT_MIN_LENGTH = 50
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_TOP_P = 0.9
    MAX_TEXT_LENGTH = 100000
    MAX_BATCH_SIZE = 10
    ENABLE_CACHE = True
    CACHE_TTL_SECONDS = 86400  # 24 hours
```

---

## Redis Integration

### Streams

#### 1. `nlp:insights`
- **Producer**: NLP Service
- **Message Format**: JSON with keywords, speakers, and insights
- **Max Length**: 10,000 messages (approximate)
- **Consumers**: API layer, storage service, analytics

#### 2. `summary:output`
- **Producer**: Summary Service
- **Message Format**: JSON with summary and metadata
- **Max Length**: 10,000 messages (approximate)
- **Consumers**: API layer, storage service

### Cache Keys

#### `summary:cache:*`
- **Format**: `summary:cache:{SHA256_HASH}`
- **TTL**: 24 hours (configurable)
- **Content**: Generated summary text
- **Purpose**: Avoid regenerating summaries for identical inputs

### Consumer Groups

Example of consuming from streams:

```python
import redis

client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Create consumer group
client.xgroup_create('nlp:insights', 'api_consumers', id='0', mkstream=True)

# Read messages
messages = client.xreadgroup(
    'api_consumers',
    'consumer_1',
    {'nlp:insights': '>'},
    count=10,
    block=5000
)

# Process messages
for stream_name, stream_messages in messages:
    for msg_id, msg_data in stream_messages:
        data = json.loads(msg_data['data'])
        # Process data...

        # Acknowledge message
        client.xack('nlp:insights', 'api_consumers', msg_id)
```

---

## Testing

### Unit Tests

```bash
# Test NLP Service
pytest tests/test_nlp_service_integration.py -v

# Test Summary Service
pytest tests/test_summary_service_integration.py -v
```

### Redis Streams Test

```bash
# Ensure Redis is running
redis-server

# Run integration test
python tests/test_redis_streams.py
```

### Manual Testing

```python
# Test NLP Service
python -m core.nlp_insights.nlp_service

# Test Summary Service
python -m core.summary_generator.summary_service
```

---

## Performance Metrics

### NLP Service
- **Processing Time**: ~100-200ms per transcription (without diarization)
- **With Diarization**: +2-5 seconds (depends on audio length)
- **Memory Usage**: ~2GB (KeyBERT + SentenceTransformer)
- **Throughput**: ~5-10 requests/second

### Summary Service
- **First Load Time**: 1-2 minutes (model download and loading)
- **Processing Time**:
  - Without cache: 2-5 seconds per summary
  - With cache: <100ms
- **Memory Usage**:
  - Without quantization: ~16GB
  - With 8-bit quantization: ~8GB
- **Cache Hit Rate**: 40-60% (typical)
- **Throughput**: ~2-3 requests/second (uncached)

---

## Deployment

### Environment Variables

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# HuggingFace Token (for speaker diarization)
HF_TOKEN=your_token_here

# GPU Configuration
CUDA_VISIBLE_DEVICES=0
```

### Docker Deployment

```dockerfile
# Dockerfile example
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/

# Environment
ENV PYTHONPATH=/app
ENV REDIS_HOST=redis

# Run service
CMD ["python", "-m", "core.nlp_insights.nlp_service"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  nlp-service:
    build: .
    environment:
      - REDIS_HOST=redis
      - HF_TOKEN=${HF_TOKEN}
    depends_on:
      - redis

  summary-service:
    build: .
    command: python -m core.summary_generator.summary_service
    environment:
      - REDIS_HOST=redis
    depends_on:
      - redis
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  redis-data:
```

---

## Monitoring

### Health Checks

```python
# NLP Service
health = nlp_service.health_check()
# Returns: {"status": "healthy", "components": {...}}

# Summary Service
health = summary_service.health_check()
# Returns: {"status": "healthy", "components": {...}}
```

### Metrics

```python
# Get service metrics
metrics = service.get_metrics()

# NLP Service metrics
{
    "total_processed": 1234,
    "total_keywords_extracted": 12340,
    "total_speakers_identified": 2468,
    "avg_processing_time": 0.145,
    "last_processed_at": "2025-11-21T21:00:00Z"
}

# Summary Service metrics
{
    "total_processed": 567,
    "total_cached_hits": 234,
    "total_cached_misses": 333,
    "avg_processing_time": 2.345,
    "avg_summary_length": 120,
    "cache": {
        "hit_rate": 0.41,
        "total_cached": 150
    }
}
```

### Redis Monitoring

```bash
# Monitor streams
redis-cli XINFO STREAM nlp:insights
redis-cli XINFO STREAM summary:output

# Check cache size
redis-cli KEYS "summary:cache:*" | wc -l

# Monitor memory
redis-cli INFO memory
```

---

## Troubleshooting

### Redis Connection Issues

```python
# Test Redis connection
import redis
client = redis.Redis(host='localhost', port=6379)
client.ping()  # Should return True
```

### Model Loading Issues

```python
# Check HuggingFace cache
from pathlib import Path
cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
print(f"Cache directory: {cache_dir}")
print(f"Exists: {cache_dir.exists()}")

# Clear cache if needed
import shutil
shutil.rmtree(cache_dir, ignore_errors=True)
```

### GPU Memory Issues

```python
# Enable 8-bit quantization
service = SummaryService(use_quantization=True)

# Or use CPU
service = SummaryService(use_gpu=False)

# Check GPU memory
import torch
if torch.cuda.is_available():
    print(torch.cuda.memory_summary())
```

---

## References

- [KeyBERT Documentation](https://github.com/MaartenGr/KeyBERT)
- [PyAnnote Audio Documentation](https://github.com/pyannote/pyannote-audio)
- [Llama Models](https://huggingface.co/meta-llama)
- [Redis Streams Guide](https://redis.io/docs/data-types/streams/)

---

**Last Updated**: 2025-11-21
**Version**: 1.0
**Maintainer**: ML Team (ONDATA 2)
