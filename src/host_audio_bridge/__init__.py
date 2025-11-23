"""
Host Audio Bridge

Standalone service that captures audio on the host machine and
streams it to the RTSTT backend via WebSocket.

Critical for WSL2 deployments where audio hardware is on Windows host
but processing services run in Linux containers.
"""

from .audio_bridge import AudioBridge
from .config import BridgeConfig

__all__ = ['AudioBridge', 'BridgeConfig']
