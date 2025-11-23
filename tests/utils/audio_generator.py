"""
Audio Generator Utility for Test Fixtures

Generates synthetic audio samples for testing the real-time audio pipeline.
All generated audio conforms to the required format: 16kHz, 16-bit PCM, mono.
"""

import numpy as np
import wave
import struct
from pathlib import Path
from typing import Optional


class AudioGenerator:
    """Generate synthetic audio samples for testing."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1, bit_depth: int = 16):
        """
        Initialize the audio generator.

        Args:
            sample_rate: Sample rate in Hz (default: 16000)
            channels: Number of audio channels (default: 1 - mono)
            bit_depth: Bit depth of audio (default: 16)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.bit_depth = bit_depth
        self.max_amplitude = 2 ** (bit_depth - 1) - 1

    def _save_wav(self, samples: np.ndarray, filename: str, output_dir: Optional[str] = None):
        """
        Save audio samples to WAV file.

        Args:
            samples: Audio samples as numpy array
            filename: Output filename
            output_dir: Output directory (default: tests/fixtures/audio/generated/)
        """
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "fixtures" / "audio" / "generated"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / filename

        # Normalize to int16 range
        samples_int16 = np.int16(samples * self.max_amplitude)

        with wave.open(str(filepath), 'w') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(self.bit_depth // 8)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(samples_int16.tobytes())

        return filepath

    def generate_sine_wave(
        self,
        duration: float,
        frequency: float,
        amplitude: float = 0.5,
        filename: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate a sine wave (test tone).

        Args:
            duration: Duration in seconds
            frequency: Frequency in Hz
            amplitude: Amplitude (0.0 to 1.0)
            filename: Output filename (if provided, saves to file)
            output_dir: Output directory

        Returns:
            Audio samples as numpy array
        """
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        samples = amplitude * np.sin(2 * np.pi * frequency * t)

        if filename:
            self._save_wav(samples, filename, output_dir)

        return samples

    def generate_silence(
        self,
        duration: float,
        filename: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate silence (zeros).

        Args:
            duration: Duration in seconds
            filename: Output filename (if provided, saves to file)
            output_dir: Output directory

        Returns:
            Audio samples as numpy array
        """
        num_samples = int(self.sample_rate * duration)
        samples = np.zeros(num_samples, dtype=np.float32)

        if filename:
            self._save_wav(samples, filename, output_dir)

        return samples

    def generate_white_noise(
        self,
        duration: float,
        amplitude: float = 0.3,
        filename: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate white noise.

        Args:
            duration: Duration in seconds
            amplitude: Amplitude (0.0 to 1.0)
            filename: Output filename (if provided, saves to file)
            output_dir: Output directory

        Returns:
            Audio samples as numpy array
        """
        num_samples = int(self.sample_rate * duration)
        samples = amplitude * np.random.uniform(-1.0, 1.0, num_samples)

        if filename:
            self._save_wav(samples, filename, output_dir)

        return samples

    def generate_pink_noise(
        self,
        duration: float,
        amplitude: float = 0.3,
        filename: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate pink noise (1/f noise) - more realistic than white noise.

        Args:
            duration: Duration in seconds
            amplitude: Amplitude (0.0 to 1.0)
            filename: Output filename (if provided, saves to file)
            output_dir: Output directory

        Returns:
            Audio samples as numpy array
        """
        num_samples = int(self.sample_rate * duration)

        # Generate white noise
        white = np.random.randn(num_samples)

        # Apply pink noise filter (simple approximation)
        # Using Voss-McCartney algorithm approximation
        pink = np.zeros(num_samples)
        num_generators = 16
        generators = np.zeros(num_generators)

        for i in range(num_samples):
            # Update generators based on bit patterns
            for j in range(num_generators):
                if i % (2 ** j) == 0:
                    generators[j] = np.random.randn()
            pink[i] = np.sum(generators)

        # Normalize
        pink = pink / np.max(np.abs(pink))
        samples = amplitude * pink

        if filename:
            self._save_wav(samples, filename, output_dir)

        return samples

    def generate_speech_like_pattern(
        self,
        duration: float,
        amplitude: float = 0.5,
        filename: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate speech-like audio pattern (multiple frequency components).

        Simulates formants and speech characteristics for VAD testing.

        Args:
            duration: Duration in seconds
            amplitude: Amplitude (0.0 to 1.0)
            filename: Output filename (if provided, saves to file)
            output_dir: Output directory

        Returns:
            Audio samples as numpy array
        """
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)

        # Simulate speech formants (F1, F2, F3)
        f1 = 800  # First formant
        f2 = 1200  # Second formant
        f3 = 2400  # Third formant

        # Fundamental frequency (pitch)
        f0 = 120

        # Generate components
        fundamental = 0.4 * np.sin(2 * np.pi * f0 * t)
        formant1 = 0.3 * np.sin(2 * np.pi * f1 * t)
        formant2 = 0.2 * np.sin(2 * np.pi * f2 * t)
        formant3 = 0.1 * np.sin(2 * np.pi * f3 * t)

        # Combine components
        samples = fundamental + formant1 + formant2 + formant3

        # Add envelope (speech amplitude variation)
        envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)  # 3 Hz modulation
        samples = samples * envelope

        # Normalize
        samples = samples / np.max(np.abs(samples))
        samples = amplitude * samples

        if filename:
            self._save_wav(samples, filename, output_dir)

        return samples

    def generate_mixed_content(
        self,
        patterns: list,
        filename: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate mixed content by concatenating different patterns.

        Args:
            patterns: List of (type, duration, params) tuples
                     Example: [("speech", 2.0, {}), ("silence", 1.0, {}), ("speech", 2.0, {})]
            filename: Output filename (if provided, saves to file)
            output_dir: Output directory

        Returns:
            Audio samples as numpy array
        """
        segments = []

        for pattern_type, duration, params in patterns:
            if pattern_type == "speech":
                segment = self.generate_speech_like_pattern(duration, **params)
            elif pattern_type == "silence":
                segment = self.generate_silence(duration)
            elif pattern_type == "noise":
                segment = self.generate_white_noise(duration, **params)
            elif pattern_type == "tone":
                segment = self.generate_sine_wave(duration, **params)
            else:
                raise ValueError(f"Unknown pattern type: {pattern_type}")

            segments.append(segment)

        # Concatenate all segments
        samples = np.concatenate(segments)

        if filename:
            self._save_wav(samples, filename, output_dir)

        return samples

    def generate_empty_file(
        self,
        filename: str = "empty_0s.wav",
        output_dir: Optional[str] = None
    ):
        """
        Generate an empty WAV file (edge case for testing).

        Args:
            filename: Output filename
            output_dir: Output directory
        """
        samples = np.array([], dtype=np.float32)
        self._save_wav(samples, filename, output_dir)

    def generate_test_suite(self, output_dir: Optional[str] = None):
        """
        Generate complete test suite of audio fixtures.

        Args:
            output_dir: Output directory (default: tests/fixtures/audio/generated/)
        """
        print("Generating audio test fixtures...")

        # Speech samples
        print("  - speech_5s.wav (speech-like pattern)")
        self.generate_speech_like_pattern(5.0, filename="speech_5s.wav", output_dir=output_dir)

        # Silence samples
        print("  - silence_2s.wav")
        self.generate_silence(2.0, filename="silence_2s.wav", output_dir=output_dir)

        print("  - silence_10s.wav")
        self.generate_silence(10.0, filename="silence_10s.wav", output_dir=output_dir)

        # Noise samples
        print("  - noise_3s.wav (white noise)")
        self.generate_white_noise(3.0, filename="noise_3s.wav", output_dir=output_dir)

        print("  - noise_pink.wav (pink noise)")
        self.generate_pink_noise(3.0, filename="noise_pink.wav", output_dir=output_dir)

        # Mixed content
        print("  - mixed_speech_silence.wav")
        self.generate_mixed_content(
            [
                ("speech", 2.0, {}),
                ("silence", 1.0, {}),
                ("speech", 2.0, {})
            ],
            filename="mixed_speech_silence.wav",
            output_dir=output_dir
        )

        # Test tones
        print("  - test_tone_440hz.wav")
        self.generate_sine_wave(2.0, 440, filename="test_tone_440hz.wav", output_dir=output_dir)

        # Edge cases
        print("  - very_quiet.wav")
        self.generate_speech_like_pattern(3.0, amplitude=0.05, filename="very_quiet.wav", output_dir=output_dir)

        print("  - very_loud.wav")
        self.generate_speech_like_pattern(3.0, amplitude=0.95, filename="very_loud.wav", output_dir=output_dir)

        print("  - empty_0s.wav")
        self.generate_empty_file(filename="empty_0s.wav", output_dir=output_dir)

        print("Audio test fixtures generated successfully!")


if __name__ == "__main__":
    # Generate all test fixtures
    generator = AudioGenerator(sample_rate=16000)
    generator.generate_test_suite()
