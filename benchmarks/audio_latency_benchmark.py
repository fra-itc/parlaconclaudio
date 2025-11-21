"""
RTSTT Audio Capture - Performance Benchmark Suite

Comprehensive benchmarks for measuring:
- Latency (end-to-end pipeline)
- Throughput (samples/sec processing)
- CPU usage
- Memory usage
- VAD processing performance

Author: RTSTT Team
Date: 2025-11-21
"""

import time
import numpy as np
import psutil
import logging
from typing import Dict, List, Any, Callable
from dataclasses import dataclass, field
import statistics
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.audio_capture.wasapi_capture import WASAPICapture
from core.audio_capture.circular_buffer import CircularBuffer
from core.audio_capture.vad_silero import SileroVAD

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Container for benchmark results"""
    name: str
    duration_seconds: float
    samples_processed: int
    throughput_samples_per_sec: float
    latency_ms: float
    cpu_usage_percent: float
    memory_mb: float
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        return (
            f"\n{'='*60}\n"
            f"Benchmark: {self.name}\n"
            f"{'='*60}\n"
            f"Duration:     {self.duration_seconds:.2f}s\n"
            f"Samples:      {self.samples_processed:,}\n"
            f"Throughput:   {self.throughput_samples_per_sec:,.0f} samples/sec\n"
            f"Latency:      {self.latency_ms:.2f}ms\n"
            f"CPU Usage:    {self.cpu_usage_percent:.1f}%\n"
            f"Memory:       {self.memory_mb:.1f} MB\n"
            f"{'='*60}"
        )


class AudioBenchmark:
    """Audio pipeline benchmark suite"""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.process = psutil.Process()

    def benchmark_wasapi_capture(self, duration_seconds: float = 5.0) -> BenchmarkResult:
        """Benchmark WASAPI capture latency and throughput"""
        logger.info(f"Running WASAPI capture benchmark for {duration_seconds}s...")

        chunks_captured = []
        latencies = []

        def capture_callback(audio_data):
            capture_time = time.perf_counter()
            chunks_captured.append((capture_time, len(audio_data)))

        # Start monitoring
        cpu_before = self.process.cpu_percent()
        mem_before = self.process.memory_info().rss / 1024 / 1024

        # Create capture
        capture = WASAPICapture(
            sample_rate=self.sample_rate,
            channels=1,
            chunk_duration_ms=100
        )

        start_time = time.perf_counter()
        capture.start(capture_callback)

        # Run for duration
        time.sleep(duration_seconds)

        # Stop and measure
        end_time = time.perf_counter()
        capture.stop()

        # Measure resources
        cpu_after = self.process.cpu_percent()
        mem_after = self.process.memory_info().rss / 1024 / 1024

        # Calculate metrics
        total_duration = end_time - start_time
        total_samples = sum(count for _, count in chunks_captured)
        throughput = total_samples / total_duration if total_duration > 0 else 0

        # Calculate latency (time between chunks)
        if len(chunks_captured) > 1:
            inter_chunk_times = [
                (chunks_captured[i][0] - chunks_captured[i-1][0]) * 1000
                for i in range(1, len(chunks_captured))
            ]
            avg_latency = statistics.mean(inter_chunk_times)
            latency_jitter = statistics.stdev(inter_chunk_times) if len(inter_chunk_times) > 1 else 0
        else:
            avg_latency = 0.0
            latency_jitter = 0.0

        return BenchmarkResult(
            name="WASAPI Capture",
            duration_seconds=total_duration,
            samples_processed=total_samples,
            throughput_samples_per_sec=throughput,
            latency_ms=avg_latency,
            cpu_usage_percent=(cpu_after + cpu_before) / 2,
            memory_mb=mem_after - mem_before,
            details={
                'chunks_captured': len(chunks_captured),
                'expected_latency_ms': 100,  # chunk duration
                'latency_jitter_ms': latency_jitter,
                'real_time_factor': throughput / self.sample_rate if throughput > 0 else 0
            }
        )

    def benchmark_circular_buffer(self, duration_seconds: float = 5.0) -> BenchmarkResult:
        """Benchmark circular buffer write/read performance"""
        logger.info(f"Running circular buffer benchmark for {duration_seconds}s...")

        buffer = CircularBuffer(
            capacity_seconds=10.0,
            sample_rate=self.sample_rate,
            channels=1
        )

        # Prepare test data
        chunk_size = int(self.sample_rate * 0.1)  # 100ms chunks
        test_chunk = np.random.randn(chunk_size, 1).astype(np.float32)

        # Benchmark writes
        cpu_before = self.process.cpu_percent()
        mem_before = self.process.memory_info().rss / 1024 / 1024

        start_time = time.perf_counter()
        samples_written = 0
        write_times = []

        while time.perf_counter() - start_time < duration_seconds:
            write_start = time.perf_counter()
            buffer.write(test_chunk)
            write_end = time.perf_counter()
            write_times.append((write_end - write_start) * 1000)
            samples_written += chunk_size

        end_time = time.perf_counter()

        # Benchmark reads
        samples_read = 0
        read_times = []
        read_start = time.perf_counter()

        while buffer.available() >= chunk_size:
            read_op_start = time.perf_counter()
            data = buffer.read(chunk_size)
            read_op_end = time.perf_counter()
            if data is not None:
                read_times.append((read_op_end - read_op_start) * 1000)
                samples_read += chunk_size

        read_end = time.perf_counter()

        cpu_after = self.process.cpu_percent()
        mem_after = self.process.memory_info().rss / 1024 / 1024

        total_duration = end_time - start_time
        write_throughput = samples_written / total_duration
        read_duration = read_end - read_start
        read_throughput = samples_read / read_duration if read_duration > 0 else 0

        avg_write_time = statistics.mean(write_times) if write_times else 0
        avg_read_time = statistics.mean(read_times) if read_times else 0

        return BenchmarkResult(
            name="Circular Buffer",
            duration_seconds=total_duration,
            samples_processed=samples_written + samples_read,
            throughput_samples_per_sec=write_throughput,
            latency_ms=avg_write_time,  # Write latency is critical
            cpu_usage_percent=(cpu_after + cpu_before) / 2,
            memory_mb=mem_after - mem_before,
            details={
                'samples_written': samples_written,
                'samples_read': samples_read,
                'write_throughput': write_throughput,
                'read_throughput': read_throughput,
                'avg_write_time_ms': avg_write_time,
                'avg_read_time_ms': avg_read_time,
                'max_write_time_ms': max(write_times) if write_times else 0,
                'max_read_time_ms': max(read_times) if read_times else 0
            }
        )

    def benchmark_vad_processing(self, duration_seconds: float = 5.0) -> BenchmarkResult:
        """Benchmark Silero VAD processing speed"""
        logger.info(f"Running VAD processing benchmark for {duration_seconds}s...")

        vad = SileroVAD(threshold=0.5, sample_rate=self.sample_rate)

        # VAD requires specific chunk size
        vad_chunk_size = 512 if self.sample_rate == 16000 else 256
        test_chunk = np.random.randn(vad_chunk_size).astype(np.float32)

        cpu_before = self.process.cpu_percent()
        mem_before = self.process.memory_info().rss / 1024 / 1024

        start_time = time.perf_counter()
        chunks_processed = 0
        processing_times = []
        speech_detected = 0

        while time.perf_counter() - start_time < duration_seconds:
            chunk_start = time.perf_counter()
            is_speech, confidence = vad.process_chunk(test_chunk)
            chunk_end = time.perf_counter()

            processing_times.append((chunk_end - chunk_start) * 1000)  # ms
            chunks_processed += 1
            if is_speech:
                speech_detected += 1

        end_time = time.perf_counter()

        cpu_after = self.process.cpu_percent()
        mem_after = self.process.memory_info().rss / 1024 / 1024

        total_duration = end_time - start_time
        total_samples = chunks_processed * vad_chunk_size
        throughput = total_samples / total_duration
        avg_processing_time = statistics.mean(processing_times)

        # Calculate real-time factor (should be >> 1.0 for real-time processing)
        chunk_duration_sec = vad_chunk_size / self.sample_rate
        real_time_factor = chunk_duration_sec / (avg_processing_time / 1000)

        return BenchmarkResult(
            name="Silero VAD Processing",
            duration_seconds=total_duration,
            samples_processed=total_samples,
            throughput_samples_per_sec=throughput,
            latency_ms=avg_processing_time,
            cpu_usage_percent=(cpu_after + cpu_before) / 2,
            memory_mb=mem_after - mem_before,
            details={
                'chunks_processed': chunks_processed,
                'speech_detected': speech_detected,
                'avg_processing_time_ms': avg_processing_time,
                'max_processing_time_ms': max(processing_times),
                'min_processing_time_ms': min(processing_times),
                'processing_time_std_ms': statistics.stdev(processing_times) if len(processing_times) > 1 else 0,
                'real_time_factor': real_time_factor,
                'chunk_size': vad_chunk_size
            }
        )

    def benchmark_end_to_end_pipeline(self, duration_seconds: float = 5.0) -> BenchmarkResult:
        """Benchmark complete audio pipeline with VAD"""
        logger.info(f"Running end-to-end pipeline benchmark for {duration_seconds}s...")

        # Setup components
        buffer = CircularBuffer(
            capacity_seconds=10.0,
            sample_rate=self.sample_rate,
            channels=1
        )
        vad = SileroVAD(threshold=0.5, sample_rate=self.sample_rate)
        vad_chunk_size = 512 if self.sample_rate == 16000 else 256

        pipeline_metrics = {
            'chunks_captured': 0,
            'chunks_processed_vad': 0,
            'speech_chunks': 0,
            'capture_times': [],
            'vad_times': []
        }

        def capture_callback(audio_data):
            """Callback that processes through buffer and VAD"""
            capture_start = time.perf_counter()

            # Write to buffer
            buffer.write(audio_data)
            pipeline_metrics['chunks_captured'] += 1

            # Process with VAD if enough data available
            while buffer.available() >= vad_chunk_size:
                vad_data = buffer.read(vad_chunk_size)
                if vad_data is not None:
                    vad_start = time.perf_counter()
                    is_speech, confidence = vad.process_chunk(vad_data.flatten())
                    vad_end = time.perf_counter()

                    pipeline_metrics['vad_times'].append((vad_end - vad_start) * 1000)
                    pipeline_metrics['chunks_processed_vad'] += 1
                    if is_speech:
                        pipeline_metrics['speech_chunks'] += 1

            capture_end = time.perf_counter()
            pipeline_metrics['capture_times'].append((capture_end - capture_start) * 1000)

        # Start monitoring
        cpu_before = self.process.cpu_percent()
        mem_before = self.process.memory_info().rss / 1024 / 1024

        # Create and start capture
        capture = WASAPICapture(
            sample_rate=self.sample_rate,
            channels=1,
            chunk_duration_ms=100
        )

        start_time = time.perf_counter()
        capture.start(capture_callback)

        # Run for duration
        time.sleep(duration_seconds)

        # Stop and measure
        end_time = time.perf_counter()
        capture.stop()

        cpu_after = self.process.cpu_percent()
        mem_after = self.process.memory_info().rss / 1024 / 1024

        total_duration = end_time - start_time
        total_samples = pipeline_metrics['chunks_processed_vad'] * vad_chunk_size
        throughput = total_samples / total_duration if total_duration > 0 else 0

        avg_pipeline_latency = statistics.mean(pipeline_metrics['capture_times']) if pipeline_metrics['capture_times'] else 0
        avg_vad_latency = statistics.mean(pipeline_metrics['vad_times']) if pipeline_metrics['vad_times'] else 0

        return BenchmarkResult(
            name="End-to-End Pipeline",
            duration_seconds=total_duration,
            samples_processed=total_samples,
            throughput_samples_per_sec=throughput,
            latency_ms=avg_pipeline_latency,
            cpu_usage_percent=(cpu_after + cpu_before) / 2,
            memory_mb=mem_after - mem_before,
            details={
                'chunks_captured': pipeline_metrics['chunks_captured'],
                'chunks_processed_vad': pipeline_metrics['chunks_processed_vad'],
                'speech_chunks': pipeline_metrics['speech_chunks'],
                'avg_pipeline_latency_ms': avg_pipeline_latency,
                'avg_vad_latency_ms': avg_vad_latency,
                'max_pipeline_latency_ms': max(pipeline_metrics['capture_times']) if pipeline_metrics['capture_times'] else 0,
                'max_vad_latency_ms': max(pipeline_metrics['vad_times']) if pipeline_metrics['vad_times'] else 0
            }
        )

    def run_all_benchmarks(self, duration_per_benchmark: float = 5.0) -> List[BenchmarkResult]:
        """Run all benchmarks and return results"""
        logger.info("Starting comprehensive benchmark suite...")

        results = []

        # Benchmark 1: WASAPI Capture
        try:
            result = self.benchmark_wasapi_capture(duration_per_benchmark)
            results.append(result)
            print(result)
        except Exception as e:
            logger.error(f"WASAPI benchmark failed: {e}", exc_info=True)

        # Benchmark 2: Circular Buffer
        try:
            result = self.benchmark_circular_buffer(duration_per_benchmark)
            results.append(result)
            print(result)
        except Exception as e:
            logger.error(f"Buffer benchmark failed: {e}", exc_info=True)

        # Benchmark 3: VAD Processing
        try:
            result = self.benchmark_vad_processing(duration_per_benchmark)
            results.append(result)
            print(result)
        except Exception as e:
            logger.error(f"VAD benchmark failed: {e}", exc_info=True)

        # Benchmark 4: End-to-End Pipeline
        try:
            result = self.benchmark_end_to_end_pipeline(duration_per_benchmark)
            results.append(result)
            print(result)
        except Exception as e:
            logger.error(f"Pipeline benchmark failed: {e}", exc_info=True)

        return results


def generate_benchmark_report(results: List[BenchmarkResult], output_file: str = "benchmark_report.txt"):
    """Generate detailed benchmark report"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("RTSTT AUDIO CAPTURE - PERFORMANCE BENCHMARK REPORT\n")
        f.write("="*80 + "\n\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Sample Rate: 16000 Hz\n")
        f.write(f"Benchmarks Run: {len(results)}\n\n")

        for result in results:
            f.write(str(result) + "\n\n")

            # Write detailed metrics
            if result.details:
                f.write("Detailed Metrics:\n")
                for key, value in result.details.items():
                    if isinstance(value, float):
                        f.write(f"  {key}: {value:.4f}\n")
                    else:
                        f.write(f"  {key}: {value}\n")
                f.write("\n")

        # Summary
        f.write("="*80 + "\n")
        f.write("SUMMARY\n")
        f.write("="*80 + "\n")

        if results:
            avg_cpu = statistics.mean([r.cpu_usage_percent for r in results])
            latencies = [r.latency_ms for r in results if r.latency_ms > 0]
            avg_latency = statistics.mean(latencies) if latencies else 0
            total_throughput = sum([r.throughput_samples_per_sec for r in results])
            total_memory = sum([r.memory_mb for r in results])

            f.write(f"Average CPU Usage:    {avg_cpu:.1f}%\n")
            f.write(f"Average Latency:      {avg_latency:.2f}ms\n")
            f.write(f"Total Throughput:     {total_throughput:,.0f} samples/sec\n")
            f.write(f"Total Memory Delta:   {total_memory:.1f} MB\n\n")

            # Performance assessment
            f.write("PERFORMANCE ASSESSMENT:\n")
            f.write("-" * 40 + "\n")

            # Check latency target (<10ms)
            if avg_latency < 10.0:
                f.write(f"[PASS] Latency: {avg_latency:.2f}ms < 10ms target\n")
            else:
                f.write(f"[FAIL] Latency: {avg_latency:.2f}ms >= 10ms target\n")

            # Check CPU target (<5%)
            if avg_cpu < 5.0:
                f.write(f"[PASS] CPU Usage: {avg_cpu:.1f}% < 5% target\n")
            else:
                f.write(f"[FAIL] CPU Usage: {avg_cpu:.1f}% >= 5% target\n")

            # Check throughput target (>16000 samples/sec per benchmark)
            avg_throughput = total_throughput / len(results)
            if avg_throughput > 16000:
                f.write(f"[PASS] Throughput: {avg_throughput:,.0f} > 16000 samples/sec target\n")
            else:
                f.write(f"[FAIL] Throughput: {avg_throughput:,.0f} <= 16000 samples/sec target\n")

        f.write("="*80 + "\n")

    logger.info(f"Benchmark report saved to {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RTSTT Audio Capture Benchmark Suite")
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Duration for each benchmark in seconds (default: 5.0)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmarks/audio_benchmark_report.txt",
        help="Output file for benchmark report"
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Sample rate for audio processing (default: 16000)"
    )

    args = parser.parse_args()

    # Run benchmarks
    print("\n" + "="*80)
    print("RTSTT AUDIO CAPTURE - BENCHMARK SUITE")
    print("="*80)
    print(f"Duration per benchmark: {args.duration}s")
    print(f"Sample rate: {args.sample_rate} Hz")
    print("="*80 + "\n")

    benchmark = AudioBenchmark(sample_rate=args.sample_rate)
    results = benchmark.run_all_benchmarks(duration_per_benchmark=args.duration)

    # Generate report
    generate_benchmark_report(results, output_file=args.output)

    print("\n" + "="*80)
    print("BENCHMARK SUITE COMPLETED!")
    print("="*80)
    print(f"Total benchmarks run: {len(results)}")
    print(f"Report saved to: {args.output}")
    print("="*80 + "\n")
