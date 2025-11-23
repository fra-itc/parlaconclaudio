# TERMINAL 2: Real-time Audio Testing

**Branch:** `feature/realtime-audio-tests`
**Worktree:** `/home/frisco/projects/RTSTT-audio-tests`
**Estimated Time:** 3-4 hours
**Priority:** HIGH

## Objective
Create comprehensive real-time audio testing infrastructure with microphone capture, WebSocket streaming, and full pipeline validation.

---

## Task Checklist

### Phase 1: Test Infrastructure Setup (30 min)

- [ ] Review existing test structure:
  ```bash
  ls -la tests/unit/
  ls -la tests/integration/
  ```

- [ ] Create audio fixtures directory:
  ```bash
  mkdir -p tests/fixtures/audio/samples
  mkdir -p tests/fixtures/audio/generated
  ```

- [ ] Create fixtures README:
  - Document audio format requirements (16kHz, 16-bit PCM)
  - Explain fixture categories (speech, silence, noise, multilingual)
  - List required test samples

### Phase 2: Audio Test Fixtures (45 min)

- [ ] Create synthetic audio generator (`tests/utils/audio_generator.py`):
  - Generate sine waves (test tones)
  - Generate white noise
  - Generate silence
  - Generate speech-like patterns
  - Save as WAV files for testing

- [ ] Add fixture loader utility (`tests/utils/audio_loader.py`):
  - Load audio files
  - Convert to required format
  - Normalize audio levels
  - Chunk audio for streaming tests

- [ ] Create test audio samples:
  - 5 second speech sample
  - 2 second silence
  - 3 second noise
  - Mixed content (speech + silence + speech)

### Phase 3: Real-time Microphone Testing (60 min)

- [ ] Create microphone test script (`tests/manual/test_microphone_capture.py`):
  ```python
  # Test live microphone input
  # - Record for N seconds
  # - Display audio levels
  # - Show VAD detection
  # - Save to file for verification
  ```

- [ ] Implement VAD (Voice Activity Detection) test:
  - Test with speech audio
  - Test with silence
  - Test with background noise
  - Measure accuracy

- [ ] Create circular buffer test:
  - Test buffer overflow handling
  - Test buffer underflow scenarios
  - Verify no audio loss

### Phase 4: WebSocket Streaming Tests (60 min)

- [ ] Create WebSocket client test (`tests/integration/test_websocket_audio_stream.py`):
  - Connect to WebSocket gateway
  - Stream audio chunks
  - Receive transcription responses
  - Measure round-trip latency

- [ ] Implement streaming scenarios:
  - Continuous speech streaming
  - Chunked audio with pauses
  - Rapid start/stop cycles
  - Connection recovery after disconnect

- [ ] Add performance metrics:
  - Latency measurement (audio sent → transcription received)
  - Throughput measurement (chunks per second)
  - Resource usage monitoring

### Phase 5: Full Pipeline Integration Test (45 min)

- [ ] Create end-to-end pipeline test (`tests/integration/test_audio_pipeline_e2e.py`):
  ```
  Microphone → VAD → Buffer → WebSocket → STT → NLP → Summary
  ```

- [ ] Test pipeline stages:
  - Audio capture working
  - VAD triggers correctly
  - WebSocket connection stable
  - STT transcription accurate
  - NLP insights extracted
  - Summary generated

- [ ] Add validation checks:
  - Verify transcription text not empty
  - Check NLP entities extracted
  - Ensure summary generated
  - Validate timestamps

### Phase 6: Latency & Performance Testing (30 min)

- [ ] Create latency benchmark (`tests/performance/test_audio_latency.py`):
  - Measure STT processing time
  - Measure NLP processing time
  - Measure total pipeline latency
  - Target: < 500ms end-to-end

- [ ] Create throughput test:
  - Test concurrent audio streams
  - Test long-duration streaming (5+ minutes)
  - Monitor memory usage
  - Check for resource leaks

- [ ] Generate performance report:
  - Average latency by audio length
  - P50, P95, P99 latency percentiles
  - Throughput metrics
  - Resource utilization graphs

### Phase 7: Test Automation & CI Integration (30 min)

- [ ] Update pytest configuration:
  ```bash
  # Add markers for audio tests
  # Configure timeouts
  # Set up fixtures
  ```

- [ ] Create test runner script (`scripts/run_audio_tests.sh`):
  ```bash
  #!/bin/bash
  # Run unit tests
  pytest tests/unit/test_*audio* -v

  # Run integration tests (requires services running)
  pytest tests/integration/test_audio* -v

  # Generate coverage report
  pytest --cov=src/core/audio_capture --cov-report=html
  ```

- [ ] Document CI/CD integration:
  - Which tests run on every PR
  - Which tests require manual trigger
  - How to run performance tests

### Phase 8: Documentation & Commit (15 min)

- [ ] Create comprehensive test documentation:
  - `tests/AUDIO_TESTING.md`
  - How to run tests locally
  - How to add new test cases
  - Interpreting test results

- [ ] Update main README with testing section

- [ ] Commit all changes:
  ```bash
  git add -A
  git commit -m "feat: Add comprehensive real-time audio testing suite

  - Create audio fixture generation utilities
  - Implement microphone capture tests
  - Add WebSocket streaming integration tests
  - Build end-to-end pipeline validation
  - Add latency and performance benchmarks
  - Document testing procedures

  Tests cover: audio capture, VAD, WebSocket streaming, STT pipeline,
  NLP integration, and full E2E workflow with performance metrics.

  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

---

## Files to Create

### New Test Files:
```
tests/fixtures/audio/
├── README.md
├── samples/
│   ├── speech_5s.wav
│   ├── silence_2s.wav
│   └── noise_3s.wav
└── generated/

tests/utils/
├── audio_generator.py
└── audio_loader.py

tests/manual/
└── test_microphone_capture.py

tests/integration/
├── test_websocket_audio_stream.py
└── test_audio_pipeline_e2e.py

tests/performance/
└── test_audio_latency.py

scripts/
└── run_audio_tests.sh

tests/AUDIO_TESTING.md
```

### Files to Modify:
```
pytest.ini (add audio test markers)
README.md (add testing section)
```

---

## Test Scenarios

### 1. Microphone Capture Test
```python
def test_microphone_capture():
    """Test live microphone input capture."""
    # Start capture
    # Record 5 seconds
    # Verify audio data received
    # Check format (16kHz, 16-bit PCM)
    # Validate audio levels
```

### 2. VAD Detection Test
```python
def test_vad_speech_detection():
    """Test Voice Activity Detection accuracy."""
    # Load speech audio
    # Run VAD
    # Verify speech segments detected
    # Check silence segments ignored
```

### 3. WebSocket Streaming Test
```python
def test_websocket_audio_stream():
    """Test audio streaming over WebSocket."""
    # Connect to ws://localhost:8000/ws
    # Stream audio chunks
    # Receive transcription events
    # Measure latency
    # Verify text accuracy
```

### 4. End-to-End Pipeline Test
```python
def test_full_audio_pipeline():
    """Test complete audio processing pipeline."""
    # Simulate microphone input
    # Process through VAD
    # Send to STT via WebSocket
    # Receive transcription
    # Verify NLP insights
    # Check summary generation
    # Total time < 500ms
```

---

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| STT Latency | < 200ms | < 500ms |
| NLP Processing | < 100ms | < 200ms |
| Summary Generation | < 150ms | < 300ms |
| **Total Pipeline** | **< 500ms** | **< 1000ms** |
| Throughput | > 10 chunks/sec | > 5 chunks/sec |
| Memory Usage | < 500MB | < 1GB |

---

## Testing Checklist

- [ ] Synthetic audio generator working
- [ ] Audio fixtures created and validated
- [ ] Microphone capture test passes
- [ ] VAD detection accurate (>90%)
- [ ] WebSocket streaming stable
- [ ] Full pipeline E2E test passes
- [ ] Latency within targets (<500ms)
- [ ] Performance benchmarks documented
- [ ] Test documentation complete
- [ ] CI/CD integration documented

---

## Completion Criteria

✅ Audio test infrastructure complete
✅ Real-time microphone testing working
✅ WebSocket streaming tests passing
✅ E2E pipeline validated
✅ Performance benchmarks meet targets
✅ Documentation comprehensive
✅ Changes committed to branch

---

**Next Steps After Completion:**
1. Wait for other terminals to complete
2. Participate in Wave 2 Sync Agent
3. Merge to develop after sync validation
4. Run full integration test with frontend
