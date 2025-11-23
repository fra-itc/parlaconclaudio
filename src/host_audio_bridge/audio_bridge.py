"""
Audio Bridge Service

Captures audio on the host and streams it to the backend via WebSocket.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
except ImportError:
    raise ImportError("websockets library required. Install with: pip install websockets")

from src.core.audio_capture.audio_factory import create_audio_capture
from src.core.audio_capture.audio_capture_base import AudioCaptureConfig
from .config import BridgeConfig


logger = logging.getLogger(__name__)


@dataclass
class BridgeStats:
    """Statistics for the bridge"""
    chunks_sent: int = 0
    bytes_sent: int = 0
    reconnections: int = 0
    errors: int = 0
    start_time: float = 0.0

    def get_uptime(self) -> float:
        """Get uptime in seconds"""
        return time.time() - self.start_time if self.start_time > 0 else 0

    def get_throughput_mbps(self) -> float:
        """Get throughput in Mbps"""
        uptime = self.get_uptime()
        if uptime == 0:
            return 0.0
        return (self.bytes_sent * 8) / (uptime * 1_000_000)


class AudioBridge:
    """
    Audio Bridge Service

    Captures audio on the host machine and streams it to the RTSTT backend.
    Handles reconnection, buffering, and error recovery.

    Usage:
        config = BridgeConfig(websocket_url="ws://localhost:8000/ws")
        bridge = AudioBridge(config)
        await bridge.run()
    """

    def __init__(self, config: BridgeConfig):
        """
        Initialize audio bridge.

        Args:
            config: Bridge configuration
        """
        self.config = config
        self.config.validate()

        self.stats = BridgeStats()
        self._audio_capture: Optional[object] = None
        self._websocket: Optional[WebSocketClientProtocol] = None
        self._audio_buffer: List[bytes] = []
        self._running = False
        self._chunk_number = 0
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        logger.info(f"AudioBridge initialized: {config.websocket_url}")

    async def run(self) -> None:
        """
        Run the audio bridge.

        This is the main entry point. It will run until stopped or an unrecoverable error occurs.
        """
        self.stats.start_time = time.time()
        self._running = True
        self._loop = asyncio.get_running_loop()

        logger.info("Starting Audio Bridge")
        logger.info(f"  WebSocket: {self.config.websocket_url}")
        logger.info(f"  Driver: {self.config.driver or 'auto-detect'}")
        logger.info(f"  Sample Rate: {self.config.sample_rate}Hz")
        logger.info(f"  Channels: {self.config.channels}")
        logger.info(f"  Buffer: {self.config.buffer_seconds}s")

        # Initialize audio capture
        self._initialize_audio_capture()

        # Run with reconnection logic
        attempt = 0
        while self._running:
            try:
                attempt += 1
                logger.info(f"Connection attempt {attempt}")

                await self._connect_and_stream()

            except websockets.exceptions.WebSocketException as e:
                logger.error(f"WebSocket error: {e}")
                self.stats.errors += 1

            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                self.stats.errors += 1

            # Check if we should stop
            if not self._running:
                break

            # Check reconnection limits
            if self.config.max_reconnect_attempts > 0 and attempt >= self.config.max_reconnect_attempts:
                logger.error(f"Max reconnection attempts ({self.config.max_reconnect_attempts}) reached")
                break

            # Wait before reconnecting
            if self._running:
                logger.info(f"Reconnecting in {self.config.reconnect_delay}s...")
                await asyncio.sleep(self.config.reconnect_delay)
                self.stats.reconnections += 1

        # Cleanup
        self._cleanup()
        logger.info("Audio Bridge stopped")

    async def _connect_and_stream(self) -> None:
        """Connect to WebSocket and stream audio"""
        logger.info(f"Connecting to {self.config.websocket_url}...")

        async with websockets.connect(self.config.websocket_url) as websocket:
            self._websocket = websocket
            logger.info("✅ Connected to backend")

            # Start audio capture
            self._audio_capture.start(callback=self._on_audio_chunk)
            logger.info("✅ Audio capture started")

            # Wait for messages (including ping/pong) and send heartbeat
            try:
                while self._running:
                    try:
                        # Wait for incoming messages with timeout
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=self.config.ping_interval
                        )

                        # Process incoming message
                        await self._handle_server_message(message)

                    except asyncio.TimeoutError:
                        # Send ping to keep connection alive
                        await self._send_ping()

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed by server")
                raise

            finally:
                # Stop audio capture
                if self._audio_capture and self._audio_capture.is_capturing():
                    self._audio_capture.stop()
                    logger.info("Audio capture stopped")

    def _initialize_audio_capture(self) -> None:
        """Initialize audio capture driver"""
        logger.info("Initializing audio capture...")

        # Create audio config
        audio_config = AudioCaptureConfig(
            sample_rate=self.config.sample_rate,
            channels=self.config.channels,
            chunk_size=self.config.chunk_size,
            device_id=self.config.device_id
        )

        # Create capture driver
        try:
            # For mock driver, pass pattern parameter
            if self.config.driver == "mock":
                self._audio_capture = create_audio_capture(
                    driver=self.config.driver,
                    config=audio_config,
                    pattern=self.config.pattern
                )
            else:
                self._audio_capture = create_audio_capture(
                    driver=self.config.driver,
                    config=audio_config
                )

            logger.info(f"✅ Audio driver initialized: {type(self._audio_capture).__name__}")

        except Exception as e:
            logger.error(f"Failed to initialize audio capture: {e}")
            raise

    def _on_audio_chunk(self, audio_data: bytes) -> None:
        """
        Callback when audio chunk is captured.

        Args:
            audio_data: Raw audio bytes
        """
        # Add to buffer
        self._audio_buffer.append(audio_data)

        # Calculate buffer size
        buffer_size = sum(len(chunk) for chunk in self._audio_buffer)
        min_buffer_size = self.config.get_min_buffer_size()

        # Send when we have enough buffered
        if buffer_size >= min_buffer_size:
            # Combine buffered chunks
            combined_audio = b''.join(self._audio_buffer)
            self._audio_buffer.clear()

            # Send to WebSocket (schedule on event loop from callback thread)
            if self._loop:
                asyncio.run_coroutine_threadsafe(
                    self._send_audio_chunk(combined_audio),
                    self._loop
                )

    async def _send_audio_chunk(self, audio_data: bytes) -> None:
        """
        Send audio chunk to backend via WebSocket.

        Args:
            audio_data: Raw audio bytes
        """
        if not self._websocket:
            return

        try:
            # Determine if this is the final chunk (for testing)
            is_final = False
            if self.config.test_duration:
                elapsed = time.time() - self.stats.start_time
                is_final = elapsed >= self.config.test_duration

            # Create message in same format as demo_audio_test.py
            message = {
                "type": "audio_chunk",
                "data": list(audio_data),  # Convert bytes to list for JSON
                "sample_rate": self.config.sample_rate,
                "chunk_number": self._chunk_number,
                "is_final": is_final,
                "timestamp": datetime.now().isoformat()
            }

            # Send to WebSocket
            await self._websocket.send(json.dumps(message))

            # Update stats
            self._chunk_number += 1
            self.stats.chunks_sent += 1
            self.stats.bytes_sent += len(audio_data)

            # Log periodically
            if self._chunk_number % 10 == 0:
                logger.debug(
                    f"Sent chunk #{self._chunk_number}: "
                    f"{len(audio_data)} bytes, "
                    f"{self.stats.get_throughput_mbps():.2f} Mbps"
                )

            # Stop if test duration exceeded
            if is_final:
                logger.info(f"Test duration ({self.config.test_duration}s) reached")
                self._running = False

        except Exception as e:
            logger.error(f"Error sending audio chunk: {e}")
            self.stats.errors += 1

    async def _send_ping(self) -> None:
        """Send ping to keep connection alive"""
        if not self._websocket:
            return

        try:
            message = {
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            }
            await self._websocket.send(json.dumps(message))
            logger.debug("Sent ping")

        except Exception as e:
            logger.error(f"Error sending ping: {e}")

    async def _handle_server_message(self, message: str) -> None:
        """
        Handle incoming message from server.

        Args:
            message: JSON message from server
        """
        try:
            data = json.loads(message)
            msg_type = data.get("type", "unknown")

            if msg_type == "transcription":
                # Log transcription results
                text = data.get("text", "")
                latency = data.get("latency_ms", 0)
                logger.info(f"📝 Transcription: '{text}' (latency: {latency:.0f}ms)")

            elif msg_type == "pong":
                logger.debug("Received pong")

            elif msg_type == "error":
                error = data.get("error", {})
                logger.error(f"Server error: {error}")

            else:
                logger.debug(f"Received message: {msg_type}")

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from server: {message[:100]}")

    def _cleanup(self) -> None:
        """Cleanup resources"""
        if self._audio_capture and self._audio_capture.is_capturing():
            self._audio_capture.stop()

        # Log final stats
        logger.info("="* 60)
        logger.info("Bridge Statistics:")
        logger.info(f"  Uptime: {self.stats.get_uptime():.1f}s")
        logger.info(f"  Chunks sent: {self.stats.chunks_sent}")
        logger.info(f"  Bytes sent: {self.stats.bytes_sent:,}")
        logger.info(f"  Throughput: {self.stats.get_throughput_mbps():.2f} Mbps")
        logger.info(f"  Reconnections: {self.stats.reconnections}")
        logger.info(f"  Errors: {self.stats.errors}")
        logger.info("=" * 60)

    def stop(self) -> None:
        """Stop the bridge"""
        logger.info("Stopping Audio Bridge...")
        self._running = False
