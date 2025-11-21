# ISTRUZIONI PER CLAUDE CODE CLI - BENCHMARK & MODEL EVALUATION
## Real-Time STT - Metrics Collection, Model Testing & Hyperparameter Tuning

**IMPORTANTE**: Sei un agente autonomo Claude Code CLI. Esegui TUTTE le istruzioni in questo file dall'inizio alla fine. **GPU SAFETY CRITICAL**: Models are loaded SEQUENTIALLY on GPU, NEVER concurrently. Usa sub-agenti SOLO per CPU-bound tasks.

---

## 🎯 OBIETTIVO

Comprehensive benchmarking and evaluation system for RTSTT ML models with:
- Baseline performance metrics (WER, latency, GPU memory)
- Alternative model comparison (Whisper variants, Llama variants)
- Hyperparameter optimization (grid search, Optuna)
- Load testing (concurrent sessions, sustained operation)
- Automated reporting (HTML, metrics DB, Pareto frontiers)

## 📊 METRICHE TARGET

- **Durata Totale**: 3.5 hours (GPU-safe sequential testing)
- **Modelli Testati**: 8 models (4 Whisper + 3 LLM + 1 NLP baseline)
- **Parametri Tuning**: 144 combinations (beam_size × compute_type × batch_size × temperature)
- **GPU Safety**: ZERO OOM errors (sequential loading with cleanup)
- **Deliverables**:
  - ✅ Baseline WER established
  - ✅ Best alternative models identified
  - ✅ Optimal hyperparameters found
  - ✅ Concurrent session limits validated
  - ✅ HTML comparison report
  - ✅ SQLite metrics database

---

## ⚠️ GPU SAFETY RULES - CRITICAL

### **RULE 1: SEQUENTIAL GPU MODEL LOADING**

```
❌ NEVER:  Load Whisper Large AND Whisper Medium simultaneously
✅ ALWAYS: Load → Test → Unload → Clear Cache → Load Next
```

### **RULE 2: EXPLICIT CLEANUP BETWEEN MODELS**

```python
# After each model test:
del model
torch.cuda.empty_cache()
time.sleep(2)  # Wait for GPU memory release
```

### **RULE 3: MEMORY CHECK BEFORE LOAD**

```python
available_gb = get_gpu_free_memory() / 1024
required_gb = MODEL_MEMORY_REQUIREMENTS[model_name]

if available_gb < required_gb + 1:  # +1 GB safety margin
    raise GPUMemoryError(f"Insufficient GPU memory")
```

### **RULE 4: CONCURRENT SESSION LIMITS**

```
Max concurrent sessions during load testing: 3
GPU memory monitoring: Every 5 seconds
Auto-throttle trigger: >14 GB usage
Emergency stop: >15 GB usage
```

---

## 🔀 STRATEGIA PARALLELIZZAZIONE & GPU SEQUENCING

### DEPENDENCY GRAPH

```
WAVE 1: Baseline Metrics (GPU Sequential)
  ↓
WAVE 2: Model Downloads (CPU Parallel - 5 agents)
  ↓
WAVE 3: Whisper Model Tests (GPU Sequential - 1 agent at a time)
  ↓
WAVE 4: LLM Model Tests (GPU Sequential - 1 agent at a time)
  ↓
WAVE 5: Hyperparameter Tuning (GPU Single Model - param sweep)
  ↓
WAVE 6: Load Testing & Reports (CPU Parallel reporting, GPU monitored)
```

### GPU LOAD TIMELINE

```
Time  0 min: [Whisper Large-v3 loaded] ← Baseline
Time 10 min: [GPU IDLE] ← Downloads start
Time 40 min: [Whisper Large-v3] → unload → [Distil-Whisper] → unload → [Medium] → unload
Time 85 min: [GPU IDLE] ← Cleanup
Time 87 min: [Llama 8B] → unload → [Llama 3B] → unload → [Llama 1B]
Time 117 min: [Best Whisper model loaded] ← Tuning
Time 177 min: [Current models] ← Load testing (max 3 concurrent)
Time 207 min: [GPU IDLE] ← Cleanup complete
```

### CONFLICT AVOIDANCE

- **Wave 1**: Single model tests → No conflict
- **Wave 2**: File downloads to separate paths → No conflict
- **Wave 3**: Sequential GPU loading (explicit unload) → No conflict
- **Wave 4**: Sequential GPU loading (explicit unload) → No conflict
- **Wave 5**: Single model, multiple configs → No conflict
- **Wave 6**: Controlled concurrent (max 3, monitored) → Monitored for safety

---

## 🚀 WAVE 1: BASELINE METRICS COLLECTION (10 minuti)

**Obiettivo**: Establish current performance baseline for all models

**GPU Strategy**: Sequential testing of current deployed models

**Parallelismo**: NONE (GPU sequential only)

### Task 1.1: Baseline Whisper Large-v3 Benchmark

```bash
# Sequential GPU execution - NO parallelization
python benchmarks/ml_benchmark.py \
  --model whisper-large-v3 \
  --mode baseline \
  --test-set librispeech-clean-100 \
  --metrics wer,latency,gpu_memory \
  --output baseline_whisper.json
```

**Output Atteso**:
```json
{
  "model": "whisper-large-v3",
  "wer": 0.025,
  "latency_p95_ms": 180,
  "gpu_memory_mb": 3100,
  "rtf": 8.2
}
```

### Task 1.2: Baseline Llama-3.2-8B Benchmark

```bash
# IMPORTANT: Unload Whisper first
python benchmarks/gpu_manager.py --unload-all --wait 5

# Then load Llama
python benchmarks/ml_benchmark.py \
  --model llama-3.2-8b-8bit \
  --mode baseline \
  --test-set summary-eval-100 \
  --metrics rouge,latency,gpu_memory \
  --output baseline_llama.json
```

**Output Atteso**:
```json
{
  "model": "llama-3.2-8b-8bit",
  "rouge_l": 0.42,
  "latency_p95_ms": 2500,
  "gpu_memory_mb": 8200,
  "tokens_per_sec": 35
}
```

### Task 1.3: Baseline NLP Models Benchmark

```bash
# Unload Llama first
python benchmarks/gpu_manager.py --unload-all --wait 5

# Test NLP models (lightweight, can run together)
python benchmarks/ml_benchmark.py \
  --model sentence-bert,pyannote \
  --mode baseline \
  --test-set nlp-eval-100 \
  --metrics precision,latency,gpu_memory \
  --output baseline_nlp.json
```

**✅ Wave 1 Completion Criteria**:
- 3 baseline JSON files created
- Current WER, ROUGE, precision documented
- GPU memory usage profiled
- No OOM errors encountered

---

## 🚀 WAVE 2: ALTERNATIVE MODEL DOWNLOADS (30 minuti)

**Obiettivo**: Download all alternative models for testing

**GPU Strategy**: GPU IDLE during downloads (CPU-only operation)

**Parallelismo**: 5 sub-agenti in parallelo (CPU-bound, no GPU conflict)

### Sub-Agent 1: Download Distil-Whisper Large-v3

**Task tool prompt**:
```
Scarica Distil-Whisper Large-v3 model per speed comparison.

IMPORTANTE: Questo è CPU-only download, GPU deve essere IDLE.

Steps:
1. Verifica GPU idle:
   python -c "import torch; print(f'GPU mem: {torch.cuda.memory_allocated(0)/1024**3:.1f} GB')"
   Expected: <1 GB (models unloaded)

2. Download Distil-Whisper:
   python scripts/download_models.py \
     --model distil-whisper-large-v3 \
     --cache-dir models/whisper/

3. Verifica download:
   ls -lh models/whisper/distil-large-v3/
   Expected: ~390 MB model files

Output atteso:
- Model size: 390 MB
- Download time: ~5 minuti
- Location: models/whisper/distil-large-v3/

Esegui con timeout di 600000ms.
```

### Sub-Agent 2: Download Whisper Medium & Small

**Task tool prompt**:
```
Scarica Whisper Medium e Small models.

Steps:
1. Download Medium:
   python scripts/download_models.py \
     --model whisper-medium \
     --cache-dir models/whisper/

2. Download Small:
   python scripts/download_models.py \
     --model whisper-small \
     --cache-dir models/whisper/

Output atteso:
- Medium: ~1.5 GB
- Small: ~466 MB
- Total time: ~10 minuti

Esegui con timeout di 600000ms.
```

### Sub-Agent 3: Download Llama-3.2-3B & 1B

**Task tool prompt**:
```
Scarica Llama-3.2-3B e 1B models con 8-bit quantization.

IMPORTANTE: Requires HF_TOKEN in environment.

Steps:
1. Verifica HF_TOKEN:
   python -c "import os; print('Token OK' if os.getenv('HF_TOKEN') else 'ERROR: No token')"

2. Download Llama-3.2-3B (8-bit):
   python scripts/download_models.py \
     --model llama-3.2-3b \
     --use-8bit \
     --cache-dir models/transformers/

3. Download Llama-3.2-1B (8-bit):
   python scripts/download_models.py \
     --model llama-3.2-1b \
     --use-8bit \
     --cache-dir models/transformers/

Output atteso:
- Llama-3.2-3B (8-bit): ~3 GB
- Llama-3.2-1B (8-bit): ~1 GB
- Total time: ~15 minuti

Se HF_TOKEN mancante, skip with warning.

Esegui con timeout di 600000ms.
```

### Sub-Agent 4: Prepare Test Datasets

**Task tool prompt**:
```
Download e prepara test datasets per benchmarking.

Steps:
1. Download LibriSpeech test-clean (100 samples):
   python benchmarks/test_datasets.py \
     --dataset librispeech-clean \
     --samples 100 \
     --output tests/fixtures/librispeech_clean_100.json

2. Prepare summary evaluation set:
   python benchmarks/test_datasets.py \
     --dataset summary-eval \
     --samples 100 \
     --output tests/fixtures/summary_eval_100.json

3. Prepare NLP evaluation set:
   python benchmarks/test_datasets.py \
     --dataset nlp-eval \
     --samples 100 \
     --output tests/fixtures/nlp_eval_100.json

Output atteso:
- 3 test dataset files in tests/fixtures/
- Total size: ~500 MB
- Time: ~10 minuti

Esegui con timeout di 600000ms.
```

### Sub-Agent 5: Initialize Metrics Database

**Task tool prompt**:
```
Crea SQLite database per storage metriche.

Steps:
1. Create database schema:
   python benchmarks/metrics_db.py --init

2. Verify schema:
   sqlite3 benchmarks/metrics.db ".schema"

Output atteso:
- Database: benchmarks/metrics.db
- Tables: models, benchmarks, hyperparameters, comparisons
- Indexes created for fast queries

Time: <1 minuto

Esegui con timeout di 60000ms.
```

**✅ Wave 2 Completion Criteria**:
- Distil-Whisper Large-v3 downloaded (~390 MB)
- Whisper Medium + Small downloaded (~2 GB)
- Llama-3.2-3B + 1B downloaded (~4 GB) or skipped if no HF_TOKEN
- 3 test datasets prepared
- Metrics database initialized
- GPU remained IDLE (no models loaded)

---

## 🚀 WAVE 3: WHISPER MODEL COMPARISON (45 minuti)

**Obiettivo**: Test alternative Whisper models and compare performance

**GPU Strategy**: ⚠️ SEQUENTIAL LOADING - One model at a time, explicit cleanup

**Parallelismo**: NONE - Sequential GPU execution only

### ⚠️ CRITICAL: Sequential Execution Pattern

```
FOR EACH model IN [large-v3, distil-large-v3, medium, small]:
    1. Check GPU free memory
    2. Load model on GPU
    3. Run benchmark
    4. Save results
    5. Unload model
    6. Clear GPU cache
    7. Wait 2 seconds
    8. Proceed to next model
```

### Test 3.1: Whisper Large-v3 (Baseline)

```bash
# Already tested in Wave 1, use baseline results
echo "Using baseline_whisper.json from Wave 1"
```

### Test 3.2: Distil-Whisper Large-v3

```bash
# ENSURE GPU is clear first
python benchmarks/gpu_manager.py --check-memory --required 2000  # Need 2 GB free

# Load and test Distil-Whisper
python benchmarks/ml_benchmark.py \
  --model distil-whisper-large-v3 \
  --test-set tests/fixtures/librispeech_clean_100.json \
  --compute-type float16 \
  --beam-size 5 \
  --metrics wer,latency,throughput,gpu_memory \
  --compare-to baseline_whisper.json \
  --output results/distil_whisper_large_v3.json

# CRITICAL: Unload after test
python benchmarks/gpu_manager.py --unload-all --wait 5
```

**Expected Output**:
```json
{
  "model": "distil-whisper-large-v3",
  "wer": 0.027,  // +2% vs baseline
  "latency_p95_ms": 52,  // 3.5x faster than baseline
  "gpu_memory_mb": 800,  // 3.9x less memory
  "rtf": 28.7,  // 3.5x higher throughput
  "improvement_vs_baseline": {
    "speed": 3.5,
    "memory_saving_mb": 2300
  }
}
```

### Test 3.3: Whisper Medium

```bash
# Check memory again
python benchmarks/gpu_manager.py --check-memory --required 2500

# Load and test Medium
python benchmarks/ml_benchmark.py \
  --model whisper-medium \
  --test-set tests/fixtures/librispeech_clean_100.json \
  --compute-type float16 \
  --beam-size 5 \
  --metrics wer,latency,throughput,gpu_memory \
  --compare-to baseline_whisper.json \
  --output results/whisper_medium.json

# Unload
python benchmarks/gpu_manager.py --unload-all --wait 5
```

**Expected Output**:
```json
{
  "model": "whisper-medium",
  "wer": 0.034,  // +1.5% vs baseline
  "latency_p95_ms": 90,  // 2x faster
  "gpu_memory_mb": 1500,  // 2x less memory
  "rtf": 16.4,  // 2x throughput
  "improvement_vs_baseline": {
    "speed": 2.0,
    "memory_saving_mb": 1600
  }
}
```

### Test 3.4: Whisper Small

```bash
# Check memory
python benchmarks/gpu_manager.py --check-memory --required 1000

# Load and test Small
python benchmarks/ml_benchmark.py \
  --model whisper-small \
  --test-set tests/fixtures/librispeech_clean_100.json \
  --compute-type float16 \
  --beam-size 5 \
  --metrics wer,latency,throughput,gpu_memory \
  --compare-to baseline_whisper.json \
  --output results/whisper_small.json

# Unload
python benchmarks/gpu_manager.py --unload-all --wait 5
```

**Expected Output**:
```json
{
  "model": "whisper-small",
  "wer": 0.054,  // +4% vs baseline
  "latency_p95_ms": 36,  // 5x faster
  "gpu_memory_mb": 500,  // 6x less memory
  "rtf": 41.0,  // 5x throughput
  "improvement_vs_baseline": {
    "speed": 5.0,
    "memory_saving_mb": 2600
  }
}
```

### Test 3.5: Generate Whisper Comparison Report

```bash
# CPU-only task, GPU can be idle
python benchmarks/model_comparator.py \
  --models baseline_whisper.json,distil_whisper_large_v3.json,whisper_medium.json,whisper_small.json \
  --metrics wer,latency_p95_ms,gpu_memory_mb,rtf \
  --pareto-frontier wer,latency_p95_ms \
  --output-html reports/whisper_comparison.html \
  --output-db benchmarks/metrics.db
```

**✅ Wave 3 Completion Criteria**:
- 4 Whisper models tested SEQUENTIALLY
- Zero GPU OOM errors
- WER comparison documented
- Speed vs quality Pareto frontier generated
- HTML comparison report created
- Results stored in metrics DB

---

## 🚀 WAVE 4: LLM MODEL COMPARISON (30 minuti)

**Obiettivo**: Test alternative Llama models for summary generation

**GPU Strategy**: ⚠️ SEQUENTIAL LOADING - Explicit cleanup between models

**Parallelismo**: NONE - Sequential GPU execution

### Test 4.1: Llama-3.2-8B-8bit (Baseline)

```bash
# Use baseline from Wave 1
echo "Using baseline_llama.json from Wave 1"
```

### Test 4.2: Llama-3.2-3B-8bit

```bash
# Check memory
python benchmarks/gpu_manager.py --check-memory --required 4000  # Need 4 GB

# Load and test Llama 3B
python benchmarks/ml_benchmark.py \
  --model llama-3.2-3b-8bit \
  --test-set tests/fixtures/summary_eval_100.json \
  --max-new-tokens 300 \
  --temperature 0.7 \
  --metrics rouge,latency,throughput,gpu_memory \
  --compare-to baseline_llama.json \
  --output results/llama_3b_8bit.json

# CRITICAL: Unload
python benchmarks/gpu_manager.py --unload-all --wait 5
```

**Expected Output**:
```json
{
  "model": "llama-3.2-3b-8bit",
  "rouge_l": 0.38,  // -4 points vs baseline
  "latency_p95_ms": 800,  // 3x faster
  "gpu_memory_mb": 3000,  // 2.7x less memory
  "tokens_per_sec": 105,  // 3x throughput
  "improvement_vs_baseline": {
    "speed": 3.1,
    "memory_saving_mb": 5200
  }
}
```

### Test 4.3: Llama-3.2-1B-8bit

```bash
# Check memory
python benchmarks/gpu_manager.py --check-memory --required 2000

# Load and test Llama 1B
python benchmarks/ml_benchmark.py \
  --model llama-3.2-1b-8bit \
  --test-set tests/fixtures/summary_eval_100.json \
  --max-new-tokens 300 \
  --temperature 0.7 \
  --metrics rouge,latency,throughput,gpu_memory \
  --compare-to baseline_llama.json \
  --output results/llama_1b_8bit.json

# Unload
python benchmarks/gpu_manager.py --unload-all --wait 5
```

**Expected Output**:
```json
{
  "model": "llama-3.2-1b-8bit",
  "rouge_l": 0.32,  // -10 points vs baseline
  "latency_p95_ms": 300,  // 8x faster
  "gpu_memory_mb": 1000,  // 8x less memory
  "tokens_per_sec": 280,  // 8x throughput
  "improvement_vs_baseline": {
    "speed": 8.3,
    "memory_saving_mb": 7200
  }
}
```

### Test 4.4: Generate LLM Comparison Report

```bash
# CPU-only task
python benchmarks/model_comparator.py \
  --models baseline_llama.json,llama_3b_8bit.json,llama_1b_8bit.json \
  --metrics rouge_l,latency_p95_ms,gpu_memory_mb,tokens_per_sec \
  --pareto-frontier rouge_l,latency_p95_ms \
  --output-html reports/llm_comparison.html \
  --output-db benchmarks/metrics.db
```

**✅ Wave 4 Completion Criteria**:
- 3 Llama models tested SEQUENTIALLY
- Zero GPU OOM errors
- ROUGE comparison documented
- Speed vs quality trade-offs analyzed
- HTML comparison report created

---

## 🚀 WAVE 5: HYPERPARAMETER TUNING (60 minuti)

**Obiettivo**: Optimize hyperparameters for best models from Waves 3-4

**GPU Strategy**: Single model loaded, multiple parameter configurations tested

**Parallelismo**: Sequential configs (GPU can't test multiple configs in parallel)

### Task 5.1: Select Best Models from Previous Waves

```bash
# Automatic selection based on Pareto frontier
python benchmarks/model_comparator.py \
  --select-best \
  --criteria "wer<0.03,latency_p95_ms<100" \
  --output best_whisper_model.txt

# Likely result: distil-whisper-large-v3 or whisper-medium
```

### Task 5.2: Whisper Hyperparameter Grid Search

```bash
# Load best Whisper model (e.g., distil-whisper-large-v3)
BEST_WHISPER=$(cat best_whisper_model.txt)

# Grid search (144 combinations)
python benchmarks/hyperparameter_tuner.py \
  --model $BEST_WHISPER \
  --param beam_size:1,3,5,10 \
  --param compute_type:float16,int8 \
  --param batch_size:1,2,4 \
  --param temperature:0.0,0.2,0.4 \
  --test-set tests/fixtures/librispeech_clean_100.json \
  --metrics wer,latency_p95_ms \
  --optimize-for "min(wer),min(latency_p95_ms)" \
  --output results/whisper_tuning.json \
  --output-html reports/whisper_tuning.html

# This takes ~40 minutes (144 configs × 15 seconds each)
```

**Expected Output**:
```json
{
  "best_config": {
    "beam_size": 3,
    "compute_type": "int8",
    "batch_size": 4,
    "temperature": 0.0,
    "wer": 0.024,  // Best quality
    "latency_p95_ms": 28  // 6.4x faster than baseline
  },
  "pareto_optimal_configs": [
    {"beam_size": 1, "compute_type": "int8", ...},  // Fastest
    {"beam_size": 3, "compute_type": "int8", ...},  // Balanced
    {"beam_size": 10, "compute_type": "float16", ...}  // Best quality
  ]
}
```

### Task 5.3: LLM Hyperparameter Grid Search

```bash
# Unload Whisper first
python benchmarks/gpu_manager.py --unload-all --wait 5

# Select best LLM (likely llama-3.2-3b for balance)
BEST_LLM="llama-3.2-3b-8bit"

# Grid search (36 combinations)
python benchmarks/hyperparameter_tuner.py \
  --model $BEST_LLM \
  --param temperature:0.5,0.7,0.9 \
  --param top_p:0.8,0.9,0.95 \
  --param max_new_tokens:150,300,500 \
  --param repetition_penalty:1.0,1.1,1.2 \
  --test-set tests/fixtures/summary_eval_100.json \
  --metrics rouge_l,latency_p95_ms \
  --optimize-for "max(rouge_l),min(latency_p95_ms)" \
  --output results/llm_tuning.json \
  --output-html reports/llm_tuning.html

# This takes ~20 minutes
```

**Expected Output**:
```json
{
  "best_config": {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_new_tokens": 300,
    "repetition_penalty": 1.1,
    "rouge_l": 0.40,
    "latency_p95_ms": 750
  }
}
```

### Task 5.4: Store Optimal Configurations

```bash
# Save to database and config files
python benchmarks/hyperparameter_tuner.py \
  --export-configs \
  --whisper-tuning results/whisper_tuning.json \
  --llm-tuning results/llm_tuning.json \
  --output-env config/optimized.env \
  --output-db benchmarks/metrics.db

# Generate config file
cat config/optimized.env
```

**Output**:
```bash
# Optimized Whisper Configuration
STT_MODEL_NAME=distil-whisper-large-v3
STT_BEAM_SIZE=3
STT_COMPUTE_TYPE=int8
STT_BATCH_SIZE=4
STT_TEMPERATURE=0.0

# Optimized Llama Configuration
SUMMARY_MODEL=llama-3.2-3b-8bit
SUMMARY_TEMPERATURE=0.7
SUMMARY_TOP_P=0.9
SUMMARY_MAX_NEW_TOKENS=300
SUMMARY_REPETITION_PENALTY=1.1
```

**✅ Wave 5 Completion Criteria**:
- Hyperparameter grid search completed (180 configs tested)
- Optimal configurations identified
- Pareto frontiers documented
- Optimized .env config file generated
- Results stored in metrics DB

---

## 🚀 WAVE 6: LOAD TESTING & FINAL REPORTS (30 minuti)

**Obiettivo**: Validate concurrent session handling and generate final reports

**GPU Strategy**: Controlled concurrent loading (max 3 sessions) with monitoring

**Parallelismo**: 3 sub-agenti for reporting (CPU-bound)

### Task 6.1: Concurrent Session Load Test

```bash
# Load optimized models from Wave 5
# MONITOR GPU closely - auto-throttle if >14 GB

python benchmarks/load_test.py \
  --concurrent-sessions 1,2,3,4,5 \
  --duration-per-test 5min \
  --whisper-config config/optimized.env \
  --llama-config config/optimized.env \
  --gpu-memory-limit 14000 \  # MB - auto-throttle above this
  --auto-throttle \
  --output results/load_test.json

# Expected: Max 3 concurrent sessions before GPU limit
```

**Expected Output**:
```json
{
  "max_safe_sessions": 3,
  "sessions_tested": {
    "1": {"latency_p95_ms": 28, "gpu_memory_mb": 4200, "success": true},
    "2": {"latency_p95_ms": 35, "gpu_memory_mb": 8100, "success": true},
    "3": {"latency_p95_ms": 52, "gpu_memory_mb": 12400, "success": true},
    "4": {"latency_p95_ms": 180, "gpu_memory_mb": 15800, "success": false, "error": "GPU memory limit exceeded"}
  },
  "recommendation": "max_concurrent_sessions=3"
}
```

### Sub-Agent 1: Generate HTML Master Report

**Task tool prompt**:
```
Genera report HTML completo con tutti i risultati del benchmarking.

Steps:
1. Collect all results:
   - Baseline metrics
   - Model comparisons
   - Hyperparameter tuning
   - Load testing

2. Generate comprehensive HTML report:
   python benchmarks/report_generator.py \
     --input-dir results/ \
     --template templates/benchmark_report.html \
     --include-charts \
     --pareto-frontiers \
     --output reports/master_benchmark_report.html

3. Open report in browser:
   start reports/master_benchmark_report.html

Report include:
- Executive summary
- Baseline vs alternatives comparison tables
- Pareto frontier charts
- Hyperparameter heatmaps
- Load testing results
- Recommendations

Time: ~5 minuti
```

### Sub-Agent 2: Generate Markdown Summary

**Task tool prompt**:
```
Genera Markdown summary per documentation.

python benchmarks/report_generator.py \
  --input-dir results/ \
  --format markdown \
  --output docs/BENCHMARK_RESULTS.md

Include:
- Key findings (best models, optimal params)
- Performance improvements
- Recommendations for production

Time: ~2 minuti
```

### Sub-Agent 3: Export Metrics to CSV

**Task tool prompt**:
```
Esporta tutte le metriche in CSV per analysis esterna.

python benchmarks/metrics_db.py \
  --export-all \
  --format csv \
  --output-dir exports/

Files generati:
- exports/models_comparison.csv
- exports/hyperparameters.csv
- exports/load_test_results.csv

Time: ~1 minuto
```

**✅ Wave 6 Completion Criteria**:
- Load testing completed (max 3 concurrent sessions validated)
- HTML master report generated
- Markdown documentation created
- CSV exports for external analysis
- Recommendations documented

---

## 📊 EXPECTED RESULTS SUMMARY

### Best Alternative Models (Predicted)

**STT (Whisper)**:
```
Winner: Distil-Whisper Large-v3
- WER: 0.027 (+2% vs baseline, acceptable)
- Speed: 3.5x faster than Large-v3
- Memory: 800 MB (vs 3100 MB)
- Recommendation: USE for production (best speed/quality)
```

**Summary (Llama)**:
```
Winner: Llama-3.2-3B-8bit
- ROUGE-L: 0.38 (-4 points vs 8B, acceptable)
- Speed: 3.1x faster
- Memory: 3 GB (vs 8.2 GB)
- Recommendation: USE for multi-session scenarios
```

### Optimal Hyperparameters (Predicted)

**Whisper**:
```
beam_size: 3 (balance quality/speed)
compute_type: int8 (2x memory savings, <1% WER increase)
batch_size: 4 (maximize throughput)
temperature: 0.0 (deterministic)
```

**Llama**:
```
temperature: 0.7 (balanced creativity)
top_p: 0.9 (nucleus sampling)
max_new_tokens: 300 (optimal summary length)
repetition_penalty: 1.1 (avoid repetition)
```

### GPU Configuration Recommendations

**Single High-Quality Session**:
```
Whisper: Large-v3 (float16)
Llama: 8B (8-bit)
Total GPU: ~11 GB
Concurrent: 1 session
```

**Multiple Balanced Sessions**:
```
Whisper: Distil-Large-v3 (int8)
Llama: 3B (8-bit)
Total GPU per session: ~4 GB
Concurrent: 3 sessions (12 GB total)
```

**Maximum Throughput**:
```
Whisper: Medium (int8)
Llama: 1B (8-bit)
Total GPU per session: ~2.5 GB
Concurrent: 5 sessions (12.5 GB total)
```

---

## 🎯 VALIDATION CHECKLIST

Prima di completare, verificare:

- [ ] Zero GPU OOM errors occurred
- [ ] All models tested SEQUENTIALLY (no concurrent GPU loading)
- [ ] Baseline WER documented (expected: ~2.5%)
- [ ] Distil-Whisper tested (expected: 3.5x speed, +2% WER)
- [ ] Llama-3B tested (expected: 3x speed, -4 ROUGE points)
- [ ] Hyperparameter grid search completed (324 total configs)
- [ ] Optimal configs exported to .env file
- [ ] Max concurrent sessions validated (expected: 3)
- [ ] HTML master report generated
- [ ] SQLite metrics.db populated
- [ ] No memory leaks detected (sustained testing passed)

---

## 📈 FILES GENERATED

**Results** (in results/ directory):
```
baseline_whisper.json
distil_whisper_large_v3.json
whisper_medium.json
whisper_small.json
baseline_llama.json
llama_3b_8bit.json
llama_1b_8bit.json
whisper_tuning.json
llm_tuning.json
load_test.json
```

**Reports** (in reports/ directory):
```
whisper_comparison.html
llm_comparison.html
whisper_tuning.html
llm_tuning.html
master_benchmark_report.html
```

**Configuration** (in config/ directory):
```
optimized.env  # Drop-in replacement for .env
```

**Database**:
```
benchmarks/metrics.db  # SQLite with all metrics
```

**Documentation**:
```
docs/BENCHMARK_RESULTS.md  # Markdown summary
```

**Exports**:
```
exports/models_comparison.csv
exports/hyperparameters.csv
exports/load_test_results.csv
```

---

## 🚀 USAGE

### Automated Execution

```bash
cd C:\PROJECTS\RTSTT
claude
> Read orchestration/benchmark-evaluation-terminal.md and execute all waves
```

### Manual Wave Execution

```bash
# Wave 1: Baseline
python benchmarks/ml_benchmark.py --mode baseline

# Wave 2: Downloads (in parallel terminals)
# Terminal 2: python scripts/download_models.py --model distil-whisper-large-v3
# Terminal 3: python scripts/download_models.py --model whisper-medium
# Terminal 4: python scripts/download_models.py --model llama-3.2-3b
# etc.

# Wave 3: Sequential Whisper tests
python benchmarks/ml_benchmark.py --model distil-whisper-large-v3
python benchmarks/gpu_manager.py --unload-all --wait 5
python benchmarks/ml_benchmark.py --model whisper-medium
# etc.

# Wave 5: Hyperparameter tuning
python benchmarks/hyperparameter_tuner.py --model distil-whisper-large-v3

# Wave 6: Load testing
python benchmarks/load_test.py --concurrent-sessions 1,2,3
```

---

## 🎉 BENCHMARK COMPLETE!

Al completamento, il sistema RTSTT avrà:

✅ **Performance Baseline** documented
✅ **Best alternative models** identified (2-3x speed improvements)
✅ **Optimal hyperparameters** found via grid search
✅ **Production configurations** ready (optimized.env)
✅ **Concurrent limits** validated (max safe sessions)
✅ **Comprehensive reports** (HTML + Markdown + CSV)
✅ **Metrics database** for ongoing analysis

**Ready for production deployment with optimized models! 🚀**
