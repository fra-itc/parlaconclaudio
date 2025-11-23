"""
Audio capture drivers

Platform-specific audio capture implementations.
"""

from typing import Dict, Type
import logging

logger = logging.getLogger(__name__)

# Always available drivers
from .mock_driver import MockAudioDriver

# Driver registry for factory
AVAILABLE_DRIVERS: Dict[str, Type] = {
    'mock': MockAudioDriver,
}

# Optional drivers (platform-specific)
# PulseAudio (Linux)
try:
    from .pulseaudio_driver import PulseAudioDriver
    AVAILABLE_DRIVERS['pulseaudio'] = PulseAudioDriver
    logger.info("PulseAudio driver registered")
except ImportError as e:
    logger.debug(f"PulseAudio driver not available: {e}")

# WASAPI (Windows)
# try:
#     from .wasapi_driver import WASAPIDriver
#     AVAILABLE_DRIVERS['wasapi'] = WASAPIDriver
#     logger.info("WASAPI driver registered")
# except ImportError as e:
#     logger.debug(f"WASAPI driver not available: {e}")

# ALSA (Linux alternative)
# try:
#     from .alsa_driver import ALSADriver
#     AVAILABLE_DRIVERS['alsa'] = ALSADriver
#     logger.info("ALSA driver registered")
# except ImportError as e:
#     logger.debug(f"ALSA driver not available: {e}")

# PortAudio (Universal fallback)
try:
    from .portaudio_driver import PortAudioDriver
    AVAILABLE_DRIVERS['portaudio'] = PortAudioDriver
    logger.info("PortAudio driver registered")
except ImportError as e:
    logger.debug(f"PortAudio driver not available: {e}")

__all__ = [
    'MockAudioDriver',
    'AVAILABLE_DRIVERS',
]
