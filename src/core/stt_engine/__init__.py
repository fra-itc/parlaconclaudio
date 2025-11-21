"""
STT (Speech-to-Text) Engine module.

Provides optimized Whisper Large V3 inference for real-time transcription
on NVIDIA RTX GPUs using FasterWhisper with TensorRT optimization.
"""

from .whisper_rtx import (
    WhisperRTXEngine,
    TranscriptionSegment,
    TranscriptionResult,
    create_engine
)
from .model_setup import (
    download_whisper_model,
    verify_model_exists,
    get_model_cache_dir
)

__all__ = [
    "WhisperRTXEngine",
    "TranscriptionSegment",
    "TranscriptionResult",
    "create_engine",
    "download_whisper_model",
    "verify_model_exists",
    "get_model_cache_dir",
]
