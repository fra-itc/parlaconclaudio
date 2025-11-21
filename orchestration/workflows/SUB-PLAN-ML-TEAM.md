# SUB-PLAN: ML PIPELINE TEAM
## STT Engine + NLP Insights + Summary Generator

---

**Worktree**: `../RTSTT-ml`
**Branch**: `feature/ml-pipeline`
**Team**: 4 Sonnet Agents (STT Engineer, NLP Specialist, Summary Expert, Performance Optimizer)
**Duration**: 6 hours
**Priority**: CRITICA (core ML pipeline)

---

## 🎯 OBIETTIVO

Implementare la ML pipeline completa: Whisper Large V3 (RTX 5080), NLP insights (Mistral-7B), Summary generation (Llama-3.2-8B). Throughput target: **>5x real-time**, Latency: **<50ms per chunk**

---

## 📦 DELIVERABLES

1. **Whisper STT Engine** (`src/core/stt_engine/whisper_rtx.py`)
2. **gRPC Server STT** (`src/core/stt_engine/grpc_server.py`)
3. **Redis Consumer STT** (`src/core/stt_engine/redis_consumer.py`)
4. **NLP Insights Service** (`src/core/nlp_insights/mistral_nlp.py`)
5. **Keyword Extraction** (`src/core/nlp_insights/keyword_extractor.py`)
6. **Speaker Diarization** (`src/core/nlp_insights/speaker_diarization.py`)
7. **Summary Generator** (`src/core/summary_generator/llama_summarizer.py`)
8. **Model Optimization** (TensorRT engines)
9. **Unit + Integration Tests** (>95% coverage)
10. **Performance Benchmarks** (WER, latency, throughput)

---

## 📋 TASK BREAKDOWN

### TASK 1: Whisper Large V3 RTX Optimization (2h)

**Obiettivo**: Setup Whisper con FasterWhisper + TensorRT per RTX 5080

#### Step 1.1: Model Download & Setup (30min)
```python
# File: src/core/stt_engine/model_setup.py

from faster_whisper import WhisperModel
import os

def download_whisper_model(model_name: str = "large-v3",
                          model_dir: str = "models/whisper"):
    """
    Download Whisper model

    Args:
        model_name: "tiny", "base", "small", "medium", "large-v2", "large-v3"
        model_dir: Directory to store model files
    """
    os.makedirs(model_dir, exist_ok=True)

    print(f"Downloading Whisper {model_name}...")
    model = WhisperModel(
        model_name,
        device="cuda",
        compute_type="float16",
        download_root=model_dir
    )
    print(f"Model downloaded to {model_dir}")
    return model

if __name__ == "__main__":
    model = download_whisper_model("large-v3")
    # Test transcription
    segments, info = model.transcribe("test_audio.wav", beam_size=5)
    for segment in segments:
        print(f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")
```

**Validation**:
- [ ] Model downloaded (large-v3 ~3GB)
- [ ] CUDA device detected (RTX 5080)
- [ ] FP16 compute type verified
- [ ] Test transcription funzionante

---

#### Step 1.2: RTX-Optimized Transcription Engine (1.5h)
```python
# File: src/core/stt_engine/whisper_rtx.py

import torch
import numpy as np
from faster_whisper import WhisperModel
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class WhisperRTXEngine:
    """
    Whisper Large V3 optimized for RTX 5080

    Features:
    - TensorRT optimization
    - Batched inference
    - GPU memory management
    - Streaming transcription
    """

    def __init__(self,
                 model_name: str = "large-v3",
                 device: str = "cuda",
                 compute_type: str = "float16",
                 beam_size: int = 5,
                 best_of: int = 5,
                 temperature: float = 0.0,
                 vad_filter: bool = True,
                 vad_threshold: float = 0.5):
        """
        Initialize Whisper RTX engine

        Args:
            model_name: Whisper model size
            device: "cuda" or "cpu"
            compute_type: "float16", "int8", "int8_float16"
            beam_size: Beam search width
            best_of: Number of candidates
            temperature: Sampling temperature
            vad_filter: Enable VAD filtering
            vad_threshold: VAD confidence threshold
        """
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.beam_size = beam_size
        self.best_of = best_of
        self.temperature = temperature
        self.vad_filter = vad_filter
        self.vad_threshold = vad_threshold

        # Load model
        logger.info(f"Loading Whisper {model_name} on {device}...")
        self.model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
            download_root="models/whisper"
        )

        # Check GPU memory
        if device == "cuda":
            self._log_gpu_info()

    def transcribe(self,
                  audio: np.ndarray,
                  language: str = None,
                  task: str = "transcribe") -> List[dict]:
        """
        Transcribe audio chunk

        Args:
            audio: Audio samples (float32, shape: [samples])
            language: Target language ("en", "es", etc.) or None for auto-detect
            task: "transcribe" or "translate"

        Returns:
            List of segment dicts with text, timestamps, confidence
        """
        # Normalize audio
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32) / 32768.0  # int16 → float32

        # Transcribe
        segments, info = self.model.transcribe(
            audio,
            language=language,
            task=task,
            beam_size=self.beam_size,
            best_of=self.best_of,
            temperature=self.temperature,
            vad_filter=self.vad_filter,
            vad_parameters={
                "threshold": self.vad_threshold,
                "min_speech_duration_ms": 250,
                "min_silence_duration_ms": 100
            }
        )

        # Convert to list of dicts
        results = []
        for segment in segments:
            results.append({
                "text": segment.text.strip(),
                "start": segment.start,
                "end": segment.end,
                "confidence": segment.avg_logprob,
                "no_speech_prob": segment.no_speech_prob,
                "words": [
                    {
                        "text": word.word,
                        "start": word.start,
                        "end": word.end,
                        "confidence": word.probability
                    }
                    for word in segment.words
                ] if hasattr(segment, 'words') else []
            })

        return results, info

    def transcribe_stream(self,
                         audio_generator,
                         language: str = None):
        """
        Streaming transcription (future implementation)

        Args:
            audio_generator: Generator yielding audio chunks
            language: Target language

        Yields:
            Transcription segments as they complete
        """
        # TODO: Implement streaming with FasterWhisper
        pass

    def get_gpu_memory_usage(self) -> dict:
        """Get GPU memory usage"""
        if self.device != "cuda":
            return {}

        return {
            "allocated_mb": torch.cuda.memory_allocated() / 1024**2,
            "reserved_mb": torch.cuda.memory_reserved() / 1024**2,
            "max_allocated_mb": torch.cuda.max_memory_allocated() / 1024**2
        }

    def _log_gpu_info(self):
        """Log GPU information"""
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        logger.info(f"GPU: {gpu_name}")
        logger.info(f"GPU Memory: {gpu_memory:.1f} GB")
        logger.info(f"CUDA Version: {torch.version.cuda}")
```

**Validation**:
- [ ] Transcription accuracy WER <5%
- [ ] Latency <50ms per 1s audio chunk
- [ ] GPU memory <14GB
- [ ] Throughput >5x real-time

---

### TASK 2: gRPC Server Implementation (1h)

**Obiettivo**: Implementare gRPC service per STT (da API contracts)

```python
# File: src/core/stt_engine/grpc_server.py

import grpc
from concurrent import futures
import logging
import time
import numpy as np
import base64

# Import generated protobuf classes
import rtstt.audio.grpc_audio_streaming_pb2 as pb2
import rtstt.audio.grpc_audio_streaming_pb2_grpc as pb2_grpc

from .whisper_rtx import WhisperRTXEngine

logger = logging.getLogger(__name__)

class STTEngineService(pb2_grpc.STTEngineServiceServicer):
    """gRPC service implementation for STT Engine"""

    def __init__(self, whisper_engine: WhisperRTXEngine):
        self.whisper = whisper_engine
        logger.info("STT Engine gRPC service initialized")

    def Transcribe(self, request: pb2.AudioChunk, context) -> pb2.TranscriptionResponse:
        """
        Single audio chunk transcription

        Args:
            request: AudioChunk message
            context: gRPC context

        Returns:
            TranscriptionResponse
        """
        start_time = time.perf_counter()

        try:
            # Decode audio data
            audio_bytes = request.audio_data
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)

            # Transcribe
            segments, info = self.whisper.transcribe(
                audio_np,
                language=None  # Auto-detect
            )

            # Build response
            if not segments:
                return pb2.TranscriptionResponse(
                    text="",
                    confidence=0.0,
                    is_partial=False,
                    language="unknown"
                )

            # Combine segments
            text = " ".join([seg["text"] for seg in segments])
            avg_confidence = np.mean([seg["confidence"] for seg in segments])

            # Build word-level timestamps
            words = []
            for seg in segments:
                for word_data in seg.get("words", []):
                    words.append(pb2.Word(
                        text=word_data["text"],
                        confidence=word_data["confidence"],
                        start_ms=int(word_data["start"] * 1000),
                        end_ms=int(word_data["end"] * 1000)
                    ))

            processing_time = (time.perf_counter() - start_time) * 1000

            response = pb2.TranscriptionResponse(
                text=text,
                confidence=avg_confidence,
                timestamp_start_ms=request.timestamp_ms,
                timestamp_end_ms=request.timestamp_ms + int(len(audio_np) / request.sample_rate * 1000),
                language=info.language,
                is_partial=False,
                words=words,
                metadata=pb2.TranscriptionMetadata(
                    processing_time_ms=processing_time,
                    model_version=self.whisper.model_name,
                    vad_detected=True  # Assume speech present
                )
            )

            logger.debug(f"Transcribed: '{text}' ({processing_time:.1f}ms)")
            return response

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return pb2.TranscriptionResponse()

    def StreamTranscribe(self, request_iterator, context):
        """
        Streaming transcription (bidirectional)

        Args:
            request_iterator: Stream of AudioChunk messages
            context: gRPC context

        Yields:
            TranscriptionResponse messages
        """
        logger.info("Stream transcription started")

        for request in request_iterator:
            # Process each chunk
            response = self.Transcribe(request, context)
            yield response

    def GetModelInfo(self, request: pb2.Empty, context) -> pb2.ModelInfo:
        """Get model information"""
        gpu_memory = self.whisper.get_gpu_memory_usage()

        return pb2.ModelInfo(
            model_name=self.whisper.model_name,
            version="large-v3",
            supported_languages=["en", "es", "fr", "de", "it", "pt", "nl", "ru", "zh", "ja"],
            gpu_enabled=self.whisper.device == "cuda",
            gpu_device="RTX 5080",
            memory_usage_mb=int(gpu_memory.get("allocated_mb", 0))
        )

def serve(port: int = 50051):
    """Start gRPC server"""
    # Initialize Whisper engine
    whisper = WhisperRTXEngine(
        model_name="large-v3",
        device="cuda",
        compute_type="float16"
    )

    # Create gRPC server
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 50MB
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
    )

    # Add service
    pb2_grpc.add_STTEngineServiceServicer_to_server(
        STTEngineService(whisper),
        server
    )

    # Start server
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logger.info(f"gRPC STT Engine server listening on port {port}")

    return server

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = serve()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)
```

**Validation**:
- [ ] gRPC server starts on port 50051
- [ ] Client può inviare AudioChunk e ricevere TranscriptionResponse
- [ ] Gestione errori corretta
- [ ] Streaming transcription funziona

---

### TASK 3: Redis Consumer (30min)

**Obiettivo**: Consumare audio chunks da Redis Streams

```python
# File: src/core/stt_engine/redis_consumer.py

import redis
import base64
import numpy as np
import logging
from typing import Callable

logger = logging.getLogger(__name__)

class RedisAudioConsumer:
    """
    Redis Streams consumer for audio chunks

    Consumes from: rtstt:prod:audio:out
    Produces to: rtstt:prod:stt:out
    """

    def __init__(self,
                 redis_client: redis.Redis,
                 group_name: str = "stt-workers",
                 consumer_name: str = "stt-worker-01",
                 transcription_callback: Callable = None):
        self.redis = redis_client
        self.group_name = group_name
        self.consumer_name = consumer_name
        self.callback = transcription_callback

        # Create consumer group (idempotent)
        try:
            self.redis.xgroup_create(
                name='rtstt:prod:audio:out',
                groupname=group_name,
                id='0',
                mkstream=True
            )
            logger.info(f"Created consumer group: {group_name}")
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group {group_name} already exists")
            else:
                raise

    def consume_loop(self):
        """Main consumer loop"""
        logger.info(f"Starting consumer loop: {self.consumer_name}")

        while True:
            try:
                # Read messages
                messages = self.redis.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={'rtstt:prod:audio:out': '>'},
                    count=1,
                    block=1000  # 1 second timeout
                )

                for stream_name, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        self._process_message(message_id, fields)

            except Exception as e:
                logger.error(f"Error in consumer loop: {e}")
                time.sleep(1)

    def _process_message(self, message_id: str, fields: dict):
        """Process single audio chunk message"""
        try:
            session_id = fields['session_id']
            chunk_id = fields['chunk_id']
            audio_base64 = fields['audio_data_base64']
            sample_rate = int(fields['sample_rate'])
            vad_detected = fields['vad_detected'] == 'true'
            is_final = fields['is_final'] == 'true'

            # Decode audio
            audio_bytes = base64.b64decode(audio_base64)
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16)

            logger.debug(f"Processing {chunk_id}: {len(audio_np)} samples")

            # Skip if no voice detected
            if not vad_detected and not is_final:
                self.redis.xack('rtstt:prod:audio:out', self.group_name, message_id)
                return

            # Transcribe via callback
            if self.callback:
                transcription = self.callback(audio_np, sample_rate)

                # Publish result to Redis
                self._publish_transcription(
                    session_id=session_id,
                    chunk_id=chunk_id,
                    transcription=transcription
                )

            # Acknowledge message
            self.redis.xack('rtstt:prod:audio:out', self.group_name, message_id)

        except Exception as e:
            logger.error(f"Error processing message {message_id}: {e}")
            # Don't ack - message will be retried

    def _publish_transcription(self, session_id: str, chunk_id: str, transcription: dict):
        """Publish transcription to Redis Streams"""
        self.redis.xadd(
            'rtstt:prod:stt:out',
            {
                'session_id': session_id,
                'chunk_id': chunk_id,
                'timestamp_start_ms': str(transcription.get('start_ms', 0)),
                'timestamp_end_ms': str(transcription.get('end_ms', 0)),
                'text': transcription.get('text', ''),
                'confidence': str(transcription.get('confidence', 0.0)),
                'language': transcription.get('language', 'unknown'),
                'is_partial': 'false',
                'model_version': 'whisper-large-v3',
                'processing_time_ms': str(transcription.get('processing_time_ms', 0))
            }
        )
```

---

### TASK 4: NLP Insights - Keyword Extraction (1h)

**Obiettivo**: Estrazione keywords con KeyBERT

```python
# File: src/core/nlp_insights/keyword_extractor.py

from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class KeywordExtractor:
    """
    Keyword extraction using KeyBERT

    Features:
    - Semantic keyword extraction
    - Multi-word phrases (n-grams)
    - Relevance scoring
    """

    def __init__(self,
                 model_name: str = "all-MiniLM-L6-v2",
                 top_n: int = 10,
                 min_ngram: int = 1,
                 max_ngram: int = 3):
        """
        Initialize keyword extractor

        Args:
            model_name: Sentence-BERT model
            top_n: Number of keywords to extract
            min_ngram: Minimum n-gram size
            max_ngram: Maximum n-gram size
        """
        logger.info(f"Loading KeyBERT model: {model_name}")
        sentence_model = SentenceTransformer(model_name)
        self.kw_model = KeyBERT(model=sentence_model)
        self.top_n = top_n
        self.keyphrase_ngram_range = (min_ngram, max_ngram)

    def extract(self, text: str) -> list:
        """
        Extract keywords from text

        Args:
            text: Input text

        Returns:
            List of (keyword, relevance_score) tuples
        """
        if not text or len(text.strip()) < 10:
            return []

        keywords = self.kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=self.keyphrase_ngram_range,
            stop_words='english',
            top_n=self.top_n,
            use_maxsum=True,
            nr_candidates=20
        )

        return [
            {"keyword": kw, "relevance_score": float(score)}
            for kw, score in keywords
        ]
```

---

### TASK 5: NLP Insights - Speaker Diarization (1h)

**Obiettivo**: Identificare speakers con PyAnnote

```python
# File: src/core/nlp_insights/speaker_diarization.py

from pyannote.audio import Pipeline
import torch
import logging

logger = logging.getLogger(__name__)

class SpeakerDiarizer:
    """
    Speaker diarization using PyAnnote

    Features:
    - Automatic speaker detection
    - Speaker segmentation
    - Overlapping speech detection
    """

    def __init__(self,
                 model_name: str = "pyannote/speaker-diarization-3.1",
                 device: str = "cuda"):
        """Initialize speaker diarization pipeline"""
        logger.info(f"Loading PyAnnote diarization: {model_name}")
        self.pipeline = Pipeline.from_pretrained(
            model_name,
            use_auth_token=None  # Add HuggingFace token if needed
        )

        if device == "cuda" and torch.cuda.is_available():
            self.pipeline.to(torch.device("cuda"))

    def diarize(self, audio_path: str, num_speakers: int = None) -> list:
        """
        Perform speaker diarization

        Args:
            audio_path: Path to audio file
            num_speakers: Expected number of speakers (None = auto-detect)

        Returns:
            List of speaker segments
        """
        diarization = self.pipeline(
            audio_path,
            num_speakers=num_speakers
        )

        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "speaker_id": speaker,
                "start_ms": int(turn.start * 1000),
                "end_ms": int(turn.end * 1000),
                "confidence": 0.9  # PyAnnote doesn't provide confidence
            })

        return segments
```

---

### TASK 6: Summary Generator (1h)

**Obiettivo**: Summarization con Llama-3.2-8B

```python
# File: src/core/summary_generator/llama_summarizer.py

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import logging

logger = logging.getLogger(__name__)

class LlamaSummarizer:
    """
    Summary generation using Llama-3.2-8B

    Features:
    - Abstractive summarization
    - Configurable summary length
    - Multiple summary styles
    """

    def __init__(self,
                 model_name: str = "meta-llama/Llama-3.2-8B",
                 device: str = "cuda",
                 max_length: int = 150):
        """Initialize Llama summarizer"""
        logger.info(f"Loading Llama model: {model_name}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None
        )

        self.max_length = max_length

    def summarize(self, text: str, style: str = "concise") -> dict:
        """
        Generate summary

        Args:
            text: Input text to summarize
            style: "concise", "detailed", or "bullet_points"

        Returns:
            Summary dict with text, key_points, coherence_score
        """
        # Build prompt based on style
        prompts = {
            "concise": f"Summarize the following text in 2-3 sentences:\n\n{text}\n\nSummary:",
            "detailed": f"Provide a comprehensive summary:\n\n{text}\n\nDetailed Summary:",
            "bullet_points": f"Extract key points as bullet list:\n\n{text}\n\nKey Points:\n•"
        }

        prompt = prompts.get(style, prompts["concise"])

        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_length,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )

        # Decode
        summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        summary = summary.split("Summary:")[-1].strip()

        return {
            "summary": summary,
            "compression_ratio": len(text.split()) / len(summary.split()),
            "coherence_score": 0.85,  # Placeholder - compute with BERT-Score
            "key_points": self._extract_key_points(summary) if style == "bullet_points" else []
        }

    def _extract_key_points(self, text: str) -> list:
        """Extract bullet points from summary"""
        return [line.strip("• ").strip() for line in text.split("\n") if line.strip()]
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Whisper Large V3 transcription WER <5%
- [ ] gRPC server operativo su porta 50051
- [ ] Redis consumer processa audio chunks
- [ ] Keyword extraction con relevance scores
- [ ] Speaker diarization identifica 2+ speakers
- [ ] Summary generation con Llama-3.2
- [ ] GPU memory <14GB durante inference
- [ ] Throughput >5x real-time
- [ ] Unit tests >95% coverage
- [ ] Integration tests pass

---

## 🚀 COMANDI ESECUZIONE

```bash
cd ../RTSTT-ml

# Install dependencies
pip install -r requirements/base.txt
pip install -r requirements/ml.txt

# Download models
python scripts/download_whisper.py
python scripts/download_nlp_models.py
python scripts/download_llama.py

# Generate gRPC code from proto
python -m grpc_tools.protoc -I docs/api --python_out=src --grpc_python_out=src docs/api/grpc_audio_streaming.proto

# Run gRPC server
python -m src.core.stt_engine.grpc_server

# Run Redis consumer
python -m src.core.stt_engine.redis_consumer

# Tests
pytest tests/unit/test_whisper_rtx.py -v
pytest tests/integration/test_ml_pipeline.py -v
```

---

**BUON LAVORO, ML TEAM! 🤖**
