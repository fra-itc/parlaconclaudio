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


class TestCircularBufferOverflow:
    """Test buffer overflow handling scenarios."""

    def test_buffer_overflow_oldest_discarded(self):
        """Test that oldest data is discarded on overflow."""
        buffer = CircularBuffer(capacity_seconds=0.01, sample_rate=16000, channels=1)
        capacity = buffer.capacity

        # Write known sequence that fills buffer
        data1 = np.ones((capacity, 1), dtype=np.float32)
        buffer.write(data1)

        # Write more data to cause overflow
        data2 = np.ones((100, 1), dtype=np.float32) * 2
        buffer.write(data2)

        # Buffer should contain only capacity samples
        assert buffer.available() == capacity

        # Read all data - should contain data2 (newer data)
        read_data = buffer.read(capacity)
        assert read_data is not None

        # Check that we have newer data (2s) at the end
        assert np.any(read_data[-50:] == 2.0)

    def test_buffer_overflow_continuous_write(self):
        """Test continuous writing beyond buffer capacity."""
        buffer = CircularBuffer(capacity_seconds=0.1, sample_rate=16000, channels=1)
        capacity = buffer.capacity

        # Write 3x capacity in small chunks
        total_to_write = capacity * 3
        chunk_size = 100

        for i in range(0, total_to_write, chunk_size):
            data = np.random.randn(chunk_size, 1).astype(np.float32)
            buffer.write(data)

        # Buffer should not exceed capacity
        assert buffer.available() <= capacity

    def test_buffer_overflow_large_chunk(self):
        """Test writing a single chunk larger than buffer capacity."""
        buffer = CircularBuffer(capacity_seconds=0.01, sample_rate=16000, channels=1)
        capacity = buffer.capacity

        # Write more than capacity in single write
        large_data = np.random.randn(capacity * 2, 1).astype(np.float32)
        written = buffer.write(large_data)

        # Should write only capacity samples
        assert buffer.available() <= capacity


class TestCircularBufferUnderflow:
    """Test buffer underflow scenarios."""

    def test_buffer_underflow_returns_none(self):
        """Test that reading more than available returns None."""
        buffer = CircularBuffer(capacity_seconds=1.0, sample_rate=16000, channels=1)

        # Write 50 samples
        data = np.random.randn(50, 1).astype(np.float32)
        buffer.write(data)

        # Try to read 100 samples (underflow)
        result = buffer.read(100)
        assert result is None

        # Original data should still be available
        assert buffer.available() == 50

    def test_buffer_underflow_empty_read(self):
        """Test reading from empty buffer."""
        buffer = CircularBuffer(capacity_seconds=1.0, sample_rate=16000, channels=1)

        # Try to read from empty buffer
        result = buffer.read(10)
        assert result is None
        assert buffer.available() == 0

    def test_buffer_underflow_exact_amount(self):
        """Test reading exactly the amount available."""
        buffer = CircularBuffer(capacity_seconds=1.0, sample_rate=16000, channels=1)

        # Write 100 samples
        data = np.random.randn(100, 1).astype(np.float32)
        buffer.write(data)

        # Read exactly 100 samples (should succeed)
        result = buffer.read(100)
        assert result is not None
        assert len(result) == 100
        assert buffer.available() == 0


class TestCircularBufferDataLoss:
    """Test that no audio data is lost during normal operation."""

    def test_no_data_loss_sequential(self):
        """Test no data loss with sequential write/read operations."""
        buffer = CircularBuffer(capacity_seconds=1.0, sample_rate=16000, channels=1)

        # Write sequential numbers
        written_data = []
        for i in range(10):
            data = np.arange(i * 100, (i + 1) * 100, dtype=np.float32).reshape(100, 1)
            buffer.write(data)
            written_data.append(data)

        # Read all data back
        total_available = buffer.available()
        read_data = buffer.read(total_available)

        # Verify all data is present
        assert read_data is not None
        assert len(read_data) == 1000  # 10 chunks * 100 samples

        # Verify data integrity
        expected_data = np.concatenate(written_data)
        np.testing.assert_array_equal(read_data, expected_data)

    def test_no_data_loss_with_partial_reads(self):
        """Test no data loss when reading in smaller chunks."""
        buffer = CircularBuffer(capacity_seconds=1.0, sample_rate=16000, channels=1)

        # Write 1000 samples
        original_data = np.arange(1000, dtype=np.float32).reshape(1000, 1)
        buffer.write(original_data)

        # Read in chunks of 100
        read_chunks = []
        for i in range(10):
            chunk = buffer.read(100)
            assert chunk is not None
            read_chunks.append(chunk)

        # Concatenate and verify
        read_data = np.concatenate(read_chunks)
        np.testing.assert_array_equal(read_data, original_data)
        assert buffer.available() == 0

    def test_no_data_loss_concurrent_operations(self):
        """Test no data loss with concurrent read/write."""
        buffer = CircularBuffer(capacity_seconds=1.0, sample_rate=16000, channels=1)

        written_samples = []
        read_samples = []
        lock = threading.Lock()

        def writer():
            for i in range(10):
                data = np.ones((100, 1), dtype=np.float32) * i
                buffer.write(data)
                with lock:
                    written_samples.append(data)
                time.sleep(0.01)

        def reader():
            for i in range(10):
                while buffer.available() < 100:
                    time.sleep(0.001)
                data = buffer.read(100)
                if data is not None:
                    with lock:
                        read_samples.append(data)

        t1 = threading.Thread(target=writer)
        t2 = threading.Thread(target=reader)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Verify same amount written and read
        total_written = sum(len(d) for d in written_samples)
        total_read = sum(len(d) for d in read_samples)
        assert total_written == total_read == 1000

    def test_data_preservation_across_wraparound(self):
        """Test that data is preserved correctly across buffer wraparound."""
        buffer = CircularBuffer(capacity_seconds=0.01, sample_rate=16000, channels=1)
        capacity = buffer.capacity

        # Write unique values
        data1 = np.arange(capacity, dtype=np.float32).reshape(capacity, 1)
        buffer.write(data1)

        # Read half
        half = capacity // 2
        read1 = buffer.read(half)
        assert read1 is not None
        np.testing.assert_array_equal(read1, data1[:half])

        # Write more (will wrap around)
        data2 = np.arange(capacity, capacity * 2, dtype=np.float32).reshape(capacity, 1)
        buffer.write(data2)

        # Read remaining data
        read2 = buffer.read(capacity + half)
        assert read2 is not None

        # Verify data integrity
        expected = np.concatenate([data1[half:], data2[:capacity]])
        np.testing.assert_array_equal(read2, expected)
