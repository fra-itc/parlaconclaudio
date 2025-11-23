import numpy as np
from collections import deque
from typing import List

class VADSegmenter:
    """Segment audio based on VAD output"""

    def __init__(self,
                 sample_rate: int,
                 min_speech_duration_ms: int = 250,
                 min_silence_duration_ms: int = 100):
        self.sample_rate = sample_rate
        self.min_speech_samples = int(min_speech_duration_ms * sample_rate / 1000)
        self.min_silence_samples = int(min_silence_duration_ms * sample_rate / 1000)

        self._buffer = deque()
        self._in_speech = False
        self._silence_duration = 0

    def add_frame(self, audio: np.ndarray, is_speech: bool) -> List[np.ndarray]:
        """Add VAD frame and return complete segments"""
        segments = []

        self._buffer.append((audio, is_speech))

        if is_speech:
            if not self._in_speech:
                self._in_speech = True
                self._silence_duration = 0
        else:
            if self._in_speech:
                self._silence_duration += len(audio)

                if self._silence_duration >= self.min_silence_samples:
                    # Extract segment
                    audio_chunks = [chunk for chunk, _ in self._buffer]
                    segment = np.concatenate(audio_chunks)

                    if len(segment) >= self.min_speech_samples:
                        segments.append(segment)

                    self._in_speech = False
                    self._buffer.clear()

        return segments
