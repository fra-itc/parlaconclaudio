"""
Bridge Configuration

Configuration management for audio bridge service.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class BridgeConfig:
    """Configuration for audio bridge service"""

    # WebSocket connection
    websocket_url: str = "ws://localhost:8000/ws"
    reconnect_delay: float = 5.0
    max_reconnect_attempts: int = 0  # 0 = infinite
    ping_interval: float = 30.0

    # Audio capture
    driver: Optional[str] = None  # None = auto-detect
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 4096
    device_id: Optional[int] = None
    pattern: str = "sine"  # For mock driver

    # Buffering
    buffer_seconds: float = 2.0  # Minimum audio before sending

    # Logging
    log_level: str = "INFO"
    log_file: Optional[Path] = None

    # Runtime
    test_duration: Optional[float] = None  # For testing, None = run forever

    @classmethod
    def from_env(cls) -> "BridgeConfig":
        """Create config from environment variables"""
        return cls(
            websocket_url=os.getenv("RTSTT_WEBSOCKET_URL", "ws://localhost:8000/ws"),
            reconnect_delay=float(os.getenv("RTSTT_RECONNECT_DELAY", "5.0")),
            max_reconnect_attempts=int(os.getenv("RTSTT_MAX_RECONNECT", "0")),
            ping_interval=float(os.getenv("RTSTT_PING_INTERVAL", "30.0")),
            driver=os.getenv("RTSTT_AUDIO_DRIVER"),
            sample_rate=int(os.getenv("RTSTT_SAMPLE_RATE", "16000")),
            channels=int(os.getenv("RTSTT_CHANNELS", "1")),
            chunk_size=int(os.getenv("RTSTT_CHUNK_SIZE", "4096")),
            pattern=os.getenv("RTSTT_PATTERN", "sine"),
            buffer_seconds=float(os.getenv("RTSTT_BUFFER_SECONDS", "2.0")),
            log_level=os.getenv("RTSTT_LOG_LEVEL", "INFO"),
        )

    def get_min_buffer_size(self) -> int:
        """Calculate minimum buffer size in bytes"""
        # sample_rate * channels * bytes_per_sample * duration
        return int(self.sample_rate * self.channels * 2 * self.buffer_seconds)

    def validate(self) -> None:
        """Validate configuration"""
        if self.sample_rate not in [8000, 16000, 22050, 44100, 48000]:
            raise ValueError(f"Invalid sample rate: {self.sample_rate}")

        if self.channels not in [1, 2]:
            raise ValueError(f"Invalid channels: {self.channels}")

        if self.chunk_size < 128 or self.chunk_size > 16384:
            raise ValueError(f"Invalid chunk size: {self.chunk_size}")

        if self.buffer_seconds < 0.5 or self.buffer_seconds > 10.0:
            raise ValueError(f"Invalid buffer duration: {self.buffer_seconds}")

        if not self.websocket_url.startswith(("ws://", "wss://")):
            raise ValueError(f"Invalid WebSocket URL: {self.websocket_url}")
