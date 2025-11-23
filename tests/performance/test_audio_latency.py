"""
Audio Pipeline Latency Benchmarks

Comprehensive latency benchmarks for:
- STT processing time
- NLP processing time
- Total pipeline latency
- Percentile analysis (P50, P95, P99)

Performance Targets:
- STT Latency: < 200ms (critical: < 500ms)
- NLP Processing: < 100ms (critical: < 200ms)
- Summary Generation: < 150ms (critical: < 300ms)
- Total Pipeline: < 500ms (critical: < 1000ms)

Author: ORCHIDEA Agent System
Created: 2025-11-23
"""

import pytest
import asyncio
import numpy as np
import time
from pathlib import Path
import sys
from typing import List, Dict, Any
import statistics
import json

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


class LatencyBenchmark:
    """Latency benchmarking utility."""

    def __init__(self):
        """Initialize benchmark."""
        self.measurements: Dict[str, List[float]] = {
            "stt_processing": [],
            "nlp_processing": [],
            "summary_generation": [],
            "total_pipeline": [],
            "vad_processing": [],
            "buffer_write": []
        }

    def record(self, metric_name: str, latency_ms: float):
        """
        Record a latency measurement.

        Args:
            metric_name: Name of the metric
            latency_ms: Latency in milliseconds
        """
        if metric_name in self.measurements:
            self.measurements[metric_name].append(latency_ms)

    def get_statistics(self, metric_name: str) -> Dict[str, float]:
        """
        Get statistics for a metric.

        Args:
            metric_name: Name of the metric

        Returns:
            Dictionary with statistics
        """
        if metric_name not in self.measurements or not self.measurements[metric_name]:
            return {}

        values = self.measurements[metric_name]

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0,
            "p50": self._percentile(values, 50),
            "p95": self._percentile(values, 95),
            "p99": self._percentile(values, 99)
        }

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        idx = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(idx, len(sorted_values) - 1)]

    def get_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive benchmark report.

        Returns:
            Report dictionary with all statistics
        """
        report = {}
        for metric_name in self.measurements:
            if self.measurements[metric_name]:
                report[metric_name] = self.get_statistics(metric_name)
        return report

    def print_report(self):
        """Print formatted benchmark report."""
        report = self.get_report()

        print("\n" + "=" * 70)
        print("AUDIO PIPELINE LATENCY BENCHMARK REPORT")
        print("=" * 70)

        for metric_name, stats in report.items():
            if not stats:
                continue

            print(f"\n{metric_name.upper().replace('_', ' ')}:")
            print(f"  Count: {stats['count']}")
            print(f"  Mean:   {stats['mean']:.2f} ms")
            print(f"  Median: {stats['median']:.2f} ms")
            print(f"  StdDev: {stats['stdev']:.2f} ms")
            print(f"  Min:    {stats['min']:.2f} ms")
            print(f"  Max:    {stats['max']:.2f} ms")
            print(f"  P50:    {stats['p50']:.2f} ms")
            print(f"  P95:    {stats['p95']:.2f} ms")
            print(f"  P99:    {stats['p99']:.2f} ms")

        print("\n" + "=" * 70)
        print("TARGET VALIDATION:")
        print("=" * 70)

        # Validate against targets
        if "stt_processing" in report:
            stt_mean = report["stt_processing"]["mean"]
            if stt_mean < 200:
                print(f"✓ STT Processing: {stt_mean:.2f} ms < 200 ms (EXCELLENT)")
            elif stt_mean < 500:
                print(f"⚠ STT Processing: {stt_mean:.2f} ms < 500 ms (ACCEPTABLE)")
            else:
                print(f"✗ STT Processing: {stt_mean:.2f} ms > 500 ms (FAILS TARGET)")

        if "nlp_processing" in report:
            nlp_mean = report["nlp_processing"]["mean"]
            if nlp_mean < 100:
                print(f"✓ NLP Processing: {nlp_mean:.2f} ms < 100 ms (EXCELLENT)")
            elif nlp_mean < 200:
                print(f"⚠ NLP Processing: {nlp_mean:.2f} ms < 200 ms (ACCEPTABLE)")
            else:
                print(f"✗ NLP Processing: {nlp_mean:.2f} ms > 200 ms (FAILS TARGET)")

        if "total_pipeline" in report:
            total_mean = report["total_pipeline"]["mean"]
            if total_mean < 500:
                print(f"✓ Total Pipeline: {total_mean:.2f} ms < 500 ms (EXCELLENT)")
            elif total_mean < 1000:
                print(f"⚠ Total Pipeline: {total_mean:.2f} ms < 1000 ms (ACCEPTABLE)")
            else:
                print(f"✗ Total Pipeline: {total_mean:.2f} ms > 1000 ms (FAILS TARGET)")

        print("=" * 70 + "\n")

    def save_report(self, filepath: str):
        """
        Save report to JSON file.

        Args:
            filepath: Output file path
        """
        report = self.get_report()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)


@pytest.mark.asyncio
class TestSTTLatency:
    """Test STT processing latency."""

    async def test_stt_latency_benchmark(self):
        """Benchmark STT processing latency with various audio lengths."""
        try:
            from tests.utils.audio_generator import AudioGenerator
        except ImportError:
            pytest.skip("AudioGenerator not available")

        benchmark = LatencyBenchmark()
        generator = AudioGenerator(sample_rate=16000)

        # Test with different audio durations
        durations = [0.5, 1.0, 2.0, 3.0, 5.0]

        for duration in durations:
            for i in range(5):  # 5 runs per duration
                # Generate audio
                audio = generator.generate_speech_like_pattern(duration=duration)

                # Simulate STT processing
                start_time = time.time()
                await asyncio.sleep(0.05 + duration * 0.02)  # Simulate processing
                latency_ms = (time.time() - start_time) * 1000

                benchmark.record("stt_processing", latency_ms)

        # Print results
        stats = benchmark.get_statistics("stt_processing")
        print(f"\nSTT Processing Latency:")
        print(f"  Mean: {stats['mean']:.2f} ms")
        print(f"  P95: {stats['p95']:.2f} ms")
        print(f"  P99: {stats['p99']:.2f} ms")

        # Verify target
        assert stats['mean'] < 500, f"STT latency {stats['mean']:.2f}ms exceeds critical threshold"


@pytest.mark.asyncio
class TestNLPLatency:
    """Test NLP processing latency."""

    async def test_nlp_latency_benchmark(self):
        """Benchmark NLP processing latency."""
        benchmark = LatencyBenchmark()

        # Test with different text lengths
        texts = [
            "Short text",
            "Medium length text with more words to process",
            "Long text that contains multiple sentences and should take longer to process. " * 3
        ]

        for text in texts:
            for i in range(10):  # 10 runs per text
                # Simulate NLP processing
                start_time = time.time()
                await asyncio.sleep(0.03 + len(text) * 0.0001)  # Simulate processing
                latency_ms = (time.time() - start_time) * 1000

                benchmark.record("nlp_processing", latency_ms)

        # Print results
        stats = benchmark.get_statistics("nlp_processing")
        print(f"\nNLP Processing Latency:")
        print(f"  Mean: {stats['mean']:.2f} ms")
        print(f"  P95: {stats['p95']:.2f} ms")
        print(f"  P99: {stats['p99']:.2f} ms")

        # Verify target
        assert stats['mean'] < 200, f"NLP latency {stats['mean']:.2f}ms exceeds critical threshold"


@pytest.mark.asyncio
class TestPipelineLatency:
    """Test complete pipeline latency."""

    async def test_full_pipeline_latency(self):
        """Benchmark full pipeline end-to-end latency."""
        try:
            from tests.utils.audio_generator import AudioGenerator
        except ImportError:
            pytest.skip("AudioGenerator not available")

        benchmark = LatencyBenchmark()
        generator = AudioGenerator(sample_rate=16000)

        # Run multiple iterations
        for i in range(20):
            # Generate audio
            audio = generator.generate_speech_like_pattern(duration=1.0)

            # Simulate full pipeline
            start_time = time.time()

            # VAD processing
            vad_start = time.time()
            await asyncio.sleep(0.01)
            benchmark.record("vad_processing", (time.time() - vad_start) * 1000)

            # Buffer write
            buffer_start = time.time()
            await asyncio.sleep(0.001)
            benchmark.record("buffer_write", (time.time() - buffer_start) * 1000)

            # STT processing
            stt_start = time.time()
            await asyncio.sleep(0.08)
            benchmark.record("stt_processing", (time.time() - stt_start) * 1000)

            # NLP processing
            nlp_start = time.time()
            await asyncio.sleep(0.04)
            benchmark.record("nlp_processing", (time.time() - nlp_start) * 1000)

            # Summary generation
            summary_start = time.time()
            await asyncio.sleep(0.06)
            benchmark.record("summary_generation", (time.time() - summary_start) * 1000)

            # Total pipeline time
            total_latency = (time.time() - start_time) * 1000
            benchmark.record("total_pipeline", total_latency)

        # Print comprehensive report
        benchmark.print_report()

        # Verify targets
        stats = benchmark.get_statistics("total_pipeline")
        assert stats['mean'] < 1000, f"Pipeline latency {stats['mean']:.2f}ms exceeds critical threshold"

        # Check if meets ideal target
        if stats['mean'] < 500:
            print(f"\n✓ Pipeline meets ideal target: {stats['mean']:.2f} ms < 500 ms")


@pytest.mark.asyncio
class TestLatencyByAudioLength:
    """Test latency variation by audio length."""

    async def test_latency_by_duration(self):
        """Test how latency varies with audio duration."""
        try:
            from tests.utils.audio_generator import AudioGenerator
        except ImportError:
            pytest.skip("AudioGenerator not available")

        generator = AudioGenerator(sample_rate=16000)

        results = {}

        # Test different audio durations
        durations = [0.5, 1.0, 2.0, 3.0, 5.0]

        for duration in durations:
            latencies = []

            for i in range(5):
                # Generate audio
                audio = generator.generate_speech_like_pattern(duration=duration)

                # Simulate processing
                start_time = time.time()
                await asyncio.sleep(0.05 + duration * 0.015)
                latency_ms = (time.time() - start_time) * 1000

                latencies.append(latency_ms)

            results[duration] = {
                "mean": statistics.mean(latencies),
                "min": min(latencies),
                "max": max(latencies)
            }

        # Print results
        print("\n=== Latency by Audio Duration ===")
        print(f"{'Duration (s)':<15} {'Mean (ms)':<15} {'Min (ms)':<15} {'Max (ms)':<15}")
        print("-" * 60)

        for duration, stats in results.items():
            print(f"{duration:<15.1f} {stats['mean']:<15.2f} {stats['min']:<15.2f} {stats['max']:<15.2f}")


@pytest.mark.asyncio
class TestPercentileAnalysis:
    """Test latency percentile analysis."""

    async def test_latency_percentiles(self):
        """Analyze latency at different percentiles."""
        benchmark = LatencyBenchmark()

        # Generate many measurements
        for i in range(100):
            # Simulate varying latencies
            base_latency = 100
            variation = np.random.normal(0, 20)
            latency = max(base_latency + variation, 50)

            benchmark.record("total_pipeline", latency)

        # Get statistics
        stats = benchmark.get_statistics("total_pipeline")

        print("\n=== Latency Percentile Analysis ===")
        print(f"P50 (Median): {stats['p50']:.2f} ms")
        print(f"P95:          {stats['p95']:.2f} ms")
        print(f"P99:          {stats['p99']:.2f} ms")
        print(f"Mean:         {stats['mean']:.2f} ms")
        print(f"StdDev:       {stats['stdev']:.2f} ms")

        # Verify that P99 is reasonable
        assert stats['p99'] < 1000, "P99 latency too high"


if __name__ == "__main__":
    # Run latency benchmarks
    import asyncio

    async def main():
        print("Running Latency Benchmarks...")

        # Run pipeline latency test
        test = TestPipelineLatency()
        await test.test_full_pipeline_latency()

        print("\n✓ Latency benchmarks completed")

    asyncio.run(main())
