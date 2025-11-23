"""
Test script to validate FastAPI and WebSocket functionality
"""

import asyncio
import json
import sys
from datetime import datetime

try:
    import httpx
    from websockets import connect
except ImportError:
    print("Installing test dependencies...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "httpx", "websockets"])
    import httpx
    from websockets import connect


async def test_http_endpoints():
    """Test HTTP endpoints."""
    print("\n=== Testing HTTP Endpoints ===\n")

    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("1. Testing /health endpoint...")
        try:
            response = await client.get("http://localhost:8001/health")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}\n")
        except Exception as e:
            print(f"   Error: {e}\n")
            return False

        # Test root endpoint
        print("2. Testing / endpoint...")
        try:
            response = await client.get("http://localhost:8001/")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}\n")
        except Exception as e:
            print(f"   Error: {e}\n")
            return False

        # Test connections endpoint
        print("3. Testing /connections endpoint...")
        try:
            response = await client.get("http://localhost:8001/connections")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}\n")
        except Exception as e:
            print(f"   Error: {e}\n")
            return False

    return True


async def test_websocket():
    """Test WebSocket endpoint."""
    print("\n=== Testing WebSocket Endpoint ===\n")

    try:
        print("1. Connecting to WebSocket at ws://localhost:8001/ws...")
        async with connect("ws://localhost:8001/ws") as websocket:
            print("   Connected successfully!\n")

            # Receive connection acknowledgment
            print("2. Receiving connection message...")
            message = await websocket.recv()
            data = json.loads(message)
            print(f"   Received: {json.dumps(data, indent=2)}\n")

            # Send a ping message
            print("3. Sending PING message...")
            ping_message = json.dumps({
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            })
            await websocket.send(ping_message)
            print(f"   Sent: {ping_message}\n")

            # Receive pong response
            print("4. Receiving PONG response...")
            message = await websocket.recv()
            data = json.loads(message)
            print(f"   Received: {json.dumps(data, indent=2)}\n")

            # Send a test message
            print("5. Sending test message...")
            test_message = json.dumps({
                "type": "test",
                "data": "Hello from test client!"
            })
            await websocket.send(test_message)
            print(f"   Sent: {test_message}\n")

            # Wait a bit for any response
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(message)
                print(f"   Received: {json.dumps(data, indent=2)}\n")
            except asyncio.TimeoutError:
                print("   No response received (expected for test message)\n")

            print("6. Closing WebSocket connection...")
            await websocket.close()
            print("   Connection closed successfully!\n")

        return True

    except Exception as e:
        print(f"   Error: {e}\n")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("FastAPI + WebSocket Gateway Test Suite")
    print("=" * 60)

    # Test HTTP endpoints
    http_success = await test_http_endpoints()

    # Test WebSocket
    ws_success = await test_websocket()

    # Print summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"HTTP Endpoints: {'PASSED' if http_success else 'FAILED'}")
    print(f"WebSocket:      {'PASSED' if ws_success else 'FAILED'}")
    print("=" * 60)

    return http_success and ws_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
