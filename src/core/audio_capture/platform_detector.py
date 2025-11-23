"""
Platform Detection Module

Detects the operating system, environment (WSL, native), and available
audio subsystems to determine the best audio capture driver to use.
"""

import platform
import os
import subprocess
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass


class PlatformType(Enum):
    """Supported platform types"""
    WINDOWS_NATIVE = "windows_native"  # Native Windows
    WSL1 = "wsl1"  # Windows Subsystem for Linux v1
    WSL2 = "wsl2"  # Windows Subsystem for Linux v2
    LINUX_NATIVE = "linux_native"  # Native Linux
    MACOS = "macos"  # macOS
    UNKNOWN = "unknown"


class AudioSubsystem(Enum):
    """Available audio subsystems"""
    WASAPI = "wasapi"  # Windows Audio Session API
    PULSEAUDIO = "pulseaudio"  # PulseAudio (Linux)
    ALSA = "alsa"  # ALSA (Linux)
    COREAUDIO = "coreaudio"  # CoreAudio (macOS)
    PORTAUDIO = "portaudio"  # PortAudio (cross-platform)
    NONE = "none"


@dataclass
class PlatformInfo:
    """Information about the detected platform"""
    platform_type: PlatformType
    os_name: str  # 'Windows', 'Linux', 'Darwin'
    os_version: str
    is_wsl: bool
    wsl_version: Optional[int] = None
    available_subsystems: List[AudioSubsystem] = None
    recommended_driver: Optional[str] = None

    def __post_init__(self):
        if self.available_subsystems is None:
            self.available_subsystems = []

    def __repr__(self) -> str:
        wsl_info = f" (WSL{self.wsl_version})" if self.is_wsl else ""
        return f"PlatformInfo({self.platform_type.value}{wsl_info}, subsystems={[s.value for s in self.available_subsystems]})"


class PlatformDetector:
    """
    Detects platform and available audio subsystems.

    Usage:
        detector = PlatformDetector()
        info = detector.detect()
        print(f"Platform: {info.platform_type}")
        print(f"Recommended: {info.recommended_driver}")
    """

    def __init__(self):
        self._cache: Optional[PlatformInfo] = None

    def detect(self, force_refresh: bool = False) -> PlatformInfo:
        """
        Detect platform and available audio subsystems.

        Args:
            force_refresh: Force re-detection even if cached

        Returns:
            PlatformInfo with detection results
        """
        if self._cache and not force_refresh:
            return self._cache

        platform_type = self._detect_platform_type()
        os_name = platform.system()
        os_version = platform.release()
        is_wsl, wsl_version = self._is_wsl()

        available_subsystems = self._detect_audio_subsystems(platform_type)
        recommended_driver = self._recommend_driver(platform_type, available_subsystems)

        self._cache = PlatformInfo(
            platform_type=platform_type,
            os_name=os_name,
            os_version=os_version,
            is_wsl=is_wsl,
            wsl_version=wsl_version,
            available_subsystems=available_subsystems,
            recommended_driver=recommended_driver
        )

        return self._cache

    def _detect_platform_type(self) -> PlatformType:
        """Detect the platform type"""
        os_name = platform.system()

        if os_name == "Windows":
            return PlatformType.WINDOWS_NATIVE

        elif os_name == "Linux":
            is_wsl, wsl_version = self._is_wsl()
            if is_wsl:
                if wsl_version == 1:
                    return PlatformType.WSL1
                elif wsl_version == 2:
                    return PlatformType.WSL2
            return PlatformType.LINUX_NATIVE

        elif os_name == "Darwin":
            return PlatformType.MACOS

        return PlatformType.UNKNOWN

    def _is_wsl(self) -> tuple[bool, Optional[int]]:
        """
        Detect if running under WSL and which version.

        Returns:
            Tuple of (is_wsl, wsl_version)
        """
        # Check /proc/version for WSL markers
        try:
            with open("/proc/version", "r") as f:
                version_info = f.read().lower()

            if "microsoft" in version_info or "wsl" in version_info:
                # WSL2 has its own kernel
                if "wsl2" in version_info or "microsoft-standard" in version_info:
                    return (True, 2)
                # WSL1 uses Windows kernel
                elif "microsoft" in version_info:
                    return (True, 1)

        except FileNotFoundError:
            pass

        # Also check environment variables
        if os.environ.get("WSL_DISTRO_NAME"):
            # If kernel version contains 'microsoft', likely WSL2, otherwise WSL1
            uname = platform.release().lower()
            if "microsoft-standard" in uname:
                return (True, 2)
            return (True, 1)

        return (False, None)

    def _detect_audio_subsystems(self, platform_type: PlatformType) -> List[AudioSubsystem]:
        """Detect available audio subsystems"""
        available = []

        if platform_type == PlatformType.WINDOWS_NATIVE:
            # Windows always has WASAPI
            available.append(AudioSubsystem.WASAPI)

        elif platform_type in [PlatformType.WSL1, PlatformType.WSL2, PlatformType.LINUX_NATIVE]:
            # Check for PulseAudio
            if self._check_pulseaudio():
                available.append(AudioSubsystem.PULSEAUDIO)

            # Check for ALSA
            if self._check_alsa():
                available.append(AudioSubsystem.ALSA)

        elif platform_type == PlatformType.MACOS:
            # macOS always has CoreAudio
            available.append(AudioSubsystem.COREAUDIO)

        # Check for PortAudio (universal fallback)
        if self._check_portaudio():
            available.append(AudioSubsystem.PORTAUDIO)

        return available if available else [AudioSubsystem.NONE]

    def _check_pulseaudio(self) -> bool:
        """Check if PulseAudio is available"""
        try:
            # Check if pulseaudio server is running
            result = subprocess.run(
                ["pulseaudio", "--check"],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                return True

            # Also check for pactl command
            result = subprocess.run(
                ["pactl", "info"],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_alsa(self) -> bool:
        """Check if ALSA is available"""
        try:
            # Check for ALSA devices
            result = subprocess.run(
                ["arecord", "-l"],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0 and b"card" in result.stdout

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_portaudio(self) -> bool:
        """Check if PortAudio is available via PyAudio"""
        try:
            import pyaudio
            return True
        except ImportError:
            return False

    def _recommend_driver(
        self,
        platform_type: PlatformType,
        available_subsystems: List[AudioSubsystem]
    ) -> Optional[str]:
        """
        Recommend the best audio driver for this platform.

        Returns:
            Driver name (e.g., 'wasapi', 'pulseaudio', 'portaudio')
        """
        # Windows Native: Use WASAPI
        if platform_type == PlatformType.WINDOWS_NATIVE:
            if AudioSubsystem.WASAPI in available_subsystems:
                return "wasapi"
            elif AudioSubsystem.PORTAUDIO in available_subsystems:
                return "portaudio"

        # WSL: Recommend WebSocket bridge to Windows host
        elif platform_type in [PlatformType.WSL1, PlatformType.WSL2]:
            # WSL cannot directly access Windows audio hardware
            # Recommend using WebSocket bridge from Windows host
            return "websocket_bridge"

        # Linux Native: Prefer PulseAudio, fallback to ALSA
        elif platform_type == PlatformType.LINUX_NATIVE:
            if AudioSubsystem.PULSEAUDIO in available_subsystems:
                return "pulseaudio"
            elif AudioSubsystem.ALSA in available_subsystems:
                return "alsa"
            elif AudioSubsystem.PORTAUDIO in available_subsystems:
                return "portaudio"

        # macOS: Use CoreAudio
        elif platform_type == PlatformType.MACOS:
            if AudioSubsystem.COREAUDIO in available_subsystems:
                return "coreaudio"
            elif AudioSubsystem.PORTAUDIO in available_subsystems:
                return "portaudio"

        return None

    def get_platform_capabilities(self) -> Dict[str, bool]:
        """
        Get platform capabilities.

        Returns:
            Dictionary of capability flags
        """
        info = self.detect()

        return {
            "has_native_audio": info.platform_type in [
                PlatformType.WINDOWS_NATIVE,
                PlatformType.LINUX_NATIVE,
                PlatformType.MACOS
            ],
            "needs_audio_bridge": info.platform_type in [
                PlatformType.WSL1,
                PlatformType.WSL2
            ],
            "supports_loopback": AudioSubsystem.WASAPI in info.available_subsystems or
                                 AudioSubsystem.PULSEAUDIO in info.available_subsystems,
            "has_fallback": AudioSubsystem.PORTAUDIO in info.available_subsystems,
            "is_wsl": info.is_wsl,
        }


# Singleton instance for easy access
_detector_instance: Optional[PlatformDetector] = None


def get_platform_detector() -> PlatformDetector:
    """Get or create singleton platform detector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = PlatformDetector()
    return _detector_instance


def detect_platform() -> PlatformInfo:
    """Convenience function to detect platform"""
    return get_platform_detector().detect()


def is_wsl() -> bool:
    """Check if running under WSL"""
    info = detect_platform()
    return info.is_wsl


def get_recommended_driver() -> Optional[str]:
    """Get recommended audio driver for this platform"""
    info = detect_platform()
    return info.recommended_driver
