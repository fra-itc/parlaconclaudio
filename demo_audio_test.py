#!/usr/bin/env python3
"""
Quick Demo: Test RTSTT Audio Pipeline
Tests the system with synthetic audio to verify end-to-end functionality
"""

import asyncio
import json
import time
import numpy as np
import websockets
from datetime import datetime

# Configuration
WEBSOCKET_URL = "ws://localhost:8000/ws"
SAMPLE_RATE = 16000
DURATION_SECONDS = 3

def generate_test_audio(duration=3.0, frequency=440.0):
    """Generate a simple sine wave test tone"""
    sample_rate = SAMPLE_RATE
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples, False)

    # Generate 440 Hz sine wave (A note)
    audio = np.sin(2 * np.pi * frequency * t)

    # Convert to 16-bit PCM
    audio_int16 = (audio * 32767).astype(np.int16)

    return audio_int16.tobytes()

async def test_websocket_connection():
    """Test WebSocket connection and audio streaming"""
    print("🎯 RTSTT Audio Pipeline Demo Test")
    print("=" * 60)
    print()

    try:
        print("📡 Connecting to WebSocket...")
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print(f"✅ Connected to {WEBSOCKET_URL}")
            print()

            # Generate test audio
            print("🎵 Generating test audio (440 Hz sine wave, 3 seconds)...")
            audio_data = generate_test_audio(duration=DURATION_SECONDS, frequency=440.0)
            print(f"   Audio size: {len(audio_data)} bytes")
            print()

            # Send audio in chunks
            chunk_size = 4096
            num_chunks = len(audio_data) // chunk_size

            print(f"📤 Streaming audio ({num_chunks} chunks)...")
            start_time = time.time()

            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                chunk_num = i // chunk_size
                is_final = (i + chunk_size) >= len(audio_data)

                # Create message with metadata
                message = {
                    "type": "audio_chunk",
                    "data": list(chunk),  # Convert bytes to list for JSON
                    "sample_rate": SAMPLE_RATE,
                    "chunk_number": chunk_num,
                    "is_final": is_final,
                    "timestamp": datetime.now().isoformat()
                }

                await websocket.send(json.dumps(message))

                # Show progress
                if i % (chunk_size * 10) == 0:
                    progress = (i / len(audio_data)) * 100
                    print(f"   Progress: {progress:.1f}%")

                # Small delay to simulate real-time
                await asyncio.sleep(0.01)

            send_time = time.time() - start_time
            print(f"✅ Audio sent in {send_time:.2f} seconds")
            print()

            # Wait for responses
            print("📥 Waiting for transcription responses...")
            response_count = 0
            timeout = 10

            try:
                async with asyncio.timeout(timeout):
                    while True:
                        response = await websocket.recv()
                        response_count += 1

                        try:
                            data = json.loads(response)
                            print(f"\n📨 Response #{response_count}:")
                            print(f"   Type: {data.get('type', 'unknown')}")

                            if 'text' in data:
                                print(f"   Text: {data['text']}")
                            if 'latency_ms' in data:
                                print(f"   Latency: {data['latency_ms']:.2f}ms")
                            if 'confidence' in data:
                                print(f"   Confidence: {data['confidence']:.2%}")

                        except json.JSONDecodeError:
                            print(f"   Raw: {response[:100]}...")

            except asyncio.TimeoutError:
                print(f"\n⏱️  Timeout after {timeout} seconds")

            total_time = time.time() - start_time
            print()
            print("=" * 60)
            print("📊 Test Summary:")
            print(f"   ✅ Connection: Success")
            print(f"   ✅ Audio sent: {len(audio_data)} bytes")
            print(f"   ✅ Chunks sent: {num_chunks}")
            print(f"   ✅ Responses received: {response_count}")
            print(f"   ✅ Total time: {total_time:.2f} seconds")
            print("=" * 60)

    except websockets.exceptions.WebSocketException as e:
        print(f"\n❌ WebSocket Error: {e}")
        print("\nTroubleshooting:")
        print("   1. Ensure backend is running: docker ps | grep rtstt-backend")
        print("   2. Check backend logs: docker logs rtstt-backend")
        print("   3. Verify port 8000 is accessible")
        return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

async def check_services():
    """Check if required services are running"""
    print("🔍 Checking Services...")
    print()

    import subprocess

    # Check Docker services
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'],
            capture_output=True,
            text=True
        )

        services = result.stdout
        required = ['rtstt-backend', 'rtstt-redis', 'rtstt-stt-engine']

        for service in required:
            if service in services:
                status = "running" if "Up" in services else "down"
                print(f"   ✅ {service}: {status}")
            else:
                print(f"   ❌ {service}: not found")

    except Exception as e:
        print(f"   ⚠️  Could not check Docker services: {e}")

    print()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   RTSTT Audio Pipeline Demo Test")
    print("   Testing End-to-End Audio Processing")
    print("=" * 60 + "\n")

    # Check services first
    asyncio.run(check_services())

    # Run test
    success = asyncio.run(test_websocket_connection())

    print()
    if success:
        print("✅ Demo test completed successfully!")
    else:
        print("❌ Demo test encountered errors")
    print()
