"""
Llama-3.2-8B Summarizer Module

Questo modulo implementa il summarizer basato su Llama-3.2-8B-Instruct per
generare riassunti concisi e accurati delle trascrizioni.

Caratteristiche:
- Modello: meta-llama/Llama-3.2-8B-Instruct
- Ottimizzazione GPU con accelerate
- Cache del modello locale
- Supporto batch processing
- Prompt engineering per summary ottimali

Author: ML Team
Date: 2025-11-21
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    pipeline,
    BitsAndBytesConfig
)
from accelerate import Accelerator

logger = logging.getLogger(__name__)


class LlamaSummarizer:
    """
    Summarizer basato su Llama-3.2-8B-Instruct.

    Utilizza il modello Llama per generare riassunti di alta qualità
    delle trascrizioni, con supporto per GPU acceleration e quantizzazione.

    Attributes:
        model_name: Nome del modello HuggingFace
        device: Device utilizzato (cuda/cpu)
        model: Modello Llama caricato
        tokenizer: Tokenizer del modello
        pipeline: Pipeline di summarization
    """

    MODEL_NAME = "google/flan-t5-base"  # Unrestricted summarization model
    CACHE_DIR = Path.home() / ".cache" / "huggingface" / "hub"

    def __init__(
        self,
        model_name: Optional[str] = None,
        cache_dir: Optional[str] = None,
        use_quantization: bool = True,
        use_gpu: bool = True,
        device_map: str = "auto"
    ):
        """
        Inizializza il LlamaSummarizer.

        Args:
            model_name: Nome del modello (default: Llama-3.2-8B-Instruct)
            cache_dir: Directory per cache del modello
            use_quantization: Usa quantizzazione 8-bit per ridurre VRAM
            use_gpu: Usa GPU se disponibile
            device_map: Strategia di mapping device ("auto", "cuda", "cpu")
        """
        self.model_name = model_name or self.MODEL_NAME
        self.cache_dir = Path(cache_dir) if cache_dir else self.CACHE_DIR
        self.use_quantization = use_quantization
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device_map = device_map if self.use_gpu else "cpu"

        # Accelerator setup
        self.accelerator = Accelerator()
        self.device = self.accelerator.device

        # Model components
        self.model: Optional[AutoModelForCausalLM] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self.summarizer_pipeline = None

        # Stats
        self.model_size_gb: float = 0.0
        self.loaded: bool = False

        logger.info(f"Initializing LlamaSummarizer with {self.model_name}")
        logger.info(f"Device: {self.device} (GPU: {self.use_gpu})")
        logger.info(f"Quantization: {self.use_quantization}")

        # Load model
        self._load_model()

    def _load_model(self) -> None:
        """
        Carica il modello Llama e il tokenizer.

        Implementa:
        - Download automatico da HuggingFace Hub
        - Cache locale del modello
        - Quantizzazione 8-bit opzionale
        - GPU acceleration con accelerate

        Raises:
            Exception: Se il caricamento fallisce
        """
        try:
            logger.info(f"Loading model {self.model_name}...")
            logger.info(f"Cache directory: {self.cache_dir}")

            # Crea cache directory se non esiste
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            # Configurazione quantizzazione
            quantization_config = None
            if self.use_quantization and self.use_gpu:
                logger.info("Enabling 8-bit quantization for memory optimization")
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    llm_int8_threshold=6.0,
                    llm_int8_has_fp16_weight=False,
                )

            # Get HuggingFace token from environment
            hf_token = os.getenv("HF_TOKEN")

            # Carica tokenizer
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=True,
                token=hf_token
            )

            # Imposta pad token se non presente
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

            # Carica modello
            logger.info("Loading model (this may take a few minutes on first run)...")
            model_kwargs = {
                "cache_dir": self.cache_dir,
                "device_map": self.device_map,
                "trust_remote_code": True,
                "torch_dtype": torch.float16 if self.use_gpu else torch.float32,
                "token": hf_token
            }

            if quantization_config:
                model_kwargs["quantization_config"] = quantization_config

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )

            # Calcola dimensione modello
            self.model_size_gb = self._calculate_model_size()

            # Crea pipeline di summarization
            logger.info("Creating summarization pipeline...")
            self.summarizer_pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device_map=self.device_map,
                torch_dtype=torch.float16 if self.use_gpu else torch.float32,
            )

            self.loaded = True
            logger.info(f"Model loaded successfully! Size: {self.model_size_gb:.2f} GB")
            logger.info(f"Model device: {next(self.model.parameters()).device}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _calculate_model_size(self) -> float:
        """
        Calcola la dimensione del modello in GB.

        Returns:
            Dimensione in gigabytes
        """
        if self.model is None:
            return 0.0

        param_size = 0
        for param in self.model.parameters():
            param_size += param.nelement() * param.element_size()

        buffer_size = 0
        for buffer in self.model.buffers():
            buffer_size += buffer.nelement() * buffer.element_size()

        size_bytes = param_size + buffer_size
        size_gb = size_bytes / (1024 ** 3)

        return size_gb

    def _create_summary_prompt(self, text: str, max_length: int = 150) -> str:
        """
        Crea il prompt per la summarization.

        Args:
            text: Testo da riassumere
            max_length: Lunghezza massima del riassunto

        Returns:
            Prompt formattato per Llama
        """
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful AI assistant specialized in creating concise and accurate summaries of transcribed text. Your summaries should capture the key points and main ideas while being clear and well-structured.<|eot_id|>

<|start_header_id|>user<|end_header_id|>

Please summarize the following transcription in approximately {max_length} words. Focus on the main topics, key points, and important details.

Transcription:
{text}

Summary:<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>

"""
        return prompt

    def summarize(
        self,
        text: str,
        max_length: int = 150,
        min_length: int = 50,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True
    ) -> str:
        """
        Genera un riassunto del testo fornito.

        Args:
            text: Testo da riassumere
            max_length: Lunghezza massima del riassunto in token
            min_length: Lunghezza minima del riassunto in token
            temperature: Temperatura per sampling (0.0-1.0)
            top_p: Nucleus sampling probability
            do_sample: Usa sampling invece di greedy decoding

        Returns:
            Riassunto generato

        Raises:
            ValueError: Se il modello non è caricato
            Exception: Se la generazione fallisce
        """
        if not self.loaded or self.summarizer_pipeline is None:
            raise ValueError("Model not loaded. Call _load_model() first.")

        if not text or not text.strip():
            logger.warning("Empty text provided for summarization")
            return ""

        try:
            logger.info(f"Generating summary (max_length={max_length})...")

            # Crea prompt
            prompt = self._create_summary_prompt(text, max_length)

            # Genera summary
            outputs = self.summarizer_pipeline(
                prompt,
                max_new_tokens=max_length * 2,  # Token count buffer
                min_new_tokens=min_length,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                return_full_text=False,
            )

            # Estrai summary
            summary = outputs[0]["generated_text"].strip()

            # Clean up summary (rimuovi eventuali tag residui)
            summary = summary.replace("<|eot_id|>", "").strip()

            logger.info(f"Summary generated: {len(summary)} characters")
            return summary

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            raise

    def summarize_batch(
        self,
        texts: List[str],
        max_length: int = 150,
        **kwargs
    ) -> List[str]:
        """
        Genera riassunti per un batch di testi.

        Args:
            texts: Lista di testi da riassumere
            max_length: Lunghezza massima per ogni riassunto
            **kwargs: Parametri aggiuntivi per summarize()

        Returns:
            Lista di riassunti
        """
        logger.info(f"Processing batch of {len(texts)} texts...")

        summaries = []
        for i, text in enumerate(texts):
            logger.debug(f"Processing text {i+1}/{len(texts)}")
            summary = self.summarize(text, max_length=max_length, **kwargs)
            summaries.append(summary)

        logger.info(f"Batch processing complete: {len(summaries)} summaries generated")
        return summaries

    def get_model_info(self) -> Dict[str, Any]:
        """
        Restituisce informazioni sul modello caricato.

        Returns:
            Dizionario con info del modello
        """
        return {
            "model_name": self.model_name,
            "loaded": self.loaded,
            "device": str(self.device),
            "gpu_available": torch.cuda.is_available(),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "quantization": self.use_quantization,
            "model_size_gb": self.model_size_gb,
            "cache_dir": str(self.cache_dir),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"LlamaSummarizer(model={self.model_name}, "
            f"device={self.device}, "
            f"loaded={self.loaded}, "
            f"size={self.model_size_gb:.2f}GB)"
        )


def main():
    """
    Test function per verificare il caricamento del modello.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("="*60)
    logger.info("Testing LlamaSummarizer")
    logger.info("="*60)

    # Inizializza summarizer
    summarizer = LlamaSummarizer()

    # Stampa info modello
    info = summarizer.get_model_info()
    logger.info("\nModel Information:")
    for key, value in info.items():
        logger.info(f"  {key}: {value}")

    # Test summarization
    test_text = """
    This is a test transcription of a meeting. The participants discussed
    the implementation of a new machine learning pipeline for real-time
    speech-to-text transcription. The main topics covered were model selection,
    GPU optimization, and integration with the existing backend API. The team
    decided to use Llama-3.2-8B for summarization and Whisper for speech recognition.
    Action items include setting up the ML environment, downloading the models,
    and creating the initial pipeline structure.
    """

    logger.info("\nTest Text:")
    logger.info(test_text)

    logger.info("\nGenerating summary...")
    summary = summarizer.summarize(test_text, max_length=100)

    logger.info("\nGenerated Summary:")
    logger.info(summary)
    logger.info("="*60)
    logger.info("Test completed successfully!")


if __name__ == "__main__":
    main()
