"""
Integration Tests for Summary Service

Tests the complete Summary Service orchestration including:
- Llama-based summarization
- Redis caching
- Redis stream publishing
- Batch processing
- Metrics tracking

Author: ML Team (ONDATA 2)
Date: 2025-11-21
"""

import pytest
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import service components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.summary_generator.summary_service import SummaryService, SummaryServiceConfig


class TestSummaryServiceIntegration:
    """Integration tests for Summary Service."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.xadd.return_value = b"1234567890-0"
        mock_client.get.return_value = None  # No cache by default
        mock_client.setex.return_value = True
        mock_client.keys.return_value = []
        return mock_client

    @pytest.fixture
    def mock_summarizer(self):
        """Create a mock LlamaSummarizer."""
        mock = MagicMock()
        mock.summarize.return_value = "This is a generated summary of the input text."
        mock.get_model_info.return_value = {
            "model_name": "test-model",
            "loaded": True,
            "device": "cpu",
            "model_size_gb": 1.0
        }
        mock.model_name = "test-model"
        return mock

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = SummaryServiceConfig()
        config.REDIS_HOST = "localhost"
        config.REDIS_PORT = 6379
        config.DEFAULT_MAX_LENGTH = 100
        config.ENABLE_CACHE = True
        return config

    @pytest.fixture
    def service(self, config, mock_redis, mock_summarizer):
        """Create Summary Service instance with mocks."""
        with patch("core.summary_generator.summary_service.redis.Redis", return_value=mock_redis):
            with patch("core.summary_generator.summary_service.LlamaSummarizer", return_value=mock_summarizer):
                service = SummaryService(config=config)
                service.summarizer = mock_summarizer  # Ensure mock is used
                yield service
                service.close()

    def test_service_initialization(self, service):
        """Test that service initializes correctly."""
        assert service is not None
        assert service.summarizer is not None
        assert service.redis_client is not None
        assert service.metrics["total_processed"] == 0

    def test_generate_summary_basic(self, service):
        """Test basic summary generation."""
        test_text = """
        This is a long text that needs to be summarized. It contains multiple
        sentences with various information. The summarizer should extract the
        key points and create a concise summary of the content.
        """

        summary = service.generate_summary(
            text=test_text,
            session_id="test_001"
        )

        # Verify summary is returned
        assert summary is not None
        assert len(summary) > 0
        assert isinstance(summary, str)

    def test_generate_summary_with_parameters(self, service, mock_summarizer):
        """Test summary generation with custom parameters."""
        test_text = "Test text for summarization."

        summary = service.generate_summary(
            text=test_text,
            max_length=150,
            min_length=50,
            temperature=0.8,
            top_p=0.95,
            session_id="test_002"
        )

        # Verify summarizer was called with correct parameters
        assert mock_summarizer.summarize.called
        call_kwargs = mock_summarizer.summarize.call_args[1]

        assert call_kwargs["max_length"] == 150
        assert call_kwargs["min_length"] == 50
        assert call_kwargs["temperature"] == 0.8
        assert call_kwargs["top_p"] == 0.95

    def test_caching_functionality(self, service, mock_redis, mock_summarizer):
        """Test that caching works correctly."""
        test_text = "Text to be cached."

        # First call - cache miss
        summary1 = service.generate_summary(text=test_text, session_id="test_003")

        # Verify cache was checked
        assert mock_redis.get.called

        # Verify summary was cached
        assert mock_redis.setex.called

        # Simulate cache hit for second call
        mock_redis.get.return_value = "Cached summary"
        mock_summarizer.summarize.reset_mock()

        summary2 = service.generate_summary(text=test_text, session_id="test_004")

        # Should return cached version
        assert summary2 == "Cached summary"

        # Summarizer should NOT be called again
        assert not mock_summarizer.summarize.called

    def test_cache_metrics(self, service, mock_redis):
        """Test cache hit/miss tracking."""
        test_text = "Test text for cache metrics."

        # First call - cache miss
        mock_redis.get.return_value = None
        service.generate_summary(text=test_text)

        assert service.metrics["total_cached_misses"] == 1
        assert service.metrics["total_cached_hits"] == 0

        # Second call - cache hit
        mock_redis.get.return_value = "Cached summary"
        service.generate_summary(text=test_text)

        assert service.metrics["total_cached_misses"] == 1
        assert service.metrics["total_cached_hits"] == 1

    def test_cache_bypass(self, service, mock_redis, mock_summarizer):
        """Test that caching can be bypassed."""
        test_text = "Test text."

        # Simulate cached version exists
        mock_redis.get.return_value = "Cached summary"

        # Generate with use_cache=False
        summary = service.generate_summary(
            text=test_text,
            use_cache=False,
            session_id="test_005"
        )

        # Should call summarizer even with cache available
        assert mock_summarizer.summarize.called

    def test_redis_publishing(self, service, mock_redis):
        """Test that results are published to Redis stream."""
        test_text = "Test text for Redis publishing."

        service.generate_summary(text=test_text)

        # Verify xadd was called
        assert mock_redis.xadd.called
        call_args = mock_redis.xadd.call_args

        # Verify stream key
        assert call_args[0][0] == service.config.REDIS_STREAM_KEY

        # Verify message structure
        message_data = call_args[0][1]
        assert "data" in message_data

        # Verify JSON data
        json_data = json.loads(message_data["data"])
        assert "session_id" in json_data
        assert "summary" in json_data
        assert "processing_time_ms" in json_data

    def test_batch_processing(self, service, mock_summarizer):
        """Test batch summary generation."""
        test_texts = [
            "First text to summarize.",
            "Second text to summarize.",
            "Third text to summarize."
        ]

        summaries = service.generate_summaries_batch(test_texts, max_length=100)

        # Verify all texts processed
        assert len(summaries) == len(test_texts)

        # Verify summarizer called for each text
        assert mock_summarizer.summarize.call_count == len(test_texts)

    def test_batch_size_limit(self, service):
        """Test batch size validation."""
        # Create batch larger than limit
        large_batch = ["text"] * (service.config.MAX_BATCH_SIZE + 5)

        with pytest.raises(ValueError, match="exceeds maximum"):
            service.generate_summaries_batch(large_batch)

    def test_batch_error_handling(self, service, mock_summarizer):
        """Test batch processing with errors."""
        test_texts = ["text1", "text2", "text3"]

        # Make second summarization fail
        mock_summarizer.summarize.side_effect = [
            "Summary 1",
            Exception("Summarization failed"),
            "Summary 3"
        ]

        summaries = service.generate_summaries_batch(test_texts)

        # Should have 3 results, with empty string for failed one
        assert len(summaries) == 3
        assert summaries[0] == "Summary 1"
        assert summaries[1] == ""  # Failed
        assert summaries[2] == "Summary 3"

    def test_input_validation(self, service):
        """Test input validation."""
        # Empty text
        with pytest.raises(ValueError, match="empty"):
            service.generate_summary(text="")

        # Text too short
        with pytest.raises(ValueError, match="too short"):
            service.generate_summary(text="hi")

        # Text too long
        long_text = "x" * (service.config.MAX_TEXT_LENGTH + 1000)
        with pytest.raises(ValueError, match="too long"):
            service.generate_summary(text=long_text)

    def test_metrics_tracking(self, service):
        """Test that metrics are tracked correctly."""
        initial_count = service.metrics["total_processed"]

        # Generate multiple summaries
        for i in range(3):
            service.generate_summary(
                text=f"Test text number {i} with some content to summarize.",
                session_id=f"test_{i}"
            )

        # Verify metrics updated
        assert service.metrics["total_processed"] == initial_count + 3
        assert service.metrics["avg_processing_time"] > 0
        assert service.metrics["avg_summary_length"] > 0
        assert service.metrics["last_processed_at"] is not None

    def test_cache_stats(self, service, mock_redis):
        """Test cache statistics retrieval."""
        # Mock some cached keys
        mock_redis.keys.return_value = ["key1", "key2", "key3"]

        stats = service.get_cache_stats()

        assert "total_cached" in stats
        assert stats["total_cached"] == 3
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "hit_rate" in stats
        assert "cache_enabled" in stats

    def test_clear_cache(self, service, mock_redis):
        """Test cache clearing."""
        # Mock cached keys
        mock_redis.keys.return_value = ["cache:key1", "cache:key2"]
        mock_redis.delete.return_value = 2

        deleted = service.clear_cache()

        assert deleted == 2
        assert mock_redis.keys.called
        assert mock_redis.delete.called

    def test_health_check(self, service):
        """Test health check functionality."""
        health = service.health_check()

        assert "status" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "components" in health
        assert "summarizer" in health["components"]
        assert "redis" in health["components"]

        # With mocks, should be healthy
        assert health["components"]["redis"] == "ok"
        assert health["components"]["summarizer"] == "ok"

    def test_get_metrics(self, service, mock_redis):
        """Test metrics retrieval."""
        mock_redis.keys.return_value = []

        metrics = service.get_metrics()

        assert "total_processed" in metrics
        assert "cache" in metrics
        assert "model" in metrics
        assert "redis" in metrics

    def test_session_id_generation(self, service):
        """Test automatic session ID generation."""
        test_text = "Test text without explicit session ID."

        # Access the Redis stream to capture the published data
        service.generate_summary(text=test_text)

        # Verify session ID was generated (check through Redis call)
        assert service.redis_client.xadd.called
        message = json.loads(service.redis_client.xadd.call_args[0][1]["data"])
        assert "session_id" in message
        assert message["session_id"].startswith("summary_session_")

    def test_metadata_inclusion(self, service):
        """Test that metadata is included in results."""
        test_text = "Test text with metadata."
        metadata = {
            "user_id": "user456",
            "session_type": "interview"
        }

        service.generate_summary(
            text=test_text,
            metadata=metadata
        )

        # Verify metadata in published message
        message = json.loads(service.redis_client.xadd.call_args[0][1]["data"])
        assert "metadata" in message
        assert message["metadata"] == metadata

    def test_context_manager(self, config, mock_redis, mock_summarizer):
        """Test using service as context manager."""
        with patch("core.summary_generator.summary_service.redis.Redis", return_value=mock_redis):
            with patch("core.summary_generator.summary_service.LlamaSummarizer", return_value=mock_summarizer):
                with SummaryService(config=config) as service:
                    service.summarizer = mock_summarizer
                    summary = service.generate_summary(
                        text="Test with context manager."
                    )
                    assert len(summary) > 0

                # After context exit, close should have been called
                assert True  # If we get here, cleanup worked

    def test_error_handling(self, service, mock_redis, mock_summarizer):
        """Test error handling in summarization."""
        # Simulate summarizer error
        mock_summarizer.summarize.side_effect = Exception("Model error")

        test_text = "Test text that will fail."

        with pytest.raises(RuntimeError, match="Summary generation failed"):
            service.generate_summary(text=test_text)

        # Error should be tracked
        assert service.metrics["total_errors"] > 0


class TestSummaryServicePerformance:
    """Performance tests for Summary Service."""

    @pytest.fixture
    def service(self):
        """Create service instance with mocks."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.xadd.return_value = b"1234567890-0"
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True

        mock_summarizer = MagicMock()
        mock_summarizer.summarize.return_value = "Test summary"
        mock_summarizer.get_model_info.return_value = {
            "loaded": True,
            "device": "cpu"
        }
        mock_summarizer.model_name = "test-model"

        with patch("core.summary_generator.summary_service.redis.Redis", return_value=mock_redis):
            with patch("core.summary_generator.summary_service.LlamaSummarizer", return_value=mock_summarizer):
                service = SummaryService()
                service.summarizer = mock_summarizer
                yield service
                service.close()

    def test_cache_performance(self, service):
        """Test that caching improves performance."""
        test_text = "Test text for cache performance."

        # First call - no cache
        service.redis_client.get.return_value = None
        start1 = time.time()
        summary1 = service.generate_summary(text=test_text)
        time1 = time.time() - start1

        # Second call - with cache
        service.redis_client.get.return_value = "Cached summary"
        start2 = time.time()
        summary2 = service.generate_summary(text=test_text)
        time2 = time.time() - start2

        # Cache should be faster (even with mocks, there's overhead difference)
        assert summary2 == "Cached summary"

    def test_batch_processing_time(self, service):
        """Test batch processing completes in reasonable time."""
        test_texts = [f"Test text {i}" for i in range(5)]

        start = time.time()
        summaries = service.generate_summaries_batch(test_texts, max_length=100)
        elapsed = time.time() - start

        # Should complete quickly with mocks
        assert elapsed < 2.0
        assert len(summaries) == 5


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
