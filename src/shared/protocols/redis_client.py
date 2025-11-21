"""
Redis Client with pub/sub support for RTSTT Integration.

This module provides a robust Redis client with:
- Pub/Sub support for real-time messaging
- Connection management with automatic retry logic
- Async operations using asyncio
- Error handling and logging
- Health check capabilities
"""

import asyncio
import logging
from typing import Optional, Callable, Dict, Any, List
import json
from datetime import datetime

import redis.asyncio as redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError


logger = logging.getLogger(__name__)


class RedisClient:
    """
    Async Redis client with pub/sub support and connection management.

    Features:
    - Automatic reconnection with exponential backoff
    - Subscribe to multiple channels
    - Publish messages to channels
    - Message serialization/deserialization
    - Health monitoring
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_retries: int = 5,
        retry_delay: float = 1.0,
        max_retry_delay: float = 30.0,
        connection_timeout: int = 10,
        socket_keepalive: bool = True,
    ):
        """
        Initialize Redis client.

        Args:
            host: Redis host address
            port: Redis port number
            db: Redis database number
            password: Redis password (if required)
            max_retries: Maximum number of connection retry attempts
            retry_delay: Initial retry delay in seconds
            max_retry_delay: Maximum retry delay in seconds (for exponential backoff)
            connection_timeout: Connection timeout in seconds
            socket_keepalive: Enable TCP keepalive
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_retry_delay = max_retry_delay
        self.connection_timeout = connection_timeout
        self.socket_keepalive = socket_keepalive

        self._client: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._is_connected: bool = False
        self._subscribed_channels: Dict[str, Callable] = {}
        self._listen_task: Optional[asyncio.Task] = None

        logger.info(
            f"RedisClient initialized for {host}:{port} (db={db})"
        )

    async def connect(self) -> bool:
        """
        Establish connection to Redis server with retry logic.

        Returns:
            bool: True if connection successful, False otherwise
        """
        retry_count = 0
        current_delay = self.retry_delay

        while retry_count < self.max_retries:
            try:
                logger.info(
                    f"Attempting to connect to Redis at {self.host}:{self.port} "
                    f"(attempt {retry_count + 1}/{self.max_retries})"
                )

                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    socket_timeout=self.connection_timeout,
                    socket_keepalive=self.socket_keepalive,
                    decode_responses=True,
                    retry_on_timeout=True,
                )

                # Test connection
                await self._client.ping()

                self._is_connected = True
                logger.info(
                    f"Successfully connected to Redis at {self.host}:{self.port}"
                )
                return True

            except (ConnectionError, TimeoutError, RedisError) as e:
                retry_count += 1
                logger.warning(
                    f"Failed to connect to Redis (attempt {retry_count}/{self.max_retries}): {e}"
                )

                if retry_count < self.max_retries:
                    logger.info(f"Retrying in {current_delay:.1f} seconds...")
                    await asyncio.sleep(current_delay)
                    # Exponential backoff
                    current_delay = min(current_delay * 2, self.max_retry_delay)
                else:
                    logger.error(
                        f"Failed to connect to Redis after {self.max_retries} attempts"
                    )
                    self._is_connected = False
                    return False

        return False

    async def disconnect(self):
        """Disconnect from Redis server and cleanup resources."""
        logger.info("Disconnecting from Redis...")

        # Cancel listen task if running
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        # Close pubsub connection
        if self._pubsub:
            try:
                await self._pubsub.unsubscribe()
                await self._pubsub.close()
            except Exception as e:
                logger.error(f"Error closing pubsub connection: {e}")
            finally:
                self._pubsub = None

        # Close main connection
        if self._client:
            try:
                await self._client.close()
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self._client = None

        self._is_connected = False
        self._subscribed_channels.clear()
        logger.info("Disconnected from Redis")

    async def ensure_connected(self) -> bool:
        """
        Ensure Redis connection is active, reconnect if necessary.

        Returns:
            bool: True if connected, False otherwise
        """
        if not self._is_connected or not self._client:
            return await self.connect()

        try:
            await self._client.ping()
            return True
        except (ConnectionError, RedisError) as e:
            logger.warning(f"Connection lost, reconnecting: {e}")
            self._is_connected = False
            return await self.connect()

    async def publish(
        self,
        channel: str,
        message: Any,
        serialize: bool = True
    ) -> bool:
        """
        Publish a message to a Redis channel.

        Args:
            channel: Channel name to publish to
            message: Message to publish (will be JSON-serialized if serialize=True)
            serialize: Whether to JSON-serialize the message

        Returns:
            bool: True if published successfully, False otherwise
        """
        if not await self.ensure_connected():
            logger.error("Cannot publish: not connected to Redis")
            return False

        try:
            # Serialize message if needed
            if serialize:
                if not isinstance(message, str):
                    message = json.dumps(message, default=str)

            # Publish to channel
            num_subscribers = await self._client.publish(channel, message)

            logger.debug(
                f"Published message to channel '{channel}' "
                f"(received by {num_subscribers} subscribers)"
            )
            return True

        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error publishing to channel '{channel}': {e}")
            return False

    async def subscribe(
        self,
        channels: List[str],
        callback: Callable[[str, Dict[str, Any]], None]
    ) -> bool:
        """
        Subscribe to one or more Redis channels.

        Args:
            channels: List of channel names to subscribe to
            callback: Async callback function(channel, message) to handle messages

        Returns:
            bool: True if subscription successful, False otherwise
        """
        if not await self.ensure_connected():
            logger.error("Cannot subscribe: not connected to Redis")
            return False

        try:
            # Create pubsub instance if not exists
            if not self._pubsub:
                self._pubsub = self._client.pubsub()

            # Subscribe to channels
            await self._pubsub.subscribe(*channels)

            # Store callbacks
            for channel in channels:
                self._subscribed_channels[channel] = callback

            logger.info(f"Subscribed to channels: {', '.join(channels)}")

            # Start listening if not already running
            if not self._listen_task or self._listen_task.done():
                self._listen_task = asyncio.create_task(self._listen())

            return True

        except RedisError as e:
            logger.error(f"Error subscribing to channels: {e}")
            return False

    async def unsubscribe(self, channels: Optional[List[str]] = None) -> bool:
        """
        Unsubscribe from Redis channels.

        Args:
            channels: List of channels to unsubscribe from (None = all channels)

        Returns:
            bool: True if unsubscription successful, False otherwise
        """
        if not self._pubsub:
            logger.warning("No active pubsub connection")
            return False

        try:
            if channels:
                await self._pubsub.unsubscribe(*channels)
                for channel in channels:
                    self._subscribed_channels.pop(channel, None)
                logger.info(f"Unsubscribed from channels: {', '.join(channels)}")
            else:
                await self._pubsub.unsubscribe()
                self._subscribed_channels.clear()
                logger.info("Unsubscribed from all channels")

            return True

        except RedisError as e:
            logger.error(f"Error unsubscribing from channels: {e}")
            return False

    async def _listen(self):
        """
        Internal method to listen for messages on subscribed channels.
        Runs as a background task and calls registered callbacks.
        """
        logger.info("Started listening for Redis messages...")

        try:
            while self._is_connected and self._pubsub:
                try:
                    message = await self._pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0
                    )

                    if message and message['type'] == 'message':
                        channel = message['channel']
                        data = message['data']

                        # Try to deserialize JSON
                        try:
                            if isinstance(data, str):
                                data = json.loads(data)
                        except json.JSONDecodeError:
                            logger.warning(
                                f"Received non-JSON message from channel '{channel}'"
                            )

                        # Call registered callback
                        callback = self._subscribed_channels.get(channel)
                        if callback:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(channel, data)
                                else:
                                    callback(channel, data)
                            except Exception as e:
                                logger.error(
                                    f"Error in callback for channel '{channel}': {e}",
                                    exc_info=True
                                )

                    # Small delay to prevent busy loop
                    await asyncio.sleep(0.01)

                except asyncio.CancelledError:
                    logger.info("Listen task cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error receiving message: {e}", exc_info=True)
                    await asyncio.sleep(1)  # Back off on error

        except Exception as e:
            logger.error(f"Fatal error in listen loop: {e}", exc_info=True)
        finally:
            logger.info("Stopped listening for Redis messages")

    async def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis key.

        Args:
            key: Redis key

        Returns:
            Value as string, or None if not found
        """
        if not await self.ensure_connected():
            return None

        try:
            return await self._client.get(key)
        except RedisError as e:
            logger.error(f"Error getting key '{key}': {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        Set value in Redis.

        Args:
            key: Redis key
            value: Value to set
            expire: Optional expiration time in seconds

        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.ensure_connected():
            return False

        try:
            await self._client.set(key, value, ex=expire)
            return True
        except RedisError as e:
            logger.error(f"Error setting key '{key}': {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Redis connection.

        Returns:
            Dict with health status information
        """
        health = {
            "connected": False,
            "timestamp": datetime.utcnow().isoformat(),
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "subscribed_channels": list(self._subscribed_channels.keys()),
        }

        try:
            if self._client:
                await self._client.ping()
                health["connected"] = True

                # Get additional info
                info = await self._client.info("server")
                health["redis_version"] = info.get("redis_version")
                health["uptime_seconds"] = info.get("uptime_in_seconds")

        except Exception as e:
            health["error"] = str(e)
            logger.error(f"Health check failed: {e}")

        return health

    @property
    def is_connected(self) -> bool:
        """Check if client is connected to Redis."""
        return self._is_connected

    @property
    def subscribed_channels(self) -> List[str]:
        """Get list of currently subscribed channels."""
        return list(self._subscribed_channels.keys())
