"""
Example FastAPI application with gRPC pool and health checks

This demonstrates how to integrate the gRPC connection pool
and health monitoring into a FastAPI application.

Usage:
    uvicorn src.agents.orchestrator.example_app:app --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse

from ...shared.protocols.grpc_pool import (
    ServiceType,
    ServiceConfig,
    get_pool_manager,
    initialize_grpc_pools,
    close_grpc_pools
)
from .health import (
    HealthChecker,
    create_health_router,
    initialize_health_checker,
    close_health_checker
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager

    Handles startup and shutdown of:
    - gRPC connection pools
    - Health checker
    """
    logger.info("Starting application...")

    # Configure gRPC services
    service_configs = {
        ServiceType.STT: ServiceConfig(
            host="localhost",
            port=50051,
            pool_size=3,
            max_retries=3,
            timeout=30.0
        ),
        ServiceType.NLP: ServiceConfig(
            host="localhost",
            port=50052,
            pool_size=2,
            max_retries=3,
            timeout=30.0
        ),
        ServiceType.SUMMARY: ServiceConfig(
            host="localhost",
            port=50053,
            pool_size=2,
            max_retries=3,
            timeout=30.0
        ),
    }

    try:
        # Initialize gRPC pools
        logger.info("Initializing gRPC connection pools...")
        await initialize_grpc_pools(service_configs)
        logger.info("gRPC pools initialized")

        # Initialize health checker
        logger.info("Initializing health checker...")
        health_checker = await initialize_health_checker(
            redis_url="redis://localhost:6379/0"
        )
        logger.info("Health checker initialized")

        # Store health checker in app state
        app.state.health_checker = health_checker

        logger.info("Application startup complete")

        yield

    finally:
        # Cleanup on shutdown
        logger.info("Shutting down application...")

        await close_health_checker()
        logger.info("Health checker closed")

        await close_grpc_pools()
        logger.info("gRPC pools closed")

        logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Real-Time STT Orchestrator",
    description="Multi-agent orchestrated speech-to-text system",
    version="1.0.0",
    lifespan=lifespan
)


# Include health check router
@app.on_event("startup")
async def setup_routes():
    """Setup routes after health checker is initialized"""
    health_checker = app.state.health_checker
    health_router = create_health_router(health_checker)
    app.include_router(health_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Real-Time STT Orchestrator",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/v1/services")
async def list_services():
    """List available gRPC services"""
    pool_manager = get_pool_manager()

    services = []
    for service_type, pool in pool_manager.pools.items():
        metrics = pool.get_metrics()
        services.append({
            "service": service_type.value,
            "address": f"{pool.config.host}:{pool.config.port}",
            "status": "healthy" if metrics["healthy_connections"] > 0 else "unhealthy",
            "pool_size": metrics["pool_size"],
            "healthy_connections": metrics["healthy_connections"],
            "metrics": metrics
        })

    return {"services": services}


@app.post("/api/v1/transcribe")
async def transcribe_audio():
    """
    Example endpoint to transcribe audio using STT service

    In production, this would:
    1. Get connection from STT pool
    2. Make gRPC call to STT service
    3. Return transcription result
    """
    pool_manager = get_pool_manager()

    try:
        async with pool_manager.get_connection(ServiceType.STT) as conn:
            # Here you would make actual gRPC call
            # channel = conn.get_channel()
            # stub = stt_pb2_grpc.STTServiceStub(channel)
            # response = await stub.Transcribe(request)

            return {
                "status": "success",
                "message": "This is a mock response. Implement actual gRPC call.",
                "connection_id": conn.connection_id,
                "service": ServiceType.STT.value
            }

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.post("/api/v1/analyze")
async def analyze_text():
    """
    Example endpoint to analyze text using NLP service

    In production, this would:
    1. Get connection from NLP pool
    2. Make gRPC call to NLP service
    3. Return analysis result
    """
    pool_manager = get_pool_manager()

    try:
        async with pool_manager.get_connection(ServiceType.NLP) as conn:
            # Here you would make actual gRPC call
            # channel = conn.get_channel()
            # stub = nlp_pb2_grpc.NLPServiceStub(channel)
            # response = await stub.Analyze(request)

            return {
                "status": "success",
                "message": "This is a mock response. Implement actual gRPC call.",
                "connection_id": conn.connection_id,
                "service": ServiceType.NLP.value
            }

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.post("/api/v1/summarize")
async def summarize_text():
    """
    Example endpoint to summarize text using Summary service

    In production, this would:
    1. Get connection from Summary pool
    2. Make gRPC call to Summary service
    3. Return summary result
    """
    pool_manager = get_pool_manager()

    try:
        async with pool_manager.get_connection(ServiceType.SUMMARY) as conn:
            # Here you would make actual gRPC call
            # channel = conn.get_channel()
            # stub = summary_pb2_grpc.SummaryServiceStub(channel)
            # response = await stub.Summarize(request)

            return {
                "status": "success",
                "message": "This is a mock response. Implement actual gRPC call.",
                "connection_id": conn.connection_id,
                "service": ServiceType.SUMMARY.value
            }

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "example_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
