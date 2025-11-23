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
