"""
STT (Speech-to-Text) Engine module.

Whisper Large V3 inference via FasterWhisper on NVIDIA CUDA GPUs.
"""

from .whisper_rtx import (
    WhisperRTXEngine,
    TranscriptionSegment,
    TranscriptionResult,
    create_engine,
)

__all__ = [
    "WhisperRTXEngine",
    "TranscriptionSegment",
    "TranscriptionResult",
    "create_engine",
]
