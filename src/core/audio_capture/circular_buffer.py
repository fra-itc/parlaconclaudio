"""
Circular buffer implementation for audio streaming.

This module provides a thread-safe circular buffer optimized for real-time
audio data streaming with lock-based synchronization.
"""

import numpy as np
import threading
from typing import Optional


class CircularBuffer:
    """Lock-free circular buffer for audio streaming.

    This buffer is designed to handle continuous audio streaming with a fixed
    capacity, automatically overwriting old data when full. It uses a lock-based
    approach to ensure thread safety during concurrent read/write operations.

    Attributes:
        capacity (int): Maximum number of samples the buffer can hold
        sample_rate (int): Audio sample rate in Hz
        channels (int): Number of audio channels
        buffer (np.ndarray): Pre-allocated numpy array for audio data
    """

    def __init__(self, capacity_seconds: float, sample_rate: int, channels: int):
        """Initialize circular buffer with specified capacity.

        Args:
            capacity_seconds: Buffer capacity in seconds
            sample_rate: Audio sample rate in Hz (e.g., 16000)
            channels: Number of audio channels (e.g., 1 for mono)
        """
        self.capacity = int(capacity_seconds * sample_rate)
        self.sample_rate = sample_rate
        self.channels = channels

        # Pre-allocate buffer for efficient memory usage
        self.buffer = np.zeros((self.capacity, channels), dtype=np.float32)

        # Index tracking
        self._write_index = 0
        self._read_index = 0
        self._lock = threading.Lock()
        self._available_samples = 0

    def write(self, data: np.ndarray) -> int:
        """Write audio data to buffer.

        Writes the provided audio data to the circular buffer. If the write
        would exceed the buffer capacity, it wraps around to the beginning,
        overwriting old data.

        Args:
            data: Audio data as numpy array with shape (num_samples, channels)

        Returns:
            Number of samples written
        """
        num_samples = len(data)

        with self._lock:
            write_pos = self._write_index % self.capacity

            if write_pos + num_samples > self.capacity:
                # Wrap around - split write into two chunks
                first_chunk = self.capacity - write_pos
                self.buffer[write_pos:] = data[:first_chunk]
                self.buffer[:num_samples - first_chunk] = data[first_chunk:]
            else:
                # Simple write - no wraparound needed
                self.buffer[write_pos:write_pos + num_samples] = data

            self._write_index += num_samples
            self._available_samples = min(
                self._available_samples + num_samples,
                self.capacity
            )

        return num_samples

    def read(self, num_samples: int) -> Optional[np.ndarray]:
        """Read audio data from buffer.

        Reads the specified number of samples from the buffer. If insufficient
        samples are available, returns None.

        Args:
            num_samples: Number of samples to read

        Returns:
            Audio data as numpy array with shape (num_samples, channels),
            or None if insufficient samples available
        """
        with self._lock:
            if self._available_samples < num_samples:
                return None

            read_pos = self._read_index % self.capacity

            if read_pos + num_samples > self.capacity:
                # Wrap around - concatenate two chunks
                first_chunk = self.capacity - read_pos
                data = np.concatenate([
                    self.buffer[read_pos:],
                    self.buffer[:num_samples - first_chunk]
                ])
            else:
                # Simple read - no wraparound needed
                data = self.buffer[read_pos:read_pos + num_samples].copy()

            self._read_index += num_samples
            self._available_samples -= num_samples

        return data

    def available(self) -> int:
        """Get number of available samples.

        Returns:
            Number of samples currently available for reading
        """
        with self._lock:
            return self._available_samples

    def clear(self):
        """Clear buffer and reset all indices.

        This method resets the buffer to its initial state, clearing all
        data and resetting read/write indices.
        """
        with self._lock:
            self._write_index = 0
            self._read_index = 0
            self._available_samples = 0
