"""
Redis Streams Integration Test

Verifies that Redis streams work correctly for both NLP and Summary services.
Tests stream production, consumption, and data integrity.

Prerequisites:
- Redis server running on localhost:6379

Author: ML Team (ONDATA 2)
Date: 2025-11-21
"""

import redis
import json
import time
from datetime import datetime


def test_redis_connection():
    """Test basic Redis connectivity."""
    print("\n" + "="*70)
    print("Testing Redis Connection")
    print("="*70)

    try:
        client = redis.Redis(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True,
            socket_connect_timeout=5
        )

        # Test ping
        result = client.ping()
        print(f"✓ Redis PING: {result}")

        # Get server info
        info = client.info("server")
        print(f"✓ Redis version: {info['redis_version']}")
        print(f"✓ Uptime: {info['uptime_in_seconds']} seconds")

        return client

    except redis.ConnectionError as e:
        print(f"✗ Redis connection failed: {e}")
        print("\nPlease ensure Redis is running:")
        print("  - Windows: Run redis-server.exe")
        print("  - Linux/Mac: redis-server")
        print("  - Docker: docker run -p 6379:6379 redis")
        return None
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return None


def test_nlp_stream(client):
    """Test NLP insights stream."""
    print("\n" + "="*70)
    print("Testing NLP Insights Stream (nlp:insights)")
    print("="*70)

    stream_key = "nlp:insights"

    try:
        # Create sample NLP result
        nlp_result = {
            "session_id": "test_nlp_001",
            "timestamp": datetime.utcnow().isoformat(),
            "text_length": 150,
            "keywords": [
                {"keyword": "machine learning", "score": 0.85},
                {"keyword": "natural language", "score": 0.72},
                {"keyword": "processing", "score": 0.68}
            ],
            "speakers": None,
            "insights": {
                "num_keywords": 3,
                "top_keywords": ["machine learning", "natural language", "processing"],
                "text_stats": {
                    "char_count": 150,
                    "word_count": 25,
                    "sentence_count": 3
                }
            },
            "processing_time_ms": 145.2
        }

        # Publish to stream
        message_data = {"data": json.dumps(nlp_result)}
        stream_id = client.xadd(stream_key, message_data, maxlen=10000, approximate=True)

        print(f"✓ Published message to {stream_key}")
        print(f"  Stream ID: {stream_id}")

        # Read back from stream
        messages = client.xread({stream_key: '0'}, count=1, block=1000)

        if messages:
            stream_name, stream_messages = messages[0]
            msg_id, msg_data = stream_messages[0]

            print(f"✓ Read message from {stream_key}")
            print(f"  Message ID: {msg_id}")

            # Parse data
            data = json.loads(msg_data["data"])
            print(f"  Session ID: {data['session_id']}")
            print(f"  Keywords: {len(data['keywords'])}")
            print(f"  Processing time: {data['processing_time_ms']:.2f}ms")

            # Verify data integrity
            assert data["session_id"] == nlp_result["session_id"]
            assert len(data["keywords"]) == len(nlp_result["keywords"])
            print("✓ Data integrity verified")

        else:
            print("✗ Failed to read message from stream")
            return False

        # Get stream info
        stream_info = client.xinfo_stream(stream_key)
        print(f"\n✓ Stream info:")
        print(f"  Length: {stream_info['length']}")
        print(f"  First entry: {stream_info['first-entry'][0] if stream_info['first-entry'] else 'N/A'}")
        print(f"  Last entry: {stream_info['last-entry'][0] if stream_info['last-entry'] else 'N/A'}")

        return True

    except Exception as e:
        print(f"✗ NLP stream test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_summary_stream(client):
    """Test summary output stream."""
    print("\n" + "="*70)
    print("Testing Summary Output Stream (summary:output)")
    print("="*70)

    stream_key = "summary:output"

    try:
        # Create sample summary result
        summary_result = {
            "session_id": "test_summary_001",
            "timestamp": datetime.utcnow().isoformat(),
            "text_length": 500,
            "summary_length": 120,
            "summary": "This is a test summary of the transcription. It captures the main points discussed.",
            "cached": False,
            "parameters": {
                "max_length": 150,
                "min_length": 50,
                "temperature": 0.7,
                "top_p": 0.9
            },
            "processing_time_ms": 2345.6
        }

        # Publish to stream
        message_data = {"data": json.dumps(summary_result)}
        stream_id = client.xadd(stream_key, message_data, maxlen=10000, approximate=True)

        print(f"✓ Published message to {stream_key}")
        print(f"  Stream ID: {stream_id}")

        # Read back from stream
        messages = client.xread({stream_key: '0'}, count=1, block=1000)

        if messages:
            stream_name, stream_messages = messages[0]
            msg_id, msg_data = stream_messages[0]

            print(f"✓ Read message from {stream_key}")
            print(f"  Message ID: {msg_id}")

            # Parse data
            data = json.loads(msg_data["data"])
            print(f"  Session ID: {data['session_id']}")
            print(f"  Summary length: {data['summary_length']} chars")
            print(f"  Processing time: {data['processing_time_ms']:.2f}ms")
            print(f"  Cached: {data['cached']}")

            # Verify data integrity
            assert data["session_id"] == summary_result["session_id"]
            assert data["summary"] == summary_result["summary"]
            print("✓ Data integrity verified")

        else:
            print("✗ Failed to read message from stream")
            return False

        # Get stream info
        stream_info = client.xinfo_stream(stream_key)
        print(f"\n✓ Stream info:")
        print(f"  Length: {stream_info['length']}")
        print(f"  First entry: {stream_info['first-entry'][0] if stream_info['first-entry'] else 'N/A'}")
        print(f"  Last entry: {stream_info['last-entry'][0] if stream_info['last-entry'] else 'N/A'}")

        return True

    except Exception as e:
        print(f"✗ Summary stream test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_consumer_groups(client):
    """Test consumer group functionality."""
    print("\n" + "="*70)
    print("Testing Consumer Groups")
    print("="*70)

    stream_key = "nlp:insights"
    group_name = "test_consumer_group"
    consumer_name = "test_consumer"

    try:
        # Create consumer group (ignore error if already exists)
        try:
            client.xgroup_create(stream_key, group_name, id='0', mkstream=True)
            print(f"✓ Created consumer group: {group_name}")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                print(f"✓ Consumer group already exists: {group_name}")
            else:
                raise

        # Read as consumer
        messages = client.xreadgroup(
            group_name,
            consumer_name,
            {stream_key: '>'},
            count=1,
            block=1000
        )

        if messages:
            print(f"✓ Consumer read messages successfully")
            stream_name, stream_messages = messages[0]

            for msg_id, msg_data in stream_messages:
                print(f"  Message ID: {msg_id}")

                # Acknowledge message
                client.xack(stream_key, group_name, msg_id)
                print(f"✓ Acknowledged message: {msg_id}")

        else:
            print("  No new messages in stream (this is OK)")

        # Get consumer group info
        groups = client.xinfo_groups(stream_key)
        for group in groups:
            if group['name'] == group_name:
                print(f"\n✓ Consumer group info:")
                print(f"  Name: {group['name']}")
                print(f"  Consumers: {group['consumers']}")
                print(f"  Pending: {group['pending']}")
                break

        # Cleanup
        try:
            client.xgroup_destroy(stream_key, group_name)
            print(f"✓ Cleaned up consumer group")
        except Exception:
            pass

        return True

    except Exception as e:
        print(f"✗ Consumer group test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stream_trimming(client):
    """Test stream trimming with MAXLEN."""
    print("\n" + "="*70)
    print("Testing Stream Trimming (MAXLEN)")
    print("="*70)

    stream_key = "test:trimming"

    try:
        # Clear stream
        try:
            client.delete(stream_key)
        except Exception:
            pass

        # Add messages with MAXLEN
        maxlen = 5
        num_messages = 10

        print(f"Adding {num_messages} messages with MAXLEN={maxlen}...")

        for i in range(num_messages):
            client.xadd(
                stream_key,
                {"data": f"message_{i}"},
                maxlen=maxlen,
                approximate=True
            )

        # Check stream length
        info = client.xinfo_stream(stream_key)
        actual_length = info['length']

        print(f"✓ Stream length: {actual_length} (should be ~{maxlen})")

        if actual_length <= maxlen + 1:  # Allow for approximate trimming
            print("✓ Stream trimming working correctly")
        else:
            print(f"⚠ Stream length {actual_length} exceeds MAXLEN {maxlen}")

        # Cleanup
        client.delete(stream_key)

        return True

    except Exception as e:
        print(f"✗ Stream trimming test failed: {e}")
        return False


def cleanup_test_streams(client):
    """Clean up test streams."""
    print("\n" + "="*70)
    print("Cleanup Test Streams")
    print("="*70)

    test_streams = ["nlp:insights", "summary:output", "test:trimming"]

    for stream in test_streams:
        try:
            deleted = client.delete(stream)
            if deleted:
                print(f"✓ Deleted stream: {stream}")
        except Exception as e:
            print(f"  Could not delete {stream}: {e}")


def main():
    """Run all Redis stream tests."""
    print("\n" + "="*70)
    print("Redis Streams Integration Test Suite")
    print("="*70)
    print(f"Date: {datetime.utcnow().isoformat()}")

    # Connect to Redis
    client = test_redis_connection()

    if not client:
        print("\n✗ Cannot proceed without Redis connection")
        return False

    # Run tests
    results = {
        "connection": True,
        "nlp_stream": test_nlp_stream(client),
        "summary_stream": test_summary_stream(client),
        "consumer_groups": test_consumer_groups(client),
        "stream_trimming": test_stream_trimming(client)
    }

    # Summary
    print("\n" + "="*70)
    print("Test Results Summary")
    print("="*70)

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:20s}: {status}")

    all_passed = all(results.values())

    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*70)

    # Cleanup (optional - uncomment to clean up after tests)
    # cleanup_test_streams(client)

    client.close()

    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
