"""
WebSocket Audio Streaming Integration Tests

Tests real-time audio streaming over WebSocket, including:
- Connection establishment and lifecycle
- Audio chunk streaming
- Transcription response handling
- Latency measurement
- Connection recovery
- Various streaming scenarios

Requires: WebSocket gateway running on ws://localhost:8000/ws

Author: ORCHIDEA Agent System
Created: 2025-11-23
"""

import pytest
import asyncio
import json
import time
import numpy as np
from pathlib import Path
import sys
from typing import List, Dict, Any
import websockets
from websockets.exceptions import ConnectionClosed

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


class WebSocketAudioTester:
    """WebSocket audio streaming tester."""

    def __init__(self, ws_url: str = "ws://localhost:8000/ws"):
        """
        Initialize WebSocket tester.

        Args:
            ws_url: WebSocket URL
        """
        self.ws_url = ws_url
        self.websocket = None
        self.received_messages: List[Dict[str, Any]] = []
        self.latencies: List[float] = []
        self.send_timestamps: Dict[int, float] = {}

    async def connect(self, client_id: str = "test_client"):
        """
        Connect to WebSocket server.

        Args:
            client_id: Client identifier
        """
        url_with_id = f"{self.ws_url}?client_id={client_id}"
        self.websocket = await websockets.connect(url_with_id)

        # Wait for connection acknowledgment
        msg = await self.websocket.recv()
        ack = json.loads(msg)
        assert ack["type"] == "connection"
        assert ack["status"] == "connected"

        return ack

    async def disconnect(self):
        """Disconnect from WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def send_audio_chunk(self, audio_data: np.ndarray, chunk_id: int = 0):
        """
        Send audio chunk to server.

        Args:
            audio_data: Audio samples (int16)
            chunk_id: Chunk identifier for latency tracking
        """
        # Record send time for latency measurement
        send_time = time.time()
        self.send_timestamps[chunk_id] = send_time

        # Convert to bytes
        audio_bytes = audio_data.tobytes()

        # Send as binary message
        await self.websocket.send(audio_bytes)

    async def send_audio_chunk_json(self, audio_data: np.ndarray, chunk_id: int = 0):
        """
        Send audio chunk as JSON message.

        Args:
            audio_data: Audio samples (int16)
            chunk_id: Chunk identifier
        """
        send_time = time.time()
        self.send_timestamps[chunk_id] = send_time

        # Convert to list for JSON
        audio_list = audio_data.tolist()

        message = {
            "type": "audio",
            "chunk_id": chunk_id,
            "audio_data": audio_list,
            "sample_rate": 16000,
            "timestamp": send_time
        }

        await self.websocket.send(json.dumps(message))

    async def receive_message(self, timeout: float = 5.0):
        """
        Receive message from server.

        Args:
            timeout: Timeout in seconds

        Returns:
            Received message (parsed JSON)
        """
        try:
            msg = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)

            # Parse message
            if isinstance(msg, str):
                parsed = json.loads(msg)
            else:
                # Binary message
                parsed = {"type": "binary", "data": msg}

            # Calculate latency if this is a response to a chunk
            if "chunk_id" in parsed and parsed["chunk_id"] in self.send_timestamps:
                receive_time = time.time()
                send_time = self.send_timestamps[parsed["chunk_id"]]
                latency = (receive_time - send_time) * 1000  # ms
                self.latencies.append(latency)
                parsed["latency_ms"] = latency

            self.received_messages.append(parsed)
            return parsed

        except asyncio.TimeoutError:
            return None

    def get_average_latency(self) -> float:
        """Get average latency in milliseconds."""
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    def get_latency_percentile(self, percentile: float) -> float:
        """Get latency percentile in milliseconds."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * percentile / 100)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]


@pytest.mark.asyncio
class TestWebSocketConnection:
    """Test WebSocket connection lifecycle."""

    async def test_connection_establishment(self):
        """Test successful WebSocket connection."""
        tester = WebSocketAudioTester()

        try:
            ack = await tester.connect(client_id="test_conn_1")

            assert ack["client_id"] == "test_conn_1"
            assert "timestamp" in ack

        finally:
            await tester.disconnect()

    async def test_multiple_connections(self):
        """Test multiple concurrent connections."""
        testers = []

        try:
            # Connect multiple clients
            for i in range(3):
                tester = WebSocketAudioTester()
                await tester.connect(client_id=f"test_client_{i}")
                testers.append(tester)

            # Verify all connected
            assert len(testers) == 3

        finally:
            # Disconnect all
            for tester in testers:
                await tester.disconnect()

    async def test_reconnection(self):
        """Test reconnection after disconnect."""
        tester = WebSocketAudioTester()

        try:
            # Connect
            await tester.connect(client_id="test_reconnect")

            # Disconnect
            await tester.disconnect()

            # Reconnect
            await tester.connect(client_id="test_reconnect")

            # Should succeed
            assert tester.websocket is not None

        finally:
            await tester.disconnect()


@pytest.mark.asyncio
class TestAudioStreaming:
    """Test audio streaming over WebSocket."""

    async def test_send_audio_chunk(self):
        """Test sending a single audio chunk."""
        try:
            from tests.utils.audio_loader import AudioLoader
        except ImportError:
            pytest.skip("AudioLoader not available (numpy not installed)")

        tester = WebSocketAudioTester()
        loader = AudioLoader(sample_rate=16000)

        try:
            await tester.connect(client_id="test_audio_1")

            # Generate test audio
            audio_float = np.random.randn(1600).astype(np.float32)  # 100ms at 16kHz
            audio_int16 = loader.to_int16(audio_float)

            # Send audio chunk
            await tester.send_audio_chunk(audio_int16, chunk_id=0)

            # Wait for response (may timeout if server doesn't respond)
            response = await tester.receive_message(timeout=2.0)

            # If we got a response, verify it
            if response:
                assert "type" in response

        finally:
            await tester.disconnect()

    async def test_continuous_audio_stream(self):
        """Test continuous audio streaming."""
        try:
            from tests.utils.audio_loader import AudioLoader
        except ImportError:
            pytest.skip("AudioLoader not available")

        tester = WebSocketAudioTester()
        loader = AudioLoader(sample_rate=16000)

        try:
            await tester.connect(client_id="test_stream_1")

            # Stream multiple chunks
            num_chunks = 10
            for i in range(num_chunks):
                audio_float = np.random.randn(1600).astype(np.float32)
                audio_int16 = loader.to_int16(audio_float)

                await tester.send_audio_chunk(audio_int16, chunk_id=i)

                # Small delay to simulate real-time streaming
                await asyncio.sleep(0.01)

            # Verify chunks were sent
            assert len(tester.send_timestamps) == num_chunks

        finally:
            await tester.disconnect()

    async def test_chunked_audio_with_pauses(self):
        """Test streaming with pauses between chunks."""
        try:
            from tests.utils.audio_loader import AudioLoader
        except ImportError:
            pytest.skip("AudioLoader not available")

        tester = WebSocketAudioTester()
        loader = AudioLoader(sample_rate=16000)

        try:
            await tester.connect(client_id="test_pauses")

            # Send chunk, pause, send chunk
            for i in range(3):
                audio_float = np.random.randn(1600).astype(np.float32)
                audio_int16 = loader.to_int16(audio_float)

                await tester.send_audio_chunk(audio_int16, chunk_id=i)

                # Pause between chunks
                await asyncio.sleep(0.5)

            assert len(tester.send_timestamps) == 3

        finally:
            await tester.disconnect()


@pytest.mark.asyncio
class TestStreamingScenarios:
    """Test various streaming scenarios."""

    async def test_rapid_start_stop(self):
        """Test rapid connection start/stop cycles."""
        for i in range(5):
            tester = WebSocketAudioTester()

            # Connect
            await tester.connect(client_id=f"test_rapid_{i}")

            # Send single chunk
            audio = np.random.randint(-32768, 32767, size=1600, dtype=np.int16)
            await tester.send_audio_chunk(audio, chunk_id=0)

            # Immediately disconnect
            await tester.disconnect()

    async def test_large_audio_chunk(self):
        """Test streaming large audio chunk."""
        try:
            from tests.utils.audio_loader import AudioLoader
        except ImportError:
            pytest.skip("AudioLoader not available")

        tester = WebSocketAudioTester()
        loader = AudioLoader(sample_rate=16000)

        try:
            await tester.connect(client_id="test_large")

            # Generate 1 second of audio (large chunk)
            audio_float = np.random.randn(16000).astype(np.float32)
            audio_int16 = loader.to_int16(audio_float)

            await tester.send_audio_chunk(audio_int16, chunk_id=0)

            # Should not crash
            assert tester.websocket is not None

        finally:
            await tester.disconnect()

    async def test_empty_audio_chunk(self):
        """Test sending empty audio chunk."""
        tester = WebSocketAudioTester()

        try:
            await tester.connect(client_id="test_empty")

            # Send empty audio
            empty_audio = np.array([], dtype=np.int16)
            await tester.send_audio_chunk(empty_audio, chunk_id=0)

            # Should not crash (may get error response)
            await asyncio.sleep(0.1)

        finally:
            await tester.disconnect()


@pytest.mark.asyncio
class TestLatencyMeasurement:
    """Test round-trip latency measurement."""

    async def test_measure_latency(self):
        """Test latency measurement for audio streaming."""
        try:
            from tests.utils.audio_loader import AudioLoader
        except ImportError:
            pytest.skip("AudioLoader not available")

        tester = WebSocketAudioTester()
        loader = AudioLoader(sample_rate=16000)

        try:
            await tester.connect(client_id="test_latency")

            # Send chunks and track latency
            for i in range(5):
                audio_float = np.random.randn(1600).astype(np.float32)
                audio_int16 = loader.to_int16(audio_float)

                await tester.send_audio_chunk(audio_int16, chunk_id=i)

                # Try to receive response
                response = await tester.receive_message(timeout=1.0)

                await asyncio.sleep(0.1)

            # Check if we measured any latencies
            if tester.latencies:
                avg_latency = tester.get_average_latency()
                print(f"\nAverage latency: {avg_latency:.2f} ms")

                # Latency should be reasonable (< 5 seconds)
                assert avg_latency < 5000

        finally:
            await tester.disconnect()


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and edge cases."""

    async def test_invalid_message_format(self):
        """Test sending invalid message format."""
        tester = WebSocketAudioTester()

        try:
            await tester.connect(client_id="test_invalid")

            # Send invalid JSON
            await tester.websocket.send("invalid json {{{")

            # Should either get error response or disconnect
            await asyncio.sleep(0.1)

        except Exception:
            # Exception is acceptable
            pass
        finally:
            try:
                await tester.disconnect()
            except:
                pass

    async def test_connection_timeout(self):
        """Test connection behavior without activity."""
        tester = WebSocketAudioTester()

        try:
            await tester.connect(client_id="test_timeout")

            # Wait without sending anything
            await asyncio.sleep(2.0)

            # Connection should still be alive (or timeout gracefully)
            # This depends on server configuration

        finally:
            await tester.disconnect()


@pytest.mark.asyncio
class TestPerformanceMetrics:
    """Test performance metrics collection."""

    async def test_throughput_measurement(self):
        """Test audio streaming throughput."""
        try:
            from tests.utils.audio_loader import AudioLoader
        except ImportError:
            pytest.skip("AudioLoader not available")

        tester = WebSocketAudioTester()
        loader = AudioLoader(sample_rate=16000)

        try:
            await tester.connect(client_id="test_throughput")

            # Stream for 1 second
            start_time = time.time()
            chunks_sent = 0

            while time.time() - start_time < 1.0:
                audio_float = np.random.randn(1600).astype(np.float32)  # 100ms
                audio_int16 = loader.to_int16(audio_float)

                await tester.send_audio_chunk(audio_int16, chunk_id=chunks_sent)
                chunks_sent += 1

                await asyncio.sleep(0.01)  # 10ms delay

            duration = time.time() - start_time
            throughput = chunks_sent / duration

            print(f"\nThroughput: {throughput:.2f} chunks/second")
            print(f"Chunks sent: {chunks_sent}")

            # Should achieve reasonable throughput (> 5 chunks/sec)
            assert throughput > 5

        finally:
            await tester.disconnect()


# Helper function to run async tests
def run_async_test(coro):
    """Run async test coroutine."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


if __name__ == "__main__":
    # Run basic connection test
    print("Testing WebSocket connection...")
    run_async_test(TestWebSocketConnection().test_connection_establishment())
    print("✓ Connection test passed")
