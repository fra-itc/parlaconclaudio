#!/usr/bin/env python3
"""
Parallel ML Model Downloader for RTSTT Project

Downloads all required ML models with optimized parallel execution and 8-bit quantization support.

Models:
- Whisper Large V3 (2.9 GB) - Speech-to-Text
- Llama-3.2-8B (8 GB 8-bit / 15 GB fp16) - Summarization
- PyAnnote Speaker Diarization (250 MB) - Speaker identification
- Sentence-BERT all-MiniLM-L6-v2 (80 MB) - Keyword extraction
- Silero VAD v4 (2 MB) - Voice Activity Detection

Usage:
    python scripts/download_models.py [--model MODEL] [--use-8bit] [--skip-hf-token]

Author: Claude Code (ORCHIDEA Framework v1.3)
"""

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional
import time


class ModelDownloader:
    """Parallel ML model downloader with progress tracking."""

    MODELS = {
        "whisper": {
            "name": "Whisper Large V3",
            "size_gb": 2.9,
            "est_time_min": 10,
            "requires_token": False,
            "requires_gpu": False,
        },
        "llama": {
            "name": "Llama-3.2-8B-Instruct",
            "size_gb": 15,  # fp16, or 8 GB with 8-bit
            "est_time_min": 45,  # or 25 min with 8-bit
            "requires_token": True,
            "requires_gpu": True,
        },
        "pyannote": {
            "name": "PyAnnote Speaker Diarization 3.1",
            "size_gb": 0.25,
            "est_time_min": 5,
            "requires_token": True,
            "requires_gpu": False,
        },
        "sbert": {
            "name": "Sentence-BERT all-MiniLM-L6-v2",
            "size_gb": 0.08,
            "est_time_min": 2,
            "requires_token": False,
            "requires_gpu": False,
        },
        "silero_vad": {
            "name": "Silero VAD v4",
            "size_gb": 0.002,
            "est_time_min": 1,
            "requires_token": False,
            "requires_gpu": False,
        },
    }

    def __init__(
        self,
        project_root: Path,
        use_8bit: bool = True,
        skip_hf_token: bool = False,
        verbose: bool = False,
    ):
        """
        Initialize downloader.

        Args:
            project_root: Path to project root
            use_8bit: Use 8-bit quantization for Llama (saves ~7 GB, reduces time)
            skip_hf_token: Skip models requiring HuggingFace token
            verbose: Show detailed output
        """
        self.project_root = project_root
        self.use_8bit = use_8bit
        self.skip_hf_token = skip_hf_token
        self.verbose = verbose
        self.models_dir = project_root / "models"
        self.hf_token = os.getenv("HF_TOKEN")

        # Adjust Llama stats if 8-bit
        if use_8bit:
            self.MODELS["llama"]["size_gb"] = 8
            self.MODELS["llama"]["est_time_min"] = 25

    def log(self, message: str, level: str = "INFO") -> None:
        """Log message."""
        timestamp = time.strftime("%H:%M:%S")
        if level == "ERROR":
            print(f"[{timestamp}] ❌ {message}", file=sys.stderr)
        elif level == "SUCCESS":
            print(f"[{timestamp}] ✅ {message}")
        elif level == "WARNING":
            print(f"[{timestamp}] ⚠️  {message}")
        elif level == "DEBUG" and self.verbose:
            print(f"[{timestamp}] 🔍 {message}")
        else:
            print(f"[{timestamp}] ℹ️  {message}")

    def check_hf_token(self) -> bool:
        """Check if HuggingFace token is available."""
        if not self.hf_token:
            self.log("HuggingFace token not found in environment", "WARNING")
            self.log("Set HF_TOKEN in .env.local or environment variables", "WARNING")
            self.log("Get token: https://huggingface.co/settings/tokens", "WARNING")
            return False
        self.log("HuggingFace token found ✓", "DEBUG")
        return True

    def download_whisper(self) -> bool:
        """Download Whisper Large V3 model."""
        try:
            self.log("Downloading Whisper Large V3...")

            from faster_whisper import WhisperModel

            cache_dir = self.models_dir / "whisper"
            cache_dir.mkdir(parents=True, exist_ok=True)

            model = WhisperModel(
                "large-v3",
                device="cpu",  # CPU for download, will use GPU at runtime
                compute_type="int8",
                download_root=str(cache_dir),
            )

            self.log(f"Whisper Large V3 downloaded ✓ ({cache_dir})", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Error downloading Whisper: {e}", "ERROR")
            return False

    def download_llama(self) -> bool:
        """Download Llama-3.2-8B model with optional 8-bit quantization."""
        if not self.hf_token and not self.skip_hf_token:
            self.log("Llama requires HuggingFace token - skipping", "WARNING")
            return False

        try:
            quant_mode = "8-bit" if self.use_8bit else "fp16"
            self.log(f"Downloading Llama-3.2-8B-Instruct ({quant_mode})...")

            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch

            model_name = "meta-llama/Llama-3.2-8B-Instruct"
            cache_dir = self.models_dir / "transformers"
            cache_dir.mkdir(parents=True, exist_ok=True)

            self.log(f"Downloading tokenizer...", "DEBUG")
            tokenizer = AutoTokenizer.from_pretrained(
                model_name, token=self.hf_token, cache_dir=str(cache_dir)
            )

            self.log(f"Downloading model ({quant_mode})...", "DEBUG")
            if self.use_8bit:
                # 8-bit quantization (saves memory and download time)
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    token=self.hf_token,
                    load_in_8bit=True,
                    device_map="auto",
                    torch_dtype=torch.float16,
                    cache_dir=str(cache_dir),
                )
                size_info = "~8 GB"
            else:
                # Full precision
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    token=self.hf_token,
                    torch_dtype=torch.float16,
                    cache_dir=str(cache_dir),
                )
                size_info = "~15 GB"

            self.log(
                f"Llama-3.2-8B downloaded ✓ ({quant_mode}, {size_info})", "SUCCESS"
            )
            return True

        except Exception as e:
            self.log(f"Error downloading Llama: {e}", "ERROR")
            return False

    def download_pyannote(self) -> bool:
        """Download PyAnnote speaker diarization model."""
        if not self.hf_token and not self.skip_hf_token:
            self.log("PyAnnote requires HuggingFace token - skipping", "WARNING")
            return False

        try:
            self.log("Downloading PyAnnote Speaker Diarization 3.1...")

            from pyannote.audio import Pipeline

            cache_dir = self.models_dir / "transformers"
            cache_dir.mkdir(parents=True, exist_ok=True)

            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.hf_token,
                cache_dir=str(cache_dir),
            )

            self.log(f"PyAnnote downloaded ✓ ({cache_dir})", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Error downloading PyAnnote: {e}", "ERROR")
            return False

    def download_sbert(self) -> bool:
        """Download Sentence-BERT model."""
        try:
            self.log("Downloading Sentence-BERT all-MiniLM-L6-v2...")

            from sentence_transformers import SentenceTransformer

            cache_dir = self.models_dir / "transformers"
            cache_dir.mkdir(parents=True, exist_ok=True)

            model = SentenceTransformer(
                "all-MiniLM-L6-v2", cache_folder=str(cache_dir)
            )

            self.log(f"Sentence-BERT downloaded ✓ ({cache_dir})", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Error downloading Sentence-BERT: {e}", "ERROR")
            return False

    def download_silero_vad(self) -> bool:
        """Download Silero VAD model."""
        try:
            self.log("Downloading Silero VAD v4...")

            import torch

            cache_dir = self.models_dir / "silero_vad"
            cache_dir.mkdir(parents=True, exist_ok=True)

            model, utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                trust_repo=True,
            )

            # Save to local cache
            model_path = cache_dir / "silero_vad.pt"
            torch.save(model.state_dict(), str(model_path))

            self.log(f"Silero VAD downloaded ✓ ({model_path})", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Error downloading Silero VAD: {e}", "ERROR")
            return False

    def download_model(self, model_key: str) -> Dict[str, any]:
        """Download a single model with error handling."""
        start_time = time.time()
        info = self.MODELS[model_key]

        self.log(f"Starting download: {info['name']}", "DEBUG")

        # Check HF token requirement
        if info["requires_token"] and not self.hf_token:
            if self.skip_hf_token:
                self.log(
                    f"{info['name']}: Skipped (requires HF token)", "WARNING"
                )
                return {"model": model_key, "success": False, "skipped": True}

        # Download based on model type
        downloaders = {
            "whisper": self.download_whisper,
            "llama": self.download_llama,
            "pyannote": self.download_pyannote,
            "sbert": self.download_sbert,
            "silero_vad": self.download_silero_vad,
        }

        success = downloaders[model_key]()
        elapsed = time.time() - start_time

        return {
            "model": model_key,
            "name": info["name"],
            "success": success,
            "elapsed_min": elapsed / 60,
            "size_gb": info["size_gb"],
        }

    def download_all(self, models: Optional[List[str]] = None) -> bool:
        """
        Download all models in parallel.

        Args:
            models: List of model keys to download (None = all)

        Returns:
            True if all succeeded, False if any failed
        """
        if models is None:
            models = list(self.MODELS.keys())

        self.log("=" * 60)
        self.log("RTSTT ML Model Downloader")
        self.log("=" * 60)

        # Check HF token
        has_token = self.check_hf_token()
        if not has_token and not self.skip_hf_token:
            needs_token = [
                k for k in models if self.MODELS[k]["requires_token"]
            ]
            if needs_token:
                self.log(
                    f"Models requiring HF token: {', '.join(needs_token)}",
                    "WARNING",
                )
                self.log("Use --skip-hf-token to skip these models", "WARNING")

        # Calculate totals
        total_size = sum(self.MODELS[k]["size_gb"] for k in models)
        total_time = sum(self.MODELS[k]["est_time_min"] for k in models)

        self.log(f"Models to download: {len(models)}")
        self.log(f"Total size: ~{total_size:.1f} GB")
        self.log(
            f"Estimated time: ~{total_time:.0f} minutes (sequential)"
        )
        self.log(f"8-bit quantization: {'Enabled' if self.use_8bit else 'Disabled'}")
        self.log("")

        # Download in parallel
        self.log("Starting parallel downloads...")
        results = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.download_model, model_key): model_key
                for model_key in models
            }

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        # Summary
        self.log("")
        self.log("=" * 60)
        self.log("DOWNLOAD SUMMARY")
        self.log("=" * 60)

        successful = [r for r in results if r.get("success", False)]
        failed = [r for r in results if not r.get("success", False) and not r.get("skipped", False)]
        skipped = [r for r in results if r.get("skipped", False)]

        for r in successful:
            self.log(
                f"{r['name']}: {r['size_gb']:.2f} GB in {r['elapsed_min']:.1f} min",
                "SUCCESS",
            )

        for r in failed:
            self.log(f"{r['model']}: Failed", "ERROR")

        for r in skipped:
            self.log(f"{r['model']}: Skipped (requires HF token)", "WARNING")

        self.log("")
        self.log(f"Successful: {len(successful)}/{len(models)}")
        self.log(f"Failed: {len(failed)}")
        self.log(f"Skipped: {len(skipped)}")

        if successful:
            total_downloaded = sum(r["size_gb"] for r in successful)
            total_time_actual = sum(r["elapsed_min"] for r in successful)
            self.log(f"Total downloaded: {total_downloaded:.1f} GB")
            self.log(f"Total time: {total_time_actual:.1f} minutes")

        return len(failed) == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download RTSTT ML models in parallel"
    )
    parser.add_argument(
        "--model",
        choices=["whisper", "llama", "pyannote", "sbert", "silero_vad"],
        help="Download specific model only (default: all)",
    )
    parser.add_argument(
        "--use-8bit",
        action="store_true",
        default=True,
        help="Use 8-bit quantization for Llama (default: True, saves ~7 GB)",
    )
    parser.add_argument(
        "--no-8bit",
        action="store_true",
        help="Disable 8-bit quantization (download full fp16 Llama)",
    )
    parser.add_argument(
        "--skip-hf-token",
        action="store_true",
        help="Skip models requiring HuggingFace token",
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

    # Resolve 8-bit setting
    use_8bit = args.use_8bit and not args.no_8bit

    # Check dependencies
    try:
        import torch
        import transformers
    except ImportError as e:
        print(f"❌ Error: Missing dependencies - {e}", file=sys.stderr)
        print("Install with: pip install -r requirements/ml.txt", file=sys.stderr)
        return 1

    # Run downloader
    downloader = ModelDownloader(
        project_root=args.project_root,
        use_8bit=use_8bit,
        skip_hf_token=args.skip_hf_token,
        verbose=args.verbose,
    )

    models = [args.model] if args.model else None
    success = downloader.download_all(models=models)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
