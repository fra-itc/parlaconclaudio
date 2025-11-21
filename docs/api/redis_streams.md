# Redis Streams Message Queue Specification

**Version:** 1.0.0
**Project:** Real-Time STT Orchestrator
**Purpose:** Define Redis Streams architecture for inter-service communication

---

## Overview

Redis Streams is used as the message queue backbone for asynchronous communication between:
- Audio Capture → STT Engine
- STT Engine → NLP Insights
- STT Engine → Summary Generator
- All services → Frontend (via WebSocket gateway)

---

## Stream Architecture

### Stream Naming Convention

```
rtstt:{environment}:{service}:{direction}
```

**Examples:**
- `rtstt:prod:audio:out` - Audio chunks produced by audio capture
- `rtstt:prod:stt:in` - STT engine input queue
- `rtstt:prod:stt:out` - STT transcription results
- `rtstt:prod:nlp:in` - NLP insights input queue
- `rtstt:prod:summary:in` - Summary generator input queue

### Consumer Groups

Each service creates a consumer group to process messages:

```
{service_name}-workers
```

**Examples:**
- `stt-workers` - STT engine consumer group
- `nlp-workers` - NLP service consumer group
- `summary-workers` - Summary service consumer group

---

## Message Formats

### 1. Audio Chunk Message

**Stream:** `rtstt:prod:audio:out`
**Producer:** Audio Capture Service
**Consumers:** STT Engine

**Fields:**
```redis
XADD rtstt:prod:audio:out * \
  session_id "session-12345" \
  chunk_id "chunk-001" \
  timestamp_ms "1679865600000" \
  audio_data_base64 "<base64-encoded-pcm-data>" \
  sample_rate "48000" \
  channels "1" \
  bit_depth "16" \
  duration_ms "100" \
  vad_detected "true" \
  is_final "false"
```

**Field Descriptions:**
- `session_id`: Unique session identifier
- `chunk_id`: Sequential chunk identifier
- `timestamp_ms`: Unix timestamp in milliseconds
- `audio_data_base64`: Base64-encoded PCM audio data
- `sample_rate`: Audio sample rate (Hz)
- `channels`: Number of audio channels (1=mono, 2=stereo)
- `bit_depth`: Bits per sample (16, 24, 32)
- `duration_ms`: Duration of audio chunk in milliseconds
- `vad_detected`: Voice activity detected (true/false)
- `is_final`: Last chunk in session (true/false)

**Max Message Size:** 1MB (Redis limit)
**Recommended Chunk Size:** ~100ms audio = ~9.6KB for 48kHz/16-bit/mono

---

### 2. Transcription Message

**Stream:** `rtstt:prod:stt:out`
**Producer:** STT Engine
**Consumers:** NLP Service, Summary Service, WebSocket Gateway

**Fields:**
```redis
XADD rtstt:prod:stt:out * \
  session_id "session-12345" \
  chunk_id "chunk-001" \
  timestamp_start_ms "1679865600000" \
  timestamp_end_ms "1679865600100" \
  text "Hello, this is a test." \
  confidence "0.95" \
  language "en" \
  is_partial "false" \
  words_json "{\"words\": [{\"text\": \"Hello\", \"confidence\": 0.98, \"start_ms\": 0, \"end_ms\": 300}]}" \
  model_version "whisper-large-v3" \
  processing_time_ms "45.2" \
  wer_estimate "0.03"
```

**Field Descriptions:**
- `session_id`: Session identifier
- `chunk_id`: Corresponding audio chunk ID
- `timestamp_start_ms`: Start time of transcribed segment
- `timestamp_end_ms`: End time of transcribed segment
- `text`: Transcribed text
- `confidence`: Confidence score (0.0-1.0)
- `language`: Detected language (ISO 639-1)
- `is_partial`: Partial transcription (true/false)
- `words_json`: JSON array of word-level timestamps
- `model_version`: STT model used
- `processing_time_ms`: Time taken to process
- `wer_estimate`: Word Error Rate estimate (0.0-1.0)

---

### 3. NLP Insights Message

**Stream:** `rtstt:prod:nlp:out`
**Producer:** NLP Service
**Consumers:** WebSocket Gateway

**Fields:**
```redis
XADD rtstt:prod:nlp:out * \
  session_id "session-12345" \
  timestamp_ms "1679865602000" \
  keywords_json "[{\"keyword\": \"test\", \"relevance_score\": 0.85, \"frequency\": 2}]" \
  speakers_json "[{\"speaker_id\": \"SPEAKER_00\", \"start_ms\": 0, \"end_ms\": 1500}]" \
  sentiment_label "neutral" \
  sentiment_score "0.72" \
  processing_time_ms "120.5"
```

**Field Descriptions:**
- `session_id`: Session identifier
- `timestamp_ms`: Analysis timestamp
- `keywords_json`: JSON array of extracted keywords
- `speakers_json`: JSON array of speaker diarization segments
- `sentiment_label`: Sentiment classification (positive/neutral/negative)
- `sentiment_score`: Sentiment confidence (0.0-1.0)
- `processing_time_ms`: NLP processing time

---

### 4. Summary Message

**Stream:** `rtstt:prod:summary:out`
**Producer:** Summary Service
**Consumers:** WebSocket Gateway

**Fields:**
```redis
XADD rtstt:prod:summary:out * \
  session_id "session-12345" \
  timestamp_ms "1679865603000" \
  summary "This is a concise summary of the transcription." \
  compression_ratio "5.2" \
  key_points_json "[\"Point 1\", \"Point 2\", \"Point 3\"]" \
  coherence_score "0.88" \
  is_final "true" \
  processing_time_ms "250.0"
```

**Field Descriptions:**
- `session_id`: Session identifier
- `timestamp_ms`: Summary generation timestamp
- `summary`: Generated summary text
- `compression_ratio`: Original/Summary length ratio
- `key_points_json`: JSON array of key points
- `coherence_score`: Summary quality metric (0.0-1.0)
- `is_final`: Final summary for session (true/false)
- `processing_time_ms`: Summary generation time

---

### 5. Status Update Message

**Stream:** `rtstt:prod:status:out`
**Producer:** All Services
**Consumers:** WebSocket Gateway, Monitoring

**Fields:**
```redis
XADD rtstt:prod:status:out * \
  session_id "session-12345" \
  service_name "stt-engine" \
  status "processing" \
  message "Transcribing audio chunk 15/30" \
  timestamp_ms "1679865601000" \
  metrics_json "{\"latency_ms\": 42.5, \"gpu_usage_percent\": 78.3}"
```

---

### 6. Error Message

**Stream:** `rtstt:prod:errors`
**Producer:** All Services
**Consumers:** Error Handler, Monitoring

**Fields:**
```redis
XADD rtstt:prod:errors * \
  session_id "session-12345" \
  service_name "stt-engine" \
  error_code "TRANSCRIPTION_FAILED" \
  error_message "GPU out of memory" \
  error_detail "CUDA error: out of memory (2)" \
  recoverable "false" \
  timestamp_ms "1679865602000" \
  stack_trace "<stack-trace-if-available>"
```

---

## Consumer Pattern

### Basic Consumer Implementation (Python)

```python
import redis
import json

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Create consumer group (idempotent)
try:
    r.xgroup_create(
        name='rtstt:prod:stt:in',
        groupname='stt-workers',
        id='0',
        mkstream=True
    )
except redis.exceptions.ResponseError as e:
    if "BUSYGROUP" not in str(e):
        raise

# Consumer loop
consumer_name = "stt-worker-01"
while True:
    # Read messages from stream
    messages = r.xreadgroup(
        groupname='stt-workers',
        consumername=consumer_name,
        streams={'rtstt:prod:stt:in': '>'},
        count=10,
        block=1000  # Block for 1 second
    )

    for stream_name, stream_messages in messages:
        for message_id, fields in stream_messages:
            try:
                # Process message
                session_id = fields['session_id']
                audio_data = base64.b64decode(fields['audio_data_base64'])

                # ... process audio ...

                # Acknowledge message
                r.xack('rtstt:prod:stt:in', 'stt-workers', message_id)

            except Exception as e:
                # Handle error, potentially move to dead letter queue
                print(f"Error processing message {message_id}: {e}")
```

---

## Performance Considerations

### Message Retention

```redis
# Trim stream to max length
XTRIM rtstt:prod:audio:out MAXLEN ~ 10000

# Trim by time (7 days retention)
XTRIM rtstt:prod:stt:out MINID <timestamp-7-days-ago>
```

### Dead Letter Queue

Messages that fail processing 3 times are moved to DLQ:

```
rtstt:prod:{service}:dlq
```

### Backpressure Handling

Monitor stream length and pause producers if needed:

```python
stream_length = r.xlen('rtstt:prod:audio:out')
if stream_length > 5000:
    # Slow down or pause audio capture
    audio_capture.pause()
```

---

## Monitoring

### Key Metrics

1. **Stream Lag**: Difference between last message ID and consumer position
2. **Processing Rate**: Messages/second per consumer
3. **Pending Messages**: Messages read but not acknowledged
4. **Consumer Count**: Active consumers per group
5. **DLQ Size**: Messages in dead letter queue

### Prometheus Metrics

```python
# Example metrics to expose
stream_lag_gauge = Gauge('rtstt_stream_lag', 'Stream lag', ['stream', 'group'])
processing_rate_counter = Counter('rtstt_messages_processed', 'Messages processed', ['service'])
pending_messages_gauge = Gauge('rtstt_pending_messages', 'Pending messages', ['stream', 'group'])
```

---

## Session Lifecycle

1. **Session Start**
   - Audio capture produces to `rtstt:prod:audio:out`
   - Session ID generated and included in all messages

2. **Processing**
   - STT consumes from `rtstt:prod:audio:out`
   - Produces to `rtstt:prod:stt:out`
   - NLP/Summary consume from `rtstt:prod:stt:out`

3. **Session End**
   - Audio capture sends final message (`is_final=true`)
   - Services flush pending messages
   - Summary generates final summary
   - WebSocket sends completion event

4. **Cleanup**
   - Archived messages moved to long-term storage
   - Stream trimmed after retention period

---

## Example: Full Message Flow

```
[Audio Capture] --XADD--> rtstt:prod:audio:out
                                 |
                                 v
                         [STT Engine] --XADD--> rtstt:prod:stt:out
                                 |                       |
                                 |                       |
                                 v                       v
                          [NLP Service]         [Summary Service]
                                 |                       |
                                 v                       v
                        rtstt:prod:nlp:out    rtstt:prod:summary:out
                                 |                       |
                                 +-----------+-----------+
                                             |
                                             v
                                   [WebSocket Gateway]
                                             |
                                             v
                                    [Frontend Client]
```

---

## Configuration

### Redis Configuration (redis.conf)

```ini
# Enable streams
stream-node-max-bytes 4096
stream-node-max-entries 100

# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
appendonly yes
appendfsync everysec
```

### Environment Variables

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=<secure-password>
REDIS_STREAM_MAX_LEN=10000
REDIS_STREAM_RETENTION_DAYS=7
REDIS_CONSUMER_BLOCK_MS=1000
REDIS_CONSUMER_COUNT=10
```

---

## Testing

### Manual Stream Testing

```bash
# Produce test message
redis-cli XADD rtstt:dev:audio:out * \
  session_id "test-001" \
  chunk_id "chunk-001" \
  timestamp_ms "$(date +%s)000" \
  audio_data_base64 "dGVzdA==" \
  sample_rate "48000"

# Read from stream
redis-cli XREAD COUNT 1 STREAMS rtstt:dev:audio:out 0

# Monitor streams
redis-cli XINFO STREAM rtstt:dev:audio:out
```

---

**Document Owner:** Integration Team
**Last Updated:** 2025-11-21
**Status:** Draft for POC Windows 11
