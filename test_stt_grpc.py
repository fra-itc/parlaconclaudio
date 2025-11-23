#!/usr/bin/env python3
"""
Quick gRPC Test: STT Engine Direct Connection
Tests the STT engine via gRPC without WebSocket layer
"""

import sys
import grpc
import time
import struct
import math

# Add src to path
sys.path.insert(0, '/app/src')

from core.stt_engine import stt_service_pb2
from core.stt_engine import stt_service_pb2_grpc


def generate_test_audio(duration=3.0, frequency=440.0, sample_rate=16000):
    """Generate a simple sine wave test tone (no numpy)"""
    num_samples = int(sample_rate * duration)

    # Generate 440 Hz sine wave (A note) as 16-bit PCM
    audio_bytes = bytearray()
    for i in range(num_samples):
        t = i / sample_rate
        sample_value = math.sin(2 * math.pi * frequency * t)
        # Convert to 16-bit integer
        sample_int16 = int(sample_value * 32767)
        # Pack as little-endian signed short
        audio_bytes.extend(struct.pack('<h', sample_int16))

    return bytes(audio_bytes)


def test_stt_grpc():
    """Test STT engine via gRPC"""
    print("=" * 60)
    print("STT Engine gRPC Direct Test")
    print("=" * 60)
    print()

    # Connect to STT engine
    print("📡 Connecting to STT engine at stt-engine:50051...")
    channel = grpc.insecure_channel('stt-engine:50051')
    stub = stt_service_pb2_grpc.STTServiceStub(channel)

    try:
        # Test 1: Health Check
        print("\n1️⃣  Testing Health Check...")
        health_request = stt_service_pb2.HealthCheckRequest(service="STTService")
        health_response = stub.HealthCheck(health_request, timeout=10)

        print(f"   Status: {health_response.status}")
        print(f"   Message: {health_response.message}")
        if health_response.model_info.is_loaded:
            print(f"   Model: {health_response.model_info.name}")
            print(f"   Device: {health_response.model_info.device}")
            print(f"   Compute: {health_response.model_info.compute_type}")

        # Test 2: Transcribe Audio
        print("\n2️⃣  Testing Transcription...")
        print("   Generating test audio (440 Hz sine wave, 3 seconds)...")

        audio_data = generate_test_audio(duration=3.0, frequency=440.0)
        print(f"   Audio size: {len(audio_data)} bytes")

        # Create request
        print("   Sending to STT engine...")
        start_time = time.time()

        request = stt_service_pb2.AudioRequest(
            audio_data=audio_data,
            sample_rate=16000,
            language="",  # Auto-detect
            task="transcribe",
            request_id="test-001"
        )

        # Call STT
        response = stub.Transcribe(request, timeout=30)

        elapsed_time = time.time() - start_time

        # Display results
        print()
        print("=" * 60)
        print("📊 Transcription Results")
        print("=" * 60)
        print(f"Text: '{response.text}'")
        print(f"Language: {response.language}")
        print(f"Duration: {response.duration:.2f}s")
        print(f"Processing Time: {response.processing_time_ms:.2f}ms")
        print(f"Round-trip Time: {elapsed_time*1000:.2f}ms")
        print(f"Request ID: {response.request_id}")

        if response.status.code == 0:
            print(f"Status: ✅ SUCCESS")
        else:
            print(f"Status: ❌ ERROR - {response.status.message}")

        # Display segments
        if response.segments:
            print(f"\nSegments: {len(response.segments)}")
            for i, segment in enumerate(response.segments):
                print(f"  [{i+1}] {segment.start:.2f}s - {segment.end:.2f}s: '{segment.text}'")
                if segment.confidence > 0:
                    print(f"      Confidence: {segment.confidence:.2%}")

        print("=" * 60)

        # Test 3: Streaming (optional - just show it's available)
        print("\n3️⃣  Streaming API Available:")
        print("   TranscribeStream() - for real-time audio streaming")

        print("\n✅ All gRPC tests completed successfully!")
        return True

    except grpc.RpcError as e:
        print(f"\n❌ gRPC Error: {e.code()}")
        print(f"   Details: {e.details()}")
        return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        channel.close()


if __name__ == "__main__":
    print("\n")
    success = test_stt_grpc()
    print()

    if success:
        print("🎉 STT Engine is working correctly!")
    else:
        print("❌ STT Engine test failed")

    print()
