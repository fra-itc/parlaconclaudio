"""
WebSocket Gateway for Real-Time STT Orchestrator
Manages WebSocket connections, broadcasts, and lifecycle management.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum


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
