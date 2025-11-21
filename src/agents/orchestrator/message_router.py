"""
Message Router for RTSTT Integration.

Routes messages from Redis channels to WebSocket clients with:
- Channel-to-client routing logic
- Message format handling (JSON)
- Error handling and recovery
- Client connection management
- Message queuing and buffering
"""

import asyncio
import logging
from typing import Dict, Set, Optional, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


logger = logging.getLogger(__name__)


class ChannelType(str, Enum):
    """Redis channel types for different pipeline stages."""
    STT_OUTPUT = "stt_output"
    NLP_OUTPUT = "nlp_output"
    SUMMARY_OUTPUT = "summary_output"
    SYSTEM_STATUS = "system_status"
    ERROR = "error"


@dataclass
class WebSocketClient:
    """Represents a WebSocket client connection."""
    client_id: str
    websocket: Any  # WebSocket connection object
    subscribed_channels: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    last_message_at: Optional[datetime] = None

    def __hash__(self):
        return hash(self.client_id)


@dataclass
class Message:
    """Represents a message to be routed."""
    channel: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: Optional[str] = None

    def to_json(self) -> str:
        """Serialize message to JSON."""
        payload = {
            "channel": self.channel,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.message_id:
            payload["message_id"] = self.message_id
        return json.dumps(payload, default=str)


class MessageRouter:
    """
    Routes messages from Redis channels to WebSocket clients.

    Features:
    - Subscribe clients to specific channels
    - Route messages based on channel subscriptions
    - Handle client connections and disconnections
    - Message buffering for disconnected clients
    - Error handling and retry logic
    - Statistics and monitoring
    """

    def __init__(
        self,
        redis_client,
        max_buffer_size: int = 100,
        buffer_ttl_seconds: int = 300,
        enable_buffering: bool = True,
    ):
        """
        Initialize message router.

        Args:
            redis_client: RedisClient instance for pub/sub
            max_buffer_size: Maximum messages to buffer per client
            buffer_ttl_seconds: Time to keep buffered messages (seconds)
            enable_buffering: Whether to buffer messages for offline clients
        """
        self.redis_client = redis_client
        self.max_buffer_size = max_buffer_size
        self.buffer_ttl_seconds = buffer_ttl_seconds
        self.enable_buffering = enable_buffering

        # Client management
        self._clients: Dict[str, WebSocketClient] = {}
        self._channel_subscriptions: Dict[str, Set[str]] = {
            channel.value: set() for channel in ChannelType
        }

        # Message buffering
        self._message_buffers: Dict[str, List[Message]] = {}

        # Statistics
        self._stats = {
            "total_messages_routed": 0,
            "total_messages_buffered": 0,
            "total_clients_connected": 0,
            "errors": 0,
        }

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

        logger.info(
            f"MessageRouter initialized (buffering={'enabled' if enable_buffering else 'disabled'})"
        )

    async def start(self) -> bool:
        """
        Start the message router and subscribe to Redis channels.

        Returns:
            bool: True if started successfully
        """
        try:
            # Subscribe to all channel types
            channels = [channel.value for channel in ChannelType]

            success = await self.redis_client.subscribe(
                channels=channels,
                callback=self._handle_redis_message
            )

            if success:
                logger.info(
                    f"MessageRouter started, subscribed to channels: {', '.join(channels)}"
                )
                return True
            else:
                logger.error("Failed to subscribe to Redis channels")
                return False

        except Exception as e:
            logger.error(f"Error starting MessageRouter: {e}", exc_info=True)
            return False

    async def stop(self):
        """Stop the message router and cleanup resources."""
        logger.info("Stopping MessageRouter...")

        # Disconnect all clients
        client_ids = list(self._clients.keys())
        for client_id in client_ids:
            await self.remove_client(client_id)

        # Unsubscribe from Redis channels
        await self.redis_client.unsubscribe()

        logger.info("MessageRouter stopped")

    async def add_client(
        self,
        client_id: str,
        websocket: Any,
        channels: Optional[List[str]] = None
    ) -> bool:
        """
        Add a WebSocket client and subscribe to channels.

        Args:
            client_id: Unique client identifier
            websocket: WebSocket connection object
            channels: List of channels to subscribe to (None = all channels)

        Returns:
            bool: True if client added successfully
        """
        async with self._lock:
            try:
                # Default to all channels if not specified
                if channels is None:
                    channels = [channel.value for channel in ChannelType]

                # Validate channels
                valid_channels = {channel.value for channel in ChannelType}
                channels = [ch for ch in channels if ch in valid_channels]

                # Create client
                client = WebSocketClient(
                    client_id=client_id,
                    websocket=websocket,
                    subscribed_channels=set(channels)
                )

                # Add to client registry
                self._clients[client_id] = client

                # Update channel subscriptions
                for channel in channels:
                    self._channel_subscriptions[channel].add(client_id)

                # Send buffered messages if any
                if self.enable_buffering and client_id in self._message_buffers:
                    await self._flush_buffer(client_id)

                self._stats["total_clients_connected"] += 1

                logger.info(
                    f"Client '{client_id}' connected, subscribed to: {', '.join(channels)}"
                )
                return True

            except Exception as e:
                logger.error(f"Error adding client '{client_id}': {e}", exc_info=True)
                self._stats["errors"] += 1
                return False

    async def remove_client(self, client_id: str) -> bool:
        """
        Remove a WebSocket client.

        Args:
            client_id: Client identifier to remove

        Returns:
            bool: True if client removed successfully
        """
        async with self._lock:
            try:
                client = self._clients.pop(client_id, None)

                if not client:
                    logger.warning(f"Client '{client_id}' not found")
                    return False

                # Remove from channel subscriptions
                for channel in client.subscribed_channels:
                    self._channel_subscriptions[channel].discard(client_id)

                # Clear message buffer if not needed
                if not self.enable_buffering:
                    self._message_buffers.pop(client_id, None)

                logger.info(
                    f"Client '{client_id}' disconnected "
                    f"(sent {client.message_count} messages)"
                )
                return True

            except Exception as e:
                logger.error(f"Error removing client '{client_id}': {e}", exc_info=True)
                self._stats["errors"] += 1
                return False

    async def subscribe_client(
        self,
        client_id: str,
        channels: List[str]
    ) -> bool:
        """
        Subscribe a client to additional channels.

        Args:
            client_id: Client identifier
            channels: List of channels to subscribe to

        Returns:
            bool: True if subscription successful
        """
        async with self._lock:
            client = self._clients.get(client_id)

            if not client:
                logger.error(f"Client '{client_id}' not found")
                return False

            try:
                # Validate channels
                valid_channels = {channel.value for channel in ChannelType}
                channels = [ch for ch in channels if ch in valid_channels]

                # Add to client subscriptions
                for channel in channels:
                    if channel not in client.subscribed_channels:
                        client.subscribed_channels.add(channel)
                        self._channel_subscriptions[channel].add(client_id)

                logger.info(
                    f"Client '{client_id}' subscribed to additional channels: {', '.join(channels)}"
                )
                return True

            except Exception as e:
                logger.error(
                    f"Error subscribing client '{client_id}' to channels: {e}",
                    exc_info=True
                )
                self._stats["errors"] += 1
                return False

    async def unsubscribe_client(
        self,
        client_id: str,
        channels: List[str]
    ) -> bool:
        """
        Unsubscribe a client from channels.

        Args:
            client_id: Client identifier
            channels: List of channels to unsubscribe from

        Returns:
            bool: True if unsubscription successful
        """
        async with self._lock:
            client = self._clients.get(client_id)

            if not client:
                logger.error(f"Client '{client_id}' not found")
                return False

            try:
                # Remove from client subscriptions
                for channel in channels:
                    client.subscribed_channels.discard(channel)
                    self._channel_subscriptions[channel].discard(client_id)

                logger.info(
                    f"Client '{client_id}' unsubscribed from channels: {', '.join(channels)}"
                )
                return True

            except Exception as e:
                logger.error(
                    f"Error unsubscribing client '{client_id}' from channels: {e}",
                    exc_info=True
                )
                self._stats["errors"] += 1
                return False

    async def _handle_redis_message(self, channel: str, data: Dict[str, Any]):
        """
        Handle incoming message from Redis channel.

        Args:
            channel: Channel name
            data: Message data
        """
        try:
            # Create message object
            message = Message(
                channel=channel,
                data=data,
                message_id=data.get("id") or data.get("message_id")
            )

            # Get subscribed clients for this channel
            client_ids = self._channel_subscriptions.get(channel, set()).copy()

            if not client_ids:
                logger.debug(f"No clients subscribed to channel '{channel}'")
                return

            logger.debug(
                f"Routing message from channel '{channel}' to {len(client_ids)} clients"
            )

            # Route to each subscribed client
            for client_id in client_ids:
                await self._route_to_client(client_id, message)

            self._stats["total_messages_routed"] += 1

        except Exception as e:
            logger.error(
                f"Error handling Redis message from channel '{channel}': {e}",
                exc_info=True
            )
            self._stats["errors"] += 1

    async def _route_to_client(self, client_id: str, message: Message):
        """
        Route a message to a specific client.

        Args:
            client_id: Target client identifier
            message: Message to send
        """
        client = self._clients.get(client_id)

        if not client:
            logger.warning(f"Client '{client_id}' not found for routing")
            return

        try:
            # Try to send message
            message_json = message.to_json()
            await client.websocket.send_text(message_json)

            # Update statistics
            client.message_count += 1
            client.last_message_at = datetime.utcnow()

            logger.debug(f"Sent message to client '{client_id}'")

        except Exception as e:
            logger.error(
                f"Error sending message to client '{client_id}': {e}",
                exc_info=True
            )

            # Buffer message if enabled
            if self.enable_buffering:
                await self._buffer_message(client_id, message)

            self._stats["errors"] += 1

    async def _buffer_message(self, client_id: str, message: Message):
        """
        Buffer a message for a client.

        Args:
            client_id: Client identifier
            message: Message to buffer
        """
        try:
            if client_id not in self._message_buffers:
                self._message_buffers[client_id] = []

            buffer = self._message_buffers[client_id]

            # Add to buffer
            buffer.append(message)

            # Trim buffer if exceeds max size
            if len(buffer) > self.max_buffer_size:
                buffer.pop(0)  # Remove oldest message

            self._stats["total_messages_buffered"] += 1

            logger.debug(
                f"Buffered message for client '{client_id}' "
                f"(buffer size: {len(buffer)})"
            )

        except Exception as e:
            logger.error(
                f"Error buffering message for client '{client_id}': {e}",
                exc_info=True
            )

    async def _flush_buffer(self, client_id: str):
        """
        Send all buffered messages to a client.

        Args:
            client_id: Client identifier
        """
        buffer = self._message_buffers.pop(client_id, [])

        if not buffer:
            return

        logger.info(
            f"Flushing {len(buffer)} buffered messages to client '{client_id}'"
        )

        for message in buffer:
            # Check if message is still within TTL
            age_seconds = (datetime.utcnow() - message.timestamp).total_seconds()
            if age_seconds > self.buffer_ttl_seconds:
                logger.debug(f"Skipping expired buffered message (age: {age_seconds}s)")
                continue

            await self._route_to_client(client_id, message)

    async def broadcast(
        self,
        channel: str,
        data: Dict[str, Any],
        client_ids: Optional[List[str]] = None
    ) -> int:
        """
        Broadcast a message to clients.

        Args:
            channel: Channel name
            data: Message data
            client_ids: Optional list of specific client IDs (None = all subscribed)

        Returns:
            int: Number of clients message was sent to
        """
        try:
            message = Message(channel=channel, data=data)

            # Determine target clients
            if client_ids is None:
                targets = self._channel_subscriptions.get(channel, set()).copy()
            else:
                targets = set(client_ids) & self._channel_subscriptions.get(channel, set())

            # Send to each target
            for client_id in targets:
                await self._route_to_client(client_id, message)

            logger.info(
                f"Broadcasted message to {len(targets)} clients on channel '{channel}'"
            )
            return len(targets)

        except Exception as e:
            logger.error(f"Error broadcasting message: {e}", exc_info=True)
            self._stats["errors"] += 1
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get router statistics.

        Returns:
            Dict with statistics
        """
        return {
            **self._stats,
            "active_clients": len(self._clients),
            "buffered_clients": len(self._message_buffers),
            "channel_subscriptions": {
                channel: len(clients)
                for channel, clients in self._channel_subscriptions.items()
            },
        }

    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific client.

        Args:
            client_id: Client identifier

        Returns:
            Dict with client info, or None if not found
        """
        client = self._clients.get(client_id)

        if not client:
            return None

        return {
            "client_id": client.client_id,
            "subscribed_channels": list(client.subscribed_channels),
            "connected_at": client.connected_at.isoformat(),
            "message_count": client.message_count,
            "last_message_at": client.last_message_at.isoformat() if client.last_message_at else None,
            "buffered_messages": len(self._message_buffers.get(client_id, [])),
        }

    def list_clients(self) -> List[Dict[str, Any]]:
        """
        List all connected clients.

        Returns:
            List of client info dicts
        """
        return [
            self.get_client_info(client_id)
            for client_id in self._clients.keys()
        ]
