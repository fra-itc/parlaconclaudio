"""
NLP Service - Orchestrator for NLP Insights Pipeline

This module orchestrates the complete NLP insights extraction pipeline,
integrating keyword extraction and speaker diarization capabilities.
Publishes results to Redis streams for downstream consumption.

Architecture:
    Input: Transcription text + audio path
    Processing:
        - KeywordExtractor: Extract key terms and phrases
        - SpeakerDiarization: Identify speakers and segments
    Output: Redis stream "nlp:insights" with combined insights

Author: ML Team (ONDATA 2)
Date: 2025-11-21
"""

import logging
import json
import os
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

try:
    import redis
    import redis.asyncio as aioredis
except ImportError as e:
    raise ImportError(
        "Redis client required. Install with: pip install redis[hiredis]"
    ) from e

from .keyword_extractor import KeywordExtractor
from .speaker_diarization import SpeakerDiarization, SpeakerSegment


logger = logging.getLogger(__name__)


class NLPServiceConfig:
    """Configuration for NLP Service."""

    # Redis configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = 0
    REDIS_STREAM_KEY: str = "nlp:insights"
    REDIS_MAX_STREAM_LEN: int = 10000

    # Keyword extraction defaults
    KEYWORD_TOP_N: int = 10
    KEYWORD_USE_MMR: bool = True
    KEYWORD_DIVERSITY: float = 0.6

    # Speaker diarization defaults
    SPEAKER_MIN_SPEAKERS: int = 1
    SPEAKER_MAX_SPEAKERS: int = 10

    # Processing limits
    MAX_TEXT_LENGTH: int = 50000  # Max characters to process
    MIN_TEXT_LENGTH: int = 10

    # Monitoring
    ENABLE_METRICS: bool = True
    LOG_LEVEL: str = "INFO"


class NLPService:
    """
    Orchestrator for NLP insights extraction pipeline.

    Coordinates keyword extraction and speaker diarization, publishes
    results to Redis streams for consumption by downstream services.

    Attributes:
        config: NLPServiceConfig instance
        keyword_extractor: KeywordExtractor instance
        speaker_diarizer: SpeakerDiarization instance (optional)
        redis_client: Redis client for stream publishing
        metrics: Processing metrics and statistics
    """

    def __init__(
        self,
        config: Optional[NLPServiceConfig] = None,
        keyword_model: Optional[str] = None,
        diarization_token: Optional[str] = None,
        enable_diarization: bool = True,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None
    ):
        """
        Initialize NLP Service orchestrator.

        Args:
            config: Configuration object (uses defaults if None)
            keyword_model: Model name for keyword extraction
            diarization_token: HuggingFace token for speaker diarization
            enable_diarization: Enable speaker diarization (requires token)
            redis_host: Redis host override
            redis_port: Redis port override

        Raises:
            ConnectionError: If Redis connection fails
            RuntimeError: If component initialization fails
        """
        self.config = config or NLPServiceConfig()
        self.enable_diarization = enable_diarization

        # Override Redis config if provided
        if redis_host:
            self.config.REDIS_HOST = redis_host
        if redis_port:
            self.config.REDIS_PORT = redis_port

        # Initialize components
        logger.info("Initializing NLP Service...")

        # 1. Keyword Extractor
        logger.info("Loading KeywordExtractor...")
        try:
            self.keyword_extractor = KeywordExtractor(model_name=keyword_model)
            logger.info("KeywordExtractor loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load KeywordExtractor: {e}")
            raise RuntimeError(f"KeywordExtractor initialization failed: {e}") from e

        # 2. Speaker Diarization (optional)
        self.speaker_diarizer: Optional[SpeakerDiarization] = None
        if self.enable_diarization:
            if not diarization_token:
                logger.warning(
                    "Speaker diarization enabled but no token provided. "
                    "Diarization will be disabled. Get token at: "
                    "https://huggingface.co/settings/tokens"
                )
                self.enable_diarization = False
            else:
                logger.info("Loading SpeakerDiarization...")
                try:
                    self.speaker_diarizer = SpeakerDiarization(
                        use_auth_token=diarization_token
                    )
                    logger.info("SpeakerDiarization loaded successfully")
                except Exception as e:
                    logger.error(f"Failed to load SpeakerDiarization: {e}")
                    logger.warning("Continuing without speaker diarization")
                    self.enable_diarization = False
                    self.speaker_diarizer = None
        else:
            logger.info("Speaker diarization disabled")

        # 3. Redis Client
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
            "total_keywords_extracted": 0,
            "total_speakers_identified": 0,
            "total_errors": 0,
            "avg_processing_time": 0.0,
            "last_processed_at": None
        }

        logger.info("NLP Service initialized successfully")

    def process_transcription(
        self,
        text: str,
        audio_path: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process transcription to extract NLP insights.

        This is the main orchestration method that:
        1. Validates input
        2. Extracts keywords from text
        3. Performs speaker diarization (if audio provided)
        4. Combines insights
        5. Publishes to Redis stream

        Args:
            text: Transcribed text to analyze
            audio_path: Path to audio file for speaker diarization (optional)
            session_id: Unique session identifier
            metadata: Additional metadata to include in output

        Returns:
            Dictionary containing:
                - keywords: List of (keyword, score) tuples
                - speakers: List of speaker segments (if diarization enabled)
                - insights: Combined analysis insights
                - metadata: Processing metadata

        Raises:
            ValueError: If input validation fails
            RuntimeError: If processing fails
        """
        start_time = time.time()
        session_id = session_id or self._generate_session_id()

        logger.info(f"Processing transcription for session: {session_id}")

        # Validate input
        self._validate_input(text, audio_path)

        try:
            # 1. Extract keywords
            logger.info("Extracting keywords...")
            keywords = self._extract_keywords(text)
            logger.info(f"Extracted {len(keywords)} keywords")

            # 2. Speaker diarization (if enabled and audio provided)
            speakers = None
            speaker_stats = None
            if self.enable_diarization and audio_path and self.speaker_diarizer:
                logger.info("Performing speaker diarization...")
                speakers = self._diarize_speakers(audio_path)
                speaker_stats = self._compute_speaker_stats(speakers)
                logger.info(f"Identified {len(speaker_stats)} speakers")
            else:
                logger.debug("Skipping speaker diarization")

            # 3. Generate insights
            insights = self._generate_insights(text, keywords, speaker_stats)

            # 4. Build result
            result = {
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "text_length": len(text),
                "keywords": [{"keyword": kw, "score": float(score)} for kw, score in keywords],
                "speakers": speaker_stats,
                "insights": insights,
                "metadata": metadata or {},
                "processing_time_ms": (time.time() - start_time) * 1000
            }

            # 5. Publish to Redis stream
            self._publish_to_redis(result)

            # 6. Update metrics
            self._update_metrics(result, time.time() - start_time)

            logger.info(
                f"Processing complete for session {session_id} "
                f"in {result['processing_time_ms']:.2f}ms"
            )

            return result

        except Exception as e:
            self.metrics["total_errors"] += 1
            logger.error(f"Processing failed for session {session_id}: {e}")
            raise RuntimeError(f"NLP processing failed: {e}") from e

    def _validate_input(self, text: str, audio_path: Optional[str]) -> None:
        """Validate input parameters."""
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

        if audio_path and not Path(audio_path).exists():
            logger.warning(f"Audio file not found: {audio_path}")
            # Don't raise error, just warn - we can still process text

    def _extract_keywords(self, text: str) -> List[tuple]:
        """Extract keywords using KeywordExtractor."""
        return self.keyword_extractor.extract_keywords(
            text,
            top_n=self.config.KEYWORD_TOP_N,
            use_mmr=self.config.KEYWORD_USE_MMR,
            diversity=self.config.KEYWORD_DIVERSITY
        )

    def _diarize_speakers(self, audio_path: str) -> List[SpeakerSegment]:
        """Perform speaker diarization on audio."""
        if not self.speaker_diarizer:
            return []

        return self.speaker_diarizer.diarize(
            audio_path,
            min_speakers=self.config.SPEAKER_MIN_SPEAKERS,
            max_speakers=self.config.SPEAKER_MAX_SPEAKERS
        )

    def _compute_speaker_stats(
        self,
        segments: List[SpeakerSegment]
    ) -> Optional[Dict[str, Dict]]:
        """Compute speaker statistics from segments."""
        if not segments or not self.speaker_diarizer:
            return None

        return self.speaker_diarizer.get_speaker_statistics(segments)

    def _generate_insights(
        self,
        text: str,
        keywords: List[tuple],
        speaker_stats: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate combined insights from analysis results."""
        insights = {
            "num_keywords": len(keywords),
            "top_keywords": [kw for kw, _ in keywords[:5]],
            "text_stats": {
                "char_count": len(text),
                "word_count": len(text.split()),
                "sentence_count": text.count('.') + text.count('!') + text.count('?')
            }
        }

        if speaker_stats:
            insights["speaker_summary"] = {
                "num_speakers": len(speaker_stats),
                "speaker_labels": list(speaker_stats.keys()),
                "dominant_speaker": max(
                    speaker_stats.items(),
                    key=lambda x: x[1]["total_time"]
                )[0] if speaker_stats else None
            }

        return insights

    def _publish_to_redis(self, result: Dict[str, Any]) -> None:
        """Publish results to Redis stream."""
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
            # Don't raise - processing succeeded, just logging failed

    def _update_metrics(self, result: Dict[str, Any], processing_time: float) -> None:
        """Update internal metrics."""
        self.metrics["total_processed"] += 1
        self.metrics["total_keywords_extracted"] += result["insights"]["num_keywords"]

        if result.get("speakers"):
            self.metrics["total_speakers_identified"] += len(result["speakers"])

        # Update average processing time
        n = self.metrics["total_processed"]
        current_avg = self.metrics["avg_processing_time"]
        self.metrics["avg_processing_time"] = (
            (current_avg * (n - 1) + processing_time) / n
        )

        self.metrics["last_processed_at"] = datetime.utcnow().isoformat()

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"nlp_session_{timestamp}_{id(self)}"

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics and statistics.

        Returns:
            Dictionary with service metrics
        """
        return {
            **self.metrics,
            "components": {
                "keyword_extractor": "enabled",
                "speaker_diarization": "enabled" if self.enable_diarization else "disabled"
            },
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

        # Check keyword extractor
        try:
            _ = self.keyword_extractor.get_model_info()
            health["components"]["keyword_extractor"] = "ok"
        except Exception as e:
            health["components"]["keyword_extractor"] = f"error: {e}"
            health["status"] = "degraded"

        # Check speaker diarizer
        if self.enable_diarization and self.speaker_diarizer:
            try:
                _ = self.speaker_diarizer.get_model_info()
                health["components"]["speaker_diarization"] = "ok"
            except Exception as e:
                health["components"]["speaker_diarization"] = f"error: {e}"
                health["status"] = "degraded"
        else:
            health["components"]["speaker_diarization"] = "disabled"

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
        logger.info("Closing NLP Service...")

        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")

        logger.info("NLP Service closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"NLPService("
            f"diarization={'enabled' if self.enable_diarization else 'disabled'}, "
            f"redis={self.config.REDIS_HOST}:{self.config.REDIS_PORT}, "
            f"processed={self.metrics['total_processed']})"
        )


def main():
    """Test function for NLP Service."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("="*70)
    logger.info("NLP Service - Testing")
    logger.info("="*70)

    # Initialize service (without diarization for testing)
    service = NLPService(enable_diarization=False)

    # Print service info
    logger.info(f"\nService: {service}")

    # Health check
    health = service.health_check()
    logger.info("\nHealth Check:")
    logger.info(json.dumps(health, indent=2))

    # Test processing
    test_text = """
    This is a test transcription for the NLP service. We are testing
    keyword extraction and the overall orchestration pipeline. The system
    should identify important terms like machine learning, natural language
    processing, and speaker diarization. This test verifies that the service
    can process text, extract meaningful keywords, and publish results to
    Redis streams for downstream consumption.
    """

    logger.info("\nProcessing test transcription...")
    result = service.process_transcription(
        text=test_text,
        session_id="test_session_001",
        metadata={"test": True, "version": "1.0"}
    )

    logger.info("\nProcessing Result:")
    logger.info(json.dumps(result, indent=2))

    # Get metrics
    metrics = service.get_metrics()
    logger.info("\nService Metrics:")
    logger.info(json.dumps(metrics, indent=2))

    # Cleanup
    service.close()

    logger.info("\n" + "="*70)
    logger.info("Test completed successfully!")


if __name__ == "__main__":
    main()
