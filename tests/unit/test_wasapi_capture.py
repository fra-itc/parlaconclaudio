"""
Unit tests for WASAPI audio capture

Tests audio capture initialization, streaming, and callbacks.

Author: ORCHIDEA Agent System
Created: 2025-11-21
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock, call
import time
from src.core.audio_capture.wasapi_capture import WASAPICapture
import pyaudio


class TestWASAPICaptureInit:
    """Test WASAPICapture initialization"""

    def test_init_default_params(self):
        """Test initialization with default parameters"""
        capture = WASAPICapture()

        assert capture.sample_rate == 48000
        assert capture.channels == 1
        assert capture.chunk_duration_ms == 100
        assert capture.chunk_size == 4800  # 48000 * 100 / 1000
        assert capture.device_id is None
        assert capture.is_running() is False

    def test_init_custom_params(self):
        """Test initialization with custom parameters"""
        capture = WASAPICapture(
            device_id='test-device',
            sample_rate=16000,
            channels=2,
            chunk_duration_ms=50
        )

        assert capture.sample_rate == 16000
        assert capture.channels == 2
        assert capture.chunk_duration_ms == 50
        assert capture.chunk_size == 800  # 16000 * 50 / 1000
        assert capture.device_id == 'test-device'

    def test_init_chunk_size_calculation(self):
        """Test chunk size calculation for various configurations"""
        # 16kHz, 100ms = 1600 samples
        capture1 = WASAPICapture(sample_rate=16000, chunk_duration_ms=100)
        assert capture1.chunk_size == 1600

        # 48kHz, 50ms = 2400 samples
        capture2 = WASAPICapture(sample_rate=48000, chunk_duration_ms=50)
        assert capture2.chunk_size == 2400


class TestWASAPICaptureStartStop:
    """Test capture start/stop functionality"""

    @patch('src.core.audio_capture.wasapi_capture.pyaudio.PyAudio')
    def test_start_success(self, mock_pyaudio_class):
        """Test successful capture start"""
        # Mock PyAudio instance and stream
        mock_audio = Mock()
        mock_stream = Mock()
        mock_stream.is_active.return_value = True

        mock_pyaudio_class.return_value = mock_audio
        mock_audio.open.return_value = mock_stream

        capture = WASAPICapture(sample_rate=16000)
        callback = Mock()

        capture.start(callback)

        # Verify PyAudio was initialized
        mock_pyaudio_class.assert_called_once()
        mock_audio.open.assert_called_once()

        # Verify stream was started
        mock_stream.start_stream.assert_called_once()

        # Verify state
        assert capture._running is True
        assert capture._callback == callback

        # Cleanup
        capture.stop()

    @patch('src.core.audio_capture.wasapi_capture.pyaudio.PyAudio')
    def test_start_already_running(self, mock_pyaudio_class):
        """Test starting capture when already running"""
        mock_audio = Mock()
        mock_stream = Mock()
        mock_stream.is_active.return_value = True

        mock_pyaudio_class.return_value = mock_audio
        mock_audio.open.return_value = mock_stream

        capture = WASAPICapture()
        callback = Mock()

        capture.start(callback)
        open_call_count_1 = mock_audio.open.call_count

        # Try to start again
        capture.start(callback)
        open_call_count_2 = mock_audio.open.call_count

        # Should not open stream again
        assert open_call_count_1 == open_call_count_2

        capture.stop()

    @patch('src.core.audio_capture.wasapi_capture.pyaudio.PyAudio')
    def test_start_with_device_id(self, mock_pyaudio_class):
        """Test starting with specific device ID"""
        mock_audio = Mock()
        mock_stream = Mock()
        mock_stream.is_active.return_value = True

        # Mock device info
        mock_audio.get_device_count.return_value = 2
        mock_audio.get_device_info_by_index.side_effect = [
            {'name': 'Device 0'},
            {'name': 'test-device'}
        ]

        mock_pyaudio_class.return_value = mock_audio
        mock_audio.open.return_value = mock_stream

        capture = WASAPICapture(device_id='test-device')
        callback = Mock()

        capture.start(callback)

        # Should find device index
        assert mock_audio.get_device_count.called

        capture.stop()

    @patch('src.core.audio_capture.wasapi_capture.pyaudio.PyAudio')
    def test_start_failure(self, mock_pyaudio_class):
        """Test capture start failure"""
        mock_audio = Mock()
        mock_audio.open.side_effect = Exception("Device not found")

        mock_pyaudio_class.return_value = mock_audio

        capture = WASAPICapture()
        callback = Mock()

        with pytest.raises(RuntimeError):
            capture.start(callback)

        # Should not be running
        assert capture.is_running() is False

    @patch('src.core.audio_capture.wasapi_capture.pyaudio.PyAudio')
    def test_stop_success(self, mock_pyaudio_class):
        """Test successful capture stop"""
        mock_audio = Mock()
        mock_stream = Mock()
        mock_stream.is_active.return_value = True

        mock_pyaudio_class.return_value = mock_audio
        mock_audio.open.return_value = mock_stream

        capture = WASAPICapture()
        callback = Mock()

        capture.start(callback)
        capture.stop()

        # Verify stream was stopped
        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()
        mock_audio.terminate.assert_called_once()

        # Verify state
        assert capture._running is False

    def test_stop_when_not_running(self):
        """Test stopping when not running"""
        capture = WASAPICapture()
        # Should not raise exception
        capture.stop()


class TestWASAPICaptureCallback:
    """Test audio callback functionality"""

    @patch('src.core.audio_capture.wasapi_capture.pyaudio.PyAudio')
    def test_audio_callback_mono(self, mock_pyaudio_class):
        """Test audio callback with mono audio"""
        mock_audio = Mock()
        mock_stream = Mock()
        mock_stream.is_active.return_value = True

        mock_pyaudio_class.return_value = mock_audio
        mock_audio.open.return_value = mock_stream

        capture = WASAPICapture(sample_rate=16000, channels=1)
        received_data = []

        def callback(audio):
            received_data.append(audio)

        capture.start(callback)

        # Simulate audio callback
        audio_bytes = np.random.randint(-32768, 32767, 1600, dtype=np.int16).tobytes()
        result = capture._audio_callback(audio_bytes, 1600, {}, 0)

        # Check callback was invoked
        assert len(received_data) == 1
        assert isinstance(received_data[0], np.ndarray)
        assert len(received_data[0]) == 1600
        assert result[1] == pyaudio.paContinue

        capture.stop()

    @patch('src.core.audio_capture.wasapi_capture.pyaudio.PyAudio')
    def test_audio_callback_stereo(self, mock_pyaudio_class):
        """Test audio callback with stereo audio"""
        mock_audio = Mock()
        mock_stream = Mock()
        mock_stream.is_active.return_value = True

        mock_pyaudio_class.return_value = mock_audio
        mock_audio.open.return_value = mock_stream

        capture = WASAPICapture(sample_rate=16000, channels=2)
        received_data = []

        def callback(audio):
            received_data.append(audio)

        capture.start(callback)

        # Simulate stereo audio callback (2 channels)
        audio_bytes = np.random.randint(-32768, 32767, 3200, dtype=np.int16).tobytes()
        result = capture._audio_callback(audio_bytes, 1600, {}, 0)

        # Check callback was invoked
        assert len(received_data) == 1
        assert isinstance(received_data[0], np.ndarray)
        assert received_data[0].shape == (1600, 2)  # Stereo reshaped

        capture.stop()

    @patch('src.core.audio_capture.wasapi_capture.pyaudio.PyAudio')
    def test_audio_callback_error_handling(self, mock_pyaudio_class):
        """Test error handling in audio callback"""
        mock_audio = Mock()
        mock_stream = Mock()
        mock_stream.is_active.return_value = True

        mock_pyaudio_class.return_value = mock_audio
        mock_audio.open.return_value = mock_stream

        capture = WASAPICapture(sample_rate=16000)

        def bad_callback(audio):
            raise Exception("Callback error")

        capture.start(bad_callback)

        # Simulate audio callback with error
        audio_bytes = np.random.randint(-32768, 32767, 1600, dtype=np.int16).tobytes()
        result = capture._audio_callback(audio_bytes, 1600, {}, 0)

        # Should still continue despite error
        assert result[1] == pyaudio.paContinue
        assert capture._error_count == 1

        capture.stop()

    @patch('src.core.audio_capture.wasapi_capture.pyaudio.PyAudio')
    def test_audio_callback_max_errors(self, mock_pyaudio_class):
        """Test max error limit in audio callback"""
        mock_audio = Mock()
        mock_stream = Mock()
        mock_stream.is_active.return_value = True

        mock_pyaudio_class.return_value = mock_audio
        mock_audio.open.return_value = mock_stream

        capture = WASAPICapture(sample_rate=16000)
        capture._max_errors = 3

        def bad_callback(audio):
            raise Exception("Callback error")

        capture.start(bad_callback)

        audio_bytes = np.random.randint(-32768, 32767, 1600, dtype=np.int16).tobytes()

        # Trigger multiple errors
        for i in range(5):
            result = capture._audio_callback(audio_bytes, 1600, {}, 0)
            if i >= 3:
                # After max errors, should stop
                assert result[1] == pyaudio.paComplete
                break

        capture.stop()


class TestWASAPICaptureStats:
    """Test capture statistics and monitoring"""

    @patch('src.core.audio_capture.wasapi_capture.pyaudio.PyAudio')
    def test_get_stats(self, mock_pyaudio_class):
        """Test getting capture statistics"""
        mock_audio = Mock()
        mock_stream = Mock()
        mock_stream.is_active.return_value = True
        mock_stream.get_input_latency.return_value = 0.005  # 5ms

        mock_pyaudio_class.return_value = mock_audio
        mock_audio.open.return_value = mock_stream

        capture = WASAPICapture(sample_rate=16000, channels=1, chunk_duration_ms=100)
        callback = Mock()

        capture.start(callback)

        # Simulate some audio chunks
        capture._total_chunks = 10
        capture._total_samples = 16000

        stats = capture.get_stats()

        assert stats['running'] is True
        assert stats['total_chunks'] == 10
        assert stats['total_samples'] == 16000
        assert stats['sample_rate'] == 16000
        assert stats['channels'] == 1
        assert stats['chunk_size'] == 1600
        assert 'latency_ms' in stats
        assert 'duration_seconds' in stats

        capture.stop()

    @patch('src.core.audio_capture.wasapi_capture.pyaudio.PyAudio')
    def test_get_latency(self, mock_pyaudio_class):
        """Test getting capture latency"""
        mock_audio = Mock()
        mock_stream = Mock()
        mock_stream.is_active.return_value = True
        mock_stream.get_input_latency.return_value = 0.008  # 8ms

        mock_pyaudio_class.return_value = mock_audio
        mock_audio.open.return_value = mock_stream

        capture = WASAPICapture()
        callback = Mock()

        capture.start(callback)

        latency_ms = capture.get_latency_ms()
        assert latency_ms == 8.0

        capture.stop()

    def test_is_running(self):
        """Test is_running status"""
        capture = WASAPICapture()
        assert capture.is_running() is False


class TestWASAPICaptureContextManager:
    """Test context manager functionality"""

    @patch('src.core.audio_capture.wasapi_capture.pyaudio.PyAudio')
    def test_context_manager(self, mock_pyaudio_class):
        """Test using WASAPICapture as context manager"""
        mock_audio = Mock()
        mock_stream = Mock()
        mock_stream.is_active.return_value = True

        mock_pyaudio_class.return_value = mock_audio
        mock_audio.open.return_value = mock_stream

        callback = Mock()

        with WASAPICapture() as capture:
            capture.start(callback)
            assert capture.is_running() is True

        # Should auto-stop on exit
        mock_stream.stop_stream.assert_called()


# Integration tests (require actual audio hardware)
class TestIntegration:
    """Integration tests - may skip if no audio available"""

    @pytest.mark.skipif(True, reason="Integration test - requires audio hardware")
    def test_real_capture(self):
        """Test real audio capture"""
        received_chunks = []

        def callback(audio):
            received_chunks.append(audio)

        capture = WASAPICapture(sample_rate=16000, chunk_duration_ms=100)
        capture.start(callback)
        time.sleep(0.5)  # Capture for 500ms
        capture.stop()

        # Should receive some chunks
        assert len(received_chunks) > 0
        assert all(isinstance(chunk, np.ndarray) for chunk in received_chunks)
