#!/usr/bin/env python3
"""
Test script for gRPC STT Server

Tests the gRPC server functionality without actually running inference.
"""

import sys
import time
import logging
from concurrent import futures

# Add src to path
sys.path.insert(0, 'src')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all required modules can be imported."""
    logger.info("Testing imports...")

    try:
        import grpc
        logger.info("  - grpc: OK")
    except ImportError as e:
        logger.error(f"  - grpc: FAILED - {e}")
        return False

    try:
        from core.stt_engine import stt_service_pb2
        from core.stt_engine import stt_service_pb2_grpc
        logger.info("  - stt_service protobuf files: OK")
    except ImportError as e:
        logger.error(f"  - stt_service protobuf files: FAILED - {e}")
        return False

    try:
        from core.stt_engine.grpc_server import STTEngineServicer
        logger.info("  - grpc_server module: OK")
    except ImportError as e:
        logger.error(f"  - grpc_server module: FAILED - {e}")
        return False

    try:
        from core.stt_engine.redis_consumer import RedisAudioConsumer
        logger.info("  - redis_consumer module: OK")
    except ImportError as e:
        logger.error(f"  - redis_consumer module: FAILED - {e}")
        return False

    logger.info("All imports successful!")
    return True


def test_server_creation():
    """Test that the gRPC server can be created (without starting Whisper)."""
    logger.info("\nTesting server creation...")

    try:
        import grpc
        from core.stt_engine import stt_service_pb2_grpc

        # Create a test server (don't initialize WhisperRTX)
        server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=1),
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),
            ]
        )

        # Test binding to port
        port = server.add_insecure_port('[::]:50051')

        logger.info(f"  - Server created successfully")
        logger.info(f"  - Bound to port: {port}")

        # Don't actually start the server, just test creation
        logger.info("  - Server creation test: OK")

        return True

    except Exception as e:
        logger.error(f"  - Server creation test: FAILED - {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_protobuf_messages():
    """Test protobuf message creation."""
    logger.info("\nTesting protobuf messages...")

    try:
        from core.stt_engine import stt_service_pb2

        # Test AudioRequest creation
        request = stt_service_pb2.AudioRequest(
            audio_data=b'\x00\x01' * 100,
            sample_rate=16000,
            language="it",
            task="transcribe",
            request_id="test_123"
        )
        logger.info("  - AudioRequest: OK")

        # Test TranscriptionResponse creation
        response = stt_service_pb2.TranscriptionResponse(
            text="Test transcription",
            language="it",
            duration=1.5,
            processing_time_ms=100.0,
            request_id="test_123"
        )
        logger.info("  - TranscriptionResponse: OK")

        # Test Segment creation
        segment = stt_service_pb2.Segment(
            text="Test segment",
            start=0.0,
            end=1.0,
            confidence=0.95
        )
        response.segments.append(segment)
        logger.info("  - Segment: OK")

        # Test HealthCheckRequest
        health_req = stt_service_pb2.HealthCheckRequest(service="stt")
        logger.info("  - HealthCheckRequest: OK")

        # Test HealthCheckResponse
        health_resp = stt_service_pb2.HealthCheckResponse(
            status=stt_service_pb2.HealthCheckResponse.SERVING,
            message="Service is operational"
        )
        logger.info("  - HealthCheckResponse: OK")

        logger.info("All protobuf message tests passed!")
        return True

    except Exception as e:
        logger.error(f"  - Protobuf test: FAILED - {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_redis_consumer_structure():
    """Test Redis consumer class structure (without connecting to Redis)."""
    logger.info("\nTesting Redis consumer structure...")

    try:
        from core.stt_engine.redis_consumer import RedisAudioConsumer

        # Check that the class has required methods
        required_methods = [
            '_connect_redis',
            '_init_engine',
            '_ensure_consumer_group',
            'start',
            'stop',
            '_process_message',
            '_publish_result',
            '_publish_error'
        ]

        for method in required_methods:
            if not hasattr(RedisAudioConsumer, method):
                logger.error(f"  - Missing method: {method}")
                return False
            logger.info(f"  - Method '{method}': OK")

        logger.info("Redis consumer structure test passed!")
        return True

    except Exception as e:
        logger.error(f"  - Redis consumer test: FAILED - {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("gRPC STT Server Test Suite")
    logger.info("=" * 60)

    results = []

    # Test 1: Imports
    results.append(("Import Test", test_imports()))

    # Test 2: Server creation
    results.append(("Server Creation Test", test_server_creation()))

    # Test 3: Protobuf messages
    results.append(("Protobuf Messages Test", test_protobuf_messages()))

    # Test 4: Redis consumer structure
    results.append(("Redis Consumer Structure Test", test_redis_consumer_structure()))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)

    passed = 0
    failed = 0

    for name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    logger.info("=" * 60)
    logger.info(f"Total: {passed} passed, {failed} failed")
    logger.info("=" * 60)

    if failed > 0:
        logger.error("\nSome tests failed!")
        sys.exit(1)
    else:
        logger.info("\nAll tests passed!")
        logger.info("\nNote: This test does NOT load the Whisper model or connect to Redis.")
        logger.info("To fully test the server, you need:")
        logger.info("  1. NVIDIA RTX GPU with CUDA support")
        logger.info("  2. Whisper model downloaded")
        logger.info("  3. Redis server running")
        sys.exit(0)


if __name__ == "__main__":
    main()
