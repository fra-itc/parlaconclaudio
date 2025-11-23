"""
WebSocket Gateway for Real-Time STT Orchestrator
Manages WebSocket connections, broadcasts, and lifecycle management.
"""

import asyncio
import json
import logging
import struct
from typing import Dict, Set, Optional, Any, List
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

from src.shared.protocols.grpc_pool import ServiceType, get_pool_manager

# Import STT service protobuf definitions
import sys
import os
sys.path.insert(0, '/app/src/core/stt_engine')
import stt_service_pb2
import stt_service_pb2_grpc


logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types."""
    CONNECTION = "connection"
    TRANSCRIPTION = "transcription"
    PARTIAL = "partial"
    FINAL = "final"
    ERROR = "error"
    STATUS = "status"
    PING = "ping"
    PONG = "pong"


class WebSocketManager:
    """
    Manages WebSocket connections for real-time communication.

    Features:
    - Connection lifecycle management
    - Broadcast messages to all or specific clients
    - Client registration and tracking
    - Error handling and recovery
    - Connection health monitoring
    """

    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_metadata: Dict[str, Dict[str, Any]] = {}
        self.audio_buffers: Dict[str, List[bytes]] = {}  # Buffer audio chunks per client
        self._lock = asyncio.Lock()
        logger.info("WebSocketManager initialized")

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            client_id: Unique identifier for the client
        """
        try:
            await websocket.accept()

            async with self._lock:
                self.active_connections[client_id] = websocket
                self.client_metadata[client_id] = {
                    "connected_at": datetime.utcnow().isoformat(),
                    "message_count": 0,
                    "last_activity": datetime.utcnow().isoformat()
                }
                self.audio_buffers[client_id] = []  # Initialize audio buffer

            logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

            # Send connection acknowledgment
            await self.send_personal_message(
                message={
                    "type": MessageType.CONNECTION,
                    "status": "connected",
                    "client_id": client_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                client_id=client_id
            )

        except Exception as e:
            logger.error(f"Error connecting client {client_id}: {e}")
            raise

    async def disconnect(self, client_id: str) -> None:
        """
        Disconnect and remove a client connection.

        Args:
            client_id: Unique identifier for the client
        """
        async with self._lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]

            if client_id in self.audio_buffers:
                del self.audio_buffers[client_id]

            if client_id in self.client_metadata:
                connection_duration = None
                if "connected_at" in self.client_metadata[client_id]:
                    connected_at = datetime.fromisoformat(self.client_metadata[client_id]["connected_at"])
                    connection_duration = (datetime.utcnow() - connected_at).total_seconds()

                del self.client_metadata[client_id]

                logger.info(
                    f"Client {client_id} disconnected. "
                    f"Duration: {connection_duration:.2f}s. "
                    f"Remaining connections: {len(self.active_connections)}"
                )

    async def send_personal_message(self, message: Dict[str, Any], client_id: str) -> bool:
        """
        Send a message to a specific client.

        Args:
            message: Message data to send
            client_id: Target client identifier

        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if client_id not in self.active_connections:
            logger.warning(f"Cannot send message to unknown client: {client_id}")
            return False

        try:
            websocket = self.active_connections[client_id]
            await websocket.send_json(message)

            # Update client metadata
            if client_id in self.client_metadata:
                self.client_metadata[client_id]["message_count"] += 1
                self.client_metadata[client_id]["last_activity"] = datetime.utcnow().isoformat()

            return True

        except WebSocketDisconnect:
            logger.warning(f"Client {client_id} disconnected during send")
            await self.disconnect(client_id)
            return False

        except Exception as e:
            logger.error(f"Error sending message to client {client_id}: {e}")
            return False

    async def broadcast(self, message: Dict[str, Any], exclude: Optional[Set[str]] = None) -> int:
        """
        Broadcast a message to all connected clients.

        Args:
            message: Message data to broadcast
            exclude: Set of client IDs to exclude from broadcast

        Returns:
            int: Number of clients that received the message
        """
        if exclude is None:
            exclude = set()

        success_count = 0
        failed_clients = []

        # Get snapshot of current connections
        async with self._lock:
            client_ids = list(self.active_connections.keys())

        for client_id in client_ids:
            if client_id in exclude:
                continue

            success = await self.send_personal_message(message, client_id)
            if success:
                success_count += 1
            else:
                failed_clients.append(client_id)

        if failed_clients:
            logger.warning(f"Failed to broadcast to clients: {failed_clients}")

        logger.debug(f"Broadcast message to {success_count} clients")
        return success_count

    async def broadcast_transcription(
        self,
        text: str,
        is_final: bool = False,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Broadcast a transcription result to all clients.

        Args:
            text: Transcription text
            is_final: Whether this is a final or partial transcription
            confidence: Confidence score (0.0 to 1.0)
            metadata: Additional metadata

        Returns:
            int: Number of clients that received the message
        """
        message = {
            "type": MessageType.FINAL if is_final else MessageType.PARTIAL,
            "data": {
                "text": text,
                "is_final": is_final,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        if metadata:
            message["data"]["metadata"] = metadata

        return await self.broadcast(message)

    async def broadcast_error(self, error_message: str, error_code: Optional[str] = None) -> int:
        """
        Broadcast an error message to all clients.

        Args:
            error_message: Error description
            error_code: Optional error code

        Returns:
            int: Number of clients that received the message
        """
        message = {
            "type": MessageType.ERROR,
            "error": {
                "message": error_message,
                "code": error_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        return await self.broadcast(message)

    async def broadcast_status(self, status: str, details: Optional[Dict[str, Any]] = None) -> int:
        """
        Broadcast a status update to all clients.

        Args:
            status: Status message
            details: Additional status details

        Returns:
            int: Number of clients that received the message
        """
        message = {
            "type": MessageType.STATUS,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }

        if details:
            message["details"] = details

        return await self.broadcast(message)

    def get_connection_count(self) -> int:
        """
        Get the number of active connections.

        Returns:
            int: Number of active connections
        """
        return len(self.active_connections)

    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific client.

        Args:
            client_id: Client identifier

        Returns:
            Optional[Dict]: Client metadata or None if not found
        """
        return self.client_metadata.get(client_id)

    def get_all_clients_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata for all connected clients.

        Returns:
            Dict: Dictionary mapping client IDs to their metadata
        """
        return self.client_metadata.copy()

    async def handle_client_message(self, client_id: str, message: Any) -> None:
        """
        Handle incoming message from a client.

        Args:
            client_id: Client identifier
            message: Message data (can be text or JSON)
        """
        try:
            # Parse message if it's a string
            if isinstance(message, str):
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    data = {"text": message}
            else:
                data = message

            # Handle different message types
            msg_type = data.get("type", "unknown")

            if msg_type == MessageType.PING:
                # Respond to ping with pong
                await self.send_personal_message(
                    message={"type": MessageType.PONG, "timestamp": datetime.utcnow().isoformat()},
                    client_id=client_id
                )

            elif msg_type == "audio_chunk":
                # Process audio chunk
                await self._process_audio_chunk(client_id, data)

            else:
                # Log other message types
                logger.info(f"Received message from {client_id}: type={msg_type}")

        except Exception as e:
            logger.error(f"Error handling message from client {client_id}: {e}")
            await self.send_personal_message(
                message={
                    "type": MessageType.ERROR,
                    "error": {"message": "Failed to process message", "code": "MESSAGE_PROCESSING_ERROR"}
                },
                client_id=client_id
            )

    async def _process_audio_chunk(self, client_id: str, data: Dict[str, Any]) -> None:
        """
        Process an audio chunk from a client.

        Args:
            client_id: Client identifier
            data: Audio chunk data
        """
        try:
            # Extract audio data (convert from list of integers to bytes)
            audio_data_list = data.get("data", [])
            if isinstance(audio_data_list, list):
                # Convert list of integers to bytes
                audio_bytes = bytes(audio_data_list)
            elif isinstance(audio_data_list, str):
                # Handle base64 if needed
                import base64
                audio_bytes = base64.b64decode(audio_data_list)
            else:
                audio_bytes = audio_data_list

            # Get audio parameters
            sample_rate = data.get("sample_rate", 16000)
            chunk_number = data.get("chunk_number", 0)
            is_final = data.get("is_final", False)

            # Buffer audio chunk
            if client_id not in self.audio_buffers:
                self.audio_buffers[client_id] = []

            self.audio_buffers[client_id].append(audio_bytes)

            # Process when we have enough audio or if it's final
            buffer_size = sum(len(chunk) for chunk in self.audio_buffers[client_id])
            min_buffer_size = sample_rate * 2 * 2  # 2 seconds at 16kHz, 16-bit = 64KB

            if buffer_size >= min_buffer_size or is_final:
                # Combine buffered chunks
                combined_audio = b''.join(self.audio_buffers[client_id])
                self.audio_buffers[client_id] = []  # Clear buffer

                # Send to STT for transcription
                await self._transcribe_audio(client_id, combined_audio, sample_rate)

        except Exception as e:
            logger.error(f"Error processing audio chunk from {client_id}: {e}")
            await self.send_personal_message(
                message={
                    "type": MessageType.ERROR,
                    "error": {"message": "Failed to process audio chunk", "code": "AUDIO_PROCESSING_ERROR"}
                },
                client_id=client_id
            )

    async def _transcribe_audio(self, client_id: str, audio_data: bytes, sample_rate: int) -> None:
        """
        Send audio to STT service for transcription, then process through NLP and Summary.

        Args:
            client_id: Client identifier
            audio_data: Raw audio bytes
            sample_rate: Audio sample rate
        """
        try:
            pipeline_start = datetime.utcnow()
            logger.info(f"[{client_id}] Starting full pipeline: STT → NLP → Summary")
            logger.info(f"[{client_id}] Sending {len(audio_data)} bytes to STT service")

            # Get gRPC connection pool
            pool_manager = get_pool_manager()

            # Step 1: STT - Transcribe audio
            stt_start = datetime.utcnow()
            async with pool_manager.get_connection(ServiceType.STT) as conn:
                channel = conn.get_channel()
                stub = stt_service_pb2_grpc.STTServiceStub(channel)

                # Create request
                request = stt_service_pb2.AudioRequest(
                    audio_data=audio_data,
                    sample_rate=sample_rate,
                    language="",  # Auto-detect
                    task="transcribe",
                    request_id=client_id
                )

                # Call STT
                stt_response = await stub.Transcribe(request)
                stt_latency = (datetime.utcnow() - stt_start).total_seconds() * 1000

                transcription_text = stt_response.text
                logger.info(f"[{client_id}] STT completed in {stt_latency:.0f}ms: '{transcription_text[:100]}...'")

            # Skip NLP/Summary for very short transcriptions
            if len(transcription_text.strip()) < 10:
                logger.info(f"[{client_id}] Transcription too short, skipping NLP/Summary")
                await self.send_personal_message(
                    message={
                        "type": MessageType.TRANSCRIPTION,
                        "text": transcription_text,
                        "language": stt_response.language,
                        "duration": stt_response.duration,
                        "latency_ms": stt_latency,
                        "confidence": stt_response.segments[0].confidence if stt_response.segments else 0.0,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    client_id=client_id
                )
                return

            # Step 2: NLP - Analyze sentiment and extract keywords
            nlp_result = None
            try:
                nlp_start = datetime.utcnow()
                # For POC, use simple keyword extraction instead of full NLP service
                # TODO: Integrate with full NLP service via Redis streams for production
                nlp_result = await self._extract_keywords(transcription_text)
                nlp_latency = (datetime.utcnow() - nlp_start).total_seconds() * 1000
                logger.info(f"[{client_id}] NLP completed in {nlp_latency:.0f}ms")
            except Exception as e:
                logger.warning(f"[{client_id}] NLP processing failed: {e}, continuing without NLP")
                nlp_latency = 0

            # Step 3: Summary - Generate summary for longer texts
            summary_result = None
            if len(transcription_text) > 100:  # Only summarize longer texts
                try:
                    summary_start = datetime.utcnow()
                    # For POC, use simple summarization
                    # TODO: Integrate with full Summary service via Redis streams for production
                    summary_result = await self._generate_summary(transcription_text)
                    summary_latency = (datetime.utcnow() - summary_start).total_seconds() * 1000
                    logger.info(f"[{client_id}] Summary completed in {summary_latency:.0f}ms")
                except Exception as e:
                    logger.warning(f"[{client_id}] Summary generation failed: {e}, continuing without summary")
                    summary_latency = 0
            else:
                summary_latency = 0

            # Calculate total pipeline latency
            total_latency = (datetime.utcnow() - pipeline_start).total_seconds() * 1000

            # Send enriched response to client
            response_message = {
                "type": MessageType.TRANSCRIPTION,
                "transcription": {
                    "text": transcription_text,
                    "language": stt_response.language,
                    "duration": stt_response.duration,
                    "confidence": stt_response.segments[0].confidence if stt_response.segments else 0.0,
                },
                "latency": {
                    "stt_ms": stt_latency,
                    "nlp_ms": nlp_latency,
                    "summary_ms": summary_latency,
                    "total_ms": total_latency
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            # Add NLP results if available
            if nlp_result:
                response_message["nlp"] = nlp_result

            # Add summary if available
            if summary_result:
                response_message["summary"] = summary_result

            await self.send_personal_message(
                message=response_message,
                client_id=client_id
            )

            logger.info(
                f"[{client_id}] Full pipeline completed in {total_latency:.0f}ms "
                f"(STT: {stt_latency:.0f}ms, NLP: {nlp_latency:.0f}ms, Summary: {summary_latency:.0f}ms)"
            )

        except Exception as e:
            logger.error(f"Error in transcription pipeline for {client_id}: {e}", exc_info=True)
            await self.send_personal_message(
                message={
                    "type": MessageType.ERROR,
                    "error": {"message": f"Pipeline failed: {str(e)}", "code": "PIPELINE_ERROR"}
                },
                client_id=client_id
            )

    async def _extract_keywords(self, text: str) -> Dict[str, Any]:
        """
        Extract keywords from text (simplified version for POC).

        Args:
            text: Input text

        Returns:
            Dictionary with keyword analysis
        """
        # Simple keyword extraction based on word frequency
        # TODO: Replace with full NLP service integration
        import re
        from collections import Counter

        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                     'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                     'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
                     'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}

        # Extract words
        words = re.findall(r'\b[a-z]+\b', text.lower())
        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]

        # Get top keywords
        word_counts = Counter(filtered_words)
        top_keywords = [{"word": word, "count": count}
                       for word, count in word_counts.most_common(5)]

        return {
            "keywords": top_keywords,
            "word_count": len(words),
            "unique_words": len(set(filtered_words))
        }

    async def _generate_summary(self, text: str, max_sentences: int = 2) -> Dict[str, Any]:
        """
        Generate summary of text (simplified version for POC).

        Args:
            text: Input text
            max_sentences: Maximum sentences in summary

        Returns:
            Dictionary with summary
        """
        # Simple extractive summarization - take first sentences
        # TODO: Replace with full Summary service integration
        import re

        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        summary_sentences = sentences[:max_sentences]
        summary_text = '. '.join(summary_sentences)
        if summary_text and not summary_text.endswith('.'):
            summary_text += '.'

        return {
            "text": summary_text,
            "original_length": len(text),
            "summary_length": len(summary_text),
            "compression_ratio": len(summary_text) / len(text) if text else 0
        }

    async def cleanup(self) -> None:
        """Clean up all connections and resources."""
        logger.info("Cleaning up WebSocketManager...")

        async with self._lock:
            client_ids = list(self.active_connections.keys())

        for client_id in client_ids:
            try:
                await self.active_connections[client_id].close()
            except Exception as e:
                logger.error(f"Error closing connection for client {client_id}: {e}")
            finally:
                await self.disconnect(client_id)

        logger.info("WebSocketManager cleanup completed")


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
