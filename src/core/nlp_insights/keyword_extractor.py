"""
KeywordExtractor for extracting keywords from transcribed text using KeyBERT.

This module provides functionality to extract meaningful keywords from text
using KeyBERT with sentence-transformers embeddings.
"""

import logging
from typing import List, Tuple, Optional
from pathlib import Path

try:
    from keybert import KeyBERT
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    raise ImportError(
        "KeyBERT and sentence-transformers are required. "
        "Install with: pip install keybert sentence-transformers"
    ) from e


logger = logging.getLogger(__name__)


class KeywordExtractor:
    """
    Extract keywords from text using KeyBERT and sentence-transformers.

    This class uses pre-trained language models to identify the most relevant
    keywords in a given text, with configurable parameters for extraction.

    Attributes:
        model_name (str): Name of the sentence-transformer model to use
        model (KeyBERT): Initialized KeyBERT model instance
    """

    DEFAULT_MODEL = "all-MiniLM-L6-v2"  # Fast and efficient model

    def __init__(
        self,
        model_name: Optional[str] = None,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the KeywordExtractor with a sentence-transformer model.

        Args:
            model_name: Name of the sentence-transformer model to use.
                       Defaults to "all-MiniLM-L6-v2"
            cache_dir: Directory to cache downloaded models. If None, uses default.

        Raises:
            RuntimeError: If model loading fails
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.cache_dir = cache_dir

        logger.info(f"Initializing KeywordExtractor with model: {self.model_name}")

        try:
            # Download and load sentence-transformer model
            if cache_dir:
                sentence_model = SentenceTransformer(
                    self.model_name,
                    cache_folder=cache_dir
                )
            else:
                sentence_model = SentenceTransformer(self.model_name)

            # Initialize KeyBERT with the sentence-transformer
            self.model = KeyBERT(model=sentence_model)

            logger.info(f"Successfully loaded model: {self.model_name}")

        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            raise RuntimeError(f"Model initialization failed: {e}") from e

    def extract_keywords(
        self,
        text: str,
        top_n: int = 10,
        keyphrase_ngram_range: Tuple[int, int] = (1, 2),
        stop_words: str = "english",
        use_maxsum: bool = False,
        use_mmr: bool = True,
        diversity: float = 0.5,
        min_score: float = 0.0
    ) -> List[Tuple[str, float]]:
        """
        Extract keywords from the given text.

        Args:
            text: Input text to extract keywords from
            top_n: Number of top keywords to extract (default: 10)
            keyphrase_ngram_range: Range of n-grams for keyphrases (default: (1, 2))
            stop_words: Language for stop words removal (default: "english")
            use_maxsum: Use Max Sum Similarity for diversification (default: False)
            use_mmr: Use Maximal Marginal Relevance for diversification (default: True)
            diversity: Diversity parameter for MMR (0-1, default: 0.5)
            min_score: Minimum score threshold for keywords (default: 0.0)

        Returns:
            List of tuples containing (keyword, score) pairs, sorted by score descending

        Raises:
            ValueError: If text is empty or invalid parameters

        Example:
            >>> extractor = KeywordExtractor()
            >>> text = "Machine learning is a subset of artificial intelligence..."
            >>> keywords = extractor.extract_keywords(text, top_n=5)
            >>> for keyword, score in keywords:
            ...     print(f"{keyword}: {score:.3f}")
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for keyword extraction")
            return []

        if top_n <= 0:
            raise ValueError("top_n must be greater than 0")

        if diversity < 0 or diversity > 1:
            raise ValueError("diversity must be between 0 and 1")

        try:
            logger.debug(f"Extracting {top_n} keywords from text of length {len(text)}")

            # Extract keywords using KeyBERT
            keywords = self.model.extract_keywords(
                text,
                keyphrase_ngram_range=keyphrase_ngram_range,
                stop_words=stop_words,
                top_n=top_n,
                use_maxsum=use_maxsum,
                use_mmr=use_mmr,
                diversity=diversity
            )

            # Filter by minimum score if specified
            if min_score > 0:
                keywords = [(kw, score) for kw, score in keywords if score >= min_score]

            logger.info(f"Extracted {len(keywords)} keywords")

            return keywords

        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            raise RuntimeError(f"Failed to extract keywords: {e}") from e

    def extract_keywords_batch(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[Tuple[str, float]]]:
        """
        Extract keywords from multiple texts in batch.

        Args:
            texts: List of input texts
            **kwargs: Additional arguments passed to extract_keywords()

        Returns:
            List of keyword lists, one for each input text

        Example:
            >>> extractor = KeywordExtractor()
            >>> texts = ["First document...", "Second document..."]
            >>> batch_results = extractor.extract_keywords_batch(texts, top_n=5)
        """
        if not texts:
            logger.warning("Empty text list provided for batch extraction")
            return []

        logger.info(f"Processing batch of {len(texts)} texts")

        results = []
        for i, text in enumerate(texts):
            try:
                keywords = self.extract_keywords(text, **kwargs)
                results.append(keywords)
            except Exception as e:
                logger.error(f"Failed to process text {i}: {e}")
                results.append([])  # Add empty result for failed text

        return results

    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "cache_dir": self.cache_dir,
            "model_type": "KeyBERT with SentenceTransformer"
        }


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)

    # Initialize extractor
    print("Initializing KeywordExtractor...")
    extractor = KeywordExtractor()

    # Test text
    test_text = """
    Real-time speech-to-text transcription is becoming increasingly important in
    modern applications. Machine learning models, particularly those based on
    transformer architectures, have revolutionized natural language processing.
    These models can perform tasks like keyword extraction, speaker diarization,
    and sentiment analysis with high accuracy. The integration of such NLP
    capabilities enables powerful insights from audio and text data.
    """

    # Extract keywords
    print("\nExtracting keywords...")
    keywords = extractor.extract_keywords(
        test_text,
        top_n=8,
        use_mmr=True,
        diversity=0.6
    )

    print("\nExtracted Keywords:")
    for keyword, score in keywords:
        print(f"  {keyword:30s} {score:.4f}")

    # Model info
    print("\nModel Information:")
    info = extractor.get_model_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
