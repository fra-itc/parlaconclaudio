#!/usr/bin/env python3
"""
Quick GPU Validation Script for RTX 5080

Validates that PyTorch 2.7.0+cu128 correctly detects and utilizes RTX 5080 GPU.

Tests:
1. CUDA availability and version
2. GPU device detection (RTX 5080)
3. Compute capability (12.0 for Blackwell)
4. Memory allocation and cleanup
5. Simple tensor operations on GPU

Usage:
    python benchmarks/quick_gpu_validation.py
    python benchmarks/quick_gpu_validation.py --verbose

Author: Claude Code - RTX 5080 Validation
"""

import argparse
import sys
import time
from datetime import datetime
from typing import Dict, Any

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("❌ ERROR: PyTorch not available")
    sys.exit(1)


class GPUValidator:
    """RTX 5080 GPU validation suite."""

    def __init__(self, verbose: bool = False):
        """Initialize validator."""
        self.verbose = verbose
        self.results = {}
        self.device_id = 0

    def log(self, message: str, level: str = "INFO") -> None:
        """Log message."""
        if not self.verbose and level == "DEBUG":
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "DEBUG": "🔍"
        }.get(level, "ℹ️")

        print(f"[{timestamp}] {emoji} {message}")

    def test_cuda_availability(self) -> bool:
        """Test 1: CUDA availability."""
        self.log("Test 1: Checking CUDA availability...", "INFO")

        cuda_available = torch.cuda.is_available()
        self.results["cuda_available"] = cuda_available

        if cuda_available:
            cuda_version = torch.version.cuda
            self.results["cuda_version"] = cuda_version
            self.log(f"CUDA available: {cuda_version}", "SUCCESS")
            return True
        else:
            self.log("CUDA not available", "ERROR")
            return False

    def test_gpu_detection(self) -> bool:
        """Test 2: GPU device detection."""
        self.log("Test 2: Detecting GPU device...", "INFO")

        device_count = torch.cuda.device_count()
        self.results["device_count"] = device_count

        if device_count == 0:
            self.log("No GPU devices found", "ERROR")
            return False

        device_name = torch.cuda.get_device_name(self.device_id)
        self.results["device_name"] = device_name

        is_rtx_5080 = "RTX 5080" in device_name or "5080" in device_name
        self.results["is_rtx_5080"] = is_rtx_5080

        if is_rtx_5080:
            self.log(f"RTX 5080 detected: {device_name}", "SUCCESS")
            return True
        else:
            self.log(f"GPU detected but not RTX 5080: {device_name}", "WARNING")
            return True  # Still pass if GPU exists

    def test_compute_capability(self) -> bool:
        """Test 3: Compute capability (Blackwell sm_120)."""
        self.log("Test 3: Checking compute capability...", "INFO")

        capability = torch.cuda.get_device_capability(self.device_id)
        self.results["compute_capability"] = f"{capability[0]}.{capability[1]}"

        is_blackwell = capability[0] == 12 and capability[1] == 0
        self.results["is_blackwell"] = is_blackwell

        if is_blackwell:
            self.log(f"Blackwell architecture detected: sm_{capability[0]}{capability[1]}", "SUCCESS")
            return True
        else:
            self.log(f"Compute capability: sm_{capability[0]}{capability[1]} (expected: sm_120)", "WARNING")
            return True

    def test_pytorch_version(self) -> bool:
        """Test 4: PyTorch version (2.7.0+cu128)."""
        self.log("Test 4: Checking PyTorch version...", "INFO")

        pytorch_version = torch.__version__
        self.results["pytorch_version"] = pytorch_version

        is_correct_version = pytorch_version.startswith("2.7.0") and "cu128" in pytorch_version
        self.results["pytorch_version_correct"] = is_correct_version

        if is_correct_version:
            self.log(f"PyTorch version correct: {pytorch_version}", "SUCCESS")
            return True
        else:
            self.log(f"PyTorch version: {pytorch_version} (expected: 2.7.0+cu128)", "WARNING")
            return False

    def test_memory_allocation(self) -> bool:
        """Test 5: GPU memory allocation and deallocation."""
        self.log("Test 5: Testing GPU memory allocation...", "INFO")

        try:
            # Get initial memory
            initial_allocated = torch.cuda.memory_allocated(self.device_id) / (1024 ** 3)
            initial_reserved = torch.cuda.memory_reserved(self.device_id) / (1024 ** 3)

            self.log(f"Initial memory: {initial_allocated:.2f} GB allocated, {initial_reserved:.2f} GB reserved", "DEBUG")

            # Allocate 1 GB tensor
            size = (1024, 1024, 256)  # ~1 GB
            tensor = torch.randn(size, device=f"cuda:{self.device_id}")

            allocated_after = torch.cuda.memory_allocated(self.device_id) / (1024 ** 3)
            self.log(f"After allocation: {allocated_after:.2f} GB", "DEBUG")

            # Free tensor
            del tensor
            torch.cuda.empty_cache()
            time.sleep(0.5)

            final_allocated = torch.cuda.memory_allocated(self.device_id) / (1024 ** 3)
            self.log(f"After cleanup: {final_allocated:.2f} GB", "DEBUG")

            self.results["memory_test_passed"] = True
            self.log("Memory allocation and cleanup successful", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Memory allocation failed: {e}", "ERROR")
            self.results["memory_test_passed"] = False
            return False

    def test_tensor_operations(self) -> bool:
        """Test 6: GPU tensor operations."""
        self.log("Test 6: Testing GPU tensor operations...", "INFO")

        try:
            # Matrix multiplication on GPU
            size = 2048
            a = torch.randn(size, size, device=f"cuda:{self.device_id}")
            b = torch.randn(size, size, device=f"cuda:{self.device_id}")

            start_time = time.time()
            c = torch.matmul(a, b)
            torch.cuda.synchronize()
            elapsed = time.time() - start_time

            self.results["matmul_time_ms"] = elapsed * 1000
            self.log(f"Matrix multiplication (2048x2048): {elapsed*1000:.2f} ms", "SUCCESS")

            # Cleanup
            del a, b, c
            torch.cuda.empty_cache()

            return True

        except Exception as e:
            self.log(f"Tensor operations failed: {e}", "ERROR")
            return False

    def test_gpu_properties(self) -> bool:
        """Test 7: GPU properties."""
        self.log("Test 7: Reading GPU properties...", "INFO")

        try:
            props = torch.cuda.get_device_properties(self.device_id)

            self.results["total_memory_gb"] = props.total_memory / (1024 ** 3)
            self.results["multi_processor_count"] = props.multi_processor_count
            self.results["major"] = props.major
            self.results["minor"] = props.minor

            self.log(f"Total memory: {self.results['total_memory_gb']:.1f} GB", "DEBUG")
            self.log(f"SM count: {props.multi_processor_count}", "DEBUG")

            return True

        except Exception as e:
            self.log(f"Failed to read GPU properties: {e}", "ERROR")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("=" * 70)
        print("RTX 5080 GPU Validation Suite")
        print("=" * 70)
        print()

        tests = [
            ("CUDA Availability", self.test_cuda_availability),
            ("GPU Detection", self.test_gpu_detection),
            ("Compute Capability", self.test_compute_capability),
            ("PyTorch Version", self.test_pytorch_version),
            ("Memory Allocation", self.test_memory_allocation),
            ("Tensor Operations", self.test_tensor_operations),
            ("GPU Properties", self.test_gpu_properties),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"Test {test_name} crashed: {e}", "ERROR")
                failed += 1

            print()  # Blank line between tests

        # Summary
        print("=" * 70)
        print("Validation Summary")
        print("=" * 70)
        print(f"Tests Passed: {passed}/{len(tests)}")
        print(f"Tests Failed: {failed}/{len(tests)}")
        print()

        # Key results
        print("Key Configuration:")
        print(f"  GPU: {self.results.get('device_name', 'Unknown')}")
        print(f"  Compute Capability: {self.results.get('compute_capability', 'Unknown')}")
        print(f"  PyTorch Version: {self.results.get('pytorch_version', 'Unknown')}")
        print(f"  CUDA Version: {self.results.get('cuda_version', 'Unknown')}")
        print(f"  Total Memory: {self.results.get('total_memory_gb', 0):.1f} GB")
        print()

        if self.results.get("is_rtx_5080") and self.results.get("is_blackwell"):
            print("✅ RTX 5080 Blackwell GPU is correctly configured!")
        elif self.results.get("cuda_available"):
            print("⚠️  GPU is available but may not be RTX 5080 Blackwell")
        else:
            print("❌ GPU validation failed")

        print("=" * 70)

        return self.results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Quick GPU Validation for RTX 5080"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file for results"
    )

    args = parser.parse_args()

    # Run validation
    validator = GPUValidator(verbose=args.verbose)
    results = validator.run_all_tests()

    # Save results if requested
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output}")

    # Exit code based on critical tests
    critical_passed = (
        results.get("cuda_available", False) and
        results.get("pytorch_version_correct", False)
    )

    return 0 if critical_passed else 1


if __name__ == "__main__":
    sys.exit(main())
