# RTSTT Performance Benchmarks

Comprehensive benchmark suite for measuring system performance across audio capture, ML models, and end-to-end pipelines.

## Overview

This benchmark suite measures:

### Audio Capture Benchmarks
- **Latency**: End-to-end pipeline latency
- **Throughput**: Samples processed per second
- **CPU Usage**: Average CPU utilization
- **Memory Usage**: Memory allocation delta
- **VAD Performance**: Voice Activity Detection processing speed

### ML Model Benchmarks (NEW)
- **WER/CER**: Word Error Rate and Character Error Rate for STT models
- **ROUGE Scores**: Summary quality evaluation (ROUGE-1, ROUGE-2, ROUGE-L)
- **GPU Memory Safety**: Sequential model loading with OOM prevention
- **Model Latency**: Inference time per sample
- **Throughput**: Real-time factor (RTF) measurement
- **Hyperparameter Tuning**: Grid search across 180+ combinations

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

---

## ML Model Benchmarking Infrastructure

### GPU Safety Manager

**File**: `benchmarks/gpu_manager.py`

Enforces **sequential GPU model loading** to prevent Out-of-Memory (OOM) errors on RTX 5080 (16GB VRAM).

**Key Features:**
- Memory requirement tracking for all models
- Pre-load safety checks with 1GB safety margin
- Automatic cleanup between model loads
- Explicit wait periods for GPU memory release

**Critical GPU Safety Rules:**
```python
# ❌ NEVER DO THIS (concurrent loading will cause OOM)
whisper_model = load_whisper()  # 3.2 GB
llama_model = load_llama()      # 8.5 GB  ← OOM!

# ✅ ALWAYS DO THIS (sequential with cleanup)
whisper_model = gpu_manager.safe_load("whisper-large-v3")
results = test_whisper(whisper_model)
del whisper_model
torch.cuda.empty_cache()
time.sleep(2)  # Wait for GPU memory release

llama_model = gpu_manager.safe_load("llama-3.2-8b")
results = test_llama(llama_model)
gpu_manager.unload_all_models(wait_seconds=3)
```

**Usage:**
```python
from benchmarks.gpu_manager import GPUManager

gpu_mgr = GPUManager()

# Check if safe to load model
gpu_mgr.safe_load_check("whisper-large-v3", required_mb=3200)

# Get current GPU status
status = gpu_mgr.get_gpu_status()
print(f"Free VRAM: {status['free_mb']} MB")

# Track loaded models
gpu_mgr.track_model("whisper-large-v3", 3200)

# Cleanup all models
gpu_mgr.unload_all_models(wait_seconds=3)
```

**Model Memory Requirements:**
| Model | VRAM (MB) | Precision |
|-------|-----------|-----------|
| Whisper Large V3 | 3,200 | FP16 |
| Whisper Medium | 1,500 | FP16 |
| Distil-Whisper Large V3 | 1,600 | FP16 |
| Llama-3.2-8B (8-bit) | 8,500 | INT8 |
| Llama-3.2-8B (FP16) | 15,000 | FP16 |
| BART Large | 1,600 | FP16 |
| T5 Base | 900 | FP16 |

**Safety Margin**: Always keeps 1GB (1000 MB) free VRAM

---

### WER Calculator

**File**: `benchmarks/wer_calculator.py`

Calculates **Word Error Rate (WER)** and **Character Error Rate (CER)** using Levenshtein distance algorithm.

**Features:**
- Levenshtein distance with operation tracking (substitutions, deletions, insertions)
- Optional text normalization (lowercase, punctuation removal, whitespace)
- Support for batch processing
- Detailed metrics including operation counts

**Usage:**
```python
from benchmarks.wer_calculator import calculate_wer, WERMetrics

# Basic usage
reference = "the quick brown fox jumps over the lazy dog"
hypothesis = "the quik brown fox jumped over a lazy dog"

metrics = calculate_wer(reference, hypothesis, normalize=True)

print(f"WER: {metrics.wer:.2%}")
print(f"CER: {metrics.cer:.2%}")
print(f"Substitutions: {metrics.substitutions}")
print(f"Deletions: {metrics.deletions}")
print(f"Insertions: {metrics.insertions}")
```

**CLI Usage:**
```bash
# Calculate WER from files
python benchmarks/wer_calculator.py \
  --reference data/reference.txt \
  --hypothesis outputs/hypothesis.txt \
  --normalize

# From strings
python benchmarks/wer_calculator.py \
  --ref-text "the quick brown fox" \
  --hyp-text "the quik brown fox" \
  --normalize
```

**Normalization Options:**
- Convert to lowercase
- Remove punctuation
- Normalize whitespace
- Remove extra spaces

**Output Metrics:**
```python
@dataclass
class WERMetrics:
    wer: float              # Word Error Rate (0.0 to 1.0+)
    cer: float              # Character Error Rate (0.0 to 1.0+)
    reference_words: int    # Number of words in reference
    hypothesis_words: int   # Number of words in hypothesis
    substitutions: int      # Word substitutions
    deletions: int          # Word deletions
    insertions: int         # Word insertions
    distance: int           # Levenshtein distance
```

---

### ML Benchmark Orchestrator

**File**: `benchmarks/ml_benchmark.py`

Main orchestrator for comprehensive ML model benchmarking (currently a stub, full implementation pending).

**Planned Features:**
- Whisper model variants (Large V3, Medium, Distil-Whisper)
- LLM summarization models (Llama, BART, T5)
- Hyperparameter tuning with grid search
- Performance profiling (latency, throughput, GPU memory)
- Results export to JSON/SQLite

**Future Usage:**
```bash
# Run baseline benchmark
python benchmarks/ml_benchmark.py --model whisper-large-v3 --mode baseline

# Compare models
python benchmarks/ml_benchmark.py --model distil-whisper-large-v3 --compare-to baseline.json

# Hyperparameter tuning
python benchmarks/ml_benchmark.py --mode tune --params beam_size temperature

# Full evaluation suite
python benchmarks/ml_benchmark.py --mode full --output results.json
```

**Components to integrate:**
1. `gpu_manager.py` - Safe model loading
2. `wer_calculator.py` - STT evaluation
3. ROUGE calculator - Summary evaluation (TODO)
4. Model loading/unloading logic (TODO)
5. Benchmark orchestration (TODO)

---

### Automated Benchmarking Workflow

**File**: `orchestration/benchmark-evaluation-terminal.md`

Complete benchmarking workflow with **6 waves of GPU-safe sequential execution** (~3.5 hours).

**Wave Structure:**
1. **Baseline Measurements** (10 min) - System metrics, GPU baseline
2. **Model Downloads** (45 min) - Validate all models downloaded
3. **Whisper Tests** (60 min) - 4 Whisper variants sequentially
4. **LLM Tests** (60 min) - Llama, BART, T5 sequentially
5. **Hyperparameter Tuning** (30 min) - 180 combinations
6. **Load Testing** (15 min) - Concurrent request handling

**GPU Safety Enforcement:**
```
WAVE 3: Whisper Model Tests (60 min - SEQUENTIAL)
├─ Test Whisper Large V3
│  ├─ Load model (3.2 GB)
│  ├─ Run benchmarks
│  ├─ Unload + clear cache
│  └─ Wait 2 seconds
├─ Test Whisper Medium
│  ├─ Load model (1.5 GB)
│  ├─ Run benchmarks
│  ├─ Unload + clear cache
│  └─ Wait 2 seconds
...
```

**Test Matrix:**
- 8 ML models total
- 180 hyperparameter combinations
- 5 test datasets
- WER, ROUGE, latency, GPU memory metrics

**Results Storage:**
- JSON exports
- SQLite database (TODO)
- HTML reports (TODO)
- Grafana dashboards (TODO)

---

## Benchmarking Best Practices

### For Audio Benchmarks
1. Close other applications to reduce noise
2. Use consistent test duration (5-10 seconds)
3. Run multiple iterations and average results
4. Monitor CPU/memory during tests

### For ML Benchmarks
1. **NEVER** load multiple models on GPU concurrently
2. **ALWAYS** use `gpu_manager.safe_load_check()` before loading
3. **ALWAYS** cleanup between models: `del model; torch.cuda.empty_cache(); time.sleep(2)`
4. Monitor GPU temperature and throttling
5. Use 8-bit quantization when possible (Llama: 15GB → 8GB)
6. Validate models downloaded before benchmarking
7. Use consistent test datasets across runs

### GPU Memory Budget (RTX 5080 16GB)
```
Total VRAM:           16,000 MB
Safety Margin:        -1,000 MB
Available for models: 15,000 MB

Safe Configurations:
✅ Whisper Large V3 (3,200 MB) + overhead → 4,200 MB
✅ Llama 8-bit (8,500 MB) + overhead → 9,500 MB
✅ BART Large (1,600 MB) + Whisper Medium (1,500 MB) → 3,100 MB
❌ Whisper Large V3 + Llama 8-bit → 11,700 MB (risky, use sequential)
❌ Llama FP16 (15,000 MB) → OOM (use 8-bit instead)
```
