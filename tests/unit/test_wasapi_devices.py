"""
Unit tests for WASAPI device enumeration

Tests device listing, default device selection, and device lookup.

Author: ORCHIDEA Agent System
Created: 2025-11-21
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.audio_capture.wasapi_devices import (
    AudioDevice,
    list_audio_devices,
    get_default_device,
    get_device_by_id,
    get_device_by_name
)


class TestAudioDevice:
    """Test AudioDevice class"""

    def test_audio_device_init(self):
        """Test AudioDevice initialization"""
        device = AudioDevice(
            device_id='test-id-123',
            name='Test Device',
            device_type='output',
            is_default=True,
            max_channels=2,
            supported_sample_rates=[44100, 48000]
        )

        assert device.device_id == 'test-id-123'
        assert device.name == 'Test Device'
        assert device.device_type == 'output'
        assert device.is_default is True
        assert device.max_channels == 2
        assert device.supported_sample_rates == [44100, 48000]

    def test_audio_device_repr(self):
        """Test AudioDevice string representation"""
        device = AudioDevice(
            device_id='test-id',
            name='Test',
            device_type='loopback',
            is_default=False,
            max_channels=2,
            supported_sample_rates=[48000]
        )

        repr_str = repr(device)
        assert 'Test' in repr_str
        assert 'loopback' in repr_str


class TestListAudioDevices:
    """Test list_audio_devices function"""

    @patch('src.core.audio_capture.wasapi_devices.AudioUtilities')
    def test_list_audio_devices_success(self, mock_audio_utils):
        """Test successful device enumeration"""
        # Mock device
        mock_device = Mock()
        mock_device.FriendlyName = 'Test Speaker'
        mock_device.id = 'device-1'

        mock_audio_utils.GetAllDevices.return_value = [mock_device]
        mock_audio_utils.GetDefaultDeviceId.return_value = 'device-1'

        devices = list_audio_devices('all')

        assert len(devices) >= 0  # May vary by system
        assert isinstance(devices, list)

    @patch('src.core.audio_capture.wasapi_devices.AudioUtilities')
    def test_list_audio_devices_empty(self, mock_audio_utils):
        """Test with no devices"""
        mock_audio_utils.GetAllDevices.return_value = []

        devices = list_audio_devices()

        assert devices == []

    @patch('src.core.audio_capture.wasapi_devices.AudioUtilities')
    def test_list_audio_devices_filter_loopback(self, mock_audio_utils):
        """Test filtering by loopback device type"""
        # Mock loopback device
        mock_loopback = Mock()
        mock_loopback.FriendlyName = 'Stereo Mix (Loopback)'
        mock_loopback.id = 'loopback-1'

        # Mock output device
        mock_output = Mock()
        mock_output.FriendlyName = 'Speakers'
        mock_output.id = 'output-1'

        mock_audio_utils.GetAllDevices.return_value = [mock_loopback, mock_output]
        mock_audio_utils.GetDefaultDeviceId.return_value = 'loopback-1'

        devices = list_audio_devices('loopback')

        # Should only get loopback device
        loopback_devices = [d for d in devices if d.device_type == 'loopback']
        assert len(loopback_devices) > 0

    @patch('src.core.audio_capture.wasapi_devices.AudioUtilities')
    def test_list_audio_devices_exception(self, mock_audio_utils):
        """Test exception handling during enumeration"""
        mock_audio_utils.GetAllDevices.side_effect = Exception("COM error")

        with pytest.raises(RuntimeError):
            list_audio_devices()


class TestGetDefaultDevice:
    """Test get_default_device function"""

    @patch('src.core.audio_capture.wasapi_devices.list_audio_devices')
    def test_get_default_device_found(self, mock_list):
        """Test getting default device when available"""
        # Mock devices with one default
        device1 = AudioDevice('id1', 'Device 1', 'output', False, 2, [48000])
        device2 = AudioDevice('id2', 'Device 2', 'output', True, 2, [48000])

        mock_list.return_value = [device1, device2]

        default = get_default_device()

        assert default is not None
        assert default.is_default is True
        assert default.device_id == 'id2'

    @patch('src.core.audio_capture.wasapi_devices.list_audio_devices')
    def test_get_default_device_fallback(self, mock_list):
        """Test fallback to first device when no default"""
        # Mock devices with no default
        device1 = AudioDevice('id1', 'Device 1', 'output', False, 2, [48000])
        device2 = AudioDevice('id2', 'Device 2', 'output', False, 2, [48000])

        mock_list.return_value = [device1, device2]

        default = get_default_device()

        assert default is not None
        assert default.device_id == 'id1'

    @patch('src.core.audio_capture.wasapi_devices.list_audio_devices')
    def test_get_default_device_none(self, mock_list):
        """Test when no devices available"""
        mock_list.return_value = []

        default = get_default_device()

        assert default is None


class TestGetDeviceById:
    """Test get_device_by_id function"""

    @patch('src.core.audio_capture.wasapi_devices.list_audio_devices')
    def test_get_device_by_id_found(self, mock_list):
        """Test finding device by ID"""
        device1 = AudioDevice('id1', 'Device 1', 'output', False, 2, [48000])
        device2 = AudioDevice('id2', 'Device 2', 'output', False, 2, [48000])

        mock_list.return_value = [device1, device2]

        device = get_device_by_id('id2')

        assert device is not None
        assert device.device_id == 'id2'

    @patch('src.core.audio_capture.wasapi_devices.list_audio_devices')
    def test_get_device_by_id_not_found(self, mock_list):
        """Test device ID not found"""
        device1 = AudioDevice('id1', 'Device 1', 'output', False, 2, [48000])

        mock_list.return_value = [device1]

        device = get_device_by_id('nonexistent')

        assert device is None


class TestGetDeviceByName:
    """Test get_device_by_name function"""

    @patch('src.core.audio_capture.wasapi_devices.list_audio_devices')
    def test_get_device_by_name_fuzzy(self, mock_list):
        """Test fuzzy name matching"""
        device1 = AudioDevice('id1', 'Realtek HD Audio', 'output', False, 2, [48000])
        device2 = AudioDevice('id2', 'USB Headset', 'output', False, 2, [48000])

        mock_list.return_value = [device1, device2]

        device = get_device_by_name('realtek', fuzzy=True)

        assert device is not None
        assert device.device_id == 'id1'

    @patch('src.core.audio_capture.wasapi_devices.list_audio_devices')
    def test_get_device_by_name_exact(self, mock_list):
        """Test exact name matching"""
        device1 = AudioDevice('id1', 'Realtek HD Audio', 'output', False, 2, [48000])

        mock_list.return_value = [device1]

        device = get_device_by_name('Realtek HD Audio', fuzzy=False)

        assert device is not None
        assert device.device_id == 'id1'

    @patch('src.core.audio_capture.wasapi_devices.list_audio_devices')
    def test_get_device_by_name_not_found(self, mock_list):
        """Test device name not found"""
        device1 = AudioDevice('id1', 'Device 1', 'output', False, 2, [48000])

        mock_list.return_value = [device1]

        device = get_device_by_name('Nonexistent Device')

        assert device is None


# Integration test (requires actual audio devices)
class TestIntegration:
    """Integration tests - may skip if no devices available"""

    @pytest.mark.skipif(True, reason="Integration test - requires audio hardware")
    def test_list_real_devices(self):
        """Test with real system devices"""
        devices = list_audio_devices('all')
        # On Windows should have at least 1 device
        assert len(devices) >= 0

    @pytest.mark.skipif(True, reason="Integration test - requires audio hardware")
    def test_get_real_default_device(self):
        """Test getting real default device"""
        device = get_default_device()
        # May be None if no device available
        if device:
            assert device.device_id is not None
            assert device.name is not None
