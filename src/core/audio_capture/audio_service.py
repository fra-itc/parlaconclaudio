"""
Integrated Audio Service for RTSTT Pipeline

This module provides a complete audio capture service that integrates:
- WASAPI audio capture
- Circular buffer management
- Silero VAD for voice detection
- Audio segmentation
- Redis publishing (optional)

Architecture:
    WASAPI Capture → Circular Buffer → VAD → Segmenter → Redis Producer

Author: ORCHIDEA Agent System
Created: 2025-11-21
"""

import threading
import queue
import logging
import time
import numpy as np
from typing import Optional, Callable, Dict, Any
from enum import Enum

from .wasapi_capture import WASAPICapture
from .circular_buffer import CircularBuffer
from .vad_silero import SileroVAD
from .vad_segmenter import VADSegmenter

logger = logging.getLogger(__name__)


class AudioServiceState(Enum):
    """Audio service state machine"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class AudioService:
    """
    Integrated audio capture service for RTSTT pipeline

    Architecture:
        WASAPI Capture → Circular Buffer → VAD → Segmenter → Redis Producer

    Features:
        - Real-time audio capture from Windows system audio
        - Voice Activity Detection with Silero VAD v4
        - Automatic speech segmentation
        - Thread-safe operation
        - Metrics and monitoring

    Example:
        >>> def on_segment(audio_segment):
        ...     print(f"Speech detected: {len(audio_segment)} samples")
        ...
        >>> service = AudioService(sample_rate=16000)
        >>> service.start(segment_callback=on_segment)
        >>> time.sleep(10)  # Capture for 10 seconds
        >>> service.stop()
    """

    def __init__(self,
                 sample_rate: int = 16000,
                 chunk_duration_ms: int = 100,
                 vad_threshold: float = 0.5,
                 min_speech_duration_ms: int = 250,
                 min_silence_duration_ms: int = 300,
                 buffer_capacity_seconds: float = 10.0,
                 redis_client = None):
        """
        Initialize audio service

        Args:
            sample_rate: Audio sample rate (16000 recommended for VAD)
            chunk_duration_ms: Audio chunk duration in milliseconds
            vad_threshold: VAD confidence threshold (0.0-1.0)
            min_speech_duration_ms: Minimum speech duration to keep
            min_silence_duration_ms: Minimum silence to segment
            buffer_capacity_seconds: Circular buffer capacity
            redis_client: Optional Redis client for segment publishing
        """
        self.sample_rate = sample_rate
        self.chunk_duration_ms = chunk_duration_ms
        self.redis_client = redis_client

        # Initialize components
        self.capture = WASAPICapture(
            sample_rate=sample_rate,
            channels=1,  # Mono for VAD
            chunk_duration_ms=chunk_duration_ms
        )

        self.buffer = CircularBuffer(
            capacity_seconds=buffer_capacity_seconds,
            sample_rate=sample_rate,
            channels=1
        )

        self.vad = SileroVAD(
            threshold=vad_threshold,
            sample_rate=sample_rate
        )

        self.segmenter = VADSegmenter(
            sample_rate=sample_rate,
            min_speech_duration_ms=min_speech_duration_ms,
            min_silence_duration_ms=min_silence_duration_ms
        )

        # State management
        self._state = AudioServiceState.STOPPED
        self._state_lock = threading.Lock()
        self._processing_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Metrics
        self._metrics = {
            'chunks_captured': 0,
            'chunks_processed': 0,
            'segments_detected': 0,
            'total_speech_duration': 0.0,
            'vad_speech_ratio': 0.0,
            'errors': 0
        }
        self._metrics_lock = threading.Lock()

        # Callbacks
        self._segment_callback: Optional[Callable[[np.ndarray], None]] = None

        logger.info(f"AudioService initialized: {sample_rate}Hz, {chunk_duration_ms}ms chunks")

    def start(self, segment_callback: Optional[Callable[[np.ndarray], None]] = None):
        """
        Start audio capture service

        Args:
            segment_callback: Callback function called when speech segment detected

        Raises:
            RuntimeError: If service fails to start
        """
        with self._state_lock:
            if self._state != AudioServiceState.STOPPED:
                logger.warning(f"Cannot start service in state {self._state}")
                return

            self._state = AudioServiceState.STARTING

        try:
            # Set callback
            self._segment_callback = segment_callback

            # Reset state
            self._stop_event.clear()
            self.buffer.clear()
            self.vad.reset()

            # Start capture
            self.capture.start(self._on_audio_chunk)

            # Start processing thread
            self._processing_thread = threading.Thread(
                target=self._processing_loop,
                name="AudioService-Processing",
                daemon=True
            )
            self._processing_thread.start()

            with self._state_lock:
                self._state = AudioServiceState.RUNNING

            logger.info("AudioService started successfully")

        except Exception as e:
            logger.error(f"Failed to start AudioService: {e}")
            with self._state_lock:
                self._state = AudioServiceState.ERROR
            raise

    def stop(self):
        """Stop audio capture service"""
        with self._state_lock:
            if self._state != AudioServiceState.RUNNING:
                logger.warning(f"Cannot stop service in state {self._state}")
                return

            self._state = AudioServiceState.STOPPING

        try:
            # Signal stop
            self._stop_event.set()

            # Stop capture
            self.capture.stop()

            # Wait for processing thread
            if self._processing_thread and self._processing_thread.is_alive():
                self._processing_thread.join(timeout=2.0)

            with self._state_lock:
                self._state = AudioServiceState.STOPPED

            logger.info("AudioService stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping AudioService: {e}")
            with self._state_lock:
                self._state = AudioServiceState.ERROR

    def _on_audio_chunk(self, audio_data: np.ndarray):
        """Callback from WASAPI capture - write to buffer"""
        try:
            # Convert to float32 and normalize
            if audio_data.dtype == np.int16:
                audio_float = audio_data.astype(np.float32) / 32768.0
            else:
                audio_float = audio_data.astype(np.float32)

            # Reshape for mono
            if audio_float.ndim == 1:
                audio_float = audio_float.reshape(-1, 1)

            # Write to buffer
            self.buffer.write(audio_float)

            with self._metrics_lock:
                self._metrics['chunks_captured'] += 1

        except Exception as e:
            logger.error(f"Error in audio chunk callback: {e}")
            with self._metrics_lock:
                self._metrics['errors'] += 1

    def _processing_loop(self):
        """Processing thread - read from buffer, run VAD, segment"""
        logger.info("Processing loop started")

        # VAD requires specific chunk sizes: 512 samples for 16kHz, 256 for 8kHz
        vad_chunk_size = 512 if self.sample_rate == 16000 else 256

        speech_frames = 0
        total_frames = 0

        while not self._stop_event.is_set():
            try:
                # Wait for data
                if self.buffer.available() < vad_chunk_size:
                    time.sleep(0.01)
                    continue

                # Read chunk
                audio_chunk = self.buffer.read(vad_chunk_size)
                if audio_chunk is None:
                    continue

                # Flatten to 1D for VAD
                audio_1d = audio_chunk.flatten()

                # Run VAD
                is_speech, confidence = self.vad.process_chunk(audio_1d)

                # Update metrics
                total_frames += 1
                if is_speech:
                    speech_frames += 1

                # Segment
                segments = self.segmenter.add_frame(audio_1d, is_speech)

                # Process segments
                for segment in segments:
                    self._on_segment_detected(segment)
                    with self._metrics_lock:
                        self._metrics['segments_detected'] += 1
                        self._metrics['total_speech_duration'] += len(segment) / self.sample_rate

                # Update metrics
                with self._metrics_lock:
                    self._metrics['chunks_processed'] += 1
                    if total_frames > 0:
                        self._metrics['vad_speech_ratio'] = speech_frames / total_frames

            except Exception as e:
                logger.error(f"Error in processing loop: {e}", exc_info=True)
                with self._metrics_lock:
                    self._metrics['errors'] += 1
                time.sleep(0.1)

        logger.info("Processing loop stopped")

    def _on_segment_detected(self, segment: np.ndarray):
        """Handle detected speech segment"""
        try:
            # Call callback if registered
            if self._segment_callback:
                self._segment_callback(segment)

            # Publish to Redis if available
            if self.redis_client:
                # Convert to bytes for Redis
                segment_bytes = segment.tobytes()
                # TODO: Implement Redis publishing with proper channel
                # self.redis_client.publish('audio:segments', segment_bytes)
                pass

        except Exception as e:
            logger.error(f"Error handling segment: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        with self._metrics_lock:
            return self._metrics.copy()

    def get_state(self) -> AudioServiceState:
        """Get current service state"""
        with self._state_lock:
            return self._state

    def is_running(self) -> bool:
        """Check if service is running"""
        return self.get_state() == AudioServiceState.RUNNING
