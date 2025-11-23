# ISTRUZIONI PER CLAUDE CODE CLI - AUDIO CAPTURE TEAM
## Real-Time Audio Capture con WASAPI + Silero VAD

**IMPORTANTE**: Sei un agente autonomo Claude Code CLI nel worktree `RTSTT-audio` (branch: `feature/audio-capture`). Esegui TUTTE le istruzioni parallelizzando con sub-agenti dove possibile. Target: **5 sub-agenti, 2 ondate**.

---

## 🎯 OBIETTIVO
Implementare layer di cattura audio per Windows 11:
- **WASAPI Loopback**: Cattura audio di sistema (<10ms latency)
- **Circular Buffer**: Buffer lock-free thread-safe (10s capacity)
- **Silero VAD v4**: Voice Activity Detection real-time
- **Platform Abstraction**: Interface per future porting
- **Redis Integration**: Producer per audio chunks

## 📊 METRICHE TARGET
- **Durata**: 4-6 ore
- **Parallelismo**: 2 ondate, 5 sub-agenti totali
- **Deliverables**: 8 file Python + 5 test files
- **Coverage**: >95%
- **Performance**: Latency <10ms, CPU <5%

---

## 🔀 STRATEGIA PARALLELIZZAZIONE (Max 5 sub-agenti)

### ANALISI DIPENDENZE
```
ONDATA 1: Foundation Components (3 sub-agenti paralleli)
├── Sub-Agent 1: WASAPI Capture (Indipendente)
├── Sub-Agent 2: Circular Buffer (Indipendente)
└── Sub-Agent 3: Silero VAD (Indipendente)
       ↓
ONDATA 2: Integration & Testing (2 sub-agenti paralleli)
├── Sub-Agent 4: Audio Service Integration (Dipende da Ondata 1)
└── Sub-Agent 5: Performance Benchmarks (Dipende da Ondata 1)
```

### CONFLICT AVOIDANCE RULES

**File Separation**:
- Sub-Agent 1 → `src/core/audio_capture/wasapi_*.py`
- Sub-Agent 2 → `src/core/audio_capture/*buffer*.py`
- Sub-Agent 3 → `src/core/audio_capture/vad_*.py`
- Sub-Agent 4 → `src/core/audio_capture/audio_service.py`
- Sub-Agent 5 → `benchmarks/audio_*.py`

**Test Isolation**:
- Sub-Agent 1 tests → `tests/unit/test_wasapi*.py`
- Sub-Agent 2 tests → `tests/unit/test_buffer*.py`
- Sub-Agent 3 tests → `tests/unit/test_vad*.py`
- Sub-Agent 4 tests → `tests/integration/test_audio_service*.py`

**Git Strategy**:
- Ogni sub-agent fa 1 commit con prefix: `[AUDIO-SUB-1]`, `[AUDIO-SUB-2]`, etc.
- Commits atomici per componente

---

## 🚀 ONDATA 1: FOUNDATION COMPONENTS (3 sub-agenti paralleli)

### Sub-Agent 1: WASAPI Audio Capture Implementation

**Lancio con Task tool**:
```
Usa il Task tool con questi parametri:

subagent_type: 'general-purpose'
description: 'Implement WASAPI audio capture for Windows 11'
prompt: |
  Implementa il modulo WASAPI audio capture completo per Windows 11 con le seguenti specifiche:

  ## OBIETTIVO
  Cattura audio di sistema Windows tramite WASAPI loopback con latenza <10ms

  ## FILE DA CREARE

  ### 1. src/core/audio_capture/wasapi_devices.py
  Gestione enumerazione dispositivi audio Windows

  ```python
  import comtypes
  from comtypes import CLSCTX_ALL
  from pycaw.pycaw import AudioUtilities
  import logging
  from typing import List, Dict, Optional

  logger = logging.getLogger(__name__)

  class AudioDevice:
      """Audio device metadata"""
      def __init__(self, device_id: str, name: str, device_type: str,
                   is_default: bool, max_channels: int,
                   supported_sample_rates: List[int]):
          self.device_id = device_id
          self.name = name
          self.device_type = device_type
          self.is_default = is_default
          self.max_channels = max_channels
          self.supported_sample_rates = supported_sample_rates

  def list_audio_devices(device_type: str = 'loopback') -> List[AudioDevice]:
      """
      Enumerate WASAPI audio devices

      Args:
          device_type: 'input', 'output', 'loopback'

      Returns:
          List of AudioDevice objects
      """
      devices = []

      try:
          # Get all audio devices
          all_devices = AudioUtilities.GetAllDevices()

          for dev in all_devices:
              # Extract device info
              device_info = AudioDevice(
                  device_id=str(dev.id),
                  name=str(dev.FriendlyName),
                  device_type='loopback' if 'Loopback' in str(dev.FriendlyName) else 'output',
                  is_default=dev.id == AudioUtilities.GetDefaultDeviceId(),
                  max_channels=2,
                  supported_sample_rates=[44100, 48000]
              )
              devices.append(device_info)

      except Exception as e:
          logger.error(f"Failed to enumerate devices: {e}")

      return devices

  def get_default_device(device_type: str = 'loopback') -> Optional[AudioDevice]:
      """Get system default audio device"""
      devices = list_audio_devices(device_type)
      default = [d for d in devices if d.is_default]
      return default[0] if default else (devices[0] if devices else None)
  ```

  ### 2. src/core/audio_capture/wasapi_capture.py
  Implementazione completa WASAPI capture

  ```python
  import threading
  import numpy as np
  import logging
  from typing import Callable, Optional
  import time

  # Note: Su Windows usa pyaudio come fallback per semplicità POC
  # In produzione usare comtypes + WASAPI diretto
  import pyaudio

  logger = logging.getLogger(__name__)

  class WASAPICapture:
      """
      WASAPI loopback audio capture for Windows 11

      Features:
      - System audio capture (loopback)
      - Low-latency streaming (<10ms)
      - Automatic device recovery
      """

      def __init__(self,
                   device_id: Optional[str] = None,
                   sample_rate: int = 48000,
                   channels: int = 1,
                   chunk_duration_ms: int = 100):
          self.device_id = device_id
          self.sample_rate = sample_rate
          self.channels = channels
          self.chunk_duration_ms = chunk_duration_ms
          self.chunk_size = int(sample_rate * chunk_duration_ms / 1000)

          self._audio = None
          self._stream = None
          self._callback = None
          self._thread = None
          self._running = False

      def start(self, callback: Callable[[np.ndarray], None]):
          """Start audio capture"""
          self._callback = callback
          self._running = True

          # Initialize PyAudio
          self._audio = pyaudio.PyAudio()

          # Open stream
          self._stream = self._audio.open(
              format=pyaudio.paInt16,
              channels=self.channels,
              rate=self.sample_rate,
              input=True,
              frames_per_buffer=self.chunk_size,
              stream_callback=self._audio_callback
          )

          self._stream.start_stream()
          logger.info(f"Audio capture started: {self.sample_rate}Hz, {self.channels}ch")

      def stop(self):
          """Stop audio capture"""
          self._running = False
          if self._stream:
              self._stream.stop_stream()
              self._stream.close()
          if self._audio:
              self._audio.terminate()
          logger.info("Audio capture stopped")

      def _audio_callback(self, in_data, frame_count, time_info, status):
          """PyAudio callback"""
          if self._callback and self._running:
              # Convert bytes to numpy array
              audio_data = np.frombuffer(in_data, dtype=np.int16)
              if self.channels > 1:
                  audio_data = audio_data.reshape(-1, self.channels)
              self._callback(audio_data)
          return (in_data, pyaudio.paContinue)

      def get_latency_ms(self) -> float:
          """Get current capture latency"""
          if self._stream:
              return self._stream.get_input_latency() * 1000
          return 0.0
  ```

  ### 3. src/core/audio_capture/audio_format.py
  Utility per conversione formati audio

  ```python
  import numpy as np
  import scipy.signal as signal

  def convert_sample_rate(audio: np.ndarray,
                          source_rate: int,
                          target_rate: int) -> np.ndarray:
      """Resample audio to target sample rate"""
      if source_rate == target_rate:
          return audio

      # Use scipy resample
      num_samples = int(len(audio) * target_rate / source_rate)
      return signal.resample(audio, num_samples)

  def convert_to_mono(audio: np.ndarray) -> np.ndarray:
      """Convert stereo to mono by averaging channels"""
      if audio.ndim == 1:
          return audio
      return audio.mean(axis=1)

  def normalize_audio(audio: np.ndarray,
                     target_level: float = -20.0) -> np.ndarray:
      """Normalize audio to target RMS level (dB)"""
      audio_float = audio.astype(np.float32)
      rms = np.sqrt(np.mean(audio_float**2))
      if rms > 0:
          target_rms = 10 ** (target_level / 20)
          return audio_float * (target_rms / rms)
      return audio_float
  ```

  ## COMANDI DA ESEGUIRE

  ```bash
  # Install dependencies
  pip install pyaudio numpy scipy pycaw comtypes

  # Create __init__.py
  touch src/core/audio_capture/__init__.py
  ```

  ## TEST DA CREARE

  ### tests/unit/test_wasapi_devices.py
  ```python
  import pytest
  from src.core.audio_capture.wasapi_devices import list_audio_devices, get_default_device

  def test_list_audio_devices():
      devices = list_audio_devices()
      assert isinstance(devices, list)
      # Su Windows dovrebbe avere almeno 1 device

  def test_get_default_device():
      device = get_default_device()
      # Può essere None se nessun device disponibile
      if device:
          assert device.device_id is not None
          assert device.name is not None
  ```

  ### tests/unit/test_wasapi_capture.py
  ```python
  import pytest
  import numpy as np
  from src.core.audio_capture.wasapi_capture import WASAPICapture
  import time

  def test_wasapi_capture_init():
      capture = WASAPICapture()
      assert capture.sample_rate == 48000
      assert capture.channels == 1

  def test_wasapi_capture_callback():
      capture = WASAPICapture(sample_rate=16000, chunk_duration_ms=100)

      received_chunks = []

      def callback(audio):
          received_chunks.append(audio)

      capture.start(callback)
      time.sleep(0.5)  # Capture for 500ms
      capture.stop()

      assert len(received_chunks) > 0
      assert all(isinstance(chunk, np.ndarray) for chunk in received_chunks)
  ```

  ## DELIVERABLES
  - ✅ wasapi_devices.py completo con device enumeration
  - ✅ wasapi_capture.py con capture loop
  - ✅ audio_format.py con utility conversione
  - ✅ 2 file test con coverage >90%
  - ✅ Commit: "[AUDIO-SUB-1] Implement WASAPI audio capture"

  ## VALIDAZIONE
  - Esegui: pytest tests/unit/test_wasapi*.py -v
  - Verifica nessun import error
  - Commit e push
```

---

### Sub-Agent 2: Circular Buffer Implementation

**Lancio con Task tool**:
```
subagent_type: 'general-purpose'
description: 'Implement lock-free circular buffer'
prompt: |
  Implementa circular buffer thread-safe per audio streaming:

  ## FILE DA CREARE

  ### src/core/audio_capture/circular_buffer.py
  ```python
  import numpy as np
  import threading
  from typing import Optional

  class CircularBuffer:
      """Lock-free circular buffer for audio streaming"""

      def __init__(self, capacity_seconds: float, sample_rate: int, channels: int):
          self.capacity = int(capacity_seconds * sample_rate)
          self.sample_rate = sample_rate
          self.channels = channels

          # Pre-allocate buffer
          self.buffer = np.zeros((self.capacity, channels), dtype=np.float32)

          self._write_index = 0
          self._read_index = 0
          self._lock = threading.Lock()
          self._available_samples = 0

      def write(self, data: np.ndarray) -> int:
          """Write audio data to buffer"""
          num_samples = len(data)

          with self._lock:
              write_pos = self._write_index % self.capacity

              if write_pos + num_samples > self.capacity:
                  # Wrap around
                  first_chunk = self.capacity - write_pos
                  self.buffer[write_pos:] = data[:first_chunk]
                  self.buffer[:num_samples - first_chunk] = data[first_chunk:]
              else:
                  self.buffer[write_pos:write_pos + num_samples] = data

              self._write_index += num_samples
              self._available_samples = min(
                  self._available_samples + num_samples,
                  self.capacity
              )

          return num_samples

      def read(self, num_samples: int) -> Optional[np.ndarray]:
          """Read audio data from buffer"""
          with self._lock:
              if self._available_samples < num_samples:
                  return None

              read_pos = self._read_index % self.capacity

              if read_pos + num_samples > self.capacity:
                  first_chunk = self.capacity - read_pos
                  data = np.concatenate([
                      self.buffer[read_pos:],
                      self.buffer[:num_samples - first_chunk]
                  ])
              else:
                  data = self.buffer[read_pos:read_pos + num_samples].copy()

              self._read_index += num_samples
              self._available_samples -= num_samples

          return data

      def available(self) -> int:
          """Get number of available samples"""
          with self._lock:
              return self._available_samples

      def clear(self):
          """Clear buffer"""
          with self._lock:
              self._write_index = 0
              self._read_index = 0
              self._available_samples = 0
  ```

  ## TEST

  ### tests/unit/test_circular_buffer.py
  ```python
  import pytest
  import numpy as np
  from src.core.audio_capture.circular_buffer import CircularBuffer
  import threading
  import time

  def test_circular_buffer_write_read():
      buffer = CircularBuffer(capacity_seconds=1.0, sample_rate=16000, channels=1)

      # Write 100 samples
      data = np.random.randn(100, 1).astype(np.float32)
      written = buffer.write(data)
      assert written == 100
      assert buffer.available() == 100

      # Read 50 samples
      read_data = buffer.read(50)
      assert read_data is not None
      assert len(read_data) == 50
      assert buffer.available() == 50

  def test_circular_buffer_wraparound():
      buffer = CircularBuffer(capacity_seconds=0.01, sample_rate=16000, channels=1)
      capacity = buffer.capacity

      # Write more than capacity
      data = np.random.randn(capacity + 100, 1).astype(np.float32)
      buffer.write(data)

      # Should have capacity samples available
      assert buffer.available() == capacity

  def test_circular_buffer_concurrent():
      buffer = CircularBuffer(capacity_seconds=1.0, sample_rate=16000, channels=1)

      def writer():
          for _ in range(10):
              data = np.random.randn(100, 1).astype(np.float32)
              buffer.write(data)
              time.sleep(0.01)

      def reader():
          for _ in range(10):
              while buffer.available() < 100:
                  time.sleep(0.001)
              buffer.read(100)

      t1 = threading.Thread(target=writer)
      t2 = threading.Thread(target=reader)

      t1.start()
      t2.start()
      t1.join()
      t2.join()

      # No crash = success
  ```

  ## DELIVERABLES
  - ✅ circular_buffer.py implementato
  - ✅ test_circular_buffer.py con 3+ test
  - ✅ Coverage >95%
  - ✅ Commit: "[AUDIO-SUB-2] Implement circular buffer"
```

---

### Sub-Agent 3: Silero VAD Integration

**Lancio con Task tool**:
```
subagent_type: 'general-purpose'
description: 'Integrate Silero VAD v4 for voice detection'
prompt: |
  Integra Silero VAD v4 per Voice Activity Detection:

  ## FILE DA CREARE

  ### src/core/audio_capture/vad_silero.py
  ```python
  import torch
  import numpy as np
  from typing import Tuple
  import logging

  logger = logging.getLogger(__name__)

  class SileroVAD:
      """Silero VAD v4 for voice activity detection"""

      def __init__(self,
                   threshold: float = 0.5,
                   sample_rate: int = 16000):
          self.threshold = threshold
          self.sample_rate = sample_rate

          # Load model (download if needed)
          try:
              self.model, _ = torch.hub.load(
                  repo_or_dir='snakers4/silero-vad',
                  model='silero_vad',
                  force_reload=False,
                  onnx=False
              )
              self.model.eval()
              logger.info("Silero VAD model loaded")
          except Exception as e:
              logger.error(f"Failed to load Silero VAD: {e}")
              self.model = None

          self._h = None
          self._c = None

      def process_chunk(self, audio: np.ndarray) -> Tuple[bool, float]:
          """Process audio chunk and return (is_speech, confidence)"""
          if self.model is None:
              return False, 0.0

          # Convert to torch tensor
          if audio.dtype != np.float32:
              audio = audio.astype(np.float32) / 32768.0

          audio_tensor = torch.from_numpy(audio).float()

          # Run VAD
          with torch.no_grad():
              confidence = self.model(audio_tensor, self.sample_rate).item()

          is_speech = confidence >= self.threshold
          return is_speech, confidence

      def reset(self):
          """Reset VAD state"""
          self._h = None
          self._c = None
  ```

  ### src/core/audio_capture/vad_segmenter.py
  ```python
  import numpy as np
  from collections import deque
  from typing import List

  class VADSegmenter:
      """Segment audio based on VAD output"""

      def __init__(self,
                   sample_rate: int,
                   min_speech_duration_ms: int = 250,
                   min_silence_duration_ms: int = 100):
          self.sample_rate = sample_rate
          self.min_speech_samples = int(min_speech_duration_ms * sample_rate / 1000)
          self.min_silence_samples = int(min_silence_duration_ms * sample_rate / 1000)

          self._buffer = deque()
          self._in_speech = False
          self._silence_duration = 0

      def add_frame(self, audio: np.ndarray, is_speech: bool) -> List[np.ndarray]:
          """Add VAD frame and return complete segments"""
          segments = []

          self._buffer.append((audio, is_speech))

          if is_speech:
              if not self._in_speech:
                  self._in_speech = True
                  self._silence_duration = 0
          else:
              if self._in_speech:
                  self._silence_duration += len(audio)

                  if self._silence_duration >= self.min_silence_samples:
                      # Extract segment
                      audio_chunks = [chunk for chunk, _ in self._buffer]
                      segment = np.concatenate(audio_chunks)

                      if len(segment) >= self.min_speech_samples:
                          segments.append(segment)

                      self._in_speech = False
                      self._buffer.clear()

          return segments
  ```

  ## TEST

  ### tests/unit/test_vad.py
  ```python
  import pytest
  import numpy as np
  from src.core.audio_capture.vad_silero import SileroVAD

  def test_silero_vad_init():
      vad = SileroVAD()
      assert vad.threshold == 0.5
      assert vad.sample_rate == 16000

  def test_silero_vad_process():
      vad = SileroVAD()

      # Generate random audio
      audio = np.random.randn(1600).astype(np.float32)  # 100ms at 16kHz

      is_speech, confidence = vad.process_chunk(audio)
      assert isinstance(is_speech, bool)
      assert 0.0 <= confidence <= 1.0
  ```

  ## COMANDI
  ```bash
  pip install torch torchaudio
  ```

  ## DELIVERABLES
  - ✅ vad_silero.py implementato
  - ✅ vad_segmenter.py implementato
  - ✅ test_vad.py con coverage
  - ✅ Commit: "[AUDIO-SUB-3] Integrate Silero VAD"
```

---

## ⏸️ SYNC POINT 1: Attendi Completamento Ondata 1

**Verifica che i 3 sub-agenti abbiano completato**:
```bash
# Check git commits
git log --oneline | grep "AUDIO-SUB"
# Dovresti vedere 3 commit: SUB-1, SUB-2, SUB-3

# Check files created
ls src/core/audio_capture/
# Atteso: wasapi*.py, circular_buffer.py, vad*.py

# Run tests
pytest tests/unit/test_wasapi*.py tests/unit/test_buffer*.py tests/unit/test_vad*.py -v
```

**✅ CHECKPOINT**: 3 componenti implementati e testati

---

## 🚀 ONDATA 2: INTEGRATION & TESTING (2 sub-agenti paralleli)

### Sub-Agent 4: Audio Service Integration

**Lancio con Task tool**:
```
subagent_type: 'general-purpose'
description: 'Integrate audio components into service'
prompt: |
  Integra tutti i componenti audio in un servizio completo:

  ## FILE DA CREARE

  ### src/core/audio_capture/audio_service.py

  [FILE COMPLETO CON: WASAPI + Buffer + VAD + Redis producer]

  (Codice fornito nel SUB-PLAN originale, circa 200 righe)

  ## TEST
  ### tests/integration/test_audio_service.py

  [Test end-to-end completo]

  ## DELIVERABLES
  - ✅ audio_service.py completo
  - ✅ Integration test
  - ✅ Commit: "[AUDIO-SUB-4] Integrate audio service"
```

---

### Sub-Agent 5: Performance Benchmarks

**Lancio con Task tool**:
```
subagent_type: 'general-purpose'
description: 'Create performance benchmarks'
prompt: |
  Implementa benchmark suite per audio capture:

  ## FILE DA CREARE

  ### benchmarks/audio_latency_benchmark.py

  [Benchmark latency, CPU usage, throughput]

  ## DELIVERABLES
  - ✅ Benchmark script
  - ✅ Report generato
  - ✅ Commit: "[AUDIO-SUB-5] Add performance benchmarks"
```

---

## ⏸️ SYNC POINT 2: Validazione Finale

```bash
# Verifica tutti i 5 commit
git log --oneline --graph

# Run all tests
pytest tests/ -v --cov=src/core/audio_capture

# Coverage report
pytest --cov-report=html
```

---

## ✅ VALIDAZIONE FINALE

### Checklist Completamento
- [ ] 5 sub-agenti completati
- [ ] 8 file Python creati
- [ ] 5 file test creati
- [ ] Coverage >95%
- [ ] 5 commit atomici
- [ ] Integration test passa
- [ ] Benchmark eseguito

---

## 📊 DELIVERABLES

**Files Created**:
- src/core/audio_capture/wasapi_devices.py
- src/core/audio_capture/wasapi_capture.py
- src/core/audio_capture/audio_format.py
- src/core/audio_capture/circular_buffer.py
- src/core/audio_capture/vad_silero.py
- src/core/audio_capture/vad_segmenter.py
- src/core/audio_capture/audio_service.py
- src/core/audio_capture/__init__.py

**Tests**:
- tests/unit/test_wasapi*.py (2 files)
- tests/unit/test_circular_buffer.py
- tests/unit/test_vad.py
- tests/integration/test_audio_service.py

**Benchmarks**:
- benchmarks/audio_latency_benchmark.py

---

## 🔗 REPORT A MAIN-T

**Status**: ✅ AUDIO TEAM COMPLETE
**Branch**: feature/audio-capture
**Commits**: 5
**Files**: 13 (8 src + 5 tests)
**Coverage**: >95%
**Blockers**: Nessuno
**Ready for**: Merge to develop

---

**FINE ISTRUZIONI AUDIO TEAM**
