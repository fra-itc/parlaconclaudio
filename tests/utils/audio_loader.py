"""
Audio Loader Utility for Test Fixtures

Loads, validates, and prepares audio samples for testing.
Ensures all audio conforms to the required format: 16kHz, 16-bit PCM, mono.
"""

import numpy as np
import wave
from pathlib import Path
from typing import Optional, Union, List, Tuple
import struct


class AudioLoader:
    """Load and prepare audio samples for testing."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1, bit_depth: int = 16):
        """
        Initialize the audio loader.

        Args:
            sample_rate: Expected sample rate in Hz (default: 16000)
            channels: Expected number of channels (default: 1 - mono)
            bit_depth: Expected bit depth (default: 16)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.bit_depth = bit_depth

    def load_wav(self, filepath: Union[str, Path]) -> Tuple[np.ndarray, int, int, int]:
        """
        Load WAV file and return audio data with metadata.

        Args:
            filepath: Path to WAV file

        Returns:
            Tuple of (samples, sample_rate, channels, bit_depth)
            samples: Audio samples as numpy array (float32, normalized to [-1, 1])
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Audio file not found: {filepath}")

        with wave.open(str(filepath), 'rb') as wav_file:
            # Get audio parameters
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            num_frames = wav_file.getnframes()

            # Read raw audio data
            raw_data = wav_file.readframes(num_frames)

        # Convert to numpy array based on bit depth
        if sample_width == 2:  # 16-bit
            samples = np.frombuffer(raw_data, dtype=np.int16)
            samples = samples.astype(np.float32) / 32768.0  # Normalize to [-1, 1]
        elif sample_width == 1:  # 8-bit
            samples = np.frombuffer(raw_data, dtype=np.uint8)
            samples = (samples.astype(np.float32) - 128) / 128.0
        elif sample_width == 4:  # 32-bit
            samples = np.frombuffer(raw_data, dtype=np.int32)
            samples = samples.astype(np.float32) / 2147483648.0
        else:
            raise ValueError(f"Unsupported bit depth: {sample_width * 8}")

        # Handle stereo to mono conversion if needed
        if channels == 2:
            samples = samples.reshape(-1, 2)
            samples = np.mean(samples, axis=1)
            channels = 1

        bit_depth = sample_width * 8

        return samples, framerate, channels, bit_depth

    def ensure_format(
        self,
        samples: np.ndarray,
        current_rate: int,
        target_rate: Optional[int] = None,
        target_channels: int = 1
    ) -> np.ndarray:
        """
        Ensure audio is in the correct format (sample rate, channels).

        Args:
            samples: Audio samples
            current_rate: Current sample rate
            target_rate: Target sample rate (default: self.sample_rate)
            target_channels: Target number of channels (default: 1)

        Returns:
            Converted audio samples
        """
        if target_rate is None:
            target_rate = self.sample_rate

        # Resample if needed (simple linear interpolation)
        if current_rate != target_rate:
            samples = self._resample(samples, current_rate, target_rate)

        # Ensure mono
        if len(samples.shape) > 1 and samples.shape[1] > 1:
            samples = np.mean(samples, axis=1)

        return samples

    def _resample(self, samples: np.ndarray, current_rate: int, target_rate: int) -> np.ndarray:
        """
        Resample audio to target sample rate using linear interpolation.

        Args:
            samples: Audio samples
            current_rate: Current sample rate
            target_rate: Target sample rate

        Returns:
            Resampled audio
        """
        if current_rate == target_rate:
            return samples

        # Calculate new length
        duration = len(samples) / current_rate
        new_length = int(duration * target_rate)

        # Linear interpolation
        old_indices = np.linspace(0, len(samples) - 1, len(samples))
        new_indices = np.linspace(0, len(samples) - 1, new_length)
        resampled = np.interp(new_indices, old_indices, samples)

        return resampled

    def normalize(
        self,
        samples: np.ndarray,
        target_level: float = 0.5,
        method: str = "peak"
    ) -> np.ndarray:
        """
        Normalize audio levels.

        Args:
            samples: Audio samples
            target_level: Target amplitude level (0.0 to 1.0)
            method: Normalization method ("peak" or "rms")

        Returns:
            Normalized audio samples
        """
        if len(samples) == 0:
            return samples

        if method == "peak":
            # Peak normalization
            peak = np.max(np.abs(samples))
            if peak > 0:
                samples = samples * (target_level / peak)

        elif method == "rms":
            # RMS normalization
            rms = np.sqrt(np.mean(samples ** 2))
            if rms > 0:
                samples = samples * (target_level / rms)

        else:
            raise ValueError(f"Unknown normalization method: {method}")

        # Clip to [-1, 1] to prevent overflow
        samples = np.clip(samples, -1.0, 1.0)

        return samples

    def chunk_audio(
        self,
        samples: np.ndarray,
        chunk_duration_ms: int = 100,
        sample_rate: Optional[int] = None
    ) -> List[np.ndarray]:
        """
        Split audio into chunks for streaming tests.

        Args:
            samples: Audio samples
            chunk_duration_ms: Chunk duration in milliseconds
            sample_rate: Sample rate (default: self.sample_rate)

        Returns:
            List of audio chunks
        """
        if sample_rate is None:
            sample_rate = self.sample_rate

        # Calculate chunk size in samples
        chunk_size = int(sample_rate * chunk_duration_ms / 1000)

        # Split into chunks
        chunks = []
        for i in range(0, len(samples), chunk_size):
            chunk = samples[i:i + chunk_size]
            chunks.append(chunk)

        return chunks

    def to_int16(self, samples: np.ndarray) -> np.ndarray:
        """
        Convert float32 samples to int16 (PCM format).

        Args:
            samples: Float32 audio samples (normalized to [-1, 1])

        Returns:
            Int16 audio samples
        """
        # Clip to prevent overflow
        samples = np.clip(samples, -1.0, 1.0)

        # Convert to int16
        samples_int16 = np.int16(samples * 32767)

        return samples_int16

    def to_bytes(self, samples: np.ndarray) -> bytes:
        """
        Convert samples to bytes for network transmission.

        Args:
            samples: Audio samples (float32 or int16)

        Returns:
            Audio data as bytes
        """
        # Convert to int16 if needed
        if samples.dtype == np.float32:
            samples = self.to_int16(samples)

        return samples.tobytes()

    def from_bytes(self, data: bytes, dtype: str = "int16") -> np.ndarray:
        """
        Convert bytes to audio samples.

        Args:
            data: Audio data as bytes
            dtype: Data type ("int16" or "float32")

        Returns:
            Audio samples as numpy array
        """
        if dtype == "int16":
            samples = np.frombuffer(data, dtype=np.int16)
            # Convert to float32 normalized
            samples = samples.astype(np.float32) / 32768.0
        elif dtype == "float32":
            samples = np.frombuffer(data, dtype=np.float32)
        else:
            raise ValueError(f"Unsupported dtype: {dtype}")

        return samples

    def calculate_rms(self, samples: np.ndarray) -> float:
        """
        Calculate RMS (Root Mean Square) level of audio.

        Args:
            samples: Audio samples

        Returns:
            RMS level
        """
        if len(samples) == 0:
            return 0.0

        rms = np.sqrt(np.mean(samples ** 2))
        return float(rms)

    def calculate_peak(self, samples: np.ndarray) -> float:
        """
        Calculate peak level of audio.

        Args:
            samples: Audio samples

        Returns:
            Peak level
        """
        if len(samples) == 0:
            return 0.0

        peak = np.max(np.abs(samples))
        return float(peak)

    def calculate_duration(self, samples: np.ndarray, sample_rate: Optional[int] = None) -> float:
        """
        Calculate duration of audio in seconds.

        Args:
            samples: Audio samples
            sample_rate: Sample rate (default: self.sample_rate)

        Returns:
            Duration in seconds
        """
        if sample_rate is None:
            sample_rate = self.sample_rate

        duration = len(samples) / sample_rate
        return duration

    def validate_format(self, filepath: Union[str, Path]) -> dict:
        """
        Validate audio file format and return metadata.

        Args:
            filepath: Path to audio file

        Returns:
            Dictionary with validation results and metadata
        """
        try:
            samples, sample_rate, channels, bit_depth = self.load_wav(filepath)

            result = {
                "valid": True,
                "filepath": str(filepath),
                "sample_rate": sample_rate,
                "channels": channels,
                "bit_depth": bit_depth,
                "duration": self.calculate_duration(samples, sample_rate),
                "num_samples": len(samples),
                "rms_level": self.calculate_rms(samples),
                "peak_level": self.calculate_peak(samples),
                "errors": [],
                "warnings": []
            }

            # Check format requirements
            if sample_rate != self.sample_rate:
                result["warnings"].append(
                    f"Sample rate {sample_rate} Hz does not match expected {self.sample_rate} Hz"
                )

            if channels != self.channels:
                result["warnings"].append(
                    f"Channel count {channels} does not match expected {self.channels}"
                )

            if bit_depth != self.bit_depth:
                result["warnings"].append(
                    f"Bit depth {bit_depth} does not match expected {self.bit_depth}"
                )

            return result

        except Exception as e:
            return {
                "valid": False,
                "filepath": str(filepath),
                "errors": [str(e)],
                "warnings": []
            }

    def load_fixture(self, filename: str, fixture_type: str = "generated") -> np.ndarray:
        """
        Load audio fixture by name.

        Args:
            filename: Fixture filename
            fixture_type: Type of fixture ("generated" or "samples")

        Returns:
            Audio samples
        """
        fixtures_dir = Path(__file__).parent.parent / "fixtures" / "audio" / fixture_type
        filepath = fixtures_dir / filename

        samples, sample_rate, channels, bit_depth = self.load_wav(filepath)

        # Ensure correct format
        samples = self.ensure_format(samples, sample_rate)

        return samples


if __name__ == "__main__":
    # Example usage and validation
    loader = AudioLoader()

    # Validate all fixtures
    fixtures_dir = Path(__file__).parent.parent / "fixtures" / "audio" / "generated"
    if fixtures_dir.exists():
        print("Validating audio fixtures:")
        for filepath in fixtures_dir.glob("*.wav"):
            result = loader.validate_format(filepath)
            status = "✓" if result["valid"] else "✗"
            print(f"  {status} {filepath.name}")
            if result["warnings"]:
                for warning in result["warnings"]:
                    print(f"    ⚠ {warning}")
            if result["errors"]:
                for error in result["errors"]:
                    print(f"    ✗ {error}")
