Analizzo il documento ORCHIDEA e il prompt tecnico per creare una struttura di progetto POC per speech-to-text real-time con architettura multi-agente distribuita.

## ?? Struttura Repository

```
realtime-stt-orchestrator/
+-- .github/
¦   +-- workflows/
¦   ¦   +-- ci-pipeline.yml
¦   ¦   +-- agent-orchestration.yml
¦   +-- CODEOWNERS
¦
+-- docs/
¦   +-- ARCHITECTURE.md
¦   +-- AGENT_SPECIFICATION.md
¦   +-- ORCHIDEA_INTEGRATION.md
¦   +-- api/
¦
+-- specs/
¦   +-- technical/
¦   ¦   +-- audio-capture.spec.md
¦   ¦   +-- stt-pipeline.spec.md
¦   ¦   +-- nlp-insights.spec.md
¦   ¦   +-- summary-engine.spec.md
¦   +-- agents/
¦   ¦   +-- orchestrator.agent.md
¦   ¦   +-- audio-team.agents.md
¦   ¦   +-- ml-team.agents.md
¦   ¦   +-- frontend-team.agents.md
¦   +-- workflows/
¦       +-- development-cycles.md
¦
+-- src/
¦   +-- core/
¦   ¦   +-- audio_capture/
¦   ¦   +-- stt_engine/
¦   ¦   +-- nlp_insights/
¦   ¦   +-- summary_generator/
¦   +-- agents/
¦   ¦   +-- orchestrator/
¦   ¦   +-- teams/
¦   ¦   +-- metrics/
¦   +-- ui/
¦   ¦   +-- desktop/
¦   ¦   +-- web/
¦   +-- shared/
¦       +-- protocols/
¦
+-- tests/
¦   +-- unit/
¦   +-- integration/
¦   +-- e2e/
¦
+-- orchestration/
¦   +-- agent_configs/
¦   +-- workflows/
¦   +-- metrics/
¦
+-- infrastructure/
¦   +-- docker/
¦   +-- k8s/
¦   +-- monitoring/
¦
+-- .env.example
+-- pyproject.toml
+-- requirements/
¦   +-- base.txt
¦   +-- audio.txt
¦   +-- ml.txt
¦   +-- dev.txt
+-- README.md
```

## ?? File Iniziali

### 1. `ARCHITECTURE.md`
```markdown
# Real-Time STT Orchestrator Architecture

## Overview
Sistema end-to-end per trascrizione real-time con architettura multi-agente basata su ORCHIDEA v1.3

## Core Components

### 1. Audio Capture Layer
- **Windows**: WASAPI + Virtual Audio Cable
- **macOS**: CoreAudio + BlackHole driver
- **Linux**: PulseAudio + module-loopback

### 2. STT Pipeline (RTX 5080)
- **Primary Model**: Whisper Large V3 (FP16 optimized)
- **Fallback**: FasterWhisper with CTranslate2
- **Chunking**: 30ms frames, 500ms buffer
- **VAD**: Silero VAD v4

### 3. NLP Insights Engine
- **Local LLM**: Mistral-7B-Instruct (4-bit quantized)
- **Topic Extraction**: KeyBERT + Sentence-BERT
- **Speaker Diarization**: PyAnnote Audio

### 4. Summary Generator
- **Model**: Llama-3.2-8B (RTX optimized)
- **Context Window**: 32K tokens
- **Output**: Structured JSON + Markdown

## Agent Architecture

### Orchestrator Team (Claude Opus)
- **Master Orchestrator**: Workflow coordination
- **Quality Gate Controller**: HAS level management
- **Metrics Collector**: ORCHIDEA telemetry

### Development Teams
- **Audio Squad** (Sonnet): Audio capture, processing
- **ML Squad** (Sonnet): Model optimization, inference
- **Frontend Squad** (Sonnet): UI/UX implementation
- **DB Squad** (Opus architect + Sonnet workers): Data persistence

### Support Teams
- **Testing Team** (Haiku): Unit/integration tests
- **Git Team** (Haiku): Version control, CI/CD
- **Documentation Team** (Sonnet): Spec maintenance
```

### 2. `specs/agents/orchestrator.agent.md`
```markdown
# Master Orchestrator Agent Specification

## Identity
- **Model**: Claude Opus 4.1
- **Role**: Chief Architecture Orchestrator
- **HAS Level**: H4 (Human-Led for critical decisions)

## Context
You are the master orchestrator for a distributed multi-agent development team building a real-time STT system. You coordinate parallel development cycles following ORCHIDEA v1.3 principles.

## Responsibilities
1. **Sprint Planning** (Phase 1-2 ORCHIDEA)
   - Parse technical specifications
   - Generate task DAG (Directed Acyclic Graph)
   - Assign tasks to agent teams

2. **Parallel Execution Management** (Phase 3-5)
   - Monitor agent progress via telemetry
   - Resolve inter-team dependencies
   - Trigger sync points every 2-hour cycle

3. **Quality Gates** (Phase 4)
   - Review critical outputs at HAS gates
   - Escalate H4/H5 decisions to humans
   - Maintain truth guardrails

4. **Metrics Collection** (Phase 7)
   - Workflow alignment (PUII)
   - Agent performance metrics
   - Quality scores per module

## Communication Protocol
```yaml
message_format:
  type: "task_assignment|status_update|sync_request|escalation"
  priority: 1-5
  has_level: "H1-H5"
  payload:
    task_id: uuid
    agent_team: string
    deadline: iso8601
    dependencies: [task_ids]
```

## Sync Cycles
- **Micro-cycle**: 30 minutes (intra-team)
- **Mini-cycle**: 2 hours (inter-team sync)
- **Sprint**: 2 days (full integration)
```

### 3. `specs/technical/audio-capture.spec.md`
```markdown
# Audio Capture Specification

## Requirements
- Latency: <10ms capture delay
- Sample Rate: 48kHz
- Bit Depth: 16-bit PCM
- Channels: Mono (mixed from stereo)

## Platform Implementations

### Windows
```python
# Virtual Audio Device approach
class WindowsAudioCapture:
    def __init__(self):
        self.wasapi = WasapiLoopbackCapture()
        self.virtual_cable = VirtualAudioCable()
    
    def capture_system_audio(self):
        """Intercept before apps via WASAPI loopback"""
        pass
    
    def capture_mic_audio(self):
        """Direct mic capture with echo cancellation"""
        pass
```

### macOS
```python
# CoreAudio + BlackHole
class MacAudioCapture:
    def __init__(self):
        self.blackhole = BlackHoleDriver()
        self.aggregate_device = CoreAudioAggregate()
```

### Linux
```python
# PulseAudio approach
class LinuxAudioCapture:
    def __init__(self):
        self.pulse = PulseAudioClient()
        self.loopback = ModuleLoopback()
```

## Audio Pipeline
1. **Capture** ? 2. **Buffer** (500ms) ? 3. **VAD** ? 4. **Chunk** ? 5. **Queue**
```

### 4. `orchestration/workflows/development-cycle.yaml`
```yaml
name: "Parallel Development Cycle"
version: "1.0"
based_on: "ORCHIDEA v1.3"

phases:
  - phase_1_planning:
      duration: "2 hours"
      agents:
        - orchestrator_opus: "Generate sprint plan"
        - db_architect_opus: "Design schema"
        - ml_lead_sonnet: "Select models"
      outputs:
        - task_dag.json
        - api_contracts.yaml
        - model_configs.yaml

  - phase_2_parallel_coding:
      duration: "4 hours"
      parallel_tracks:
        audio_track:
          agents: ["audio_sonnet_1", "audio_sonnet_2"]
          tasks: ["capture_module", "buffer_system"]
        
        ml_track:
          agents: ["ml_sonnet_1", "ml_sonnet_2", "ml_sonnet_3"]
          tasks: ["stt_pipeline", "nlp_engine", "gpu_optimization"]
        
        frontend_track:
          agents: ["ui_sonnet_1", "ui_sonnet_2"]
          tasks: ["electron_app", "react_dashboard"]

  - phase_3_sync_verify:
      duration: "1 hour"
      agents:
        - test_haiku_squad: "Run integration tests"
        - orchestrator_opus: "Verify interfaces"
      gates:
        - has_level: "H3"
          trigger: "interface_mismatch"

  - phase_4_integration:
      duration: "2 hours"
      agents:
        - orchestrator_opus: "Merge branches"
        - db_sonnet: "Migration scripts"
      human_review:
        - has_level: "H4"
        - focus: ["security", "performance"]

metrics:
  orchidea:
    - workflow_alignment_score
    - agent_collaboration_index
    - quality_gate_passes
    - human_intervention_count
```

### 5. `src/core/audio_capture/audio_interceptor.py`
```python
"""
Audio Capture Core Module
Implements platform-agnostic audio interception
"""
import asyncio
import numpy as np
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
from dataclasses import dataclass

@dataclass
class AudioConfig:
    sample_rate: int = 48000
    channels: int = 1
    chunk_size: int = 480  # 10ms at 48kHz
    buffer_size: int = 24000  # 500ms buffer
    device_id: Optional[str] = None

class AudioInterceptor(ABC):
    """Base class for platform-specific audio capture"""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.buffer = np.zeros(config.buffer_size, dtype=np.int16)
        self.is_capturing = False
        
    @abstractmethod
    async def start_capture(self) -> None:
        """Start audio capture from system/mic"""
        pass
    
    @abstractmethod
    async def stop_capture(self) -> None:
        """Stop audio capture"""
        pass
    
    @abstractmethod
    async def get_audio_stream(self) -> AsyncGenerator[np.ndarray, None]:
        """Yield audio chunks for processing"""
        pass
    
    async def process_chunk(self, chunk: np.ndarray) -> np.ndarray:
        """Apply preprocessing: normalize, denoise"""
        # Normalize to [-1, 1]
        normalized = chunk.astype(np.float32) / 32768.0
        
        # TODO: Add spectral subtraction for noise reduction
        # TODO: Add echo cancellation for call audio
        
        return normalized

# Platform-specific implementations
if sys.platform == "win32":
    from .platforms.windows import WindowsAudioInterceptor as PlatformInterceptor
elif sys.platform == "darwin":
    from .platforms.macos import MacOSAudioInterceptor as PlatformInterceptor
else:
    from .platforms.linux import LinuxAudioInterceptor as PlatformInterceptor

def create_audio_interceptor(config: AudioConfig) -> AudioInterceptor:
    """Factory function for platform-specific interceptor"""
    return PlatformInterceptor(config)
```

### 6. `src/agents/teams/audio_team.py`
```python
"""
Audio Team Agent Coordination
Manages parallel audio processing tasks
"""
from typing import List, Dict, Any
from dataclasses import dataclass
from ..base import AgentTeam, AgentTask

@dataclass
class AudioAgentConfig:
    model: str = "claude-3-sonnet"
    max_parallel: int = 3
    has_level: str = "H2"

class AudioProcessingTeam(AgentTeam):
    """Coordinates audio capture and processing agents"""
    
    def __init__(self, config: AudioAgentConfig):
        super().__init__("audio_team", config)
        self.agents = self._initialize_agents()
        
    def _initialize_agents(self) -> List[Dict]:
        return [
            {
                "id": "audio_capture_agent",
                "role": "Platform-specific audio capture implementation",
                "skills": ["WASAPI", "CoreAudio", "PulseAudio"]
            },
            {
                "id": "audio_buffer_agent",
                "role": "Circular buffer and chunk management",
                "skills": ["Ring buffer", "Lock-free queues"]
            },
            {
                "id": "audio_vad_agent",
                "role": "Voice activity detection",
                "skills": ["Silero VAD", "WebRTC VAD"]
            }
        ]
    
    async def execute_sprint(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        """Execute audio tasks in parallel"""
        results = {}
        
        # Phase 1: Parallel implementation
        parallel_tasks = [
            self.assign_task(agent, task)
            for agent, task in zip(self.agents, tasks[:3])
        ]
        
        implementations = await asyncio.gather(*parallel_tasks)
        
        # Phase 2: Integration sync
        integration_task = AgentTask(
            id="audio_integration",
            description="Integrate audio modules",
            dependencies=[t.id for t in tasks[:3]]
        )
        
        integrated = await self.orchestrate_integration(implementations)
        
        # Phase 3: Testing (delegate to test team)
        await self.request_testing(integrated)
        
        return {
            "status": "completed",
            "modules": implementations,
            "metrics": self.collect_metrics()
        }
```

### 7. `pyproject.toml`
```toml
[tool.poetry]
name = "realtime-stt-orchestrator"
version = "0.1.0"
description = "Real-time Speech-to-Text with ORCHIDEA-based orchestration"
authors = ["AI Development Team"]

[tool.poetry.dependencies]
python = "^3.11"
numpy = "^1.26"
torch = "^2.1"
transformers = "^4.36"
faster-whisper = "^1.0"
pyannote-audio = "^3.1"
sounddevice = "^0.4"
pyaudio = "^0.2"

# Platform-specific
pywin32 = {version = "*", markers = "sys_platform == 'win32'"}
pyobjc = {version = "*", markers = "sys_platform == 'darwin'"}
pulsectl = {version = "*", markers = "sys_platform == 'linux'"}

# Agent orchestration
anthropic = "^0.21"
langchain = "^0.1"
asyncio = "^3.4"

# UI
streamlit = "^1.29"
electron = {version = "*", optional = true}

# Monitoring
prometheus-client = "^0.19"
opentelemetry-api = "^1.21"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4"
pytest-asyncio = "^0.21"
black = "^23.12"
ruff = "^0.1"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

Questa struttura implementa:

1. **Architettura Multi-Agente Distribuita** con team specializzati (Opus per orchestrazione, Sonnet per sviluppo, Haiku per testing)

2. **Cicli di Sviluppo Paralleli** con sync point ogni 2 ore e gate HAS per controllo qualità

3. **Integrazione ORCHIDEA** con le 7 fasi, metriche di workflow alignment e truth guardrails

4. **Stack Tecnologico Concreto**:
   - Audio: WASAPI/CoreAudio/PulseAudio
   - STT: Whisper + FasterWhisper su RTX 5080 (proponi almeno un  alternativa a whisper)
   - NLP: Mistral/Llama quantizzati
   - UI: Electron + React

5. **Metriche per Paper** con telemetria completa per valutazione ORCHIDEA

Il sistema è progettato per sviluppo "AI-spec-driven" con specifiche dettagliate che gli agenti possono seguire autonomamente, mantenendo sync point regolari per garantire coerenza.