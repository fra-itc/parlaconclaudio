# ML Team Lead Agent - Claude Sonnet 3.5
**Role**: Machine Learning Pipeline Architect  
**HAS Level**: H3 (Equal Partnership for model selection)  
**Team Size**: 4 specialized agents  
**GPU**: NVIDIA RTX 5080 16GB  
**Sync**: 30-min internal, 2-hour with orchestrator

## 🎯 Mission
Lead the ML team to implement a real-time STT pipeline optimized for RTX 5080, with NLP insights extraction and executive summary generation. Ensure 99% accuracy validation before production handoff.

## 👥 Team Composition

```yaml
ml_team:
  agents:
    - stt_engineer:
        focus: Whisper/FasterWhisper optimization
        skills: [Model quantization, Batch processing, Streaming ASR]
    - gpu_optimizer:
        focus: CUDA optimization for RTX 5080
        skills: [TensorRT, FP16/INT8, Memory management]
    - nlp_specialist:
        focus: Real-time insights extraction
        skills: [Topic modeling, Sentiment analysis, Named entity recognition]
    - summary_architect:
        focus: Executive summary generation
        skills: [LLM fine-tuning, Prompt engineering, Structured output]
```

## 📋 Development Phases

### Phase 1: Model Selection & Benchmarking (0-45 min)
```python
class ModelBenchmarking:
    """Benchmark STT models on RTX 5080"""
    
    def __init__(self):
        self.gpu_specs = {
            'model': 'RTX_5080',
            'memory': 16384,  # MB
            'compute': 'sm_89',  # Ada Lovelace
            'tensor_cores': 4,
            'fp16_tflops': 45,
            'int8_tops': 180
        }
        
        self.models_to_test = {
            'whisper_large_v3': {
                'params': '1550M',
                'languages': ['en', 'it', 'es', 'de', 'fr'],
                'memory_fp16': 3100,  # MB
                'memory_int8': 1550   # MB
            },
            'faster_whisper_large': {
                'backend': 'CTranslate2',
                'quantization': ['fp16', 'int8'],
                'beam_size': [1, 5],
                'memory_optimized': True
            },
            'whisper_distilled': {
                'params': '390M',
                'speed_factor': 3.5,
                'quality_tradeoff': 0.02  # WER increase
            },
            'nvidia_conformer': {
                'framework': 'NeMo',
                'streaming': True,
                'chunk_size_ms': 200,
                'lookahead_ms': 1000
            }
        }
    
    def benchmark_suite(self):
        """Run comprehensive benchmarks"""
        results = {}
        
        for model_name, config in self.models_to_test.items():
            metrics = {
                'latency_ms': self.measure_latency(model_name),
                'throughput_rtf': self.measure_rtf(model_name),
                'memory_usage_mb': self.measure_memory(model_name),
                'wer_score': self.measure_accuracy(model_name),
                'gpu_utilization': self.measure_gpu_util(model_name)
            }
            
            # Score based on requirements
            metrics['composite_score'] = (
                (1 / metrics['latency_ms']) * 1000 +  # Lower is better
                metrics['throughput_rtf'] * 10 +       # Higher is better
                (1 - metrics['wer_score']) * 100 +     # Lower WER is better
                (1 - metrics['memory_usage_mb']/16384) * 50  # Memory efficiency
            )
            
            results[model_name] = metrics
        
        # Select best model
        best_model = max(results, key=lambda x: results[x]['composite_score'])
        return best_model, results
```

### Phase 2: STT Pipeline Implementation (45 min - 2.5 hours)
```python
class WhisperStreamingPipeline:
    """Optimized Whisper pipeline for RTX 5080"""
    
    def __init__(self):
        self.config = {
            'model': 'openai/whisper-large-v3',
            'device': 'cuda:0',
            'compute_type': 'float16',
            'batch_size': 4,
            'chunk_length_s': 0.5,
            'stride_length_s': 0.1,
            'language_detection': True,
            'task': 'transcribe'
        }
    
    def implementation(self):
        return '''
        import torch
        import faster_whisper
        from transformers import WhisperProcessor, WhisperForConditionalGeneration
        import tensorrt as trt
        from collections import deque
        import numpy as np
        
        class OptimizedWhisperSTT:
            def __init__(self):
                # Load model with optimization
                self.model = faster_whisper.WhisperModel(
                    "large-v3",
                    device="cuda",
                    compute_type="float16",
                    num_workers=2,
                    download_root="./models"
                )
                
                # Streaming buffer management
                self.audio_buffer = deque(maxlen=24000)  # 500ms at 48kHz
                self.context_buffer = deque(maxlen=10)  # Last 10 segments
                self.processing_queue = asyncio.Queue()
                
                # Language detection cache
                self.detected_language = None
                self.language_confidence = 0.0
                
            async def process_stream(self, audio_stream):
                """Main streaming processing loop"""
                
                async for audio_chunk in audio_stream:
                    # Add to buffer
                    self.audio_buffer.extend(audio_chunk)
                    
                    # Process when we have enough audio (500ms)
                    if len(self.audio_buffer) >= 24000:
                        await self.process_segment()
                
            async def process_segment(self):
                """Process audio segment with context"""
                
                # Get audio segment
                audio = np.array(self.audio_buffer)
                
                # Detect language if needed
                if self.detected_language is None or self.language_confidence < 0.8:
                    self.detect_language(audio)
                
                # Transcribe with context
                segments, info = self.model.transcribe(
                    audio,
                    language=self.detected_language,
                    beam_size=5,
                    best_of=5,
                    temperature=0.0,
                    vad_filter=True,
                    vad_parameters=dict(
                        threshold=0.5,
                        min_speech_duration_ms=250,
                        max_speech_duration_s=float("inf"),
                        min_silence_duration_ms=100,
                        speech_pad_ms=400
                    ),
                    initial_prompt=self.get_context_prompt()
                )
                
                # Process segments
                for segment in segments:
                    result = {
                        'text': segment.text,
                        'start': segment.start,
                        'end': segment.end,
                        'confidence': segment.avg_logprob,
                        'language': info.language,
                        'timestamp': time.time()
                    }
                    
                    # Update context
                    self.context_buffer.append(segment.text)
                    
                    # Emit result
                    await self.emit_transcription(result)
            
            def get_context_prompt(self):
                """Generate context prompt from recent segments"""
                if not self.context_buffer:
                    return None
                    
                # Use last 3 segments as context
                context = " ".join(list(self.context_buffer)[-3:])
                return f"Previous context: {context}"
            
            def detect_language(self, audio):
                """Detect spoken language"""
                # Use first 30s for language detection
                segment = audio[:min(len(audio), 48000 * 30)]
                
                segments, info = self.model.transcribe(
                    segment,
                    beam_size=1,
                    best_of=1,
                    temperature=0.0,
                    task="transcribe"
                )
                
                self.detected_language = info.language
                self.language_confidence = info.language_probability
                
                print(f"Detected language: {self.detected_language} "
                      f"(confidence: {self.language_confidence:.2f})")
        '''
    
    def gpu_optimization(self):
        """TensorRT optimization for RTX 5080"""
        return '''
        import tensorrt as trt
        import pycuda.driver as cuda
        import pycuda.autoinit
        
        class TensorRTWhisper:
            def __init__(self):
                self.trt_logger = trt.Logger(trt.Logger.WARNING)
                self.runtime = trt.Runtime(self.trt_logger)
                
            def optimize_model(self, onnx_path):
                """Convert ONNX to TensorRT engine"""
                
                builder = trt.Builder(self.trt_logger)
                network = builder.create_network(
                    1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
                )
                parser = trt.OnnxParser(network, self.trt_logger)
                
                # Parse ONNX
                with open(onnx_path, 'rb') as f:
                    parser.parse(f.read())
                
                # Configure builder
                config = builder.create_builder_config()
                
                # RTX 5080 optimization
                config.max_workspace_size = 8 << 30  # 8GB
                config.set_flag(trt.BuilderFlag.FP16)  # Enable FP16
                config.set_flag(trt.BuilderFlag.STRICT_TYPES)
                
                # Dynamic shapes for streaming
                profile = builder.create_optimization_profile()
                profile.set_shape(
                    "audio_input",
                    min=(1, 80, 3000),   # Min 1 batch, 3000 frames
                    opt=(4, 80, 24000),  # Optimal 4 batch, 24000 frames  
                    max=(8, 80, 48000)   # Max 8 batch, 48000 frames
                )
                config.add_optimization_profile(profile)
                
                # Build engine
                engine = builder.build_engine(network, config)
                
                # Serialize
                with open("whisper_trt.engine", "wb") as f:
                    f.write(engine.serialize())
                    
                return engine
            
            def allocate_buffers(self, engine):
                """Allocate GPU memory for inference"""
                inputs, outputs, bindings = [], [], []
                
                for binding in engine:
                    size = trt.volume(engine.get_binding_shape(binding))
                    dtype = trt.nptype(engine.get_binding_dtype(binding))
                    
                    # Allocate host and device buffers
                    host_mem = cuda.pagelocked_empty(size, dtype)
                    device_mem = cuda.mem_alloc(host_mem.nbytes)
                    
                    bindings.append(int(device_mem))
                    
                    if engine.binding_is_input(binding):
                        inputs.append({'host': host_mem, 'device': device_mem})
                    else:
                        outputs.append({'host': host_mem, 'device': device_mem})
                        
                return inputs, outputs, bindings
        '''
```

### Phase 3: NLP Insights Engine (2.5-3.5 hours)
```python
class RealTimeNLPInsights:
    """Extract insights from streaming transcription"""
    
    def __init__(self):
        self.models = {
            'topic_extraction': 'sentence-transformers/all-MiniLM-L6-v2',
            'sentiment': 'cardiffnlp/twitter-roberta-base-sentiment',
            'ner': 'dslim/bert-base-NER',
            'keywords': 'KeyBERT',
            'speaker_diarization': 'pyannote/speaker-diarization'
        }
        
        self.state = {
            'topics': deque(maxlen=100),
            'sentiment_history': deque(maxlen=50),
            'entities': defaultdict(list),
            'action_items': [],
            'speaker_segments': []
        }
    
    def implementation(self):
        return '''
        import torch
        from transformers import pipeline
        from sentence_transformers import SentenceTransformer
        from keybert import KeyBERT
        from sklearn.cluster import DBSCAN
        import spacy
        from collections import defaultdict, deque
        import re
        
        class StreamingNLPProcessor:
            def __init__(self):
                # Load models
                self.sentence_encoder = SentenceTransformer(
                    'all-MiniLM-L6-v2'
                ).cuda()
                
                self.sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment",
                    device=0
                )
                
                self.ner_model = pipeline(
                    "ner",
                    model="dslim/bert-base-NER",
                    aggregation_strategy="simple",
                    device=0
                )
                
                self.keyword_model = KeyBERT(
                    model=self.sentence_encoder
                )
                
                # Conversational state
                self.conversation_buffer = deque(maxlen=1000)
                self.topic_embeddings = []
                self.current_topics = set()
                
            async def process_transcription(self, text_segment):
                """Process incoming transcription segment"""
                
                # Add to conversation buffer
                self.conversation_buffer.append({
                    'text': text_segment['text'],
                    'timestamp': text_segment['timestamp'],
                    'speaker': text_segment.get('speaker', 'unknown')
                })
                
                # Run all analyses in parallel
                results = await asyncio.gather(
                    self.extract_topics(text_segment['text']),
                    self.analyze_sentiment(text_segment['text']),
                    self.extract_entities(text_segment['text']),
                    self.detect_action_items(text_segment['text']),
                    return_exceptions=True
                )
                
                return {
                    'topics': results[0],
                    'sentiment': results[1],
                    'entities': results[2],
                    'action_items': results[3],
                    'timestamp': text_segment['timestamp']
                }
            
            async def extract_topics(self, text, window_size=5):
                """Dynamic topic extraction"""
                
                # Get recent context
                recent_texts = [
                    seg['text'] for seg in 
                    list(self.conversation_buffer)[-window_size:]
                ]
                context = " ".join(recent_texts)
                
                # Extract keywords
                keywords = self.keyword_model.extract_keywords(
                    context,
                    keyphrase_ngram_range=(1, 3),
                    stop_words='english',
                    top_n=5
                )
                
                # Get embeddings for clustering
                if len(context.split()) > 10:
                    embedding = self.sentence_encoder.encode(context)
                    self.topic_embeddings.append(embedding)
                    
                    # Cluster topics if we have enough data
                    if len(self.topic_embeddings) > 10:
                        clusters = DBSCAN(
                            eps=0.3,
                            min_samples=2,
                            metric='cosine'
                        ).fit(self.topic_embeddings[-50:])
                        
                        # Update current topics
                        self.current_topics = set(keywords[0] for keywords in keywords[:3])
                
                return {
                    'keywords': keywords,
                    'main_topics': list(self.current_topics)
                }
            
            async def analyze_sentiment(self, text):
                """Real-time sentiment tracking"""
                
                if len(text.split()) < 3:
                    return None
                    
                result = self.sentiment_analyzer(text)[0]
                
                # Track sentiment trend
                self.state['sentiment_history'].append({
                    'label': result['label'],
                    'score': result['score'],
                    'timestamp': time.time()
                })
                
                # Calculate rolling average
                recent_sentiments = list(self.state['sentiment_history'])[-10:]
                avg_sentiment = np.mean([
                    s['score'] if s['label'] == 'POSITIVE' else -s['score']
                    for s in recent_sentiments
                ])
                
                return {
                    'current': result['label'],
                    'confidence': result['score'],
                    'trend': 'positive' if avg_sentiment > 0 else 'negative',
                    'intensity': abs(avg_sentiment)
                }
            
            async def extract_entities(self, text):
                """Named entity recognition"""
                
                entities = self.ner_model(text)
                
                # Group by entity type
                grouped = defaultdict(list)
                for entity in entities:
                    grouped[entity['entity_group']].append({
                        'text': entity['word'],
                        'confidence': entity['score']
                    })
                
                # Update global entity state
                for entity_type, items in grouped.items():
                    for item in items:
                        self.state['entities'][entity_type].append(item)
                
                return grouped
            
            async def detect_action_items(self, text):
                """Detect potential action items"""
                
                action_patterns = [
                    r'(I|we|you|they) will \w+',
                    r'(I|we|you|they) (need|have) to \w+',
                    r'(let\'s|let us) \w+',
                    r'(please|kindly) \w+',
                    r'by (monday|tuesday|wednesday|thursday|friday|tomorrow|next week)',
                    r'deadline is',
                    r'due (date|by)',
                    r'action item:',
                    r'todo:',
                    r'task:'
                ]
                
                detected_actions = []
                for pattern in action_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        detected_actions.append({
                            'text': text,
                            'pattern': pattern,
                            'confidence': 0.7
                        })
                
                # Use LLM for better detection (if available)
                if detected_actions or 'will' in text.lower():
                    # This would call a small LLM for confirmation
                    self.state['action_items'].append({
                        'text': text,
                        'timestamp': time.time(),
                        'confirmed': False
                    })
                
                return detected_actions
        '''
```

### Phase 4: Executive Summary Generator (3.5-4 hours)
```python
class ExecutiveSummaryEngine:
    """Generate structured summaries using local LLM"""
    
    def __init__(self):
        self.config = {
            'model': 'meta-llama/Llama-3.2-8B-Instruct',
            'quantization': '4bit',
            'max_context': 32768,
            'device': 'cuda:0',
            'memory_reserved': 8192  # MB for LLM on RTX 5080
        }
    
    def implementation(self):
        return '''
        import torch
        from transformers import (
            AutoModelForCausalLM, 
            AutoTokenizer,
            BitsAndBytesConfig
        )
        from langchain.prompts import PromptTemplate
        from langchain.chains.summarize import load_summarize_chain
        from dataclasses import dataclass
        import json
        
        @dataclass
        class ExecutiveSummary:
            meeting_context: str
            key_topics: list
            decisions_made: list
            action_items: list
            participants: list
            sentiment_summary: str
            next_steps: list
            
        class LlamaSummaryGenerator:
            def __init__(self):
                # 4-bit quantization config for RTX 5080
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True
                )
                
                # Load model
                self.model = AutoModelForCausalLM.from_pretrained(
                    "meta-llama/Llama-3.2-8B-Instruct",
                    quantization_config=bnb_config,
                    device_map="auto",
                    trust_remote_code=True
                )
                
                self.tokenizer = AutoTokenizer.from_pretrained(
                    "meta-llama/Llama-3.2-8B-Instruct"
                )
                
                # Summary prompt template
                self.summary_prompt = PromptTemplate(
                    input_variables=["transcript", "insights"],
                    template="""
                    You are an expert executive assistant creating a meeting summary.
                    
                    TRANSCRIPT:
                    {transcript}
                    
                    EXTRACTED INSIGHTS:
                    {insights}
                    
                    Create a structured executive summary with:
                    1. Meeting Context (2-3 sentences about purpose and participants)
                    2. Key Topics Discussed (bullet points)
                    3. Decisions Made (clear, actionable statements)
                    4. Action Items (who, what, when format)
                    5. Sentiment Summary (overall tone and dynamics)
                    6. Next Steps and Follow-ups
                    
                    Format as JSON with these exact keys:
                    - meeting_context
                    - key_topics (array)
                    - decisions_made (array)
                    - action_items (array of objects with owner, task, deadline)
                    - sentiment_summary
                    - next_steps (array)
                    
                    Be concise, professional, and focus on actionable information.
                    """
                )
                
            async def generate_summary(self, transcript, nlp_insights):
                """Generate executive summary from full transcript"""
                
                # Prepare insights summary
                insights_text = self.format_insights(nlp_insights)
                
                # Chunk transcript if too long
                if len(self.tokenizer.encode(transcript)) > 28000:
                    transcript = self.chunk_and_summarize(transcript)
                
                # Generate summary
                prompt = self.summary_prompt.format(
                    transcript=transcript,
                    insights=insights_text
                )
                
                inputs = self.tokenizer(
                    prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=30000
                ).to("cuda")
                
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=2048,
                        temperature=0.7,
                        do_sample=True,
                        top_p=0.95,
                        repetition_penalty=1.1
                    )
                
                summary_text = self.tokenizer.decode(
                    outputs[0][inputs['input_ids'].shape[1]:],
                    skip_special_tokens=True
                )
                
                # Parse JSON response
                try:
                    summary_json = json.loads(
                        self.extract_json(summary_text)
                    )
                    return ExecutiveSummary(**summary_json)
                except:
                    # Fallback to text parsing
                    return self.parse_text_summary(summary_text)
            
            def chunk_and_summarize(self, transcript, chunk_size=25000):
                """Handle long transcripts with recursive summarization"""
                
                tokens = self.tokenizer.encode(transcript)
                chunks = []
                
                for i in range(0, len(tokens), chunk_size):
                    chunk_tokens = tokens[i:i + chunk_size]
                    chunk_text = self.tokenizer.decode(
                        chunk_tokens,
                        skip_special_tokens=True
                    )
                    
                    # Summarize each chunk
                    chunk_summary = self.summarize_chunk(chunk_text)
                    chunks.append(chunk_summary)
                
                # Combine chunk summaries
                combined = "\\n\\n".join(chunks)
                return combined
            
            def format_insights(self, nlp_insights):
                """Format NLP insights for summary context"""
                
                return f"""
                Topics: {', '.join(nlp_insights.get('main_topics', []))}
                Key Entities: {json.dumps(nlp_insights.get('entities', {}))}
                Detected Action Items: {json.dumps(nlp_insights.get('action_items', []))}
                Overall Sentiment: {nlp_insights.get('sentiment_trend', 'neutral')}
                Speaker Distribution: {json.dumps(nlp_insights.get('speakers', {}))}
                """
            
            def extract_json(self, text):
                """Extract JSON from model output"""
                
                # Find JSON block
                import re
                json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                matches = re.findall(json_pattern, text, re.DOTALL)
                
                if matches:
                    # Return the largest JSON block
                    return max(matches, key=len)
                    
                return text
        '''
```

## 📊 Validation Gates (99% Required)

```python
class MLPipelineValidation:
    """Comprehensive ML system validation"""
    
    def __init__(self):
        self.benchmarks = {
            'stt_accuracy': 0.95,      # WER < 5%
            'latency_p95': 100,        # ms
            'throughput_rtf': 5.0,     # Real-time factor
            'gpu_memory': 14000,       # MB (leaving headroom)
            'nlp_f1_score': 0.85,      # Entity extraction
            'summary_quality': 4.0     # Human eval score /5
        }
    
    def run_validation_suite(self):
        """Execute all validation tests"""
        
        test_results = {
            'stt_tests': self.validate_stt_pipeline(),
            'nlp_tests': self.validate_nlp_insights(),
            'summary_tests': self.validate_summary_quality(),
            'integration_tests': self.validate_end_to_end(),
            'stress_tests': self.validate_under_load()
        }
        
        # Calculate overall score
        total_tests = sum(len(v) for v in test_results.values())
        passed_tests = sum(
            sum(1 for t in v.values() if t['passed'])
            for v in test_results.values()
        )
        
        success_rate = passed_tests / total_tests
        
        if success_rate < 0.99:
            self.escalate_to_human(test_results)
            return False
            
        return True
    
    def validate_stt_pipeline(self):
        """Test STT accuracy and performance"""
        
        test_cases = {
            'english_clean': 'test_audio/en_clean.wav',
            'italian_accent': 'test_audio/it_accent.wav',
            'noisy_environment': 'test_audio/noisy.wav',
            'multiple_speakers': 'test_audio/multi_speaker.wav',
            'technical_jargon': 'test_audio/technical.wav'
        }
        
        results = {}
        for test_name, audio_file in test_cases.items():
            wer, latency = self.test_stt_accuracy(audio_file)
            results[test_name] = {
                'wer': wer,
                'latency': latency,
                'passed': wer < 0.05 and latency < 100
            }
            
        return results
    
    def validate_under_load(self):
        """Stress test with concurrent streams"""
        
        # Simulate 5 concurrent calls
        concurrent_streams = 5
        duration_minutes = 5
        
        metrics = self.run_stress_test(
            concurrent_streams,
            duration_minutes
        )
        
        return {
            'gpu_memory_stable': metrics['memory_peak'] < 14000,
            'no_oom_errors': metrics['oom_count'] == 0,
            'latency_maintained': metrics['p99_latency'] < 150,
            'throughput_maintained': metrics['avg_rtf'] > 3.0
        }
```

## 🔄 Integration Protocol with Audio Team

```yaml
dependencies_from_audio:
  audio_stream:
    format: PCM_16_48000_MONO
    chunk_size_ms: 10
    buffer_size_ms: 500
    
  vad_events:
    speech_start: callback
    speech_end: callback
    speech_segment: numpy.ndarray
    
handoff_to_frontend:
  websocket_api:
    endpoints:
      - /ws/transcription  # Real-time text
      - /ws/insights      # Live insights
      - /api/summary      # Final summary
    
  data_format:
    transcription:
      text: string
      timestamp: float
      confidence: float
      is_final: boolean
    
    insights:
      topics: array
      sentiment: object
      entities: object
      action_items: array
```

## 📈 Success Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| WER (Word Error Rate) | <5% | - | ⏳ |
| Latency P95 | <100ms | - | ⏳ |
| Throughput (RTF) | >5x | - | ⏳ |
| GPU Memory Usage | <14GB | - | ⏳ |
| NLP F1 Score | >0.85 | - | ⏳ |
| Summary Quality | >4/5 | - | ⏳ |
| Concurrent Streams | ≥5 | - | ⏳ |
| Test Coverage | >95% | - | ⏳ |

## 🚨 Escalation Matrix

```python
ML_ESCALATION = {
    'MODEL_LOAD_FAILURE': 'H4_IMMEDIATE',
    'GPU_OOM': 'H4_IMMEDIATE', 
    'ACCURACY_BELOW_THRESHOLD': 'H3_REVIEW',
    'LATENCY_SPIKE': 'H3_REVIEW',
    'CUDA_ERROR': 'H4_IMMEDIATE',
    'LANGUAGE_NOT_SUPPORTED': 'H2_MONITOR'
}
```

Remember: The RTX 5080 is our competitive advantage. Optimize aggressively for GPU utilization while maintaining quality. The 99% validation gate is non-negotiable.
