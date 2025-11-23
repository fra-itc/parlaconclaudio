# Audio Testing Guide

Comprehensive guide for testing the RTSTT real-time audio processing pipeline.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Performance Targets](#performance-targets)
- [Writing New Tests](#writing-new-tests)
- [Troubleshooting](#troubleshooting)

## Overview

The RTSTT audio testing suite provides comprehensive validation of:

- **Audio Capture**: Microphone input, WASAPI, format conversion
- **Voice Activity Detection (VAD)**: Speech detection, segmentation
- **Circular Buffer**: Thread-safe audio buffering
- **WebSocket Streaming**: Real-time audio transmission
- **End-to-End Pipeline**: Complete audio processing workflow
- **Performance**: Latency and throughput benchmarks

## Test Structure

```
tests/
├── fixtures/
│   └── audio/
│       ├── README.md           # Fixture documentation
│       ├── samples/            # Pre-recorded audio samples
│       └── generated/          # Synthetically generated audio
│
├── utils/
│   ├── audio_generator.py      # Synthetic audio generation
│   └── audio_loader.py         # Audio loading and processing
│
├── unit/
│   ├── test_audio_format.py    # Audio format validation
│   ├── test_circular_buffer.py # Circular buffer tests
│   ├── test_vad.py             # VAD detection tests
│   ├── test_wasapi_capture.py  # WASAPI capture tests
│   └── test_wasapi_devices.py  # Device enumeration tests
│
├── integration/
│   ├── test_audio_service.py           # Audio service integration
│   ├── test_websocket_audio_stream.py  # WebSocket streaming
│   └── test_audio_pipeline_e2e.py      # End-to-end pipeline
│
├── performance/
│   ├── test_audio_latency.py   # Latency benchmarks
│   └── test_throughput.py      # Throughput tests
│
├── manual/
│   └── test_microphone_capture.py      # Interactive mic test
│
└── AUDIO_TESTING.md            # This document
```

## Running Tests

### Quick Start

Run all audio tests:

```bash
./scripts/run_audio_tests.sh --all
```

### Test Categories

Run specific test categories:

```bash
# Unit tests only
./scripts/run_audio_tests.sh --unit

# Integration tests only
./scripts/run_audio_tests.sh --integration

# Performance benchmarks only
./scripts/run_audio_tests.sh --performance
```

### Using Pytest Directly

Run all tests:

```bash
pytest tests/ -v
```

Run tests by marker:

```bash
pytest -m audio -v          # All audio tests
pytest -m vad -v            # VAD tests only
pytest -m websocket -v      # WebSocket tests only
pytest -m performance -v    # Performance tests only
pytest -m "not slow" -v     # Skip slow tests
```

Run specific test file:

```bash
pytest tests/unit/test_vad.py -v
```

Run specific test function:

```bash
pytest tests/unit/test_vad.py::TestSileroVADInit::test_vad_init_default_params -v
```

### Coverage Reports

Generate coverage report:

```bash
./scripts/run_audio_tests.sh --coverage

# Or with pytest directly
pytest --cov=src/core/audio_capture --cov-report=html --cov-report=term
```

View HTML coverage report:

```bash
# Open htmlcov/index.html in your browser
```

### Quick Tests (Skip Slow)

Skip time-consuming tests:

```bash
./scripts/run_audio_tests.sh --quick

# Or with pytest
pytest -m "not slow" -v
```

## Test Categories

### Unit Tests

Test individual components in isolation.

**test_vad.py** - Voice Activity Detection
- VAD initialization and configuration
- Speech vs silence detection
- Edge cases (empty audio, clipping, etc.)
- Accuracy validation (>90% for silence)
- Consistency checks

**test_circular_buffer.py** - Audio Buffering
- Read/write operations
- Wraparound behavior
- Thread safety
- Overflow/underflow handling
- Data integrity validation

**test_wasapi_capture.py** - Windows Audio Capture
- Device initialization
- Audio streaming
- Callback mechanisms
- Error handling

### Integration Tests

Test component interactions and workflows.

**test_websocket_audio_stream.py** - WebSocket Streaming
- Connection lifecycle
- Audio chunk transmission
- Latency measurement
- Error recovery
- Multiple concurrent connections

**test_audio_pipeline_e2e.py** - End-to-End Pipeline
- Complete workflow: Mic → VAD → Buffer → WS → STT → NLP → Summary
- Pipeline validation
- Component integration
- Output verification

### Performance Tests

Benchmark performance and resource utilization.

**test_audio_latency.py** - Latency Benchmarks
- STT processing latency
- NLP processing latency
- Total pipeline latency
- Percentile analysis (P50, P95, P99)

**test_throughput.py** - Throughput Tests
- Concurrent stream processing
- Long-duration streaming
- Memory usage monitoring
- Resource leak detection

### Manual Tests

Interactive tests requiring human intervention.

**test_microphone_capture.py** - Live Microphone Test
- Real-time audio capture
- Audio level visualization
- VAD detection display
- Recording and playback

Run manually:

```bash
python -m tests.manual.test_microphone_capture --duration 5 --show-levels --show-vad
```

## Performance Targets

### Latency Targets

| Component | Target | Critical |
|-----------|--------|----------|
| STT Processing | < 200ms | < 500ms |
| NLP Processing | < 100ms | < 200ms |
| Summary Generation | < 150ms | < 300ms |
| **Total Pipeline** | **< 500ms** | **< 1000ms** |

### Throughput Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Throughput | > 10 chunks/sec | > 5 chunks/sec |
| Memory Usage | < 500MB | < 1GB |
| Memory Growth | < 50MB | < 100MB |

### Validation

Tests automatically validate against these targets and report:
- ✓ **EXCELLENT**: Meets ideal target
- ⚠ **ACCEPTABLE**: Meets critical threshold
- ✗ **FAILS TARGET**: Below critical threshold

## Writing New Tests

### Test Structure

```python
"""
Test Module Description

Brief description of what this module tests.

Author: Your Name
Created: YYYY-MM-DD
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Add paths if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestFeatureName:
    """Test class for feature."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        expected = "expected_value"

        # Act
        result = function_under_test()

        # Assert
        assert result == expected
```

### Using Test Markers

Mark tests appropriately:

```python
@pytest.mark.audio
def test_audio_feature():
    """Test audio feature."""
    pass

@pytest.mark.slow
def test_long_running():
    """Test that takes > 5 seconds."""
    pass

@pytest.mark.integration
def test_integration():
    """Test component integration."""
    pass
```

### Using Fixtures

Use audio fixtures from tests/fixtures/audio/:

```python
from tests.utils.audio_loader import AudioLoader

def test_with_fixture():
    loader = AudioLoader()

    # Load generated fixture
    audio = loader.load_fixture("speech_5s.wav", fixture_type="generated")

    # Process audio
    # ...
```

### Generating Test Audio

```python
from tests.utils.audio_generator import AudioGenerator

def test_with_generated_audio():
    generator = AudioGenerator(sample_rate=16000)

    # Generate speech-like audio
    audio = generator.generate_speech_like_pattern(duration=2.0, amplitude=0.5)

    # Generate silence
    silence = generator.generate_silence(duration=1.0)

    # Generate noise
    noise = generator.generate_white_noise(duration=1.0)
```

### Async Tests

For async functionality:

```python
import pytest
import asyncio

@pytest.mark.asyncio
class TestAsyncFeature:
    """Test async feature."""

    async def test_async_function(self):
        """Test async function."""
        result = await async_function()
        assert result is not None
```

## Troubleshooting

### Common Issues

#### Tests fail with "numpy not installed"

Install required dependencies:

```bash
pip install numpy scipy
```

Or install from requirements:

```bash
pip install -r requirements.txt
```

#### Tests fail with "torch not found"

Install PyTorch for VAD tests:

```bash
pip install torch torchaudio
```

#### WebSocket tests fail with connection errors

Ensure WebSocket gateway is running:

```bash
# Start the orchestrator service
python -m src.agents.orchestrator.fastapi_app
```

Then run tests in a separate terminal.

#### Permission errors on Windows (WASAPI tests)

Run tests with administrator privileges or skip WASAPI tests:

```bash
pytest -m "not wasapi" -v
```

#### Tests are very slow

Skip slow tests:

```bash
pytest -m "not slow" -v
```

Or run specific fast tests only:

```bash
pytest tests/unit/ -v
```

### Test Timeouts

If tests timeout, increase pytest timeout:

```bash
pytest --timeout=300 tests/
```

Or disable timeout for specific tests:

```python
@pytest.mark.timeout(0)
def test_no_timeout():
    pass
```

### Debugging Test Failures

Run with verbose output:

```bash
pytest -vv tests/unit/test_vad.py
```

Run with print statements visible:

```bash
pytest -s tests/unit/test_vad.py
```

Run single test with debugging:

```bash
pytest tests/unit/test_vad.py::test_name -vv -s
```

Use pytest's debugging mode:

```bash
pytest --pdb tests/unit/test_vad.py
```

### Audio Fixture Issues

Generate audio fixtures:

```bash
python -m tests.utils.audio_generator
```

Validate fixtures:

```bash
python -m tests.utils.audio_loader
```

## CI/CD Integration

### GitHub Actions

Example workflow configuration:

```yaml
name: Audio Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov

    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=src/core/audio_capture

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

### Which Tests to Run Where

**On Every PR:**
- Unit tests (fast, no external dependencies)
- Basic integration tests

**Nightly Builds:**
- Full integration tests
- Performance benchmarks
- Long-duration tests

**Manual Trigger:**
- Manual interactive tests
- Stress tests
- Load tests

## Best Practices

### Test Naming

- Use descriptive names: `test_vad_detects_silence_correctly`
- Group related tests in classes
- Use consistent prefixes: `test_`, `TestClassName`

### Test Organization

- One test class per feature
- One assertion per test (when possible)
- Arrange-Act-Assert pattern
- Independent tests (no shared state)

### Test Data

- Use fixtures for reusable test data
- Generate test data programmatically
- Keep test data small and focused
- Document test data requirements

### Performance Testing

- Run performance tests separately from unit tests
- Use realistic data volumes
- Measure multiple iterations
- Report percentiles (P50, P95, P99)
- Compare against baselines

### Documentation

- Document test purpose in docstring
- Explain non-obvious test logic
- Document known issues or limitations
- Keep documentation up to date

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Audio Fixtures README](fixtures/audio/README.md)
- [RTSTT Architecture Docs](../docs/)

## Support

For questions or issues:

1. Check this documentation
2. Review existing tests for examples
3. Check troubleshooting section
4. File an issue on GitHub

---

**Author**: ORCHIDEA Agent System
**Created**: 2025-11-23
**Last Updated**: 2025-11-23
