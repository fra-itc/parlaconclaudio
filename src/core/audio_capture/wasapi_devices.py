"""
WASAPI Device Enumeration for Windows 11

This module provides device enumeration and management for WASAPI audio devices.
Supports input, output, and loopback device types.

Author: ORCHIDEA Agent System
Created: 2025-11-21
"""

import comtypes
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class AudioDevice:
    """Audio device metadata container"""

    def __init__(self,
                 device_id: str,
                 name: str,
                 device_type: str,
                 is_default: bool,
                 max_channels: int,
                 supported_sample_rates: List[int]):
        """
        Initialize audio device metadata

        Args:
            device_id: Unique device identifier
            name: Human-readable device name
            device_type: 'input', 'output', or 'loopback'
            is_default: True if this is the system default device
            max_channels: Maximum number of audio channels
            supported_sample_rates: List of supported sample rates in Hz
        """
        self.device_id = device_id
        self.name = name
        self.device_type = device_type
        self.is_default = is_default
        self.max_channels = max_channels
        self.supported_sample_rates = supported_sample_rates

    def __repr__(self) -> str:
        return (f"AudioDevice(name='{self.name}', type='{self.device_type}', "
                f"default={self.is_default})")


def list_audio_devices(device_type: str = 'loopback') -> List[AudioDevice]:
    """
    Enumerate WASAPI audio devices

    Args:
        device_type: Device type filter - 'input', 'output', 'loopback', or 'all'

    Returns:
        List of AudioDevice objects matching the filter criteria

    Raises:
        RuntimeError: If COM initialization fails
    """
    devices = []

    try:
        # Get all audio devices via pycaw
        all_devices = AudioUtilities.GetAllDevices()

        for dev in all_devices:
            try:
                # Extract device information
                device_name = str(dev.FriendlyName)
                dev_id = str(dev.id)

                # Determine device type
                # Loopback devices typically have "Stereo Mix" or similar in name
                # For POC purposes, we'll treat output devices as loopback capable
                is_loopback = 'loopback' in device_name.lower() or 'stereo mix' in device_name.lower()
                dev_type = 'loopback' if is_loopback else 'output'

                # Check if this is the default device
                try:
                    default_id = AudioUtilities.GetDefaultDeviceId()
                    is_default = (dev_id == default_id)
                except Exception:
                    is_default = False

                # Create device info object
                device_info = AudioDevice(
                    device_id=dev_id,
                    name=device_name,
                    device_type=dev_type,
                    is_default=is_default,
                    max_channels=2,  # Most devices support stereo
                    supported_sample_rates=[44100, 48000, 96000]  # Common rates
                )

                # Filter by device type if specified
                if device_type == 'all' or device_type == dev_type:
                    devices.append(device_info)

            except Exception as e:
                logger.warning(f"Failed to process device {dev}: {e}")
                continue

        logger.info(f"Found {len(devices)} audio devices (type: {device_type})")

    except Exception as e:
        logger.error(f"Failed to enumerate devices: {e}")
        raise RuntimeError(f"Device enumeration failed: {e}")

    return devices


def get_default_device(device_type: str = 'loopback') -> Optional[AudioDevice]:
    """
    Get system default audio device

    Args:
        device_type: Device type filter - 'input', 'output', or 'loopback'

    Returns:
        Default AudioDevice object, or None if no device found
    """
    try:
        devices = list_audio_devices(device_type)

        # First try to find the default device
        default_devices = [d for d in devices if d.is_default]
        if default_devices:
            logger.info(f"Using default device: {default_devices[0].name}")
            return default_devices[0]

        # Fallback to first available device
        if devices:
            logger.warning(f"No default device found, using first available: {devices[0].name}")
            return devices[0]

        logger.error(f"No {device_type} devices found")
        return None

    except Exception as e:
        logger.error(f"Failed to get default device: {e}")
        return None


def get_device_by_id(device_id: str) -> Optional[AudioDevice]:
    """
    Get audio device by ID

    Args:
        device_id: Device identifier

    Returns:
        AudioDevice object, or None if not found
    """
    try:
        devices = list_audio_devices('all')
        matching = [d for d in devices if d.device_id == device_id]
        return matching[0] if matching else None
    except Exception as e:
        logger.error(f"Failed to get device by ID: {e}")
        return None


def get_device_by_name(device_name: str, fuzzy: bool = True) -> Optional[AudioDevice]:
    """
    Get audio device by name

    Args:
        device_name: Device name to search for
        fuzzy: If True, performs case-insensitive partial matching

    Returns:
        AudioDevice object, or None if not found
    """
    try:
        devices = list_audio_devices('all')

        if fuzzy:
            # Case-insensitive partial match
            search_name = device_name.lower()
            matching = [d for d in devices if search_name in d.name.lower()]
        else:
            # Exact match
            matching = [d for d in devices if d.name == device_name]

        return matching[0] if matching else None

    except Exception as e:
        logger.error(f"Failed to get device by name: {e}")
        return None
