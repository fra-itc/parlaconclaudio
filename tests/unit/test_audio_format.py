"""
Unit tests for audio format conversion utilities

Tests sample rate conversion, channel conversion, and normalization.

Author: ORCHIDEA Agent System
Created: 2025-11-21
"""

import pytest
import numpy as np
from src.core.audio_capture.audio_format import (
    convert_sample_rate,
    convert_to_mono,
    convert_to_stereo,
    normalize_audio,
    convert_int16_to_float32,
    convert_float32_to_int16,
    apply_gain,
    get_audio_stats
)


class TestConvertSampleRate:
    """Test sample rate conversion"""

    def test_same_rate(self):
        """Test when source and target rates are the same"""
        audio = np.random.randn(1000)
        result = convert_sample_rate(audio, 48000, 48000)
        np.testing.assert_array_equal(result, audio)

    def test_downsample(self):
        """Test downsampling (48kHz -> 16kHz)"""
        audio = np.random.randn(48000)
        result = convert_sample_rate(audio, 48000, 16000)
        # Should have ~16000 samples (1 second)
        assert len(result) == 16000

    def test_upsample(self):
        """Test upsampling (16kHz -> 48kHz)"""
        audio = np.random.randn(16000)
        result = convert_sample_rate(audio, 16000, 48000)
        # Should have ~48000 samples
        assert len(result) == 48000

    def test_stereo_resample(self):
        """Test resampling stereo audio"""
        audio = np.random.randn(48000, 2)  # Stereo
        result = convert_sample_rate(audio, 48000, 16000)
        assert result.shape == (16000, 2)

    def test_invalid_rates(self):
        """Test with invalid sample rates"""
        audio = np.random.randn(1000)
        with pytest.raises(ValueError):
            convert_sample_rate(audio, 0, 48000)
        with pytest.raises(ValueError):
            convert_sample_rate(audio, 48000, -1)


class TestConvertToMono:
    """Test stereo to mono conversion"""

    def test_already_mono(self):
        """Test with already mono audio"""
        audio = np.random.randn(1000)
        result = convert_to_mono(audio)
        np.testing.assert_array_equal(result, audio)

    def test_stereo_to_mono(self):
        """Test converting stereo to mono"""
        left = np.ones(1000)
        right = np.ones(1000) * 2
        stereo = np.stack([left, right], axis=1)

        result = convert_to_mono(stereo)

        # Should average to 1.5
        np.testing.assert_array_almost_equal(result, np.ones(1000) * 1.5)

    def test_multi_channel(self):
        """Test with multi-channel audio"""
        audio = np.random.randn(1000, 4)  # 4 channels
        result = convert_to_mono(audio)
        assert result.shape == (1000,)

    def test_invalid_shape(self):
        """Test with invalid shape"""
        audio = np.random.randn(10, 10, 10)  # 3D array
        with pytest.raises(ValueError):
            convert_to_mono(audio)


class TestConvertToStereo:
    """Test mono to stereo conversion"""

    def test_mono_to_stereo(self):
        """Test converting mono to stereo"""
        mono = np.random.randn(1000)
        stereo = convert_to_stereo(mono)

        assert stereo.shape == (1000, 2)
        # Both channels should be identical
        np.testing.assert_array_equal(stereo[:, 0], stereo[:, 1])

    def test_already_stereo(self):
        """Test with already stereo audio"""
        stereo = np.random.randn(1000, 2)
        result = convert_to_stereo(stereo)
        np.testing.assert_array_equal(result, stereo)

    def test_invalid_shape(self):
        """Test with invalid shape"""
        audio = np.random.randn(10, 10, 10)
        with pytest.raises(ValueError):
            convert_to_stereo(audio)


class TestNormalizeAudio:
    """Test audio normalization"""

    def test_normalize_to_target(self):
        """Test normalizing to target level"""
        # Create loud audio
        audio = np.random.randn(1000) * 100

        # Normalize to -20 dB
        normalized = normalize_audio(audio, target_level=-20.0)

        # Calculate RMS
        rms = np.sqrt(np.mean(normalized ** 2))
        rms_db = 20 * np.log10(rms)

        # Should be close to -20 dB
        assert abs(rms_db - (-20.0)) < 1.0

    def test_normalize_silent_audio(self):
        """Test with silent audio"""
        audio = np.zeros(1000)
        result = normalize_audio(audio)
        # Should remain silent
        np.testing.assert_array_equal(result, audio)

    def test_normalize_with_headroom(self):
        """Test normalization with headroom"""
        audio = np.random.randn(1000) * 100
        normalized = normalize_audio(audio, target_level=-10.0, headroom_db=6.0)

        # Peak should not exceed -6 dBFS
        peak = np.max(np.abs(normalized))
        peak_db = 20 * np.log10(peak)
        assert peak_db < -5.0  # Should have headroom

    def test_normalize_int16(self):
        """Test normalizing int16 audio"""
        audio = np.random.randint(-32768, 32767, 1000, dtype=np.int16)
        normalized = normalize_audio(audio, target_level=-20.0)
        assert normalized.dtype == np.float32


class TestInt16Float32Conversion:
    """Test int16 <-> float32 conversions"""

    def test_int16_to_float32(self):
        """Test converting int16 to float32"""
        audio_int = np.array([0, 16384, -16384, 32767, -32768], dtype=np.int16)
        audio_float = convert_int16_to_float32(audio_int)

        assert audio_float.dtype == np.float32
        # 0 should map to 0.0
        assert audio_float[0] == 0.0
        # 16384 should map to ~0.5
        assert abs(audio_float[1] - 0.5) < 0.01
        # -16384 should map to ~-0.5
        assert abs(audio_float[2] - (-0.5)) < 0.01
        # Values should be in range [-1, 1]
        assert np.all(audio_float >= -1.0)
        assert np.all(audio_float <= 1.0)

    def test_float32_to_int16(self):
        """Test converting float32 to int16"""
        audio_float = np.array([0.0, 0.5, -0.5, 1.0, -1.0], dtype=np.float32)
        audio_int = convert_float32_to_int16(audio_float)

        assert audio_int.dtype == np.int16
        # 0.0 should map to 0
        assert audio_int[0] == 0
        # 0.5 should map to ~16383
        assert abs(audio_int[1] - 16383) < 10
        # 1.0 should map to 32767
        assert audio_int[3] == 32767

    def test_float32_to_int16_clipping(self):
        """Test clipping out-of-range values"""
        audio_float = np.array([2.0, -2.0], dtype=np.float32)  # Out of range
        audio_int = convert_float32_to_int16(audio_float)

        # Should be clipped to valid range
        assert audio_int[0] == 32767
        assert audio_int[1] == -32767

    def test_roundtrip_conversion(self):
        """Test int16 -> float32 -> int16 roundtrip"""
        original = np.array([0, 1000, -1000, 10000, -10000], dtype=np.int16)
        float_audio = convert_int16_to_float32(original)
        roundtrip = convert_float32_to_int16(float_audio)

        # Should be very close (within rounding error)
        np.testing.assert_array_almost_equal(roundtrip, original, decimal=0)


class TestApplyGain:
    """Test gain application"""

    def test_positive_gain(self):
        """Test applying positive gain"""
        audio = np.ones(1000)
        gained = apply_gain(audio, 6.0)  # +6 dB

        # +6 dB is ~2x amplitude
        expected = audio * 2.0
        np.testing.assert_array_almost_equal(gained, expected, decimal=1)

    def test_negative_gain(self):
        """Test applying negative gain"""
        audio = np.ones(1000)
        gained = apply_gain(audio, -6.0)  # -6 dB

        # -6 dB is ~0.5x amplitude
        expected = audio * 0.5
        np.testing.assert_array_almost_equal(gained, expected, decimal=1)

    def test_zero_gain(self):
        """Test zero gain (0 dB)"""
        audio = np.random.randn(1000)
        gained = apply_gain(audio, 0.0)

        # Should be unchanged
        np.testing.assert_array_almost_equal(gained, audio)


class TestGetAudioStats:
    """Test audio statistics"""

    def test_stats_normal_audio(self):
        """Test stats with normal audio"""
        audio = np.random.randn(1000)
        stats = get_audio_stats(audio)

        assert stats['samples'] == 1000
        assert 'rms' in stats
        assert 'rms_db' in stats
        assert 'peak' in stats
        assert 'peak_db' in stats
        assert stats['dtype'] == 'float64'
        assert stats['shape'] == (1000,)

    def test_stats_silent_audio(self):
        """Test stats with silent audio"""
        audio = np.zeros(1000)
        stats = get_audio_stats(audio)

        assert stats['samples'] == 1000
        assert stats['rms'] == 0.0
        assert stats['rms_db'] == -np.inf
        assert stats['peak'] == 0.0
        assert stats['peak_db'] == -np.inf

    def test_stats_empty_audio(self):
        """Test stats with empty audio"""
        audio = np.array([])
        stats = get_audio_stats(audio)

        assert stats['samples'] == 0
        assert stats['rms'] == 0.0
        assert stats['peak'] == 0.0

    def test_stats_stereo_audio(self):
        """Test stats with stereo audio"""
        audio = np.random.randn(1000, 2)
        stats = get_audio_stats(audio)

        assert stats['samples'] == 1000
        assert stats['shape'] == (1000, 2)

    def test_stats_known_values(self):
        """Test stats with known values"""
        # Create audio with known RMS
        audio = np.ones(1000)  # RMS = 1.0, Peak = 1.0
        stats = get_audio_stats(audio)

        assert stats['rms'] == 1.0
        assert stats['rms_db'] == 0.0  # 20*log10(1.0) = 0
        assert stats['peak'] == 1.0
        assert stats['peak_db'] == 0.0


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_array(self):
        """Test with empty arrays"""
        empty = np.array([])

        # Should handle gracefully
        stats = get_audio_stats(empty)
        assert stats['samples'] == 0

        normalized = normalize_audio(empty)
        assert len(normalized) == 0

    def test_very_small_values(self):
        """Test with very small values"""
        audio = np.random.randn(1000) * 1e-10
        stats = get_audio_stats(audio)

        # Should not raise errors
        assert stats['rms'] < 1e-9

    def test_large_audio(self):
        """Test with large audio array"""
        audio = np.random.randn(1000000)  # 1M samples
        result = convert_to_mono(audio)

        assert len(result) == 1000000
