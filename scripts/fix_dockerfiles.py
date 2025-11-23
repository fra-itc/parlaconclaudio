#!/usr/bin/env python3
"""
Automated Dockerfile Path Fixer for RTSTT Project

Fixes incorrect CMD paths in Docker service files that prevent gRPC services from starting.

Usage:
    python scripts/fix_dockerfiles.py [--dry-run] [--verbose]

Author: Claude Code (ORCHIDEA Framework v1.3)
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class DockerfileFixer:
    """Automated fixer for Dockerfile CMD path errors."""

    # Mapping of Dockerfile -> (incorrect_path, correct_path)
    FIXES: Dict[str, Tuple[str, str]] = {
        "infrastructure/docker/Dockerfile.stt": (
            'CMD ["python", "-m", "src.agents.stt.grpc_server"]',
            'CMD ["python", "-m", "src.core.stt_engine.grpc_server"]',
        ),
        "infrastructure/docker/Dockerfile.nlp": (
            'CMD ["python", "-m", "src.agents.nlp.grpc_server"]',
            'CMD ["python", "-m", "src.core.nlp_insights.nlp_service"]',
        ),
        "infrastructure/docker/Dockerfile.summary": (
            'CMD ["python", "-m", "src.agents.summary.grpc_server"]',
            'CMD ["python", "-m", "src.core.summary_generator.summary_service"]',
        ),
    }

    def __init__(self, project_root: Path, dry_run: bool = False, verbose: bool = False):
        """
        Initialize fixer.

        Args:
            project_root: Path to project root directory
            dry_run: If True, only show what would be changed
            verbose: If True, show detailed output
        """
        self.project_root = project_root
        self.dry_run = dry_run
        self.verbose = verbose
        self.fixes_applied = 0
        self.errors = 0

    def log(self, message: str, level: str = "INFO") -> None:
        """Log message with level."""
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

    def fix_dockerfile(self, dockerfile_path: str, incorrect: str, correct: str) -> bool:
        """
        Fix a single Dockerfile.

        Args:
            dockerfile_path: Relative path to Dockerfile
            incorrect: Incorrect CMD line to find
            correct: Correct CMD line to replace with

        Returns:
            True if fix applied, False if no changes needed or error
        """
        full_path = self.project_root / dockerfile_path

        if not full_path.exists():
            self.log(f"File not found: {dockerfile_path}", "ERROR")
            self.errors += 1
            return False

        self.log(f"Checking {dockerfile_path}...", "DEBUG")

        # Read file
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.log(f"Error reading {dockerfile_path}: {e}", "ERROR")
            self.errors += 1
            return False

        # Check if fix needed
        if incorrect not in content:
            if correct in content:
                self.log(f"{dockerfile_path}: Already correct ✓", "SUCCESS")
                return False
            else:
                self.log(
                    f"{dockerfile_path}: Neither incorrect nor correct path found (manual check needed)",
                    "WARNING",
                )
                return False

        # Apply fix
        if self.dry_run:
            self.log(f"{dockerfile_path}: Would fix CMD path", "INFO")
            self.log(f"  FROM: {incorrect}", "DEBUG")
            self.log(f"  TO:   {correct}", "DEBUG")
            return True

        try:
            new_content = content.replace(incorrect, correct)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            self.log(f"{dockerfile_path}: Fixed CMD path ✓", "SUCCESS")
            self.fixes_applied += 1
            return True
        except Exception as e:
            self.log(f"Error writing {dockerfile_path}: {e}", "ERROR")
            self.errors += 1
            return False

    def run(self) -> int:
        """
        Run all fixes.

        Returns:
            Exit code (0 = success, 1 = errors)
        """
        self.log("=" * 60)
        self.log("RTSTT Dockerfile Path Fixer")
        self.log("=" * 60)

        if self.dry_run:
            self.log("DRY RUN MODE - No files will be modified", "WARNING")

        self.log(f"Project root: {self.project_root}")
        self.log(f"Dockerfiles to check: {len(self.FIXES)}")
        self.log("")

        # Apply all fixes
        for dockerfile, (incorrect, correct) in self.FIXES.items():
            self.fix_dockerfile(dockerfile, incorrect, correct)
            self.log("")

        # Summary
        self.log("=" * 60)
        self.log("SUMMARY")
        self.log("=" * 60)
        self.log(f"Fixes applied: {self.fixes_applied}")
        self.log(f"Errors: {self.errors}")

        if self.dry_run and self.fixes_applied > 0:
            self.log("")
            self.log("Run without --dry-run to apply fixes", "INFO")

        return 0 if self.errors == 0 else 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fix incorrect CMD paths in RTSTT Dockerfiles"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Path to project root (default: current directory)",
    )

    args = parser.parse_args()

    # Find project root (look for orchestration/ directory)
    project_root = args.project_root
    if not (project_root / "orchestration").exists():
        print(
            f"❌ Error: {project_root} does not appear to be RTSTT project root",
            file=sys.stderr,
        )
        print("   (orchestration/ directory not found)", file=sys.stderr)
        return 1

    # Run fixer
    fixer = DockerfileFixer(
        project_root=project_root, dry_run=args.dry_run, verbose=args.verbose
    )
    return fixer.run()


if __name__ == "__main__":
    sys.exit(main())
