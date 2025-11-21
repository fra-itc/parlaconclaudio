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
