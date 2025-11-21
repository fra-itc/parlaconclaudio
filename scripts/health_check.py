#!/usr/bin/env python3
"""
Comprehensive Health Check for RTSTT Deployment

Validates all services, checks GPU resources, tests API endpoints, and verifies monitoring.

Usage:
    python scripts/health_check.py [--timeout SECONDS] [--skip-gpu] [--json]

Author: Claude Code (ORCHIDEA Framework v1.3)
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.error


class HealthChecker:
    """Comprehensive health checker for RTSTT deployment."""

    SERVICES = {
        "redis": {
            "name": "Redis",
            "container": "rtstt-redis",
            "port": 6379,
            "http_health": None,
            "docker_health": True,
        },
        "stt-engine": {
            "name": "STT Engine (Whisper)",
            "container": "rtstt-stt-engine",
            "port": 50051,
            "http_health": None,  # gRPC, needs special client
            "docker_health": True,
        },
        "nlp-service": {
            "name": "NLP Service",
            "container": "rtstt-nlp-service",
            "port": 50052,
            "http_health": None,
            "docker_health": True,
        },
        "summary-service": {
            "name": "Summary Service (Llama)",
            "container": "rtstt-summary-service",
            "port": 50053,
            "http_health": None,
            "docker_health": True,
        },
        "backend": {
            "name": "Backend API (FastAPI)",
            "container": "rtstt-backend",
            "port": 8000,
            "http_health": "http://localhost:8000/health",
            "docker_health": True,
        },
        "prometheus": {
            "name": "Prometheus",
            "container": "rtstt-prometheus",
            "port": 9090,
            "http_health": "http://localhost:9090/-/healthy",
            "docker_health": True,
        },
        "grafana": {
            "name": "Grafana",
            "container": "rtstt-grafana",
            "port": 3001,
            "http_health": "http://localhost:3001/api/health",
            "docker_health": True,
        },
    }

    def __init__(
        self,
        timeout: int = 5,
        skip_gpu: bool = False,
        verbose: bool = False,
        json_output: bool = False,
    ):
        """
        Initialize health checker.

        Args:
            timeout: HTTP request timeout in seconds
            skip_gpu: Skip GPU-related checks
            verbose: Show detailed output
            json_output: Output results as JSON
        """
        self.timeout = timeout
        self.skip_gpu = skip_gpu
        self.verbose = verbose
        self.json_output = json_output
        self.results = {}

    def log(self, message: str, level: str = "INFO") -> None:
        """Log message (unless JSON mode)."""
        if self.json_output:
            return

        if level == "ERROR":
            print(f"❌ {message}", file=sys.stderr)
        elif level == "SUCCESS":
            print(f"✅ {message}")
        elif level == "WARNING":
            print(f"⚠️  {message}")
        elif level == "DEBUG" and self.verbose:
            print(f"🔍 {message}")
        else:
            print(f"ℹ️  {message}")

    def run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """
        Run command and return (exit_code, stdout, stderr).

        Args:
            cmd: Command as list of strings

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)

    def check_docker_running(self) -> bool:
        """Check if Docker daemon is running."""
        self.log("Checking Docker daemon...", "DEBUG")
        exit_code, stdout, stderr = self.run_command(["docker", "info"])

        if exit_code != 0:
            self.log("Docker daemon not running", "ERROR")
            self.results["docker"] = {"status": "error", "message": "Docker not running"}
            return False

        self.log("Docker daemon running ✓", "SUCCESS")
        self.results["docker"] = {"status": "ok"}
        return True

    def check_container_status(self, service_key: str) -> Dict[str, any]:
        """
        Check Docker container status.

        Args:
            service_key: Service key from SERVICES dict

        Returns:
            Dict with status info
        """
        service = self.SERVICES[service_key]
        container_name = service["container"]

        self.log(f"Checking {service['name']} container...", "DEBUG")

        # Get container status
        exit_code, stdout, stderr = self.run_command([
            "docker",
            "inspect",
            "--format",
            "{{.State.Status}}|{{.State.Health.Status}}",
            container_name,
        ])

        if exit_code != 0:
            self.log(f"{service['name']}: Container not found", "ERROR")
            return {"status": "not_found", "container": container_name}

        parts = stdout.strip().split("|")
        state = parts[0] if len(parts) > 0 else "unknown"
        health = parts[1] if len(parts) > 1 else "none"

        if state != "running":
            self.log(f"{service['name']}: Container not running (state: {state})", "ERROR")
            return {"status": "not_running", "state": state, "container": container_name}

        if health != "none" and health != "healthy":
            self.log(f"{service['name']}: Container unhealthy (health: {health})", "WARNING")
            return {"status": "unhealthy", "state": state, "health": health, "container": container_name}

        self.log(f"{service['name']}: Container running ✓", "SUCCESS")
        return {"status": "ok", "state": state, "health": health, "container": container_name}

    def check_http_health(self, service_key: str) -> Optional[Dict[str, any]]:
        """
        Check HTTP health endpoint.

        Args:
            service_key: Service key from SERVICES dict

        Returns:
            Dict with health check result, or None if no HTTP endpoint
        """
        service = self.SERVICES[service_key]
        url = service.get("http_health")

        if not url:
            return None

        self.log(f"Checking {service['name']} HTTP health...", "DEBUG")

        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                status_code = response.status
                body = response.read().decode("utf-8")

                if status_code == 200:
                    self.log(f"{service['name']}: HTTP health OK ✓", "SUCCESS")
                    return {"status": "ok", "http_code": status_code, "url": url}
                else:
                    self.log(f"{service['name']}: HTTP health returned {status_code}", "WARNING")
                    return {"status": "warning", "http_code": status_code, "url": url}

        except urllib.error.URLError as e:
            self.log(f"{service['name']}: HTTP health failed - {e.reason}", "ERROR")
            return {"status": "error", "error": str(e.reason), "url": url}
        except Exception as e:
            self.log(f"{service['name']}: HTTP health failed - {e}", "ERROR")
            return {"status": "error", "error": str(e), "url": url}

    def check_gpu_status(self) -> Dict[str, any]:
        """Check GPU status and memory usage."""
        if self.skip_gpu:
            return {"status": "skipped"}

        self.log("Checking GPU status...", "DEBUG")

        # Check nvidia-smi
        exit_code, stdout, stderr = self.run_command([
            "nvidia-smi",
            "--query-gpu=name,memory.used,memory.total,utilization.gpu",
            "--format=csv,noheader,nounits",
        ])

        if exit_code != 0:
            self.log("GPU check failed (nvidia-smi not available)", "WARNING")
            return {"status": "not_available", "message": "nvidia-smi not found"}

        # Parse output
        parts = stdout.strip().split(",")
        if len(parts) >= 4:
            gpu_name = parts[0].strip()
            memory_used_mb = int(parts[1].strip())
            memory_total_mb = int(parts[2].strip())
            utilization_pct = int(parts[3].strip())

            memory_used_gb = memory_used_mb / 1024
            memory_total_gb = memory_total_mb / 1024
            memory_pct = (memory_used_mb / memory_total_mb) * 100

            self.log(f"GPU: {gpu_name}", "SUCCESS")
            self.log(f"Memory: {memory_used_gb:.1f} / {memory_total_gb:.1f} GB ({memory_pct:.1f}%)", "SUCCESS")
            self.log(f"Utilization: {utilization_pct}%", "SUCCESS")

            # Check if memory exceeds threshold
            if memory_used_gb > 16:
                self.log("⚠️  GPU memory usage exceeds 16 GB", "WARNING")

            return {
                "status": "ok",
                "name": gpu_name,
                "memory_used_mb": memory_used_mb,
                "memory_total_mb": memory_total_mb,
                "memory_used_gb": round(memory_used_gb, 2),
                "memory_total_gb": round(memory_total_gb, 2),
                "memory_percent": round(memory_pct, 1),
                "utilization_percent": utilization_pct,
            }
        else:
            self.log("GPU check failed (unexpected output)", "ERROR")
            return {"status": "error", "message": "Unexpected nvidia-smi output"}

    def check_api_endpoints(self) -> Dict[str, any]:
        """Check key API endpoints."""
        self.log("Checking API endpoints...", "DEBUG")

        endpoints = {
            "/health": "http://localhost:8000/health",
            "/health/ready": "http://localhost:8000/health/ready",
            "/api/v1/audio/devices": "http://localhost:8000/api/v1/audio/devices",
        }

        results = {}

        for name, url in endpoints.items():
            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    status_code = response.status
                    if status_code == 200:
                        self.log(f"API {name}: OK ✓", "SUCCESS")
                        results[name] = {"status": "ok", "http_code": status_code}
                    else:
                        self.log(f"API {name}: Returned {status_code}", "WARNING")
                        results[name] = {"status": "warning", "http_code": status_code}
            except Exception as e:
                self.log(f"API {name}: Failed - {e}", "ERROR")
                results[name] = {"status": "error", "error": str(e)}

        return results

    def run_all_checks(self) -> bool:
        """
        Run all health checks.

        Returns:
            True if all checks passed, False if any failed
        """
        if not self.json_output:
            self.log("=" * 60)
            self.log("RTSTT Deployment Health Check")
            self.log("=" * 60)

        start_time = time.time()
        all_passed = True

        # Check Docker
        if not self.check_docker_running():
            return False

        # Check all services
        self.results["services"] = {}
        for service_key in self.SERVICES.keys():
            container_status = self.check_container_status(service_key)
            http_status = self.check_http_health(service_key)

            self.results["services"][service_key] = {
                "container": container_status,
                "http": http_status,
            }

            if container_status["status"] != "ok":
                all_passed = False

            if http_status and http_status["status"] == "error":
                all_passed = False

        # Check GPU
        self.results["gpu"] = self.check_gpu_status()

        # Check API endpoints
        self.results["api"] = self.check_api_endpoints()

        # Summary
        elapsed = time.time() - start_time

        if not self.json_output:
            self.log("")
            self.log("=" * 60)
            self.log("HEALTH CHECK SUMMARY")
            self.log("=" * 60)

            services_ok = sum(
                1 for s in self.results["services"].values()
                if s["container"]["status"] == "ok"
            )
            self.log(f"Services healthy: {services_ok}/{len(self.SERVICES)}")

            if self.results["gpu"]["status"] == "ok":
                gpu_info = self.results["gpu"]
                self.log(
                    f"GPU memory: {gpu_info['memory_used_gb']:.1f}/{gpu_info['memory_total_gb']:.1f} GB"
                )

            api_ok = sum(
                1 for a in self.results["api"].values()
                if a["status"] == "ok"
            )
            self.log(f"API endpoints OK: {api_ok}/{len(self.results['api'])}")

            self.log(f"Check completed in {elapsed:.1f}s")

            if all_passed:
                self.log("")
                self.log("✅ ALL CHECKS PASSED - System healthy!", "SUCCESS")
            else:
                self.log("")
                self.log("❌ SOME CHECKS FAILED - See errors above", "ERROR")

        return all_passed

    def output_json(self) -> None:
        """Output results as JSON."""
        print(json.dumps(self.results, indent=2))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive health check for RTSTT deployment"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="HTTP request timeout in seconds (default: 5)",
    )
    parser.add_argument(
        "--skip-gpu",
        action="store_true",
        help="Skip GPU checks",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    # Run health checks
    checker = HealthChecker(
        timeout=args.timeout,
        skip_gpu=args.skip_gpu,
        verbose=args.verbose,
        json_output=args.json,
    )

    all_passed = checker.run_all_checks()

    # Output JSON if requested
    if args.json:
        checker.output_json()

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
