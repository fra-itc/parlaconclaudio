"""
Mock Audio Driver

Generates synthetic audio for testing purposes.
Useful for development, CI/CD, and systems without audio hardware.
"""

import time
import math
import struct
import threading
import logging
from typing import Optional, Callable, List
from queue import Queue, Empty

from ..audio_capture_base import (
    AudioCaptureBase,
    AudioCaptureConfig,
    AudioCaptureState,
    AudioDevice,
    AudioFormat
)


logger = logging.getLogger(__name__)


class MockAudioDriver(AudioCaptureBase):
    """
    Mock audio driver that generates synthetic audio.

    Generates various test patterns:
    - Sine wave (configurable frequency)
    - White noise
    - Silence
    - Simulated speech patterns

    Useful for testing without real audio hardware.
    """

    def __init__(self, config: Optional[AudioCaptureConfig] = None, pattern: str = "sine"):
        """
        Initialize mock audio driver.

        Args:
            config: Audio configuration
            pattern: Audio pattern to generate
                    'sine' - Pure sine wave (440 Hz)
                    'noise' - White noise
                    'silence' - Silence
                    'speech' - Simulated speech-like pattern
        """
        super().__init__(config)

        self.pattern = pattern
        self._capture_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._audio_queue: Queue = Queue(maxsize=100)
        self._sample_position = 0
        self._volume = 0.5

        logger.info(f"MockAudioDriver initialized: {self.config.sample_rate}Hz, pattern={pattern}")

    def list_devices(self) -> List[AudioDevice]:
        """List mock devices"""
        return [
            AudioDevice(
                device_id=0,
                name="Mock Audio Device",
                is_default=True,
                max_channels=2,
                supported_sample_rates=[8000, 16000, 44100, 48000]
            )
        ]

    def get_default_device(self) -> Optional[AudioDevice]:
        """Get default mock device"""
        return self.list_devices()[0]

    def start(self, callback: Optional[Callable[[bytes], None]] = None) -> None:
        """Start generating audio"""
        if self.state == AudioCaptureState.RUNNING:
            logger.warning("Mock driver already running")
            return

        self.state = AudioCaptureState.STARTING
        self._callback = callback
        self._stop_event.clear()
        self._sample_position = 0

        # Start capture thread
        self._capture_thread = threading.Thread(
            target=self._generate_audio_loop,
            name="MockAudioCapture",
            daemon=True
        )
        self._capture_thread.start()

        self.state = AudioCaptureState.RUNNING
        self.metrics.start_time = time.time()
        logger.info("Mock audio capture started")

    def stop(self) -> None:
        """Stop generating audio"""
        if self.state != AudioCaptureState.RUNNING:
            return

        self.state = AudioCaptureState.STOPPING
        self._stop_event.set()

        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=2.0)

        self.state = AudioCaptureState.STOPPED
        logger.info("Mock audio capture stopped")

    def read_chunk(self, timeout: Optional[float] = None) -> Optional[bytes]:
        """Read one chunk of generated audio"""
        if self.state != AudioCaptureState.RUNNING:
            return None

        try:
            return self._audio_queue.get(timeout=timeout or 1.0)
        except Empty:
            return None

    def is_capturing(self) -> bool:
        """Check if capturing"""
        return self.state == AudioCaptureState.RUNNING

    def set_volume(self, volume: float) -> None:
        """Set generation volume"""
        self._volume = max(0.0, min(1.0, volume))

    def get_volume(self) -> float:
        """Get current volume"""
        return self._volume

    def _generate_audio_loop(self) -> None:
        """Main audio generation loop"""
        chunk_size = self.config.chunk_size
        sample_rate = self.config.sample_rate
        channels = self.config.channels

        # Calculate sleep time to maintain real-time pacing
        chunk_duration = chunk_size / sample_rate
        sleep_time = chunk_duration * 0.9  # Slightly faster to avoid underruns

        logger.info(f"Mock generation loop started: {chunk_size} samples @ {sample_rate}Hz")

        try:
            while not self._stop_event.is_set():
                start_time = time.time()

                # Generate audio chunk
                audio_chunk = self._generate_chunk(chunk_size, channels)

                # Update metrics
                self.metrics.chunks_captured += 1
                self.metrics.bytes_captured += len(audio_chunk)

                # Deliver audio
                if self._callback:
                    try:
                        self._callback(audio_chunk)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
                        self.metrics.errors += 1
                else:
                    # Queue for read_chunk()
                    try:
                        self._audio_queue.put_nowait(audio_chunk)
                    except:
                        self.metrics.buffer_overruns += 1

                # Maintain real-time pacing
                elapsed = time.time() - start_time
                if elapsed < sleep_time:
                    time.sleep(sleep_time - elapsed)

        except Exception as e:
            logger.error(f"Error in mock audio loop: {e}")
            self.metrics.errors += 1
            self.state = AudioCaptureState.ERROR

        logger.info("Mock generation loop stopped")

    def _generate_chunk(self, num_samples: int, channels: int) -> bytes:
        """Generate one chunk of audio based on pattern"""
        if self.pattern == "sine":
            return self._generate_sine_wave(num_samples, channels, frequency=440.0)
        elif self.pattern == "noise":
            return self._generate_white_noise(num_samples, channels)
        elif self.pattern == "silence":
            return self._generate_silence(num_samples, channels)
        elif self.pattern == "speech":
            return self._generate_speech_like(num_samples, channels)
        else:
            return self._generate_sine_wave(num_samples, channels)

    def _generate_sine_wave(
        self,
        num_samples: int,
        channels: int,
        frequency: float = 440.0
    ) -> bytes:
        """Generate sine wave"""
        sample_rate = self.config.sample_rate
        audio_bytes = bytearray()

        for i in range(num_samples):
            t = (self._sample_position + i) / sample_rate
            sample_value = math.sin(2 * math.pi * frequency * t) * self._volume

            # Convert to 16-bit PCM
            sample_int16 = int(sample_value * 32767)

            # Add for each channel
            for _ in range(channels):
                audio_bytes.extend(struct.pack('<h', sample_int16))

        self._sample_position += num_samples
        return bytes(audio_bytes)

    def _generate_white_noise(self, num_samples: int, channels: int) -> bytes:
        """Generate white noise"""
        import random
        audio_bytes = bytearray()

        for _ in range(num_samples):
            # Random value between -1 and 1
            sample_value = (random.random() * 2 - 1) * self._volume
            sample_int16 = int(sample_value * 32767)

            for _ in range(channels):
                audio_bytes.extend(struct.pack('<h', sample_int16))

        return bytes(audio_bytes)

    def _generate_silence(self, num_samples: int, channels: int) -> bytes:
        """Generate silence"""
        return bytes(num_samples * channels * 2)  # 2 bytes per sample

    def _generate_speech_like(self, num_samples: int, channels: int) -> bytes:
        """Generate speech-like pattern (multiple frequencies)"""
        sample_rate = self.config.sample_rate
        audio_bytes = bytearray()

        # Speech-like formants (simplified)
        formants = [500, 1500, 2500]  # F1, F2, F3
        weights = [0.5, 0.3, 0.2]

        for i in range(num_samples):
            t = (self._sample_position + i) / sample_rate

            # Combine formants
            sample_value = 0.0
            for freq, weight in zip(formants, weights):
                sample_value += math.sin(2 * math.pi * freq * t) * weight

            sample_value *= self._volume * 0.5  # Reduce amplitude
            sample_int16 = int(sample_value * 32767)

            for _ in range(channels):
                audio_bytes.extend(struct.pack('<h', sample_int16))

        self._sample_position += num_samples
        return bytes(audio_bytes)
