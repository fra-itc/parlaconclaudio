"""
Health Check Module for FastAPI Backend

Provides comprehensive health monitoring:
- Redis connectivity checks
- gRPC services availability
- Liveness probes (process alive)
- Readiness probes (ready to serve)
- Detailed metrics collection

Endpoints:
- GET /health - Simple alive check
- GET /health/ready - Readiness probe with dependency checks
- GET /health/live - Liveness probe
- GET /metrics - Prometheus metrics
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from fastapi import APIRouter, status, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

try:
    import redis.asyncio as aioredis
except ImportError:
    import aioredis

from ...shared.protocols.grpc_pool import (
    get_pool_manager,
    ServiceType,
    GrpcPoolManager
)


logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentType(str, Enum):
    """System component types"""
    REDIS = "redis"
    GRPC_STT = "grpc_stt"
    GRPC_NLP = "grpc_nlp"
    GRPC_SUMMARY = "grpc_summary"
    SYSTEM = "system"


@dataclass
class ComponentHealth:
    """Health status of a single component"""
    name: str
    component_type: ComponentType
    status: HealthStatus
    message: str = ""
    response_time_ms: float = 0.0
    last_check: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "type": self.component_type.value,
            "status": self.status.value,
            "message": self.message,
            "response_time_ms": round(self.response_time_ms, 2),
            "last_check": datetime.fromtimestamp(self.last_check).isoformat(),
            "metadata": self.metadata
        }


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: HealthStatus
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    uptime_seconds: float
    version: str = "1.0.0"
    components: Dict[str, Dict[str, Any]]
    summary: Dict[str, Any]


class MetricsResponse(BaseModel):
    """Metrics response model"""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    uptime_seconds: float
    grpc_pools: Dict[str, Any]
    redis_stats: Dict[str, Any]
    system_stats: Dict[str, Any]


class HealthChecker:
    """
    Comprehensive health checker for the orchestrator service

    Monitors:
    - Redis connectivity and performance
    - gRPC service availability
    - System resources
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        check_timeout: float = 5.0
    ):
        self.redis_url = redis_url
        self.check_timeout = check_timeout
        self.start_time = time.time()

        self._redis_client: Optional[aioredis.Redis] = None
        self._grpc_manager: Optional[GrpcPoolManager] = None
        self._component_cache: Dict[str, ComponentHealth] = {}
        self._cache_ttl = 10.0  # Cache results for 10 seconds

    async def initialize(self) -> None:
        """Initialize health checker"""
        logger.info("Initializing health checker")

        # Initialize Redis client
        try:
            self._redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis client initialized for health checks")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")

        # Get gRPC pool manager
        try:
            self._grpc_manager = get_pool_manager()
        except Exception as e:
            logger.warning(f"gRPC pool manager not available: {e}")

    async def close(self) -> None:
        """Close health checker resources"""
        if self._redis_client:
            await self._redis_client.close()
            logger.info("Redis health check client closed")

    @property
    def uptime_seconds(self) -> float:
        """Get service uptime in seconds"""
        return time.time() - self.start_time

    async def check_redis(self) -> ComponentHealth:
        """Check Redis connectivity and performance"""
        component_name = "redis"

        # Check cache
        cached = self._get_cached_result(component_name)
        if cached:
            return cached

        start_time = time.time()

        try:
            if not self._redis_client:
                return ComponentHealth(
                    name=component_name,
                    component_type=ComponentType.REDIS,
                    status=HealthStatus.UNHEALTHY,
                    message="Redis client not initialized",
                    response_time_ms=0.0
                )

            # Ping Redis
            ping_result = await asyncio.wait_for(
                self._redis_client.ping(),
                timeout=self.check_timeout
            )

            response_time = (time.time() - start_time) * 1000

            # Get Redis info
            info = await self._redis_client.info()

            health = ComponentHealth(
                name=component_name,
                component_type=ComponentType.REDIS,
                status=HealthStatus.HEALTHY,
                message="Connected",
                response_time_ms=response_time,
                metadata={
                    "version": info.get("redis_version", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "uptime_days": info.get("uptime_in_days", 0)
                }
            )

            self._cache_result(component_name, health)
            return health

        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            health = ComponentHealth(
                name=component_name,
                component_type=ComponentType.REDIS,
                status=HealthStatus.UNHEALTHY,
                message=f"Timeout after {self.check_timeout}s",
                response_time_ms=response_time
            )
            self._cache_result(component_name, health)
            return health

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            health = ComponentHealth(
                name=component_name,
                component_type=ComponentType.REDIS,
                status=HealthStatus.UNHEALTHY,
                message=f"Error: {str(e)}",
                response_time_ms=response_time
            )
            self._cache_result(component_name, health)
            return health

    async def check_grpc_service(self, service_type: ServiceType) -> ComponentHealth:
        """Check gRPC service availability"""
        component_name = f"grpc_{service_type.value}"

        # Check cache
        cached = self._get_cached_result(component_name)
        if cached:
            return cached

        start_time = time.time()

        try:
            if not self._grpc_manager:
                return ComponentHealth(
                    name=component_name,
                    component_type=getattr(ComponentType, f"GRPC_{service_type.value.upper()}"),
                    status=HealthStatus.UNHEALTHY,
                    message="gRPC pool manager not initialized",
                    response_time_ms=0.0
                )

            # Check if service pool exists
            if service_type not in self._grpc_manager.pools:
                return ComponentHealth(
                    name=component_name,
                    component_type=getattr(ComponentType, f"GRPC_{service_type.value.upper()}"),
                    status=HealthStatus.UNHEALTHY,
                    message="Service pool not configured",
                    response_time_ms=0.0
                )

            # Get pool health
            pool = self._grpc_manager.pools[service_type]
            healthy_count = sum(1 for c in pool.connections if c.is_ready)
            total_count = len(pool.connections)

            response_time = (time.time() - start_time) * 1000

            # Get pool metrics
            metrics = pool.get_metrics()

            # Determine status
            if healthy_count == 0:
                status_val = HealthStatus.UNHEALTHY
                message = "No healthy connections"
            elif healthy_count < total_count:
                status_val = HealthStatus.DEGRADED
                message = f"{healthy_count}/{total_count} connections healthy"
            else:
                status_val = HealthStatus.HEALTHY
                message = f"All {total_count} connections healthy"

            health = ComponentHealth(
                name=component_name,
                component_type=getattr(ComponentType, f"GRPC_{service_type.value.upper()}"),
                status=status_val,
                message=message,
                response_time_ms=response_time,
                metadata={
                    "pool_size": total_count,
                    "healthy_connections": healthy_count,
                    "total_requests": metrics.get("total_requests", 0),
                    "success_rate": round(metrics.get("success_rate", 0.0) * 100, 2),
                    "avg_response_time_ms": round(metrics.get("avg_response_time_ms", 0.0), 2)
                }
            )

            self._cache_result(component_name, health)
            return health

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            health = ComponentHealth(
                name=component_name,
                component_type=getattr(ComponentType, f"GRPC_{service_type.value.upper()}"),
                status=HealthStatus.UNHEALTHY,
                message=f"Error: {str(e)}",
                response_time_ms=response_time
            )
            self._cache_result(component_name, health)
            return health

    async def check_all_components(self) -> Dict[str, ComponentHealth]:
        """Check all system components"""
        checks = [
            self.check_redis(),
            self.check_grpc_service(ServiceType.STT),
            self.check_grpc_service(ServiceType.NLP),
            self.check_grpc_service(ServiceType.SUMMARY),
        ]

        results = await asyncio.gather(*checks, return_exceptions=True)

        components = {}
        for result in results:
            if isinstance(result, ComponentHealth):
                components[result.name] = result
            elif isinstance(result, Exception):
                logger.error(f"Health check failed: {result}")

        return components

    def _get_cached_result(self, component_name: str) -> Optional[ComponentHealth]:
        """Get cached health check result if still valid"""
        if component_name in self._component_cache:
            cached = self._component_cache[component_name]
            if time.time() - cached.last_check < self._cache_ttl:
                return cached
        return None

    def _cache_result(self, component_name: str, health: ComponentHealth) -> None:
        """Cache health check result"""
        self._component_cache[component_name] = health

    async def get_health_status(self) -> HealthCheckResponse:
        """Get comprehensive health status"""
        components = await self.check_all_components()

        # Calculate overall status
        statuses = [c.status for c in components.values()]
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED

        # Build summary
        summary = {
            "total_components": len(components),
            "healthy": sum(1 for c in components.values() if c.status == HealthStatus.HEALTHY),
            "degraded": sum(1 for c in components.values() if c.status == HealthStatus.DEGRADED),
            "unhealthy": sum(1 for c in components.values() if c.status == HealthStatus.UNHEALTHY),
        }

        return HealthCheckResponse(
            status=overall_status,
            uptime_seconds=self.uptime_seconds,
            components={name: comp.to_dict() for name, comp in components.items()},
            summary=summary
        )

    async def get_readiness(self) -> bool:
        """Check if service is ready to accept traffic"""
        components = await self.check_all_components()

        # Service is ready if Redis and at least one gRPC service is healthy
        redis_healthy = components.get("redis", ComponentHealth(
            name="redis",
            component_type=ComponentType.REDIS,
            status=HealthStatus.UNHEALTHY
        )).status == HealthStatus.HEALTHY

        grpc_services = [
            components.get(f"grpc_{s.value}") for s in ServiceType
        ]
        any_grpc_healthy = any(
            c and c.status == HealthStatus.HEALTHY
            for c in grpc_services
        )

        return redis_healthy and any_grpc_healthy

    async def get_liveness(self) -> bool:
        """Check if service is alive (simple check)"""
        return True

    async def get_metrics(self) -> MetricsResponse:
        """Get detailed metrics"""
        # gRPC pool metrics
        grpc_metrics = {}
        if self._grpc_manager:
            grpc_metrics = self._grpc_manager.get_all_metrics()

        # Redis stats
        redis_stats = {}
        if self._redis_client:
            try:
                info = await self._redis_client.info()
                redis_stats = {
                    "version": info.get("redis_version", "unknown"),
                    "uptime_days": info.get("uptime_in_days", 0),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_bytes": info.get("used_memory", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0)
                }
            except Exception as e:
                logger.error(f"Failed to get Redis stats: {e}")
                redis_stats = {"error": str(e)}

        # System stats
        system_stats = {
            "uptime_seconds": self.uptime_seconds,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat()
        }

        return MetricsResponse(
            uptime_seconds=self.uptime_seconds,
            grpc_pools=grpc_metrics,
            redis_stats=redis_stats,
            system_stats=system_stats
        )


# Router for health check endpoints
def create_health_router(health_checker: HealthChecker) -> APIRouter:
    """Create FastAPI router with health check endpoints"""
    router = APIRouter(prefix="/health", tags=["health"])

    @router.get(
        "",
        response_model=HealthCheckResponse,
        summary="Health check",
        description="Comprehensive health check of all components"
    )
    async def health():
        """Get overall health status"""
        return await health_checker.get_health_status()

    @router.get(
        "/ready",
        status_code=status.HTTP_200_OK,
        summary="Readiness probe",
        description="Check if service is ready to accept traffic"
    )
    async def readiness():
        """Readiness probe for Kubernetes"""
        is_ready = await health_checker.get_readiness()

        if is_ready:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": "ready", "timestamp": datetime.utcnow().isoformat()}
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready", "timestamp": datetime.utcnow().isoformat()}
            )

    @router.get(
        "/live",
        status_code=status.HTTP_200_OK,
        summary="Liveness probe",
        description="Check if service is alive"
    )
    async def liveness():
        """Liveness probe for Kubernetes"""
        is_alive = await health_checker.get_liveness()

        if is_alive:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": "alive", "timestamp": datetime.utcnow().isoformat()}
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "dead", "timestamp": datetime.utcnow().isoformat()}
            )

    @router.get(
        "/metrics",
        response_model=MetricsResponse,
        summary="Service metrics",
        description="Get detailed service metrics"
    )
    async def metrics():
        """Get service metrics"""
        return await health_checker.get_metrics()

    return router


# Singleton instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker(redis_url: str = "redis://localhost:6379/0") -> HealthChecker:
    """Get or create singleton health checker"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker(redis_url=redis_url)
    return _health_checker


async def initialize_health_checker(redis_url: str = "redis://localhost:6379/0") -> HealthChecker:
    """Initialize health checker"""
    checker = get_health_checker(redis_url)
    await checker.initialize()
    return checker


async def close_health_checker() -> None:
    """Close health checker"""
    global _health_checker
    if _health_checker:
        await _health_checker.close()
        _health_checker = None
