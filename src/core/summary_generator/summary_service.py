"""
Summary Service - Orchestrator for Text Summarization Pipeline

This module orchestrates the text summarization pipeline using Llama-3.2-8B-Instruct.
Provides caching, batch processing, and Redis stream integration for efficient
summary generation at scale.

Architecture:
    Input: Transcription text
    Processing:
        - LlamaSummarizer: Generate abstractive summary
        - Cache: Store results for frequently requested texts
    Output: Redis stream "summary:output" with generated summaries

Author: ML Team (ONDATA 2)
Date: 2025-11-21
"""

import logging
import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta

try:
    import redis
    import redis.asyncio as aioredis
except ImportError as e:
    raise ImportError(
        "Redis client required. Install with: pip install redis[hiredis]"
    ) from e

from .llama_summarizer import LlamaSummarizer


logger = logging.getLogger(__name__)


class SummaryServiceConfig:
    """Configuration for Summary Service."""

    # Redis configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_STREAM_KEY: str = "summary:output"
    REDIS_CACHE_PREFIX: str = "summary:cache:"
    REDIS_MAX_STREAM_LEN: int = 10000

    # Summarization defaults
    DEFAULT_MAX_LENGTH: int = 150
    DEFAULT_MIN_LENGTH: int = 50
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_TOP_P: float = 0.9

    # Processing limits
    MAX_TEXT_LENGTH: int = 100000  # Max characters to summarize
    MIN_TEXT_LENGTH: int = 50
    MAX_BATCH_SIZE: int = 10

    # Caching
    ENABLE_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 3600 * 24  # 24 hours
    CACHE_KEY_LENGTH: int = 32

    # Monitoring
    ENABLE_METRICS: bool = True
    LOG_LEVEL: str = "INFO"


class SummaryService:
    """
    Orchestrator for text summarization pipeline.

    Coordinates Llama-based summarization with intelligent caching
    and batch processing capabilities. Publishes results to Redis
    streams for consumption by downstream services.

    Attributes:
        config: SummaryServiceConfig instance
        summarizer: LlamaSummarizer instance
        redis_client: Redis client for caching and streaming
        metrics: Processing metrics and statistics
    """

    def __init__(
        self,
        config: Optional[SummaryServiceConfig] = None,
        model_name: Optional[str] = None,
        use_quantization: bool = True,
        use_gpu: bool = True,
        enable_cache: Optional[bool] = None,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None
    ):
        """
        Initialize Summary Service orchestrator.

        Args:
            config: Configuration object (uses defaults if None)
            model_name: Llama model name (default: Llama-3.2-8B-Instruct)
            use_quantization: Enable 8-bit quantization for memory efficiency
            use_gpu: Use GPU if available
            enable_cache: Enable Redis caching (overrides config)
            redis_host: Redis host override
            redis_port: Redis port override

        Raises:
            ConnectionError: If Redis connection fails
            RuntimeError: If component initialization fails
        """
        self.config = config or SummaryServiceConfig()

        # Override config if provided
        if enable_cache is not None:
            self.config.ENABLE_CACHE = enable_cache
        if redis_host:
            self.config.REDIS_HOST = redis_host
        if redis_port:
            self.config.REDIS_PORT = redis_port

        # Initialize components
        logger.info("Initializing Summary Service...")

        # 1. Llama Summarizer
        logger.info("Loading LlamaSummarizer (this may take a few minutes)...")
        try:
            self.summarizer = LlamaSummarizer(
                model_name=model_name,
                use_quantization=use_quantization,
                use_gpu=use_gpu
            )
            logger.info("LlamaSummarizer loaded successfully")

            # Log model info
            model_info = self.summarizer.get_model_info()
            logger.info(f"Model: {model_info['model_name']}")
            logger.info(f"Device: {model_info['device']}")
            logger.info(f"Size: {model_info['model_size_gb']:.2f} GB")

        except Exception as e:
            logger.error(f"Failed to load LlamaSummarizer: {e}")
            raise RuntimeError(f"LlamaSummarizer initialization failed: {e}") from e

        # 2. Redis Client
        logger.info(f"Connecting to Redis at {self.config.REDIS_HOST}:{self.config.REDIS_PORT}...")
        try:
            self.redis_client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                db=self.config.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise ConnectionError(f"Failed to connect to Redis: {e}") from e

        # Metrics tracking
        self.metrics = {
            "total_processed": 0,
            "total_cached_hits": 0,
            "total_cached_misses": 0,
            "total_errors": 0,
            "avg_processing_time": 0.0,
            "avg_summary_length": 0,
            "last_processed_at": None
        }

        logger.info("Summary Service initialized successfully")

    def generate_summary(
        self,
        text: str,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> str:
        """
        Generate a summary of the provided text.

        This is the main orchestration method that:
        1. Validates input
        2. Checks cache (if enabled)
        3. Generates summary using Llama
        4. Caches result
        5. Publishes to Redis stream
        6. Returns summary text

        Args:
            text: Text to summarize
            max_length: Maximum summary length in words
            min_length: Minimum summary length in words
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling probability
            session_id: Unique session identifier
            metadata: Additional metadata to include in output
            use_cache: Use cached results if available

        Returns:
            Generated summary text

        Raises:
            ValueError: If input validation fails
            RuntimeError: If summarization fails
        """
        start_time = time.time()
        session_id = session_id or self._generate_session_id()

        # Use config defaults if not provided
        max_length = max_length or self.config.DEFAULT_MAX_LENGTH
        min_length = min_length or self.config.DEFAULT_MIN_LENGTH
        temperature = temperature if temperature is not None else self.config.DEFAULT_TEMPERATURE
        top_p = top_p if top_p is not None else self.config.DEFAULT_TOP_P

        logger.info(f"Generating summary for session: {session_id}")

        # Validate input
        self._validate_input(text)

        try:
            # Check cache
            cache_key = None
            if self.config.ENABLE_CACHE and use_cache:
                cache_key = self._generate_cache_key(text, max_length, temperature)
                cached_summary = self._get_cached_summary(cache_key)

                if cached_summary:
                    logger.info(f"Cache HIT for session {session_id}")
                    self.metrics["total_cached_hits"] += 1

                    # Still publish to stream and update metrics
                    result = self._build_result(
                        session_id=session_id,
                        text=text,
                        summary=cached_summary,
                        processing_time=time.time() - start_time,
                        cached=True,
                        metadata=metadata
                    )
                    self._publish_to_redis(result)
                    self._update_metrics(result, time.time() - start_time)

                    return cached_summary

                logger.debug(f"Cache MISS for session {session_id}")
                self.metrics["total_cached_misses"] += 1

            # Generate summary
            logger.info("Generating summary with Llama...")
            summary = self.summarizer.summarize(
                text=text,
                max_length=max_length,
                min_length=min_length,
                temperature=temperature,
                top_p=top_p
            )

            # Cache result
            if self.config.ENABLE_CACHE and cache_key:
                self._cache_summary(cache_key, summary)

            # Build result
            result = self._build_result(
                session_id=session_id,
                text=text,
                summary=summary,
                processing_time=time.time() - start_time,
                cached=False,
                metadata=metadata,
                params={
                    "max_length": max_length,
                    "min_length": min_length,
                    "temperature": temperature,
                    "top_p": top_p
                }
            )

            # Publish to Redis stream
            self._publish_to_redis(result)

            # Update metrics
            self._update_metrics(result, time.time() - start_time)

            logger.info(
                f"Summary generated for session {session_id} "
                f"in {result['processing_time_ms']:.2f}ms"
            )

            return summary

        except Exception as e:
            self.metrics["total_errors"] += 1
            logger.error(f"Summarization failed for session {session_id}: {e}")
            raise RuntimeError(f"Summary generation failed: {e}") from e

    def generate_summaries_batch(
        self,
        texts: List[str],
        max_length: Optional[int] = None,
        **kwargs
    ) -> List[str]:
        """
        Generate summaries for multiple texts in batch.

        Provides efficient batch processing with progress tracking.

        Args:
            texts: List of texts to summarize
            max_length: Maximum summary length for all texts
            **kwargs: Additional arguments passed to generate_summary()

        Returns:
            List of generated summaries

        Raises:
            ValueError: If batch size exceeds limit
        """
        if not texts:
            logger.warning("Empty text list provided for batch summarization")
            return []

        if len(texts) > self.config.MAX_BATCH_SIZE:
            raise ValueError(
                f"Batch size {len(texts)} exceeds maximum {self.config.MAX_BATCH_SIZE}"
            )

        logger.info(f"Processing batch of {len(texts)} texts...")

        summaries = []
        for i, text in enumerate(texts):
            try:
                logger.info(f"Processing text {i+1}/{len(texts)}")
                summary = self.generate_summary(
                    text=text,
                    max_length=max_length,
                    session_id=f"batch_{i}",
                    **kwargs
                )
                summaries.append(summary)

            except Exception as e:
                logger.error(f"Failed to process text {i}: {e}")
                summaries.append("")  # Add empty summary for failed text

        logger.info(f"Batch processing complete: {len(summaries)}/{len(texts)} successful")
        return summaries

    def _validate_input(self, text: str) -> None:
        """Validate input text."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if len(text) < self.config.MIN_TEXT_LENGTH:
            raise ValueError(
                f"Text too short (min {self.config.MIN_TEXT_LENGTH} chars)"
            )

        if len(text) > self.config.MAX_TEXT_LENGTH:
            raise ValueError(
                f"Text too long (max {self.config.MAX_TEXT_LENGTH} chars)"
            )

    def _generate_cache_key(
        self,
        text: str,
        max_length: int,
        temperature: float
    ) -> str:
        """
        Generate cache key from text and parameters.

        Uses SHA-256 hash of text combined with parameters.
        """
        # Create hash input
        hash_input = f"{text}|{max_length}|{temperature:.2f}"

        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(hash_input.encode('utf-8'))
        cache_key = hash_obj.hexdigest()[:self.config.CACHE_KEY_LENGTH]

        return f"{self.config.REDIS_CACHE_PREFIX}{cache_key}"

    def _get_cached_summary(self, cache_key: str) -> Optional[str]:
        """Retrieve cached summary from Redis."""
        try:
            cached = self.redis_client.get(cache_key)
            return cached if cached else None
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
            return None

    def _cache_summary(self, cache_key: str, summary: str) -> None:
        """Store summary in Redis cache with TTL."""
        try:
            self.redis_client.setex(
                cache_key,
                self.config.CACHE_TTL_SECONDS,
                summary
            )
            logger.debug(f"Summary cached with key: {cache_key}")
        except Exception as e:
            logger.error(f"Cache storage failed: {e}")
            # Don't raise - caching is optional

    def _build_result(
        self,
        session_id: str,
        text: str,
        summary: str,
        processing_time: float,
        cached: bool,
        metadata: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build result dictionary."""
        return {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "text_length": len(text),
            "summary_length": len(summary),
            "summary": summary,
            "cached": cached,
            "parameters": params or {},
            "metadata": metadata or {},
            "processing_time_ms": processing_time * 1000
        }

    def _publish_to_redis(self, result: Dict[str, Any]) -> None:
        """Publish result to Redis stream."""
        try:
            # Serialize result to JSON
            message_data = {
                "data": json.dumps(result)
            }

            # Add to stream with MAXLEN for memory management
            stream_id = self.redis_client.xadd(
                self.config.REDIS_STREAM_KEY,
                message_data,
                maxlen=self.config.REDIS_MAX_STREAM_LEN,
                approximate=True
            )

            logger.debug(f"Published to Redis stream: {stream_id}")

        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")
            # Don't raise - processing succeeded, just publishing failed

    def _update_metrics(self, result: Dict[str, Any], processing_time: float) -> None:
        """Update internal metrics."""
        self.metrics["total_processed"] += 1

        # Update average processing time
        n = self.metrics["total_processed"]
        current_avg = self.metrics["avg_processing_time"]
        self.metrics["avg_processing_time"] = (
            (current_avg * (n - 1) + processing_time) / n
        )

        # Update average summary length
        current_avg_len = self.metrics["avg_summary_length"]
        self.metrics["avg_summary_length"] = (
            (current_avg_len * (n - 1) + result["summary_length"]) / n
        )

        self.metrics["last_processed_at"] = datetime.utcnow().isoformat()

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"summary_session_{timestamp}_{id(self)}"

    def clear_cache(self, pattern: Optional[str] = None) -> int:
        """
        Clear cached summaries.

        Args:
            pattern: Optional pattern to match cache keys (e.g., "summary:cache:*")
                    If None, clears all summary caches

        Returns:
            Number of keys deleted
        """
        pattern = pattern or f"{self.config.REDIS_CACHE_PREFIX}*"

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} cached summaries")
                return deleted
            else:
                logger.info("No cached summaries to clear")
                return 0
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        try:
            pattern = f"{self.config.REDIS_CACHE_PREFIX}*"
            keys = self.redis_client.keys(pattern)

            return {
                "total_cached": len(keys),
                "cache_hits": self.metrics["total_cached_hits"],
                "cache_misses": self.metrics["total_cached_misses"],
                "hit_rate": (
                    self.metrics["total_cached_hits"] /
                    (self.metrics["total_cached_hits"] + self.metrics["total_cached_misses"])
                    if (self.metrics["total_cached_hits"] + self.metrics["total_cached_misses"]) > 0
                    else 0.0
                ),
                "cache_enabled": self.config.ENABLE_CACHE,
                "ttl_seconds": self.config.CACHE_TTL_SECONDS
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics and statistics.

        Returns:
            Dictionary with service metrics
        """
        cache_stats = self.get_cache_stats()

        return {
            **self.metrics,
            "cache": cache_stats,
            "model": self.summarizer.get_model_info(),
            "redis": {
                "host": self.config.REDIS_HOST,
                "port": self.config.REDIS_PORT,
                "stream_key": self.config.REDIS_STREAM_KEY
            }
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all components.

        Returns:
            Dictionary with health status
        """
        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }

        # Check summarizer
        try:
            model_info = self.summarizer.get_model_info()
            if model_info["loaded"]:
                health["components"]["summarizer"] = "ok"
            else:
                health["components"]["summarizer"] = "not loaded"
                health["status"] = "degraded"
        except Exception as e:
            health["components"]["summarizer"] = f"error: {e}"
            health["status"] = "unhealthy"

        # Check Redis
        try:
            self.redis_client.ping()
            health["components"]["redis"] = "ok"
        except Exception as e:
            health["components"]["redis"] = f"error: {e}"
            health["status"] = "unhealthy"

        return health

    def close(self) -> None:
        """Close connections and cleanup resources."""
        logger.info("Closing Summary Service...")

        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")

        logger.info("Summary Service closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"SummaryService("
            f"model={self.summarizer.model_name}, "
            f"cache={'enabled' if self.config.ENABLE_CACHE else 'disabled'}, "
            f"redis={self.config.REDIS_HOST}:{self.config.REDIS_PORT}, "
            f"processed={self.metrics['total_processed']})"
        )


def main():
    """Test function for Summary Service."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("="*70)
    logger.info("Summary Service - Testing")
    logger.info("="*70)

    # Initialize service
    service = SummaryService()

    # Print service info
    logger.info(f"\nService: {service}")

    # Health check
    health = service.health_check()
    logger.info("\nHealth Check:")
    logger.info(json.dumps(health, indent=2))

    # Test summarization
    test_text = """
    This is a comprehensive test transcription for the Summary Service. The meeting
    covered multiple important topics including the implementation of a new machine
    learning pipeline for real-time speech-to-text transcription. The team discussed
    various technical approaches, including the use of Whisper for speech recognition,
    Llama-3.2-8B for text summarization, and KeyBERT for keyword extraction. The
    architecture includes multiple microservices that communicate via Redis streams,
    enabling scalable and efficient processing. Performance optimization was a key
    concern, with discussions about GPU utilization, model quantization, and caching
    strategies. The team also addressed deployment considerations, including Docker
    containerization and Kubernetes orchestration. Action items were assigned to
    various team members, with deadlines set for the next sprint. The meeting
    concluded with a review of the project timeline and upcoming milestones.
    """

    logger.info("\nGenerating summary...")
    summary = service.generate_summary(
        text=test_text,
        max_length=100,
        session_id="test_session_001",
        metadata={"test": True, "version": "1.0"}
    )

    logger.info("\nGenerated Summary:")
    logger.info(summary)

    # Test cache
    logger.info("\nTesting cache (should be HIT)...")
    summary2 = service.generate_summary(
        text=test_text,
        max_length=100,
        session_id="test_session_002"
    )

    # Get metrics
    metrics = service.get_metrics()
    logger.info("\nService Metrics:")
    logger.info(json.dumps(metrics, indent=2, default=str))

    # Cleanup
    service.close()

    logger.info("\n" + "="*70)
    logger.info("Test completed successfully!")


if __name__ == "__main__":
    main()
