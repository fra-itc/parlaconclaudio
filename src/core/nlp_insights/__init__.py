"""
NLP Insights Module

This module provides NLP capabilities for real-time speech transcription,
including keyword extraction and speaker diarization.

Components:
    - KeywordExtractor: Extract keywords from transcribed text using KeyBERT
    - SpeakerDiarization: Identify and segment speakers using PyAnnote
"""

from .keyword_extractor import KeywordExtractor
from .speaker_diarization import SpeakerDiarization, SpeakerSegment

__all__ = [
    "KeywordExtractor",
    "SpeakerDiarization",
    "SpeakerSegment",
]

__version__ = "0.1.0"
