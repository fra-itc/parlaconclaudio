"""
gRPC Connection Pool Implementation

Provides connection pooling, load balancing, and auto-reconnection
for STT, NLP, and Summary gRPC services.

Features:
- Connection pooling per service
- Round-robin load balancing
- Automatic reconnection on failure
- Async gRPC calls
- Health checking
- Connection lifecycle management
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import time
import random

import grpc
from grpc import aio


logger = logging.getLogger(__name__)


class ServiceType(str, Enum):
    """Supported gRPC service types"""
    STT = "stt"
    NLP = "nlp"
    SUMMARY = "summary"


class ConnectionState(str, Enum):
    """Connection state"""
    IDLE = "idle"
    CONNECTING = "connecting"
    READY = "ready"
    TRANSIENT_FAILURE = "transient_failure"
    SHUTDOWN = "shutdown"


@dataclass
class ServiceConfig:
    """Configuration for a gRPC service"""
    host: str
    port: int
    pool_size: int = 3
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    keepalive_time_ms: int = 10000
    keepalive_timeout_ms: int = 5000
    max_connection_idle_ms: int = 300000  # 5 minutes
    enable_retries: bool = True
    compression: bool = True


@dataclass
class ConnectionMetrics:
    """Connection metrics for monitoring"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_reconnections: int = 0
    avg_response_time_ms: float = 0.0
    last_used: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)


class GrpcConnection:
    """Single gRPC connection with health checking"""

    def __init__(
        self,
        service_type: ServiceType,
        config: ServiceConfig,
        connection_id: int
    ):
        self.service_type = service_type
        self.config = config
        self.connection_id = connection_id
        self.state = ConnectionState.IDLE
        self.metrics = ConnectionMetrics()

        self._channel: Optional[aio.Channel] = None
        self._lock = asyncio.Lock()
        self._reconnect_task: Optional[asyncio.Task] = None

    @property
    def is_ready(self) -> bool:
        """Check if connection is ready for requests"""
        return self.state == ConnectionState.READY and self._channel is not None

    @property
    def address(self) -> str:
        """Get service address"""
        return f"{self.config.host}:{self.config.port}"

    async def connect(self) -> None:
        """Establish gRPC connection"""
        async with self._lock:
            if self.state in (ConnectionState.READY, ConnectionState.CONNECTING):
                return

            try:
                self.state = ConnectionState.CONNECTING
                logger.info(
                    f"[{self.service_type.value}:{self.connection_id}] "
                    f"Connecting to {self.address}"
                )

                # Configure channel options
                options = [
                    ('grpc.keepalive_time_ms', self.config.keepalive_time_ms),
                    ('grpc.keepalive_timeout_ms', self.config.keepalive_timeout_ms),
                    ('grpc.max_connection_idle_ms', self.config.max_connection_idle_ms),
                    ('grpc.http2.max_pings_without_data', 0),
                    ('grpc.keepalive_permit_without_calls', 1),
                ]

                if self.config.enable_retries:
                    options.append(('grpc.enable_retries', 1))

                if self.config.compression:
                    options.append(('grpc.default_compression_algorithm', 'gzip'))

                # Create channel
                self._channel = aio.insecure_channel(
                    self.address,
                    options=options
                )

                # Wait for channel to be ready
                await asyncio.wait_for(
                    self._channel.channel_ready(),
                    timeout=self.config.timeout
                )

                self.state = ConnectionState.READY
                logger.info(
                    f"[{self.service_type.value}:{self.connection_id}] "
                    f"Connected successfully"
                )

            except asyncio.TimeoutError:
                self.state = ConnectionState.TRANSIENT_FAILURE
                logger.error(
                    f"[{self.service_type.value}:{self.connection_id}] "
                    f"Connection timeout after {self.config.timeout}s"
                )
                raise
            except Exception as e:
                self.state = ConnectionState.TRANSIENT_FAILURE
                logger.error(
                    f"[{self.service_type.value}:{self.connection_id}] "
                    f"Connection failed: {e}"
                )
                raise

    async def disconnect(self) -> None:
        """Close gRPC connection"""
        async with self._lock:
            if self._channel:
                try:
                    await self._channel.close()
                    logger.info(
                        f"[{self.service_type.value}:{self.connection_id}] "
                        f"Disconnected"
                    )
                except Exception as e:
                    logger.error(
                        f"[{self.service_type.value}:{self.connection_id}] "
                        f"Error during disconnect: {e}"
                    )
                finally:
                    self._channel = None
                    self.state = ConnectionState.SHUTDOWN

    async def check_health(self) -> bool:
        """Check connection health"""
        if not self._channel:
            return False

        try:
            # Check channel state
            state = self._channel.get_state()
            return state == grpc.ChannelConnectivity.READY
        except Exception as e:
            logger.warning(
                f"[{self.service_type.value}:{self.connection_id}] "
                f"Health check failed: {e}"
            )
            return False

    async def reconnect(self) -> None:
        """Reconnect after failure"""
        self.metrics.total_reconnections += 1

        for attempt in range(self.config.max_retries):
            try:
                await self.disconnect()
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                await self.connect()
                return
            except Exception as e:
                logger.warning(
                    f"[{self.service_type.value}:{self.connection_id}] "
                    f"Reconnection attempt {attempt + 1}/{self.config.max_retries} failed: {e}"
                )

        logger.error(
            f"[{self.service_type.value}:{self.connection_id}] "
            f"Failed to reconnect after {self.config.max_retries} attempts"
        )

    def get_channel(self) -> aio.Channel:
        """Get underlying gRPC channel"""
        if not self._channel:
            raise RuntimeError(f"Connection {self.connection_id} not established")
        return self._channel

    def update_metrics(self, success: bool, response_time_ms: float) -> None:
        """Update connection metrics"""
        self.metrics.total_requests += 1
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1

        # Update moving average
        total = self.metrics.total_requests
        avg = self.metrics.avg_response_time_ms
        self.metrics.avg_response_time_ms = (avg * (total - 1) + response_time_ms) / total
        self.metrics.last_used = time.time()


T = TypeVar('T')


class GrpcConnectionPool(Generic[T]):
    """
    Connection pool for gRPC services

    Features:
    - Multiple connections per service
    - Round-robin load balancing
    - Automatic reconnection
    - Connection health monitoring
    - Metrics collection
    """

    def __init__(
        self,
        service_type: ServiceType,
        config: ServiceConfig
    ):
        self.service_type = service_type
        self.config = config
        self.connections: List[GrpcConnection] = []
        self._current_index = 0
        self._lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize connection pool"""
        if self._initialized:
            return

        logger.info(
            f"[{self.service_type.value}] Initializing connection pool "
            f"with {self.config.pool_size} connections"
        )

        # Create connections
        for i in range(self.config.pool_size):
            conn = GrpcConnection(
                service_type=self.service_type,
                config=self.config,
                connection_id=i
            )
            self.connections.append(conn)

        # Connect all
        connect_tasks = [conn.connect() for conn in self.connections]
        try:
            await asyncio.gather(*connect_tasks, return_exceptions=False)
        except Exception as e:
            logger.error(f"[{self.service_type.value}] Pool initialization failed: {e}")
            raise

        # Start health check background task
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        self._initialized = True
        logger.info(f"[{self.service_type.value}] Connection pool initialized")

    async def close(self) -> None:
        """Close all connections"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        disconnect_tasks = [conn.disconnect() for conn in self.connections]
        await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        self._initialized = False
        logger.info(f"[{self.service_type.value}] Connection pool closed")

    @asynccontextmanager
    async def get_connection(self):
        """
        Get a connection from the pool using round-robin

        Yields:
            GrpcConnection: Available connection
        """
        if not self._initialized:
            await self.initialize()

        connection = await self._get_next_connection()

        if not connection.is_ready:
            logger.warning(
                f"[{self.service_type.value}:{connection.connection_id}] "
                f"Connection not ready, attempting reconnect"
            )
            await connection.reconnect()

        try:
            yield connection
        finally:
            # Connection returned to pool (nothing to do for round-robin)
            pass

    async def _get_next_connection(self) -> GrpcConnection:
        """Get next connection using round-robin load balancing"""
        async with self._lock:
            # Try to find a healthy connection
            for _ in range(len(self.connections)):
                conn = self.connections[self._current_index]
                self._current_index = (self._current_index + 1) % len(self.connections)

                if conn.is_ready:
                    return conn

            # No healthy connections, return first and let caller handle reconnect
            return self.connections[0]

    async def _health_check_loop(self) -> None:
        """Background task to check connection health"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                for conn in self.connections:
                    if not await conn.check_health():
                        logger.warning(
                            f"[{self.service_type.value}:{conn.connection_id}] "
                            f"Health check failed, reconnecting"
                        )
                        asyncio.create_task(conn.reconnect())

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.service_type.value}] Health check error: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated pool metrics"""
        total_requests = sum(c.metrics.total_requests for c in self.connections)
        successful_requests = sum(c.metrics.successful_requests for c in self.connections)
        failed_requests = sum(c.metrics.failed_requests for c in self.connections)
        total_reconnections = sum(c.metrics.total_reconnections for c in self.connections)

        avg_response_time = 0.0
        if total_requests > 0:
            avg_response_time = sum(
                c.metrics.avg_response_time_ms * c.metrics.total_requests
                for c in self.connections
            ) / total_requests

        return {
            "service": self.service_type.value,
            "pool_size": len(self.connections),
            "healthy_connections": sum(1 for c in self.connections if c.is_ready),
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0.0,
            "total_reconnections": total_reconnections,
            "avg_response_time_ms": avg_response_time,
        }


class GrpcPoolManager:
    """
    Manages connection pools for all gRPC services

    Usage:
        manager = GrpcPoolManager()
        await manager.initialize({
            ServiceType.STT: ServiceConfig(host="localhost", port=50051),
            ServiceType.NLP: ServiceConfig(host="localhost", port=50052),
            ServiceType.SUMMARY: ServiceConfig(host="localhost", port=50053),
        })

        async with manager.get_connection(ServiceType.STT) as conn:
            # Use connection
            channel = conn.get_channel()
            # Make gRPC calls...
    """

    def __init__(self):
        self.pools: Dict[ServiceType, GrpcConnectionPool] = {}
        self._initialized = False

    async def initialize(self, service_configs: Dict[ServiceType, ServiceConfig]) -> None:
        """Initialize all service connection pools"""
        if self._initialized:
            return

        logger.info("Initializing gRPC pool manager")

        for service_type, config in service_configs.items():
            pool = GrpcConnectionPool(service_type, config)
            self.pools[service_type] = pool

        # Initialize all pools in parallel
        init_tasks = [pool.initialize() for pool in self.pools.values()]
        await asyncio.gather(*init_tasks)

        self._initialized = True
        logger.info("gRPC pool manager initialized")

    async def close(self) -> None:
        """Close all connection pools"""
        close_tasks = [pool.close() for pool in self.pools.values()]
        await asyncio.gather(*close_tasks, return_exceptions=True)

        self.pools.clear()
        self._initialized = False
        logger.info("gRPC pool manager closed")

    @asynccontextmanager
    async def get_connection(self, service_type: ServiceType):
        """Get connection from specific service pool"""
        if service_type not in self.pools:
            raise ValueError(f"Service {service_type.value} not configured")

        pool = self.pools[service_type]
        async with pool.get_connection() as conn:
            yield conn

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics from all pools"""
        return {
            service_type.value: pool.get_metrics()
            for service_type, pool in self.pools.items()
        }

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all services"""
        results = {}
        for service_type, pool in self.pools.items():
            healthy_count = sum(1 for c in pool.connections if c.is_ready)
            results[service_type.value] = healthy_count > 0
        return results


# Singleton instance
_pool_manager: Optional[GrpcPoolManager] = None


def get_pool_manager() -> GrpcPoolManager:
    """Get or create singleton pool manager"""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = GrpcPoolManager()
    return _pool_manager


async def initialize_grpc_pools(service_configs: Dict[ServiceType, ServiceConfig]) -> None:
    """Initialize global gRPC connection pools"""
    manager = get_pool_manager()
    await manager.initialize(service_configs)


async def close_grpc_pools() -> None:
    """Close all gRPC connection pools"""
    global _pool_manager
    if _pool_manager:
        await _pool_manager.close()
        _pool_manager = None
