"""
Integration Tests for NLP Service

Tests the complete NLP Service orchestration including:
- Keyword extraction
- Speaker diarization (mocked)
- Redis stream publishing
- Metrics tracking
- Health checks

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

from core.nlp_insights.nlp_service import NLPService, NLPServiceConfig
from core.nlp_insights.speaker_diarization import SpeakerSegment


class TestNLPServiceIntegration:
    """Integration tests for NLP Service."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.xadd.return_value = b"1234567890-0"
        return mock_client

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = NLPServiceConfig()
        config.REDIS_HOST = "localhost"
        config.REDIS_PORT = 6379
        config.KEYWORD_TOP_N = 5
        return config

    @pytest.fixture
    def service(self, config, mock_redis):
        """Create NLP Service instance with mocked Redis."""
        with patch("core.nlp_insights.nlp_service.redis.Redis", return_value=mock_redis):
            service = NLPService(
                config=config,
                enable_diarization=False  # Disable for faster tests
            )
            yield service
            service.close()

    def test_service_initialization(self, service):
        """Test that service initializes correctly."""
        assert service is not None
        assert service.keyword_extractor is not None
        assert service.redis_client is not None
        assert service.metrics["total_processed"] == 0

    def test_process_transcription_basic(self, service):
        """Test basic transcription processing."""
        test_text = """
        Machine learning and artificial intelligence are transforming
        the way we process natural language. Speech recognition systems
        use deep learning models to transcribe audio in real-time.
        """

        result = service.process_transcription(
            text=test_text,
            session_id="test_001"
        )

        # Verify result structure
        assert "session_id" in result
        assert result["session_id"] == "test_001"
        assert "keywords" in result
        assert "insights" in result
        assert "processing_time_ms" in result

        # Verify keywords were extracted
        assert len(result["keywords"]) > 0
        assert all("keyword" in kw and "score" in kw for kw in result["keywords"])

        # Verify insights
        assert result["insights"]["num_keywords"] == len(result["keywords"])
        assert "text_stats" in result["insights"]

    def test_process_transcription_with_metadata(self, service):
        """Test processing with metadata."""
        test_text = "This is a test transcription with custom metadata."

        metadata = {
            "user_id": "user123",
            "session_type": "meeting",
            "duration": 300
        }

        result = service.process_transcription(
            text=test_text,
            session_id="test_002",
            metadata=metadata
        )

        # Verify metadata is included
        assert "metadata" in result
        assert result["metadata"] == metadata

    def test_keyword_extraction(self, service):
        """Test keyword extraction specifically."""
        test_text = """
        Natural language processing and machine learning are key technologies
        in modern artificial intelligence systems. Deep learning models can
        extract meaningful insights from text data.
        """

        result = service.process_transcription(text=test_text)

        keywords = result["keywords"]

        # Should have extracted keywords
        assert len(keywords) > 0
        assert len(keywords) <= service.config.KEYWORD_TOP_N

        # All keywords should have scores
        for kw_data in keywords:
            assert "keyword" in kw_data
            assert "score" in kw_data
            assert 0 <= kw_data["score"] <= 1

        # Keywords should be sorted by score (descending)
        scores = [kw["score"] for kw in keywords]
        assert scores == sorted(scores, reverse=True)

    def test_redis_publishing(self, service, mock_redis):
        """Test that results are published to Redis stream."""
        test_text = "Test text for Redis publishing."

        result = service.process_transcription(text=test_text)

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
        assert "keywords" in json_data

    def test_metrics_tracking(self, service):
        """Test that metrics are tracked correctly."""
        initial_count = service.metrics["total_processed"]

        # Process multiple transcriptions
        for i in range(3):
            service.process_transcription(
                text=f"Test transcription number {i} with some content.",
                session_id=f"test_{i}"
            )

        # Verify metrics updated
        assert service.metrics["total_processed"] == initial_count + 3
        assert service.metrics["total_keywords_extracted"] > 0
        assert service.metrics["avg_processing_time"] > 0
        assert service.metrics["last_processed_at"] is not None

    def test_input_validation(self, service):
        """Test input validation."""
        # Empty text
        with pytest.raises(ValueError, match="empty"):
            service.process_transcription(text="")

        # Text too short
        with pytest.raises(ValueError, match="too short"):
            service.process_transcription(text="hi")

        # Text too long
        long_text = "x" * (service.config.MAX_TEXT_LENGTH + 1000)
        with pytest.raises(ValueError, match="too long"):
            service.process_transcription(text=long_text)

    def test_health_check(self, service):
        """Test health check functionality."""
        health = service.health_check()

        assert "status" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "components" in health
        assert "keyword_extractor" in health["components"]
        assert "redis" in health["components"]

        # With Redis mocked, should be healthy
        assert health["components"]["redis"] == "ok"
        assert health["components"]["keyword_extractor"] == "ok"

    def test_get_metrics(self, service):
        """Test metrics retrieval."""
        metrics = service.get_metrics()

        assert "total_processed" in metrics
        assert "total_keywords_extracted" in metrics
        assert "components" in metrics
        assert "redis" in metrics

        # Verify component status
        assert metrics["components"]["keyword_extractor"] == "enabled"

    def test_session_id_generation(self, service):
        """Test automatic session ID generation."""
        result = service.process_transcription(
            text="Test text without explicit session ID."
        )

        assert "session_id" in result
        assert result["session_id"].startswith("nlp_session_")

    def test_text_statistics(self, service):
        """Test text statistics calculation."""
        test_text = """
        This is a test. It has multiple sentences! Does it work?
        Let's verify the text statistics are calculated correctly.
        """

        result = service.process_transcription(text=test_text)

        stats = result["insights"]["text_stats"]

        assert "char_count" in stats
        assert "word_count" in stats
        assert "sentence_count" in stats

        assert stats["char_count"] == len(test_text)
        assert stats["word_count"] > 0
        assert stats["sentence_count"] > 0

    def test_error_handling(self, service, mock_redis):
        """Test error handling in processing."""
        # Simulate Redis error
        mock_redis.xadd.side_effect = Exception("Redis connection lost")

        # Should still process but not fail
        test_text = "Test text with Redis failure."

        # Processing should succeed despite Redis error
        result = service.process_transcription(text=test_text)

        assert "keywords" in result
        assert len(result["keywords"]) > 0

    def test_context_manager(self, config, mock_redis):
        """Test using service as context manager."""
        with patch("core.nlp_insights.nlp_service.redis.Redis", return_value=mock_redis):
            with NLPService(config=config, enable_diarization=False) as service:
                result = service.process_transcription(
                    text="Test with context manager"
                )
                assert "keywords" in result

            # After context exit, close should have been called
            assert True  # If we get here, cleanup worked

    def test_speaker_diarization_disabled(self, service):
        """Test that speaker diarization is properly disabled."""
        result = service.process_transcription(
            text="Test without audio",
            audio_path=None
        )

        # Should not have speaker information
        assert result["speakers"] is None
        assert "speaker_summary" not in result["insights"]

    @patch("core.nlp_insights.nlp_service.SpeakerDiarization")
    def test_speaker_diarization_enabled(self, mock_diarizer_class, config, mock_redis):
        """Test with speaker diarization enabled (mocked)."""
        # Create mock segments
        mock_segments = [
            SpeakerSegment(0.0, 5.0, "SPEAKER_00"),
            SpeakerSegment(5.0, 10.0, "SPEAKER_01"),
            SpeakerSegment(10.0, 15.0, "SPEAKER_00")
        ]

        # Mock diarizer instance
        mock_diarizer = MagicMock()
        mock_diarizer.diarize.return_value = mock_segments
        mock_diarizer.get_speaker_statistics.return_value = {
            "SPEAKER_00": {
                "num_turns": 2,
                "total_time": 10.0,
                "avg_turn_duration": 5.0,
                "segments": []
            },
            "SPEAKER_01": {
                "num_turns": 1,
                "total_time": 5.0,
                "avg_turn_duration": 5.0,
                "segments": []
            }
        }
        mock_diarizer_class.return_value = mock_diarizer

        with patch("core.nlp_insights.nlp_service.redis.Redis", return_value=mock_redis):
            service = NLPService(
                config=config,
                diarization_token="fake_token",
                enable_diarization=True
            )

            result = service.process_transcription(
                text="Test with speakers",
                audio_path="/fake/audio.wav"
            )

            # Should have speaker information
            assert result["speakers"] is not None
            assert "speaker_summary" in result["insights"]
            assert result["insights"]["speaker_summary"]["num_speakers"] == 2

            service.close()


class TestNLPServicePerformance:
    """Performance tests for NLP Service."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.xadd.return_value = b"1234567890-0"

        with patch("core.nlp_insights.nlp_service.redis.Redis", return_value=mock_redis):
            service = NLPService(enable_diarization=False)
            yield service
            service.close()

    def test_processing_time(self, service):
        """Test that processing completes in reasonable time."""
        test_text = """
        This is a longer test text to evaluate processing performance.
        It contains multiple sentences with various topics including machine
        learning, natural language processing, speech recognition, and data analysis.
        The system should be able to process this efficiently and extract relevant
        keywords within a reasonable time frame.
        """ * 10  # Repeat for longer text

        start = time.time()
        result = service.process_transcription(text=test_text)
        elapsed = time.time() - start

        # Should complete within 5 seconds for this size
        assert elapsed < 5.0

        # Verify processing time is recorded
        assert result["processing_time_ms"] > 0
        assert result["processing_time_ms"] < 5000

    def test_batch_consistency(self, service):
        """Test consistent results across multiple runs."""
        test_text = "Machine learning and natural language processing are important."

        results = []
        for _ in range(3):
            result = service.process_transcription(text=test_text)
            results.append(result)

        # All results should have same number of keywords
        keyword_counts = [len(r["keywords"]) for r in results]
        assert len(set(keyword_counts)) == 1  # All same

        # Top keywords should be similar (may vary slightly due to randomness)
        top_keywords = [[kw["keyword"] for kw in r["keywords"][:3]] for r in results]
        # At least 2 of top 3 should match
        assert len(set(top_keywords[0]) & set(top_keywords[1])) >= 2


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
