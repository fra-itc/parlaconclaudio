"""
Audio Capture Module for RTSTT

Cross-platform audio capture with driver abstraction layer.

Supports:
- Windows (WASAPI)
- Linux (PulseAudio, ALSA)
- WSL2 (WebSocket bridge)
- Mock driver for testing
"""

# Core abstraction layer (always available)
from .audio_capture_base import (
    AudioCaptureBase,
    AudioCaptureConfig,
    AudioCaptureState,
    AudioDevice as BaseAudioDevice,
    AudioFormat,
    AudioCaptureMetrics
)
from .platform_detector import (
    PlatformDetector,
    PlatformType,
    AudioSubsystem,
    PlatformInfo,
    detect_platform,
    is_wsl,
    get_recommended_driver
)
from .audio_factory import (
    AudioCaptureFactory,
    create_audio_capture
)

# Optional: Original WASAPI components (only if dependencies available)
try:
    from .circular_buffer import CircularBuffer
    from .audio_format import (
        convert_sample_rate,
        convert_to_mono,
        convert_to_stereo,
        normalize_audio,
        convert_int16_to_float32,
        convert_float32_to_int16,
        apply_gain,
        get_audio_stats
    )
    from .vad_silero import SileroVAD
    from .vad_segmenter import VADSegmenter
    _legacy_available = True
except ImportError:
    _legacy_available = False

# Optional: AudioService (requires VAD)
try:
    from .audio_service import AudioService, AudioServiceState
    _service_available = True
except ImportError:
    _service_available = False

__all__ = [
    # Core abstraction layer (always available)
    'AudioCaptureBase',
    'AudioCaptureConfig',
    'AudioCaptureState',
    'BaseAudioDevice',
    'AudioFormat',
    'AudioCaptureMetrics',
    'PlatformDetector',
    'PlatformType',
    'AudioSubsystem',
    'PlatformInfo',
    'detect_platform',
    'is_wsl',
    'get_recommended_driver',
    'AudioCaptureFactory',
    'create_audio_capture',
]

# Add legacy components if available
if _legacy_available:
    __all__.extend([
        'CircularBuffer',
        'convert_sample_rate',
        'convert_to_mono',
        'convert_to_stereo',
        'normalize_audio',
        'convert_int16_to_float32',
        'convert_float32_to_int16',
        'apply_gain',
        'get_audio_stats',
        'SileroVAD',
        'VADSegmenter',
    ])

if _service_available:
    __all__.extend(['AudioService', 'AudioServiceState'])

__version__ = '0.2.0'
