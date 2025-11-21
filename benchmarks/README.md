# RTSTT Audio Capture - Performance Benchmarks

Comprehensive benchmark suite for measuring audio capture system performance.

## Overview

This benchmark suite measures:
- **Latency**: End-to-end pipeline latency
- **Throughput**: Samples processed per second
- **CPU Usage**: Average CPU utilization
- **Memory Usage**: Memory allocation delta
- **VAD Performance**: Voice Activity Detection processing speed

## Quick Start

### Run All Benchmarks

```bash
# Run with default settings (5 seconds per benchmark)
python benchmarks/audio_latency_benchmark.py

# Run with custom duration
python benchmarks/audio_latency_benchmark.py --duration 10.0

# Custom output file
python benchmarks/audio_latency_benchmark.py --output my_benchmark_report.txt

# Custom sample rate
python benchmarks/audio_latency_benchmark.py --sample-rate 8000
```

### Run Specific Tests

```bash
# Run all benchmark tests (including slow tests)
pytest tests/unit/test_benchmarks.py -v

# Run only fast tests
pytest tests/unit/test_benchmarks.py -v -m "not slow"

# Run specific test class
pytest tests/unit/test_benchmarks.py::TestCircularBufferBenchmark -v
```

## Benchmark Components

### 1. WASAPI Capture Benchmark
Measures Windows Audio Session API capture performance:
- Capture latency and jitter
- Audio chunk delivery consistency
- Real-time factor (throughput / sample rate)

**Target Metrics:**
- Latency: < 10ms
- Throughput: >= 16000 samples/sec (real-time minimum)
- Jitter: < 5ms

### 2. Circular Buffer Benchmark
Tests in-memory buffer read/write performance:
- Write throughput
- Read throughput
- Operation latency

**Target Metrics:**
- Write latency: < 1ms
- Read latency: < 1ms
- Throughput: >> 16000 samples/sec

### 3. Silero VAD Benchmark
Measures Voice Activity Detection processing speed:
- Average processing time per chunk
- Real-time factor (should be >> 1.0)
- Processing time variance

**Target Metrics:**
- Processing latency: < 5ms per chunk
- Real-time factor: > 10x (process 10x faster than real-time)
- CPU usage: < 5%

### 4. End-to-End Pipeline Benchmark
Tests complete audio pipeline with all components:
- WASAPI capture → Circular buffer → VAD processing
- Overall pipeline latency
- Speech detection rate

**Target Metrics:**
- Pipeline latency: < 10ms
- Total CPU usage: < 5%
- No dropped samples

## Interpreting Results

### Example Output

```
============================================================
Benchmark: Silero VAD Processing
============================================================
Duration:     5.00s
Samples:      8,832,000
Throughput:   1,766,400 samples/sec
Latency:      0.29ms
CPU Usage:    3.2%
Memory:       11.1 MB
============================================================

Detailed Metrics:
  chunks_processed: 17250
  speech_detected: 850
  avg_processing_time_ms: 0.29
  max_processing_time_ms: 2.5
  min_processing_time_ms: 0.25
  processing_time_std_ms: 0.15
  real_time_factor: 110.4
  chunk_size: 512
```

### Key Metrics Explained

- **Throughput**: Samples processed per second (should be >= sample_rate for real-time)
- **Latency**: Average processing time per operation
- **CPU Usage**: Percentage of CPU time used during benchmark
- **Memory**: Additional memory allocated during benchmark
- **Real-time Factor**: How many times faster than real-time (should be >> 1.0)
- **Jitter**: Variance in processing times (lower is better)

### Performance Targets

| Component | Latency | CPU | Throughput | Real-time Factor |
|-----------|---------|-----|------------|------------------|
| WASAPI Capture | < 10ms | < 2% | >= 16000 samples/sec | >= 1.0 |
| Circular Buffer | < 1ms | < 1% | >> 16000 samples/sec | N/A |
| Silero VAD | < 5ms | < 5% | >= 16000 samples/sec | > 10x |
| End-to-End | < 10ms | < 5% | >= 16000 samples/sec | >= 1.0 |

## Advanced Usage

### Python API

```python
from audio_latency_benchmark import AudioBenchmark, generate_benchmark_report

# Create benchmark instance
benchmark = AudioBenchmark(sample_rate=16000)

# Run individual benchmarks
vad_result = benchmark.benchmark_vad_processing(duration_seconds=5.0)
buffer_result = benchmark.benchmark_circular_buffer(duration_seconds=5.0)

# Run all benchmarks
results = benchmark.run_all_benchmarks(duration_per_benchmark=5.0)

# Generate report
generate_benchmark_report(results, output_file="my_report.txt")
```

### Custom Benchmarks

```python
import time
from audio_latency_benchmark import BenchmarkResult

# Create custom benchmark
def my_custom_benchmark():
    start = time.perf_counter()
    # ... your code ...
    end = time.perf_counter()

    return BenchmarkResult(
        name="My Custom Benchmark",
        duration_seconds=end - start,
        samples_processed=16000,
        throughput_samples_per_sec=16000.0,
        latency_ms=1.0,
        cpu_usage_percent=2.0,
        memory_mb=10.0
    )
```

## Troubleshooting

### WASAPI Benchmark Fails

If the WASAPI benchmark fails with "No audio device available":
1. Ensure you're running on Windows
2. Check that a microphone is connected
3. Verify microphone permissions in Windows settings

### High CPU Usage in VAD Benchmark

If VAD CPU usage is high (> 10%):
1. Ensure you're using GPU acceleration if available
2. Check PyTorch installation (`torch.cuda.is_available()`)
3. Consider using ONNX runtime for optimized inference

### Memory Issues

If benchmarks fail due to memory:
1. Reduce benchmark duration with `--duration` flag
2. Close other applications
3. Check for memory leaks in custom code

## Continuous Integration

To run benchmarks in CI/CD pipelines:

```bash
# Run fast tests only (no hardware capture)
pytest tests/unit/test_benchmarks.py -v -m "not slow"

# Generate benchmark report
python benchmarks/audio_latency_benchmark.py --duration 2.0 --output ci_benchmark.txt
```

## Contributing

When adding new benchmarks:
1. Follow the `BenchmarkResult` dataclass structure
2. Add comprehensive tests in `tests/unit/test_benchmarks.py`
3. Mark slow tests with `@pytest.mark.slow`
4. Update this README with new benchmark documentation

## Performance History

Track performance over time by saving benchmark reports with timestamps:

```bash
python benchmarks/audio_latency_benchmark.py \
    --output "benchmark_$(date +%Y%m%d_%H%M%S).txt"
```
