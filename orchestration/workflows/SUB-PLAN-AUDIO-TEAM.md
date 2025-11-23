# SUB-PLAN: AUDIO CAPTURE TEAM
## Real-Time Audio Capture with WASAPI + Silero VAD

---

**Worktree**: `../RTSTT-audio`
**Branch**: `feature/audio-capture`
**Team**: 3 Sonnet Agents (Capture Specialist, VAD Engineer, Buffer Architect)
**Duration**: 6 hours
**Priority**: CRITICA (foundation layer)

---

## 🎯 OBIETTIVO

Implementare il layer di cattura audio per Windows 11 con WASAPI loopback, Voice Activity Detection (Silero VAD v4), e circular buffer lock-free. Latency target: **<10ms**

---

## 📦 DELIVERABLES

1. **WASAPI Capture Module** (`src/core/audio_capture/wasapi_capture.py`)
2. **C++ Native Binding** (`src/core/audio_capture/audio_capture.node`)
3. **Circular Buffer** (`src/core/audio_capture/circular_buffer.py`)
4. **Silero VAD Integration** (`src/core/audio_capture/vad_silero.py`)
5. **Platform Abstraction** (`src/core/audio_capture/audio_interface.py`)
6. **Unit Tests** (>95% coverage)
7. **Integration Tests** (end-to-end capture → buffer)
8. **Performance Benchmarks** (latency, CPU usage)

---

## 📋 TASK BREAKDOWN

### TASK 1: WASAPI Loopback Capture (2.5h)

**Obiettivo**: Catturare audio di sistema Windows 11 con WASAPI loopback

#### Step 1.1: Device Enumeration (30min)
```python
# File: src/core/audio_capture/wasapi_devices.py

import comtypes
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioClient

def list_audio_devices(device_type='loopback'):
    """
    Enumerate WASAPI audio devices

    Args:
        device_type: 'input', 'output', 'loopback'

    Returns:
        List[AudioDevice]: Available devices with metadata
    """
    devices = []
    # Implementation:
    # 1. CoInitialize() COM interface
    # 2. Get IMMDeviceEnumerator
    # 3. EnumAudioEndpoints(eRender for loopback, eCapture for mic)
    # 4. For each device: GetId, GetName, GetState
    # 5. Query supported formats (48kHz, 16-bit, mono/stereo)
    return devices

def get_default_device(device_type='loopback'):
    """Get system default audio device"""
    pass

# Test:
if __name__ == "__main__":
    devices = list_audio_devices('loopback')
    for dev in devices:
        print(f"{dev.id}: {dev.name} ({dev.channels}ch, {dev.sample_rate}Hz)")
```

**Validation**:
- [ ] Enumera tutti i device WASAPI
- [ ] Identifica default loopback device
- [ ] Legge supported formats

---

#### Step 1.2: WASAPI Capture Core (1.5h)
```python
# File: src/core/audio_capture/wasapi_capture.py

import threading
import numpy as np
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioClient, IAudioCaptureClient

class WASAPICapture:
    """
    WASAPI loopback audio capture for Windows 11

    Features:
    - System audio capture (loopback)
    - Low-latency streaming (<10ms)
    - Lock-free circular buffer integration
    - Automatic device recovery
    """

    def __init__(self,
                 device_id: str = None,
                 sample_rate: int = 48000,
                 channels: int = 1,
                 bit_depth: int = 16,
                 buffer_duration_ms: int = 100):
        """
        Initialize WASAPI capture

        Args:
            device_id: WASAPI device ID (None = default)
            sample_rate: Target sample rate (Hz)
            channels: 1 (mono) or 2 (stereo)
            bit_depth: 16, 24, or 32
            buffer_duration_ms: Capture buffer size (ms)
        """
        self.device_id = device_id
        self.sample_rate = sample_rate
        self.channels = channels
        self.bit_depth = bit_depth
        self.buffer_duration_ms = buffer_duration_ms

        self._audio_client = None
        self._capture_client = None
        self._thread = None
        self._stop_event = threading.Event()
        self._callback = None

    def start(self, callback):
        """
        Start audio capture

        Args:
            callback: Function called with audio chunks (np.ndarray)
        """
        self._callback = callback
        self._stop_event.clear()

        # 1. Get device
        device = self._get_device()

        # 2. Initialize IAudioClient
        self._audio_client = device.Activate(
            IAudioClient._iid_, CLSCTX_ALL, None
        )

        # 3. Get mix format
        mix_format = self._audio_client.GetMixFormat()

        # 4. Initialize in loopback mode
        self._audio_client.Initialize(
            AUDCLNT_SHAREMODE_SHARED,
            AUDCLNT_STREAMFLAGS_LOOPBACK,
            self._buffer_duration_ms * 10000,  # hns (100ns units)
            0,
            mix_format,
            None
        )

        # 5. Get capture client
        self._capture_client = self._audio_client.GetService(
            IAudioCaptureClient._iid_
        )

        # 6. Start audio engine
        self._audio_client.Start()

        # 7. Start capture thread
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop audio capture"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._audio_client:
            self._audio_client.Stop()

    def _capture_loop(self):
        """Capture loop running in dedicated thread"""
        while not self._stop_event.is_set():
            # 1. Get next packet size
            num_frames = self._capture_client.GetNextPacketSize()

            if num_frames > 0:
                # 2. Get buffer
                data, flags = self._capture_client.GetBuffer(num_frames)

                # 3. Convert to numpy array
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                audio_chunk = audio_chunk.reshape(-1, self.channels)

                # 4. Call callback with chunk
                if self._callback:
                    self._callback(audio_chunk)

                # 5. Release buffer
                self._capture_client.ReleaseBuffer(num_frames)
            else:
                # No data available, sleep briefly
                threading.sleep(0.001)  # 1ms

    def _get_device(self):
        """Get WASAPI device by ID or default"""
        # Implementation: use wasapi_devices.py
        pass
```

**Validation**:
- [ ] Cattura audio di sistema (loopback)
- [ ] Latency <10ms verificata
- [ ] Gestione errori device disconnection
- [ ] Conversione formato audio corretta

---

#### Step 1.3: Audio Format Conversion (30min)
```python
# File: src/core/audio_capture/audio_format.py

import numpy as np
import scipy.signal as signal

def convert_sample_rate(audio: np.ndarray,
                        source_rate: int,
                        target_rate: int) -> np.ndarray:
    """Resample audio to target sample rate"""
    if source_rate == target_rate:
        return audio

    # Use scipy.signal.resample_poly for high-quality resampling
    num_samples = int(len(audio) * target_rate / source_rate)
    return signal.resample_poly(audio, target_rate, source_rate)

def convert_channels(audio: np.ndarray,
                     source_channels: int,
                     target_channels: int) -> np.ndarray:
    """Convert stereo <-> mono"""
    if source_channels == target_channels:
        return audio

    if source_channels == 2 and target_channels == 1:
        # Stereo to mono: average channels
        return audio.mean(axis=1)
    elif source_channels == 1 and target_channels == 2:
        # Mono to stereo: duplicate channel
        return np.stack([audio, audio], axis=1)

def normalize_audio(audio: np.ndarray,
                   target_level: float = -20.0) -> np.ndarray:
    """Normalize audio to target RMS level (dB)"""
    rms = np.sqrt(np.mean(audio**2))
    if rms > 0:
        target_rms = 10 ** (target_level / 20)
        return audio * (target_rms / rms)
    return audio
```

**Validation**:
- [ ] Resampling 44.1kHz → 48kHz
- [ ] Stereo → Mono conversion
- [ ] Normalizzazione RMS

---

### TASK 2: Lock-Free Circular Buffer (1.5h)

**Obiettivo**: Buffer thread-safe ad alta performance per producer-consumer pattern

#### Step 2.1: Circular Buffer Implementation (1h)
```python
# File: src/core/audio_capture/circular_buffer.py

import numpy as np
import threading
from typing import Optional

class CircularBuffer:
    """
    Lock-free circular buffer for audio streaming

    Uses atomic operations for thread-safe producer-consumer pattern.
    Capacity: fixed size in samples
    Overwrite policy: oldest data if full
    """

    def __init__(self, capacity_seconds: float, sample_rate: int, channels: int):
        """
        Initialize circular buffer

        Args:
            capacity_seconds: Buffer size in seconds
            sample_rate: Audio sample rate
            channels: Number of audio channels
        """
        self.capacity = int(capacity_seconds * sample_rate)
        self.sample_rate = sample_rate
        self.channels = channels

        # Pre-allocate buffer (avoid runtime allocation)
        self.buffer = np.zeros((self.capacity, channels), dtype=np.float32)

        # Atomic indices (using threading.Lock for simplicity)
        self._write_index = 0
        self._read_index = 0
        self._lock = threading.Lock()
        self._available_samples = 0

    def write(self, data: np.ndarray) -> int:
        """
        Write audio data to buffer

        Args:
            data: Audio samples (shape: [samples, channels])

        Returns:
            Number of samples written
        """
        num_samples = len(data)

        with self._lock:
            # Calculate write position
            write_pos = self._write_index % self.capacity

            # Split write if wrapping around
            if write_pos + num_samples > self.capacity:
                # Write in two chunks
                first_chunk_size = self.capacity - write_pos
                self.buffer[write_pos:] = data[:first_chunk_size]
                self.buffer[:num_samples - first_chunk_size] = data[first_chunk_size:]
            else:
                # Write in one chunk
                self.buffer[write_pos:write_pos + num_samples] = data

            # Update write index
            self._write_index += num_samples
            self._available_samples = min(
                self._available_samples + num_samples,
                self.capacity
            )

        return num_samples

    def read(self, num_samples: int) -> Optional[np.ndarray]:
        """
        Read audio data from buffer

        Args:
            num_samples: Number of samples to read

        Returns:
            Audio samples or None if insufficient data
        """
        with self._lock:
            if self._available_samples < num_samples:
                return None  # Not enough data

            # Calculate read position
            read_pos = self._read_index % self.capacity

            # Read data (handle wrapping)
            if read_pos + num_samples > self.capacity:
                # Read in two chunks
                first_chunk_size = self.capacity - read_pos
                data = np.concatenate([
                    self.buffer[read_pos:],
                    self.buffer[:num_samples - first_chunk_size]
                ])
            else:
                # Read in one chunk
                data = self.buffer[read_pos:read_pos + num_samples].copy()

            # Update read index
            self._read_index += num_samples
            self._available_samples -= num_samples

        return data

    def available(self) -> int:
        """Get number of available samples"""
        with self._lock:
            return self._available_samples

    def clear(self):
        """Clear buffer contents"""
        with self._lock:
            self._write_index = 0
            self._read_index = 0
            self._available_samples = 0
            self.buffer.fill(0)
```

**Validation**:
- [ ] Concurrent writes + reads senza corruption
- [ ] Wrapping corretto al boundary
- [ ] Performance: >1M samples/sec throughput

---

### TASK 3: Silero VAD Integration (1.5h)

**Obiettivo**: Rilevare voice activity per segmentazione intelligente

#### Step 3.1: Silero VAD Setup (30min)
```python
# File: src/core/audio_capture/vad_silero.py

import torch
import numpy as np
from typing import Tuple

class SileroVAD:
    """
    Silero VAD v4 for voice activity detection

    Features:
    - Real-time processing
    - Low CPU overhead (<1%)
    - Confidence scores per frame
    """

    def __init__(self,
                 model_path: str = "models/silero_vad.jit",
                 threshold: float = 0.5,
                 sample_rate: int = 16000):
        """
        Initialize Silero VAD

        Args:
            model_path: Path to Silero VAD JIT model
            threshold: Voice detection threshold (0.0-1.0)
            sample_rate: Must be 8000 or 16000 Hz
        """
        self.threshold = threshold
        self.sample_rate = sample_rate

        # Load model
        self.model = torch.jit.load(model_path)
        self.model.eval()

        # Reset state
        self._h = None
        self._c = None

    def process_chunk(self, audio: np.ndarray) -> Tuple[bool, float]:
        """
        Process audio chunk

        Args:
            audio: Audio samples (shape: [samples])

        Returns:
            (is_speech, confidence)
        """
        # Convert to torch tensor
        audio_tensor = torch.from_numpy(audio).float()

        # Run VAD
        with torch.no_grad():
            confidence, self._h, self._c = self.model(
                audio_tensor,
                self._h,
                self._c
            )

        confidence = confidence.item()
        is_speech = confidence >= self.threshold

        return is_speech, confidence

    def reset(self):
        """Reset VAD state"""
        self._h = None
        self._c = None
```

**Validation**:
- [ ] Rileva speech vs silence
- [ ] Confidence scores accurati
- [ ] CPU usage <1%

---

#### Step 3.2: VAD Segmentation (1h)
```python
# File: src/core/audio_capture/vad_segmenter.py

import numpy as np
from collections import deque
from typing import List, Tuple

class VADSegmenter:
    """
    Segmenta audio basandosi su VAD output

    Features:
    - Min speech duration
    - Min silence duration
    - Padding before/after speech
    """

    def __init__(self,
                 sample_rate: int,
                 min_speech_duration_ms: int = 250,
                 min_silence_duration_ms: int = 100,
                 padding_duration_ms: int = 30):
        """Initialize VAD segmenter"""
        self.sample_rate = sample_rate
        self.min_speech_samples = int(min_speech_duration_ms * sample_rate / 1000)
        self.min_silence_samples = int(min_silence_duration_ms * sample_rate / 1000)
        self.padding_samples = int(padding_duration_ms * sample_rate / 1000)

        self._buffer = deque()
        self._in_speech = False
        self._speech_start = 0
        self._silence_duration = 0

    def add_frame(self, audio: np.ndarray, is_speech: bool) -> List[np.ndarray]:
        """
        Add VAD frame and return complete segments

        Args:
            audio: Audio chunk
            is_speech: VAD result

        Returns:
            List of complete speech segments
        """
        segments = []

        self._buffer.append((audio, is_speech))

        if is_speech:
            if not self._in_speech:
                # Speech started
                self._in_speech = True
                self._speech_start = len(self._buffer)
                self._silence_duration = 0
            else:
                # Continuing speech
                pass
        else:
            if self._in_speech:
                # Potential end of speech
                self._silence_duration += len(audio)

                if self._silence_duration >= self.min_silence_samples:
                    # Extract speech segment with padding
                    segment = self._extract_segment()
                    if len(segment) >= self.min_speech_samples:
                        segments.append(segment)

                    # Reset state
                    self._in_speech = False
                    self._silence_duration = 0
                    self._buffer.clear()

        return segments

    def _extract_segment(self) -> np.ndarray:
        """Extract current speech segment from buffer"""
        # Concatenate all audio in buffer
        audio_chunks = [chunk for chunk, _ in self._buffer]
        return np.concatenate(audio_chunks)
```

**Validation**:
- [ ] Segmenta correttamente speech
- [ ] Rispetta min durations
- [ ] Padding corretto

---

### TASK 4: Platform Abstraction Layer (1h)

**Obiettivo**: Interface generica per future porting (macOS, Linux)

```python
# File: src/core/audio_capture/audio_interface.py

from abc import ABC, abstractmethod
from typing import Callable, List
import numpy as np

class AudioDevice:
    """Audio device metadata"""
    def __init__(self, device_id: str, name: str, device_type: str,
                 is_default: bool, max_channels: int,
                 supported_sample_rates: List[int]):
        self.device_id = device_id
        self.name = name
        self.device_type = device_type  # 'input', 'output', 'loopback'
        self.is_default = is_default
        self.max_channels = max_channels
        self.supported_sample_rates = supported_sample_rates

class AudioCaptureInterface(ABC):
    """Abstract interface for audio capture backends"""

    @abstractmethod
    def list_devices(self) -> List[AudioDevice]:
        """Enumerate available audio devices"""
        pass

    @abstractmethod
    def start(self, device_id: str, callback: Callable[[np.ndarray], None]):
        """Start audio capture"""
        pass

    @abstractmethod
    def stop(self):
        """Stop audio capture"""
        pass

    @abstractmethod
    def get_latency_ms(self) -> float:
        """Get current capture latency"""
        pass

# Platform-specific implementations
class WASAPIAudioCapture(AudioCaptureInterface):
    """Windows WASAPI implementation"""
    # Use wasapi_capture.py
    pass

class CoreAudioCapture(AudioCaptureInterface):
    """macOS CoreAudio implementation (future)"""
    pass

class PulseAudioCapture(AudioCaptureInterface):
    """Linux PulseAudio implementation (future)"""
    pass

# Factory
def create_audio_capture(platform: str = None) -> AudioCaptureInterface:
    """Create platform-appropriate audio capture"""
    import sys

    if platform is None:
        platform = sys.platform

    if platform == 'win32':
        return WASAPIAudioCapture()
    elif platform == 'darwin':
        return CoreAudioCapture()
    elif platform == 'linux':
        return PulseAudioCapture()
    else:
        raise NotImplementedError(f"Platform {platform} not supported")
```

---

### TASK 5: Integration & gRPC Producer (30min)

**Obiettivo**: Integrare tutti i componenti e produrre messaggi Redis

```python
# File: src/core/audio_capture/audio_service.py

import redis
import base64
import time
import uuid
from typing import Optional

class AudioCaptureService:
    """
    Complete audio capture service

    Pipeline:
    WASAPI → Circular Buffer → VAD → Segmentation → Redis Streams
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.session_id = None
        self.chunk_counter = 0

        # Components
        self.capture = None
        self.buffer = None
        self.vad = None
        self.segmenter = None

    def start_session(self, device_id: str, session_id: str = None):
        """Start audio capture session"""
        self.session_id = session_id or str(uuid.uuid4())
        self.chunk_counter = 0

        # Initialize components
        self.buffer = CircularBuffer(capacity_seconds=10,
                                     sample_rate=48000,
                                     channels=1)
        self.vad = SileroVAD(threshold=0.5)
        self.segmenter = VADSegmenter(sample_rate=48000)

        # Start WASAPI capture
        self.capture = WASAPICapture(device_id=device_id)
        self.capture.start(callback=self._on_audio_chunk)

    def stop_session(self):
        """Stop audio capture session"""
        if self.capture:
            self.capture.stop()

        # Send final message
        self._publish_audio_chunk(
            audio_data=np.array([]),
            vad_detected=False,
            is_final=True
        )

    def _on_audio_chunk(self, audio: np.ndarray):
        """Callback for WASAPI capture"""
        # Write to buffer
        self.buffer.write(audio)

        # Run VAD
        is_speech, confidence = self.vad.process_chunk(audio)

        # Publish to Redis
        self._publish_audio_chunk(audio, is_speech)

    def _publish_audio_chunk(self, audio: np.ndarray,
                            vad_detected: bool,
                            is_final: bool = False):
        """Publish audio chunk to Redis Streams"""
        chunk_id = f"chunk-{self.chunk_counter:06d}"
        self.chunk_counter += 1

        # Encode audio as base64
        audio_base64 = base64.b64encode(audio.tobytes()).decode('utf-8')

        # Publish to Redis
        self.redis.xadd(
            'rtstt:prod:audio:out',
            {
                'session_id': self.session_id,
                'chunk_id': chunk_id,
                'timestamp_ms': str(int(time.time() * 1000)),
                'audio_data_base64': audio_base64,
                'sample_rate': '48000',
                'channels': '1',
                'bit_depth': '16',
                'duration_ms': str(int(len(audio) / 48)),
                'vad_detected': str(vad_detected).lower(),
                'is_final': str(is_final).lower()
            }
        )
```

---

### TASK 6: Testing (1.5h)

#### Unit Tests
```python
# File: tests/unit/test_circular_buffer.py
# File: tests/unit/test_vad.py
# File: tests/unit/test_wasapi_devices.py
```

#### Integration Tests
```python
# File: tests/integration/test_audio_capture_e2e.py

def test_audio_capture_to_redis():
    """Test complete pipeline: WASAPI → Buffer → VAD → Redis"""
    # 1. Start mock WASAPI or use test audio file
    # 2. Capture 5 seconds
    # 3. Verify Redis messages
    # 4. Check latency <10ms
    pass
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] WASAPI cattura audio loopback Windows 11
- [ ] Latency <10ms verificata con benchmark
- [ ] VAD rileva speech con >90% accuracy
- [ ] Circular buffer gestisce 10s di audio senza drop
- [ ] Redis Streams riceve chunks correttamente formattati
- [ ] Unit tests >95% coverage
- [ ] Integration test end-to-end passa
- [ ] CPU usage <5% durante capture
- [ ] Documentazione API completa

---

## 📊 METRICHE

- **Latency**: Measure con `time.perf_counter()` in callback
- **CPU Usage**: Monitor con `psutil.Process().cpu_percent()`
- **Buffer Fill**: `buffer.available() / buffer.capacity`
- **VAD Accuracy**: Compare con manual labels

---

## 🔗 DIPENDENZE

**Upstream**: Nessuna (layer foundation)
**Downstream**: STT Engine (consuma da Redis `rtstt:prod:audio:out`)

---

## 🚀 COMANDI ESECUZIONE

```bash
# In ../RTSTT-audio worktree
cd ../RTSTT-audio

# Install dependencies
pip install -r requirements/base.txt
pip install -r requirements/audio.txt

# Download Silero VAD model
python scripts/download_silero_vad.py

# Run tests
pytest tests/unit/test_circular_buffer.py -v
pytest tests/integration/test_audio_capture_e2e.py -v

# Benchmark
python benchmarks/audio_latency_benchmark.py

# Start service (manual test)
python -m src.core.audio_capture.audio_service
```

---

## 🎯 SYNC POINT

**Checkpoint ogni 2 ore con MAIN-T:**
- Report progress (tasks completed)
- Upload codice a branch `feature/audio-capture`
- Verificare aderenza API contracts
- Risk mitigation se bloccati

---

**BUON LAVORO, AUDIO TEAM! 🎧**
