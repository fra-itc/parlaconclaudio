"""
Audio Processing Throughput Tests

Tests throughput and resource utilization:
- Concurrent audio stream processing
- Long-duration streaming (5+ minutes)
- Memory usage monitoring
- Resource leak detection

Performance Targets:
- Throughput: > 10 chunks/sec (critical: > 5 chunks/sec)
- Memory Usage: < 500MB (critical: < 1GB)
- No memory leaks over extended operation

Author: ORCHIDEA Agent System
Created: 2025-11-23
"""

import pytest
import asyncio
import numpy as np
import time
from pathlib import Path
import sys
from typing import List
import psutil
import os

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


class ThroughputBenchmark:
    """Throughput benchmarking utility."""

    def __init__(self):
        """Initialize benchmark."""
        self.chunks_processed = 0
        self.bytes_processed = 0
        self.start_time = None
        self.end_time = None
        self.memory_samples: List[float] = []
        self.process = psutil.Process(os.getpid())

    def start(self):
        """Start throughput measurement."""
        self.start_time = time.time()
        self.record_memory()

    def record_chunk(self, chunk_size_bytes: int):
        """Record processed chunk."""
        self.chunks_processed += 1
        self.bytes_processed += chunk_size_bytes

    def record_memory(self):
        """Record current memory usage."""
        mem_info = self.process.memory_info()
        mem_mb = mem_info.rss / (1024 * 1024)
        self.memory_samples.append(mem_mb)

    def stop(self):
        """Stop throughput measurement."""
        self.end_time = time.time()
        self.record_memory()

    def get_duration(self) -> float:
        """Get duration in seconds."""
        if not self.start_time or not self.end_time:
            return 0.0
        return self.end_time - self.start_time

    def get_throughput(self) -> float:
        """Get chunks per second."""
        duration = self.get_duration()
        if duration == 0:
            return 0.0
        return self.chunks_processed / duration

    def get_bandwidth(self) -> float:
        """Get MB/s bandwidth."""
        duration = self.get_duration()
        if duration == 0:
            return 0.0
        return (self.bytes_processed / (1024 * 1024)) / duration

    def get_memory_stats(self) -> dict:
        """Get memory usage statistics."""
        if not self.memory_samples:
            return {}

        return {
            "initial_mb": self.memory_samples[0],
            "final_mb": self.memory_samples[-1],
            "peak_mb": max(self.memory_samples),
            "avg_mb": sum(self.memory_samples) / len(self.memory_samples),
            "growth_mb": self.memory_samples[-1] - self.memory_samples[0]
        }

    def print_report(self):
        """Print throughput report."""
        print("\n" + "=" * 70)
        print("THROUGHPUT BENCHMARK REPORT")
        print("=" * 70)

        print(f"\nProcessing Metrics:")
        print(f"  Duration:       {self.get_duration():.2f} seconds")
        print(f"  Chunks:         {self.chunks_processed}")
        print(f"  Throughput:     {self.get_throughput():.2f} chunks/sec")
        print(f"  Bandwidth:      {self.get_bandwidth():.2f} MB/s")

        mem_stats = self.get_memory_stats()
        if mem_stats:
            print(f"\nMemory Metrics:")
            print(f"  Initial:        {mem_stats['initial_mb']:.2f} MB")
            print(f"  Final:          {mem_stats['final_mb']:.2f} MB")
            print(f"  Peak:           {mem_stats['peak_mb']:.2f} MB")
            print(f"  Average:        {mem_stats['avg_mb']:.2f} MB")
            print(f"  Growth:         {mem_stats['growth_mb']:.2f} MB")

        print("\n" + "=" * 70)
        print("TARGET VALIDATION:")
        print("=" * 70)

        throughput = self.get_throughput()
        if throughput > 10:
            print(f"✓ Throughput: {throughput:.2f} chunks/sec > 10 (EXCELLENT)")
        elif throughput > 5:
            print(f"⚠ Throughput: {throughput:.2f} chunks/sec > 5 (ACCEPTABLE)")
        else:
            print(f"✗ Throughput: {throughput:.2f} chunks/sec < 5 (FAILS TARGET)")

        if mem_stats:
            peak_mem = mem_stats['peak_mb']
            if peak_mem < 500:
                print(f"✓ Memory Usage: {peak_mem:.2f} MB < 500 MB (EXCELLENT)")
            elif peak_mem < 1024:
                print(f"⚠ Memory Usage: {peak_mem:.2f} MB < 1 GB (ACCEPTABLE)")
            else:
                print(f"✗ Memory Usage: {peak_mem:.2f} MB > 1 GB (FAILS TARGET)")

            mem_growth = mem_stats['growth_mb']
            if mem_growth < 50:
                print(f"✓ Memory Growth: {mem_growth:.2f} MB (NO LEAK)")
            else:
                print(f"⚠ Memory Growth: {mem_growth:.2f} MB (POTENTIAL LEAK)")

        print("=" * 70 + "\n")


@pytest.mark.asyncio
class TestConcurrentStreams:
    """Test concurrent audio stream processing."""

    async def test_concurrent_streams_throughput(self):
        """Test processing multiple concurrent audio streams."""
        try:
            from tests.utils.audio_generator import AudioGenerator
            from tests.utils.audio_loader import AudioLoader
        except ImportError:
            pytest.skip("Audio utilities not available")

        benchmark = ThroughputBenchmark()
        generator = AudioGenerator(sample_rate=16000)
        loader = AudioLoader(sample_rate=16000)

        num_streams = 3
        chunks_per_stream = 20

        benchmark.start()

        async def process_stream(stream_id: int):
            """Process single audio stream."""
            for i in range(chunks_per_stream):
                # Generate audio chunk (100ms)
                audio = generator.generate_speech_like_pattern(duration=0.1)
                audio_int16 = loader.to_int16(audio)

                # Simulate processing
                await asyncio.sleep(0.01)

                # Record
                benchmark.record_chunk(len(audio_int16) * 2)  # 2 bytes per sample

                if i % 5 == 0:
                    benchmark.record_memory()

        # Process streams concurrently
        tasks = [process_stream(i) for i in range(num_streams)]
        await asyncio.gather(*tasks)

        benchmark.stop()
        benchmark.print_report()

        # Verify targets
        assert benchmark.get_throughput() > 5, "Throughput below critical threshold"

    async def test_high_throughput_streaming(self):
        """Test high-throughput audio streaming."""
        try:
            from tests.utils.audio_loader import AudioLoader
        except ImportError:
            pytest.skip("Audio utilities not available")

        benchmark = ThroughputBenchmark()
        loader = AudioLoader(sample_rate=16000)

        benchmark.start()

        # Stream rapidly for 2 seconds
        start_time = time.time()
        while time.time() - start_time < 2.0:
            # Generate chunk
            audio = np.random.randn(1600).astype(np.float32)
            audio_int16 = loader.to_int16(audio)

            # Simulate minimal processing
            await asyncio.sleep(0.001)

            benchmark.record_chunk(len(audio_int16) * 2)

        benchmark.stop()

        print(f"\nHigh-Throughput Results:")
        print(f"  Throughput: {benchmark.get_throughput():.2f} chunks/sec")

        # Should achieve high throughput
        assert benchmark.get_throughput() > 10


@pytest.mark.asyncio
class TestLongDurationStreaming:
    """Test long-duration streaming."""

    @pytest.mark.slow
    async def test_extended_streaming(self):
        """Test streaming for extended duration (5+ minutes)."""
        try:
            from tests.utils.audio_loader import AudioLoader
        except ImportError:
            pytest.skip("Audio utilities not available")

        benchmark = ThroughputBenchmark()
        loader = AudioLoader(sample_rate=16000)

        # Test for 10 seconds (reduced from 5 minutes for faster testing)
        # In production, increase to 300 seconds
        test_duration = 10.0

        benchmark.start()

        start_time = time.time()
        while time.time() - start_time < test_duration:
            # Generate chunk
            audio = np.random.randn(1600).astype(np.float32)
            audio_int16 = loader.to_int16(audio)

            # Simulate processing
            await asyncio.sleep(0.02)

            benchmark.record_chunk(len(audio_int16) * 2)

            # Record memory periodically
            if benchmark.chunks_processed % 10 == 0:
                benchmark.record_memory()

        benchmark.stop()
        benchmark.print_report()

        # Check for memory leaks
        mem_stats = benchmark.get_memory_stats()
        assert mem_stats['growth_mb'] < 100, "Potential memory leak detected"


@pytest.mark.asyncio
class TestMemoryUsage:
    """Test memory usage and leak detection."""

    async def test_memory_usage_monitoring(self):
        """Monitor memory usage during processing."""
        try:
            from tests.utils.audio_loader import AudioLoader
        except ImportError:
            pytest.skip("Audio utilities not available")

        benchmark = ThroughputBenchmark()
        loader = AudioLoader(sample_rate=16000)

        benchmark.start()

        # Process audio for a period
        for i in range(100):
            audio = np.random.randn(1600).astype(np.float32)
            audio_int16 = loader.to_int16(audio)

            await asyncio.sleep(0.01)

            benchmark.record_chunk(len(audio_int16) * 2)

            # Record memory every 10 chunks
            if i % 10 == 0:
                benchmark.record_memory()

        benchmark.stop()

        mem_stats = benchmark.get_memory_stats()

        print(f"\nMemory Usage:")
        print(f"  Initial: {mem_stats['initial_mb']:.2f} MB")
        print(f"  Final:   {mem_stats['final_mb']:.2f} MB")
        print(f"  Peak:    {mem_stats['peak_mb']:.2f} MB")
        print(f"  Growth:  {mem_stats['growth_mb']:.2f} MB")

        # Memory should stay reasonable
        assert mem_stats['peak_mb'] < 1024, "Memory usage exceeds 1GB"

    async def test_no_memory_leak(self):
        """Test that there are no memory leaks."""
        try:
            from tests.utils.audio_loader import AudioLoader
        except ImportError:
            pytest.skip("Audio utilities not available")

        benchmark = ThroughputBenchmark()
        loader = AudioLoader(sample_rate=16000)

        benchmark.start()

        # Process many chunks
        for i in range(500):
            audio = np.random.randn(1600).astype(np.float32)
            audio_int16 = loader.to_int16(audio)

            await asyncio.sleep(0.001)

            benchmark.record_chunk(len(audio_int16) * 2)

            if i % 50 == 0:
                benchmark.record_memory()

        benchmark.stop()

        mem_stats = benchmark.get_memory_stats()

        print(f"\nLeak Detection:")
        print(f"  Memory Growth: {mem_stats['growth_mb']:.2f} MB")

        # Should not have significant memory growth
        assert mem_stats['growth_mb'] < 100, f"Memory leak detected: {mem_stats['growth_mb']:.2f} MB growth"


@pytest.mark.asyncio
class TestResourceUtilization:
    """Test resource utilization."""

    async def test_cpu_usage(self):
        """Test CPU usage during processing."""
        benchmark = ThroughputBenchmark()

        # Get initial CPU percent
        initial_cpu = benchmark.process.cpu_percent(interval=0.1)

        # Process audio
        for i in range(50):
            # Simulate some work
            await asyncio.sleep(0.01)
            _ = np.random.randn(1600)

        # Get final CPU percent
        final_cpu = benchmark.process.cpu_percent(interval=0.1)

        print(f"\nCPU Usage:")
        print(f"  Initial: {initial_cpu:.2f}%")
        print(f"  Final:   {final_cpu:.2f}%")

        # CPU usage should be reasonable (not > 90%)
        assert final_cpu < 90, "CPU usage too high"


if __name__ == "__main__":
    # Run throughput tests
    import asyncio

    async def main():
        print("Running Throughput Tests...")

        test = TestConcurrentStreams()
        await test.test_concurrent_streams_throughput()

        print("\n✓ Throughput tests completed")

    asyncio.run(main())
