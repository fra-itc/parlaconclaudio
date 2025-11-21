"""
Audio Capture Module for ORCHIDEA RTSTT

This module provides WASAPI-based audio capture for Windows 11,
with device enumeration and audio format conversion utilities.

Author: ORCHIDEA Agent System
Created: 2025-11-21
"""

from .circular_buffer import CircularBuffer
from .wasapi_capture import WASAPICapture
from .wasapi_devices import (
    AudioDevice,
    list_audio_devices,
    get_default_device,
    get_device_by_id,
    get_device_by_name
)
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
from .audio_service import AudioService, AudioServiceState

__all__ = [
    # Buffer
    'CircularBuffer',

    # Capture
    'WASAPICapture',

    # Devices
    'AudioDevice',
    'list_audio_devices',
    'get_default_device',
    'get_device_by_id',
    'get_device_by_name',

    # Format conversion
    'convert_sample_rate',
    'convert_to_mono',
    'convert_to_stereo',
    'normalize_audio',
    'convert_int16_to_float32',
    'convert_float32_to_int16',
    'apply_gain',
    'get_audio_stats',

    # VAD and Segmentation
    'SileroVAD',
    'VADSegmenter',

    # Integrated Service
    'AudioService',
    'AudioServiceState',
]

__version__ = '0.1.0'
