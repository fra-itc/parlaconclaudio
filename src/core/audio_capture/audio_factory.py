"""
Audio Capture Factory

Factory pattern for creating platform-specific audio capture drivers.
Automatically detects the platform and instantiates the appropriate driver.
"""

import logging
from typing import Optional, Dict, Any

from .audio_capture_base import AudioCaptureBase, AudioCaptureConfig
from .platform_detector import (
    PlatformDetector,
    PlatformType,
    AudioSubsystem,
    detect_platform,
    get_recommended_driver
)


logger = logging.getLogger(__name__)


class AudioCaptureFactory:
    """
    Factory for creating audio capture drivers.

    Automatically selects the best driver based on platform detection,
    or allows manual driver selection.

    Usage:
        # Automatic selection
        capture = AudioCaptureFactory.create()

        # Manual selection
        capture = AudioCaptureFactory.create(driver="pulseaudio")

        # With configuration
        config = AudioCaptureConfig(sample_rate=16000, channels=1)
        capture = AudioCaptureFactory.create(config=config)
    """

    # Registry of available drivers
    _drivers: Dict[str, type] = {}

    @classmethod
    def register_driver(cls, name: str, driver_class: type) -> None:
        """
        Register a new audio driver.

        Args:
            name: Driver name (e.g., 'wasapi', 'pulseaudio')
            driver_class: Driver class (must inherit from AudioCaptureBase)
        """
        if not issubclass(driver_class, AudioCaptureBase):
            raise TypeError(f"Driver must inherit from AudioCaptureBase: {driver_class}")

        cls._drivers[name] = driver_class
        logger.info(f"Registered audio driver: {name}")

    @classmethod
    def create(
        cls,
        driver: Optional[str] = None,
        config: Optional[AudioCaptureConfig] = None,
        **kwargs
    ) -> AudioCaptureBase:
        """
        Create an audio capture driver instance.

        Args:
            driver: Specific driver to use (None = auto-detect)
                   Options: 'wasapi', 'pulseaudio', 'alsa', 'portaudio', 'mock'
            config: Audio capture configuration
            **kwargs: Additional driver-specific parameters

        Returns:
            AudioCaptureBase instance

        Raises:
            RuntimeError: If no suitable driver is available
            ValueError: If specified driver is not found
        """
        # Auto-detect if not specified
        if driver is None:
            driver = cls._detect_best_driver()
            logger.info(f"Auto-detected driver: {driver}")

        # Check if driver is registered
        if driver not in cls._drivers:
            available = list(cls._drivers.keys())
            raise ValueError(
                f"Driver '{driver}' not found. Available: {available}\n"
                f"Make sure the driver module is imported."
            )

        # Create driver instance
        driver_class = cls._drivers[driver]
        logger.info(f"Creating audio capture driver: {driver}")

        try:
            instance = driver_class(config=config, **kwargs)
            logger.info(f"Created {driver} driver successfully")
            return instance

        except Exception as e:
            logger.error(f"Failed to create {driver} driver: {e}")
            raise RuntimeError(f"Failed to create audio driver '{driver}': {e}")

    @classmethod
    def _detect_best_driver(cls) -> str:
        """
        Detect the best audio driver for this platform.

        Returns:
            Driver name

        Raises:
            RuntimeError: If no suitable driver is found
        """
        # Get platform recommendation
        recommended = get_recommended_driver()

        # Check if recommended driver is available
        if recommended and recommended in cls._drivers:
            return recommended

        # Fallback strategy based on registered drivers
        fallback_order = ['portaudio', 'mock']

        for fallback in fallback_order:
            if fallback in cls._drivers:
                logger.warning(
                    f"Recommended driver '{recommended}' not available, "
                    f"using fallback: {fallback}"
                )
                return fallback

        # No drivers available
        available = list(cls._drivers.keys())
        raise RuntimeError(
            f"No suitable audio driver found.\n"
            f"Platform recommendation: {recommended}\n"
            f"Available drivers: {available}\n"
            f"Install required dependencies for platform-specific drivers."
        )

    @classmethod
    def list_available_drivers(cls) -> Dict[str, Dict[str, Any]]:
        """
        List all registered drivers with their capabilities.

        Returns:
            Dictionary mapping driver names to info dictionaries
        """
        platform_info = detect_platform()

        result = {}
        for name, driver_class in cls._drivers.items():
            # Check if driver is suitable for current platform
            suitable = cls._is_driver_suitable(name, platform_info.platform_type)

            result[name] = {
                "class": driver_class.__name__,
                "module": driver_class.__module__,
                "suitable_for_platform": suitable,
                "description": driver_class.__doc__.split("\n")[0] if driver_class.__doc__ else "No description"
            }

        return result

    @classmethod
    def _is_driver_suitable(cls, driver_name: str, platform_type: PlatformType) -> bool:
        """Check if driver is suitable for the platform"""
        # WASAPI: Windows only
        if driver_name == "wasapi":
            return platform_type == PlatformType.WINDOWS_NATIVE

        # PulseAudio/ALSA: Linux (not WSL)
        if driver_name in ["pulseaudio", "alsa"]:
            return platform_type == PlatformType.LINUX_NATIVE

        # CoreAudio: macOS only
        if driver_name == "coreaudio":
            return platform_type == PlatformType.MACOS

        # PortAudio, Mock: Universal
        if driver_name in ["portaudio", "mock"]:
            return True

        return False

    @classmethod
    def get_platform_info(cls) -> Dict[str, Any]:
        """
        Get information about the current platform and audio capabilities.

        Returns:
            Dictionary with platform information
        """
        platform_info = detect_platform()

        return {
            "platform_type": platform_info.platform_type.value,
            "os_name": platform_info.os_name,
            "os_version": platform_info.os_version,
            "is_wsl": platform_info.is_wsl,
            "wsl_version": platform_info.wsl_version,
            "available_subsystems": [s.value for s in platform_info.available_subsystems],
            "recommended_driver": platform_info.recommended_driver,
            "registered_drivers": list(cls._drivers.keys())
        }


# Convenience function for quick driver creation
def create_audio_capture(
    driver: Optional[str] = None,
    **kwargs
) -> AudioCaptureBase:
    """
    Convenience function to create an audio capture driver.

    Args:
        driver: Driver name (None = auto-detect)
        **kwargs: Additional parameters (config, device_id, etc.)

    Returns:
        AudioCaptureBase instance
    """
    return AudioCaptureFactory.create(driver=driver, **kwargs)


# Auto-register available drivers after class is defined
def _register_available_drivers():
    """Auto-register all available drivers"""
    try:
        from .drivers import AVAILABLE_DRIVERS
        for name, driver_class in AVAILABLE_DRIVERS.items():
            AudioCaptureFactory.register_driver(name, driver_class)
    except ImportError as e:
        logger.warning(f"Could not import drivers: {e}")


# Register drivers on module import
_register_available_drivers()


# Export for easy access
__all__ = [
    'AudioCaptureFactory',
    'create_audio_capture',
]
