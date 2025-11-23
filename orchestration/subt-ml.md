# ISTRUZIONI PER CLAUDE CODE CLI - ML PIPELINE TEAM
## Whisper STT + NLP Insights + Summary Generator

**IMPORTANTE**: Agente autonomo nel worktree `RTSTT-ml` (branch: `feature/ml-pipeline`). Parallelizza con **5 sub-agenti, 2 ondate**.

---

## 🎯 OBIETTIVO
ML pipeline completa: Whisper Large V3 (RTX 5080) + NLP (Mistral-7B) + Summary (Llama-3.2-8B)

## 📊 TARGET
- **Durata**: 4-6 ore
- **Parallelismo**: 2 ondate, 5 sub-agenti
- **Performance**: WER <5%, Latency <50ms, GPU <14GB

---

## 🔀 STRATEGIA PARALLELIZZAZIONE

```
ONDATA 1: Model Setup (3 paralleli)
├── Sub-Agent 1: Whisper Large V3 + FasterWhisper
├── Sub-Agent 2: NLP Models (Mistral + Sentence-BERT + PyAnnote)
└── Sub-Agent 3: Summary Model (Llama-3.2-8B)
      ↓
ONDATA 2: Implementation (2 paralleli)
├── Sub-Agent 4: STT Engine + gRPC + Redis
└── Sub-Agent 5: NLP Service + Summary Service
```

### CONFLICT AVOIDANCE
- Sub-Agent 1 → `src/core/stt_engine/*`
- Sub-Agent 2 → `src/core/nlp_insights/*`
- Sub-Agent 3 → `src/core/summary_generator/*`
- Sub-Agent 4 → `src/core/stt_engine/grpc_server.py`, `redis_consumer.py`
- Sub-Agent 5 → Completamento NLP + Summary

---

## 🚀 ONDATA 1: MODEL SETUP

### Sub-Agent 1: Whisper Setup
**Task tool prompt**:
```
Download e setup Whisper Large V3 con FasterWhisper ottimizzato per RTX 5080:

FILES:
- src/core/stt_engine/model_setup.py (download function)
- src/core/stt_engine/whisper_rtx.py (engine class con TensorRT)

COMANDI:
pip install faster-whisper torch torchaudio
python -m src.core.stt_engine.model_setup

DELIVERABLE: Model downloaded, WhisperRTXEngine class implementata
COMMIT: "[ML-SUB-1] Setup Whisper Large V3"
```

### Sub-Agent 2: NLP Models Setup
**Task tool**:
```
Download NLP models (Mistral, Sentence-BERT, PyAnnote):

FILES:
- src/core/nlp_insights/keyword_extractor.py (KeyBERT)
- src/core/nlp_insights/speaker_diarization.py (PyAnnote)

COMANDI:
pip install transformers sentence-transformers keybert pyannote-audio

DELIVERABLE: 2 classes implementate con models loaded
COMMIT: "[ML-SUB-2] Setup NLP models"
```

### Sub-Agent 3: Summary Model Setup
**Task tool**:
```
Download Llama-3.2-8B per summarization:

FILES:
- src/core/summary_generator/llama_summarizer.py

COMANDI:
pip install transformers accelerate

DELIVERABLE: LlamaSummarizer class con model loaded
COMMIT: "[ML-SUB-3] Setup Llama summary model"
```

---

## ⏸️ SYNC POINT 1
Verifica 3 models downloaded e 3 commit presenti.

---

## 🚀 ONDATA 2: IMPLEMENTATION

### Sub-Agent 4: STT gRPC + Redis
**Task tool**:
```
Implementa gRPC server per STT e Redis consumer:

FILES:
- src/core/stt_engine/grpc_server.py (protobuf implementation)
- src/core/stt_engine/redis_consumer.py (consume audio chunks)

STEPS:
1. Generate gRPC code: python -m grpc_tools.protoc ...
2. Implement STTEngineService class
3. Implement RedisAudioConsumer class
4. Integration test

DELIVERABLE: gRPC server funzionante su porta 50051
COMMIT: "[ML-SUB-4] Implement STT gRPC + Redis"
```

### Sub-Agent 5: NLP + Summary Integration
**Task tool**:
```
Completa NLP service e Summary service:

FILES:
- src/core/nlp_insights/nlp_service.py (orchestrator NLP)
- src/core/summary_generator/summary_service.py (orchestrator summary)

STEPS:
1. Integra keyword extractor + diarization
2. Integra Llama summarizer
3. Redis producer per insights
4. Tests

DELIVERABLE: 2 services operativi
COMMIT: "[ML-SUB-5] Integrate NLP + Summary services"
```

---

## ⏸️ SYNC POINT 2
Verifica 5 commit, tutti i services implementati, tests passano.

---

## ✅ VALIDAZIONE
```bash
git log --oneline | grep "ML-SUB"  # 5 commit
pytest tests/unit/ tests/integration/ -v
pytest --cov=src/core --cov-report=html
```

---

## 📊 DELIVERABLES
**Files**: 10+ (stt_engine/, nlp_insights/, summary_generator/)
**Tests**: 8+ test files
**Models**: 3 downloaded (~15GB totali)
**Coverage**: >95%

---

**FINE ML TEAM**
