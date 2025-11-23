"""
Test script per verificare il caricamento di Llama-3.2-8B

Questo script verifica:
1. Disponibilità delle dipendenze
2. Connessione a HuggingFace Hub
3. Disponibilità del modello
4. Setup GPU (se disponibile)

Author: ML Team
Date: 2025-11-21
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Verifica che tutte le dipendenze siano installate."""
    logger.info("Checking dependencies...")

    required_modules = [
        ('torch', 'PyTorch'),
        ('transformers', 'Transformers'),
        ('accelerate', 'Accelerate'),
    ]

    missing = []
    for module_name, display_name in required_modules:
        try:
            __import__(module_name)
            logger.info(f"  {display_name}: OK")
        except ImportError:
            logger.error(f"  {display_name}: MISSING")
            missing.append(display_name)

    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        logger.error("Install with: pip install -r requirements/ml.txt")
        return False

    return True


def check_gpu():
    """Verifica disponibilità GPU."""
    logger.info("Checking GPU availability...")

    try:
        import torch

        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_count = torch.cuda.device_count()
            logger.info(f"  GPU Available: {gpu_name}")
            logger.info(f"  GPU Count: {gpu_count}")
            logger.info(f"  CUDA Version: {torch.version.cuda}")
            return True
        else:
            logger.warning("  GPU Not Available - Will use CPU (slower)")
            return False

    except Exception as e:
        logger.error(f"  Error checking GPU: {e}")
        return False


def check_model_availability():
    """Verifica che il modello sia disponibile su HuggingFace Hub."""
    logger.info("Checking model availability on HuggingFace Hub...")

    try:
        from huggingface_hub import model_info

        model_name = "meta-llama/Llama-3.2-8B-Instruct"

        info = model_info(model_name)
        logger.info(f"  Model: {model_name}")
        logger.info(f"  Model ID: {info.modelId}")
        logger.info(f"  Author: {info.author}")

        # Check model size
        if hasattr(info, 'safetensors'):
            total_size = sum(f.size for f in info.safetensors['files'].values())
            size_gb = total_size / (1024**3)
            logger.info(f"  Model Size: {size_gb:.2f} GB")

        logger.info("  Model is available for download")
        return True

    except Exception as e:
        logger.error(f"  Error checking model: {e}")
        logger.error("  Note: You may need to accept the Llama license on HuggingFace")
        logger.error("  Visit: https://huggingface.co/meta-llama/Llama-3.2-8B-Instruct")
        return False


def test_import():
    """Testa l'import del modulo LlamaSummarizer."""
    logger.info("Testing LlamaSummarizer import...")

    try:
        # Add src to path
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))

        from core.summary_generator import LlamaSummarizer
        logger.info("  LlamaSummarizer imported successfully")
        return True

    except Exception as e:
        logger.error(f"  Import failed: {e}")
        return False


def main():
    """Main test function."""
    logger.info("="*70)
    logger.info("Llama-3.2-8B Setup Verification")
    logger.info("="*70)

    results = {
        "Dependencies": check_dependencies(),
        "GPU": check_gpu(),
        "Model Availability": check_model_availability(),
        "Module Import": test_import(),
    }

    logger.info("="*70)
    logger.info("Test Results:")
    logger.info("="*70)

    all_passed = True
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        logger.info(f"  {symbol} {test_name}: {status}")
        if not result:
            all_passed = False

    logger.info("="*70)

    if all_passed:
        logger.info("All tests passed! Ready to download and use Llama-3.2-8B")
        logger.info("\nNext steps:")
        logger.info("1. Accept Llama license on HuggingFace (if not done)")
        logger.info("2. Set HF_TOKEN environment variable (if needed)")
        logger.info("3. Run: python -m src.core.summary_generator.llama_summarizer")
        logger.info("   This will download the model on first run (~15 GB)")
        return 0
    else:
        logger.error("Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
