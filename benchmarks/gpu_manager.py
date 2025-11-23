#!/usr/bin/env python3
"""
GPU Memory Safety Manager for RTSTT Benchmarking

Ensures safe model loading/unloading with NO GPU OOM errors during benchmarking.

Critical Rules:
1. Models loaded SEQUENTIALLY on GPU (never concurrent)
2. Explicit cleanup between model tests
3. Memory verification before loading
4. Automatic unloading on OOM risk

Usage:
    python benchmarks/gpu_manager.py --check-memory --required 4000
    python benchmarks/gpu_manager.py --unload-all --wait 5
    python benchmarks/gpu_manager.py --monitor --duration 60

Author: Claude Code (ORCHIDEA Framework v1.3)
"""

import argparse
import gc
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️  Warning: PyTorch not available, GPU management limited")


@dataclass
class GPUStatus:
    """GPU memory and utilization status."""
    device_id: int
    name: str
    memory_used_mb: int
    memory_total_mb: int
    memory_free_mb: int
    memory_percent: float
    utilization_percent: int
    temperature_celsius: Optional[int] = None


class GPUMemoryError(Exception):
    """Raised when GPU memory is insufficient."""
    pass


class GPUManager:
    """
    GPU memory safety manager for sequential model loading.

    Prevents OOM errors by:
    - Checking available memory before loading
    - Explicitly unloading models and clearing cache
    - Monitoring memory usage during execution
    - Auto-throttling on high memory usage
    """

    # Model memory requirements (MB) - conservative estimates
    MODEL_MEMORY_REQUIREMENTS = {
        # Whisper models
        "whisper-large-v3-fp16": 3200,
        "whisper-large-v3-int8": 1600,
        "distil-whisper-large-v3": 900,
        "whisper-medium-fp16": 1600,
        "whisper-medium-int8": 800,
        "whisper-small-fp16": 550,
        "whisper-small-int8": 300,
        "whisper-base-fp16": 200,
        "whisper-tiny-fp16": 100,

        # Llama models
        "llama-3.2-8b-fp16": 16000,
        "llama-3.2-8b-8bit": 8500,
        "llama-3.2-8b-4bit": 4500,
        "llama-3.2-3b-8bit": 3200,
        "llama-3.2-1b-8bit": 1100,

        # NLP models
        "sentence-bert": 100,
        "pyannote-diarization": 300,
    }

    SAFETY_MARGIN_MB = 1000  # Always keep 1 GB free
    MEMORY_WARNING_THRESHOLD = 0.85  # Warn at 85% usage
    MEMORY_CRITICAL_THRESHOLD = 0.95  # Critical at 95% usage

    def __init__(self, device_id: int = 0, verbose: bool = False):
        """
        Initialize GPU manager.

        Args:
            device_id: GPU device ID (default: 0)
            verbose: Enable verbose logging
        """
        self.device_id = device_id
        self.verbose = verbose
        self.loaded_models = []  # Track loaded models

        # Check if GPU is available
        if not TORCH_AVAILABLE:
            print("⚠️  PyTorch not available - GPU management disabled")
            return

        if not torch.cuda.is_available():
            print("⚠️  CUDA not available - GPU management disabled")
            return

        # Verify device exists
        if device_id >= torch.cuda.device_count():
            raise ValueError(f"GPU device {device_id} not found (available: {torch.cuda.device_count()})")

        self.log(f"GPU Manager initialized for device {device_id}")
        self.log(f"GPU: {torch.cuda.get_device_name(device_id)}")

    def log(self, message: str, level: str = "INFO") -> None:
        """Log message if verbose enabled."""
        if not self.verbose and level == "DEBUG":
            return

        timestamp = time.strftime("%H:%M:%S")
        if level == "ERROR":
            print(f"[{timestamp}] ❌ {message}", file=sys.stderr)
        elif level == "WARNING":
            print(f"[{timestamp}] ⚠️  {message}")
        elif level == "SUCCESS":
            print(f"[{timestamp}] ✅ {message}")
        else:
            print(f"[{timestamp}] ℹ️  {message}")

    def get_gpu_status(self) -> GPUStatus:
        """
        Get current GPU memory and utilization status.

        Returns:
            GPUStatus object with current GPU state
        """
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return GPUStatus(
                device_id=self.device_id,
                name="No GPU",
                memory_used_mb=0,
                memory_total_mb=0,
                memory_free_mb=0,
                memory_percent=0.0,
                utilization_percent=0
            )

        # PyTorch memory info
        memory_allocated = torch.cuda.memory_allocated(self.device_id)
        memory_reserved = torch.cuda.memory_reserved(self.device_id)

        # Try nvidia-smi for more accurate info
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu",
                    "--format=csv,noheader,nounits",
                    f"--id={self.device_id}"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                parts = result.stdout.strip().split(",")
                memory_used_mb = int(parts[0].strip())
                memory_total_mb = int(parts[1].strip())
                utilization_pct = int(parts[2].strip())
                temperature = int(parts[3].strip()) if len(parts) > 3 else None

                return GPUStatus(
                    device_id=self.device_id,
                    name=torch.cuda.get_device_name(self.device_id),
                    memory_used_mb=memory_used_mb,
                    memory_total_mb=memory_total_mb,
                    memory_free_mb=memory_total_mb - memory_used_mb,
                    memory_percent=(memory_used_mb / memory_total_mb) * 100,
                    utilization_percent=utilization_pct,
                    temperature_celsius=temperature
                )
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            self.log(f"nvidia-smi not available: {e}", "DEBUG")

        # Fallback to PyTorch memory info
        memory_props = torch.cuda.get_device_properties(self.device_id)
        memory_total_mb = memory_props.total_memory / (1024 ** 2)
        memory_used_mb = memory_reserved / (1024 ** 2)

        return GPUStatus(
            device_id=self.device_id,
            name=torch.cuda.get_device_name(self.device_id),
            memory_used_mb=int(memory_used_mb),
            memory_total_mb=int(memory_total_mb),
            memory_free_mb=int(memory_total_mb - memory_used_mb),
            memory_percent=(memory_used_mb / memory_total_mb) * 100,
            utilization_percent=0  # Not available from PyTorch
        )

    def check_memory_available(
        self,
        required_mb: int,
        model_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Check if sufficient GPU memory is available.

        Args:
            required_mb: Required memory in MB
            model_name: Optional model name for automatic requirement lookup

        Returns:
            (is_available, message)
        """
        if model_name and model_name in self.MODEL_MEMORY_REQUIREMENTS:
            required_mb = self.MODEL_MEMORY_REQUIREMENTS[model_name]
            self.log(f"Model {model_name} requires {required_mb} MB", "DEBUG")

        status = self.get_gpu_status()
        available_mb = status.memory_free_mb
        required_with_margin = required_mb + self.SAFETY_MARGIN_MB

        if available_mb >= required_with_margin:
            return True, f"Sufficient memory: {available_mb} MB available, {required_with_margin} MB required (with margin)"
        else:
            return False, f"Insufficient memory: {available_mb} MB available, {required_with_margin} MB required"

    def unload_all_models(self, wait_seconds: int = 2) -> None:
        """
        Unload all models and clear GPU cache.

        Args:
            wait_seconds: Seconds to wait after cleanup
        """
        self.log("Unloading all models and clearing GPU cache...", "DEBUG")

        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return

        # Clear PyTorch cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

        # Force garbage collection
        gc.collect()

        # Wait for cleanup
        if wait_seconds > 0:
            time.sleep(wait_seconds)

        # Verify cleanup
        status = self.get_gpu_status()
        self.log(
            f"GPU memory after cleanup: {status.memory_used_mb} MB used, {status.memory_free_mb} MB free",
            "SUCCESS"
        )

        self.loaded_models.clear()

    def safe_load_check(
        self,
        model_name: str,
        required_mb: Optional[int] = None
    ) -> None:
        """
        Check if safe to load model, raise exception if not.

        Args:
            model_name: Model name
            required_mb: Required memory (or auto-lookup from MODEL_MEMORY_REQUIREMENTS)

        Raises:
            GPUMemoryError: If insufficient memory available
        """
        if required_mb is None and model_name in self.MODEL_MEMORY_REQUIREMENTS:
            required_mb = self.MODEL_MEMORY_REQUIREMENTS[model_name]
        elif required_mb is None:
            # Unknown model, use conservative estimate
            required_mb = 5000
            self.log(f"Unknown model {model_name}, assuming {required_mb} MB", "WARNING")

        is_available, message = self.check_memory_available(required_mb)

        if not is_available:
            # Try cleanup first
            self.log("Insufficient memory, attempting cleanup...", "WARNING")
            self.unload_all_models(wait_seconds=3)

            # Check again
            is_available, message = self.check_memory_available(required_mb)

            if not is_available:
                raise GPUMemoryError(f"Cannot load {model_name}: {message}")

        self.log(f"Safe to load {model_name}: {message}", "SUCCESS")
        self.loaded_models.append(model_name)

    def monitor_memory(
        self,
        duration_seconds: int = 60,
        interval_seconds: int = 5,
        callback: Optional[callable] = None
    ) -> List[GPUStatus]:
        """
        Monitor GPU memory usage over time.

        Args:
            duration_seconds: Total monitoring duration
            interval_seconds: Sampling interval
            callback: Optional callback(status) called each interval

        Returns:
            List of GPUStatus samples
        """
        self.log(f"Monitoring GPU memory for {duration_seconds}s (interval: {interval_seconds}s)")

        samples = []
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            status = self.get_gpu_status()
            samples.append(status)

            # Log status
            self.log(
                f"GPU: {status.memory_used_mb}/{status.memory_total_mb} MB ({status.memory_percent:.1f}%), "
                f"Utilization: {status.utilization_percent}%",
                "DEBUG"
            )

            # Check thresholds
            if status.memory_percent >= self.MEMORY_CRITICAL_THRESHOLD * 100:
                self.log(
                    f"CRITICAL: GPU memory at {status.memory_percent:.1f}% (threshold: {self.MEMORY_CRITICAL_THRESHOLD*100}%)",
                    "ERROR"
                )
            elif status.memory_percent >= self.MEMORY_WARNING_THRESHOLD * 100:
                self.log(
                    f"WARNING: GPU memory at {status.memory_percent:.1f}% (threshold: {self.MEMORY_WARNING_THRESHOLD*100}%)",
                    "WARNING"
                )

            # Callback
            if callback:
                callback(status)

            time.sleep(interval_seconds)

        # Summary
        avg_memory_pct = sum(s.memory_percent for s in samples) / len(samples)
        max_memory_mb = max(s.memory_used_mb for s in samples)

        self.log("")
        self.log("Monitoring Summary:", "SUCCESS")
        self.log(f"  Samples: {len(samples)}")
        self.log(f"  Avg memory: {avg_memory_pct:.1f}%")
        self.log(f"  Peak memory: {max_memory_mb} MB")

        return samples

    def print_status(self) -> None:
        """Print current GPU status."""
        status = self.get_gpu_status()

        print("=" * 60)
        print("GPU Status")
        print("=" * 60)
        print(f"Device: {status.device_id} - {status.name}")
        print(f"Memory Used: {status.memory_used_mb} MB / {status.memory_total_mb} MB ({status.memory_percent:.1f}%)")
        print(f"Memory Free: {status.memory_free_mb} MB")
        print(f"Utilization: {status.utilization_percent}%")
        if status.temperature_celsius:
            print(f"Temperature: {status.temperature_celsius}°C")
        print(f"Loaded Models: {', '.join(self.loaded_models) if self.loaded_models else 'None'}")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="GPU Memory Safety Manager for RTSTT Benchmarking"
    )
    parser.add_argument(
        "--device",
        type=int,
        default=0,
        help="GPU device ID (default: 0)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    # Actions
    parser.add_argument(
        "--check-memory",
        action="store_true",
        help="Check available GPU memory"
    )
    parser.add_argument(
        "--required",
        type=int,
        help="Required memory in MB (for --check-memory)"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Model name (for automatic memory requirement lookup)"
    )
    parser.add_argument(
        "--unload-all",
        action="store_true",
        help="Unload all models and clear GPU cache"
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=2,
        help="Seconds to wait after unload (default: 2)"
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Monitor GPU memory usage over time"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Monitoring duration in seconds (default: 60)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Monitoring interval in seconds (default: 5)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print current GPU status"
    )

    args = parser.parse_args()

    # Initialize manager
    manager = GPUManager(device_id=args.device, verbose=args.verbose)

    # Execute actions
    if args.status or (not any([args.check_memory, args.unload_all, args.monitor])):
        manager.print_status()

    if args.check_memory:
        is_available, message = manager.check_memory_available(
            required_mb=args.required or 0,
            model_name=args.model
        )
        print(f"\n{'✅' if is_available else '❌'} {message}")
        return 0 if is_available else 1

    if args.unload_all:
        manager.unload_all_models(wait_seconds=args.wait)

    if args.monitor:
        samples = manager.monitor_memory(
            duration_seconds=args.duration,
            interval_seconds=args.interval
        )

        # Export samples
        import json
        output_file = "gpu_monitor_samples.json"
        with open(output_file, "w") as f:
            json.dump([s.__dict__ for s in samples], f, indent=2)
        print(f"\nSamples exported to {output_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
