"""
Test script to verify module imports and basic functionality
"""

import sys
import asyncio

print("=" * 60)
print("Testing gRPC Pool and Health Check Modules")
print("=" * 60)

# Test 1: Import grpc_pool module
print("\n[1/4] Testing grpc_pool module import...")
try:
    from src.shared.protocols.grpc_pool import (
        ServiceType,
        ServiceConfig,
        GrpcConnection,
        GrpcConnectionPool,
        GrpcPoolManager,
        get_pool_manager
    )
    print("[OK] grpc_pool module imported successfully")
    print(f"  - ServiceType enum: {list(ServiceType)}")
except Exception as e:
    print(f"[FAIL] Failed to import grpc_pool: {e}")
    sys.exit(1)

# Test 2: Import health module
print("\n[2/4] Testing health module import...")
try:
    from src.agents.orchestrator.health import (
        HealthStatus,
        ComponentType,
        ComponentHealth,
        HealthChecker,
        create_health_router,
        get_health_checker
    )
    print("[OK] health module imported successfully")
    print(f"  - HealthStatus enum: {list(HealthStatus)}")
    print(f"  - ComponentType enum: {list(ComponentType)}")
except Exception as e:
    print(f"[FAIL] Failed to import health: {e}")
    sys.exit(1)

# Test 3: Test ServiceConfig creation
print("\n[3/4] Testing ServiceConfig creation...")
try:
    config = ServiceConfig(
        host="localhost",
        port=50051,
        pool_size=3,
        max_retries=3,
        timeout=30.0
    )
    print("[OK] ServiceConfig created successfully")
    print(f"  - Host: {config.host}")
    print(f"  - Port: {config.port}")
    print(f"  - Pool Size: {config.pool_size}")
    print(f"  - Timeout: {config.timeout}s")
except Exception as e:
    print(f"[FAIL] Failed to create ServiceConfig: {e}")
    sys.exit(1)

# Test 4: Test HealthChecker instantiation
print("\n[4/4] Testing HealthChecker instantiation...")
try:
    health_checker = HealthChecker(
        redis_url="redis://localhost:6379/0",
        check_timeout=5.0
    )
    print("[OK] HealthChecker instantiated successfully")
    print(f"  - Redis URL: {health_checker.redis_url}")
    print(f"  - Check Timeout: {health_checker.check_timeout}s")
    print(f"  - Uptime: {health_checker.uptime_seconds:.2f}s")
except Exception as e:
    print(f"[FAIL] Failed to instantiate HealthChecker: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("All import tests passed!")
print("=" * 60)

print("\nModule Summary:")
print("  - grpc_pool.py: gRPC connection pooling with load balancing")
print("  - health.py: Health checks for Redis and gRPC services")
print("  - example_app.py: FastAPI integration example")
print("\nReady for integration!")
print("\nTo run the example app:")
print("  uvicorn src.agents.orchestrator.example_app:app --reload")
