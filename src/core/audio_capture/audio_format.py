"""
Audio Format Conversion Utilities

Provides efficient audio format conversions including:
- Sample rate conversion (resampling)
- Channel conversion (stereo <-> mono)
- Audio normalization

Author: ORCHIDEA Agent System
Created: 2025-11-21
"""

import numpy as np
import scipy.signal as signal
import logging

logger = logging.getLogger(__name__)


def convert_sample_rate(audio: np.ndarray,
                        source_rate: int,
                        target_rate: int) -> np.ndarray:
    """
    Resample audio to target sample rate using high-quality resampling

    Args:
        audio: Input audio array (samples,) or (samples, channels)
        source_rate: Source sample rate in Hz
        target_rate: Target sample rate in Hz

    Returns:
        Resampled audio array

    Example:
        >>> audio_48k = np.random.randn(48000)  # 1 second at 48kHz
        >>> audio_16k = convert_sample_rate(audio_48k, 48000, 16000)
        >>> len(audio_16k)
        16000
    """
    if source_rate == target_rate:
        return audio

    if source_rate <= 0 or target_rate <= 0:
        raise ValueError(f"Invalid sample rates: source={source_rate}, target={target_rate}")

    try:
        # Calculate target number of samples
        num_samples = int(len(audio) * target_rate / source_rate)

        # Use scipy's high-quality resampling
        if audio.ndim == 1:
            # Mono audio
            resampled = signal.resample(audio, num_samples)
        else:
            # Multi-channel audio - resample each channel
            resampled = np.zeros((num_samples, audio.shape[1]), dtype=audio.dtype)
            for ch in range(audio.shape[1]):
                resampled[:, ch] = signal.resample(audio[:, ch], num_samples)

        logger.debug(f"Resampled audio: {source_rate}Hz -> {target_rate}Hz "
                    f"({len(audio)} -> {len(resampled)} samples)")

        return resampled

    except Exception as e:
        logger.error(f"Resampling failed: {e}")
        raise


def convert_to_mono(audio: np.ndarray) -> np.ndarray:
    """
    Convert stereo (or multi-channel) audio to mono by averaging channels

    Args:
        audio: Input audio array (samples,) or (samples, channels)

    Returns:
        Mono audio array (samples,)

    Example:
        >>> stereo = np.random.randn(1000, 2)
        >>> mono = convert_to_mono(stereo)
        >>> mono.shape
        (1000,)
    """
    if audio.ndim == 1:
        # Already mono
        return audio

    if audio.ndim == 2:
        # Multi-channel - average across channels
        mono = audio.mean(axis=1)
        logger.debug(f"Converted {audio.shape[1]} channels to mono")
        return mono

    raise ValueError(f"Unsupported audio shape: {audio.shape}")


def convert_to_stereo(audio: np.ndarray) -> np.ndarray:
    """
    Convert mono audio to stereo by duplicating the channel

    Args:
        audio: Input mono audio array (samples,)

    Returns:
        Stereo audio array (samples, 2)

    Example:
        >>> mono = np.random.randn(1000)
        >>> stereo = convert_to_stereo(mono)
        >>> stereo.shape
        (1000, 2)
    """
    if audio.ndim == 2:
        # Already multi-channel
        return audio

    if audio.ndim == 1:
        # Create stereo by duplicating
        stereo = np.stack([audio, audio], axis=1)
        logger.debug("Converted mono to stereo")
        return stereo

    raise ValueError(f"Unsupported audio shape: {audio.shape}")


def normalize_audio(audio: np.ndarray,
                   target_level: float = -20.0,
                   headroom_db: float = 3.0) -> np.ndarray:
    """
    Normalize audio to target RMS level in dB

    Args:
        audio: Input audio array (any shape)
        target_level: Target RMS level in dB (e.g., -20.0)
        headroom_db: Headroom below 0 dBFS to prevent clipping

    Returns:
        Normalized audio array (same shape as input)

    Example:
        >>> audio = np.random.randn(1000) * 100  # Loud audio
        >>> normalized = normalize_audio(audio, target_level=-20.0)
        >>> # Audio is now normalized to -20 dBFS RMS
    """
    if len(audio) == 0:
        return audio

    # Convert to float for processing
    audio_float = audio.astype(np.float32)

    # Calculate RMS
    rms = np.sqrt(np.mean(audio_float ** 2))

    if rms < 1e-10:  # Silence threshold
        logger.warning("Audio is silent, skipping normalization")
        return audio_float

    # Calculate target RMS from dB
    target_rms = 10 ** (target_level / 20.0)

    # Calculate gain
    gain = target_rms / rms

    # Apply gain
    normalized = audio_float * gain

    # Apply soft clipping if needed to prevent hard clipping
    max_val = 10 ** (-headroom_db / 20.0)
    if np.max(np.abs(normalized)) > max_val:
        logger.warning(f"Audio exceeds headroom, applying soft clipping")
        normalized = np.tanh(normalized / max_val) * max_val

    logger.debug(f"Normalized audio: RMS {20*np.log10(rms):.1f}dB -> "
                f"{20*np.log10(target_rms):.1f}dB (gain: {20*np.log10(gain):.1f}dB)")

    return normalized


def convert_int16_to_float32(audio: np.ndarray) -> np.ndarray:
    """
    Convert int16 audio to float32 normalized to [-1.0, 1.0]

    Args:
        audio: Input audio as int16

    Returns:
        Audio as float32 in range [-1.0, 1.0]

    Example:
        >>> audio_int = np.array([0, 16384, -16384], dtype=np.int16)
        >>> audio_float = convert_int16_to_float32(audio_int)
        >>> audio_float.dtype
        dtype('float32')
    """
    if audio.dtype != np.int16:
        logger.warning(f"Expected int16, got {audio.dtype}")

    # Normalize to [-1.0, 1.0]
    audio_float = audio.astype(np.float32) / 32768.0
    return audio_float


def convert_float32_to_int16(audio: np.ndarray) -> np.ndarray:
    """
    Convert float32 audio to int16

    Args:
        audio: Input audio as float32 (should be in range [-1.0, 1.0])

    Returns:
        Audio as int16

    Example:
        >>> audio_float = np.array([0.0, 0.5, -0.5], dtype=np.float32)
        >>> audio_int = convert_float32_to_int16(audio_float)
        >>> audio_int.dtype
        dtype('int16')
    """
    if audio.dtype != np.float32:
        logger.warning(f"Expected float32, got {audio.dtype}")

    # Clip to valid range
    audio_clipped = np.clip(audio, -1.0, 1.0)

    # Scale to int16 range
    audio_int = (audio_clipped * 32767.0).astype(np.int16)
    return audio_int


def apply_gain(audio: np.ndarray, gain_db: float) -> np.ndarray:
    """
    Apply gain to audio in dB

    Args:
        audio: Input audio array
        gain_db: Gain in decibels (positive = louder, negative = quieter)

    Returns:
        Audio with gain applied

    Example:
        >>> audio = np.random.randn(1000)
        >>> louder = apply_gain(audio, 6.0)  # +6dB louder
        >>> quieter = apply_gain(audio, -6.0)  # -6dB quieter
    """
    # Convert dB to linear gain
    gain_linear = 10 ** (gain_db / 20.0)

    # Apply gain
    return audio * gain_linear


def get_audio_stats(audio: np.ndarray) -> dict:
    """
    Get statistics about audio signal

    Args:
        audio: Input audio array

    Returns:
        Dictionary with audio statistics

    Example:
        >>> audio = np.random.randn(1000)
        >>> stats = get_audio_stats(audio)
        >>> print(stats['rms_db'])
    """
    if len(audio) == 0:
        return {
            'samples': 0,
            'rms': 0.0,
            'rms_db': -np.inf,
            'peak': 0.0,
            'peak_db': -np.inf
        }

    # Calculate RMS
    rms = np.sqrt(np.mean(audio ** 2))
    rms_db = 20 * np.log10(rms) if rms > 1e-10 else -np.inf

    # Calculate peak
    peak = np.max(np.abs(audio))
    peak_db = 20 * np.log10(peak) if peak > 1e-10 else -np.inf

    return {
        'samples': len(audio),
        'rms': float(rms),
        'rms_db': float(rms_db),
        'peak': float(peak),
        'peak_db': float(peak_db),
        'dtype': str(audio.dtype),
        'shape': audio.shape
    }
