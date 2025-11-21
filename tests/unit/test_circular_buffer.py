"""
Unit tests for CircularBuffer implementation.

Tests cover basic write/read operations, wraparound behavior,
thread safety, and edge cases.
"""

import pytest
import numpy as np
from src.core.audio_capture.circular_buffer import CircularBuffer
import threading
import time


def test_circular_buffer_write_read():
    """Test basic write and read operations."""
    buffer = CircularBuffer(capacity_seconds=1.0, sample_rate=16000, channels=1)

    # Write 100 samples
    data = np.random.randn(100, 1).astype(np.float32)
    written = buffer.write(data)
    assert written == 100
    assert buffer.available() == 100

    # Read 50 samples
    read_data = buffer.read(50)
    assert read_data is not None
    assert len(read_data) == 50
    assert buffer.available() == 50


def test_circular_buffer_wraparound():
    """Test buffer wraparound when exceeding capacity."""
    buffer = CircularBuffer(capacity_seconds=0.01, sample_rate=16000, channels=1)
    capacity = buffer.capacity

    # Write more than capacity
    data = np.random.randn(capacity + 100, 1).astype(np.float32)
    buffer.write(data)

    # Should have capacity samples available (not more)
    assert buffer.available() == capacity


def test_circular_buffer_concurrent():
    """Test concurrent read/write operations for thread safety."""
    buffer = CircularBuffer(capacity_seconds=1.0, sample_rate=16000, channels=1)

    def writer():
        for _ in range(10):
            data = np.random.randn(100, 1).astype(np.float32)
            buffer.write(data)
            time.sleep(0.01)

    def reader():
        for _ in range(10):
            while buffer.available() < 100:
                time.sleep(0.001)
            buffer.read(100)

    t1 = threading.Thread(target=writer)
    t2 = threading.Thread(target=reader)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # No crash = success


def test_circular_buffer_read_insufficient_data():
    """Test reading when insufficient data is available."""
    buffer = CircularBuffer(capacity_seconds=1.0, sample_rate=16000, channels=1)

    # Write 50 samples
    data = np.random.randn(50, 1).astype(np.float32)
    buffer.write(data)

    # Try to read 100 samples (should return None)
    read_data = buffer.read(100)
    assert read_data is None
    assert buffer.available() == 50  # Data should still be there


def test_circular_buffer_clear():
    """Test buffer clear operation."""
    buffer = CircularBuffer(capacity_seconds=1.0, sample_rate=16000, channels=1)

    # Write some data
    data = np.random.randn(100, 1).astype(np.float32)
    buffer.write(data)
    assert buffer.available() == 100

    # Clear buffer
    buffer.clear()
    assert buffer.available() == 0

    # Should be able to write again
    buffer.write(data)
    assert buffer.available() == 100


def test_circular_buffer_multichannel():
    """Test buffer with multiple audio channels."""
    channels = 2
    buffer = CircularBuffer(capacity_seconds=1.0, sample_rate=16000, channels=channels)

    # Write stereo data
    data = np.random.randn(100, channels).astype(np.float32)
    written = buffer.write(data)
    assert written == 100

    # Read and verify shape
    read_data = buffer.read(50)
    assert read_data is not None
    assert read_data.shape == (50, channels)


def test_circular_buffer_wraparound_read():
    """Test reading across wraparound boundary."""
    buffer = CircularBuffer(capacity_seconds=0.01, sample_rate=16000, channels=1)
    capacity = buffer.capacity

    # Fill buffer completely
    data1 = np.ones((capacity, 1), dtype=np.float32)
    buffer.write(data1)

    # Read half
    read1 = buffer.read(capacity // 2)
    assert read1 is not None
    assert len(read1) == capacity // 2

    # Write more to cause wraparound
    data2 = np.ones((capacity // 2, 1), dtype=np.float32) * 2
    buffer.write(data2)

    # Read across wraparound boundary
    read2 = buffer.read(capacity // 2 + 10)
    assert read2 is not None
    assert len(read2) == capacity // 2 + 10


def test_circular_buffer_data_integrity():
    """Test that written data matches read data."""
    buffer = CircularBuffer(capacity_seconds=1.0, sample_rate=16000, channels=1)

    # Write known data
    data = np.arange(100, dtype=np.float32).reshape(100, 1)
    buffer.write(data)

    # Read it back
    read_data = buffer.read(100)
    assert read_data is not None
    np.testing.assert_array_equal(read_data, data)


def test_circular_buffer_multiple_writes():
    """Test multiple sequential write operations."""
    buffer = CircularBuffer(capacity_seconds=1.0, sample_rate=16000, channels=1)

    # Write in chunks
    total_written = 0
    for i in range(5):
        data = np.ones((20, 1), dtype=np.float32) * i
        written = buffer.write(data)
        total_written += written

    assert buffer.available() == 100
    assert total_written == 100


def test_circular_buffer_capacity_calculation():
    """Test that capacity is calculated correctly."""
    sample_rate = 16000
    capacity_seconds = 2.5
    buffer = CircularBuffer(capacity_seconds=capacity_seconds, sample_rate=sample_rate, channels=1)

    expected_capacity = int(capacity_seconds * sample_rate)
    assert buffer.capacity == expected_capacity
    assert buffer.sample_rate == sample_rate


def test_circular_buffer_stress_test():
    """Stress test with many concurrent operations."""
    buffer = CircularBuffer(capacity_seconds=0.5, sample_rate=16000, channels=1)
    errors = []

    def writer():
        try:
            for _ in range(50):
                data = np.random.randn(50, 1).astype(np.float32)
                buffer.write(data)
                time.sleep(0.001)
        except Exception as e:
            errors.append(e)

    def reader():
        try:
            for _ in range(50):
                while buffer.available() < 50:
                    time.sleep(0.0001)
                buffer.read(50)
        except Exception as e:
            errors.append(e)

    # Create multiple threads
    threads = []
    for _ in range(2):
        threads.append(threading.Thread(target=writer))
        threads.append(threading.Thread(target=reader))

    # Start all threads
    for t in threads:
        t.start()

    # Wait for completion
    for t in threads:
        t.join()

    # Check no errors occurred
    assert len(errors) == 0
