"""
Redis Audio Consumer for STT Pipeline

Consumes audio chunks from Redis streams, processes them with WhisperRTXEngine,
and publishes transcription results back to Redis.
"""

import logging
import time
import json
import traceback
from typing import Optional, Dict, Any, List
import numpy as np
import redis

from .whisper_rtx import WhisperRTXEngine, TranscriptionResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RedisAudioConsumer:
    """
    Consumes audio chunks from Redis streams and produces transcriptions.

    Architecture:
    - Reads from Redis stream: "audio:input"
    - Processes audio with WhisperRTXEngine
    - Writes to Redis stream: "transcription:output"
    - Supports consumer groups for scalability
    """

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        input_stream: str = "audio:input",
        output_stream: str = "transcription:output",
        consumer_group: str = "stt-workers",
        consumer_name: Optional[str] = None,
        model_name: str = "large-v3",
        device: str = "cuda",
        compute_type: str = "float16",
        block_time_ms: int = 5000,
        batch_size: int = 1,
        **engine_kwargs
    ):
        """
        Initialize Redis Audio Consumer.

        Args:
            redis_host: Redis server host (default: "localhost")
            redis_port: Redis server port (default: 6379)
            redis_db: Redis database number (default: 0)
            redis_password: Redis password (optional)
            input_stream: Redis stream to read audio from (default: "audio:input")
            output_stream: Redis stream to write transcriptions to (default: "transcription:output")
            consumer_group: Consumer group name (default: "stt-workers")
            consumer_name: Unique consumer name (default: auto-generated)
            model_name: Whisper model name (default: "large-v3")
            device: Device to use (default: "cuda")
            compute_type: Computation precision (default: "float16")
            block_time_ms: Max time to block waiting for messages (default: 5000ms)
            batch_size: Number of messages to read per batch (default: 1)
            **engine_kwargs: Additional arguments for WhisperRTXEngine
        """
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.redis_password = redis_password
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name or f"consumer_{int(time.time() * 1000)}"
        self.block_time_ms = block_time_ms
        self.batch_size = batch_size

        self.redis_client: Optional[redis.Redis] = None
        self.engine: Optional[WhisperRTXEngine] = None
        self.running = False

        logger.info("Initializing RedisAudioConsumer...")
        logger.info(f"Redis: {redis_host}:{redis_port}/{redis_db}")
        logger.info(f"Input stream: {input_stream}, Output stream: {output_stream}")
        logger.info(f"Consumer group: {consumer_group}, Consumer name: {self.consumer_name}")

        # Connect to Redis
        self._connect_redis()

        # Initialize STT engine
        self._init_engine(
            model_name=model_name,
            device=device,
            compute_type=compute_type,
            **engine_kwargs
        )

        # Create consumer group if it doesn't exist
        self._ensure_consumer_group()

        logger.info("RedisAudioConsumer initialized successfully")

    def _connect_redis(self):
        """Connect to Redis server."""
        try:
            logger.info("Connecting to Redis...")
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=False  # Keep binary data as bytes
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")

        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            raise

    def _init_engine(self, **kwargs):
        """Initialize WhisperRTXEngine."""
        try:
            logger.info("Initializing WhisperRTXEngine...")
            self.engine = WhisperRTXEngine(**kwargs)
            logger.info("WhisperRTXEngine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize WhisperRTXEngine: {e}")
            raise

    def _ensure_consumer_group(self):
        """Create consumer group if it doesn't exist."""
        try:
            # Try to create consumer group
            self.redis_client.xgroup_create(
                name=self.input_stream,
                groupname=self.consumer_group,
                id='0',
                mkstream=True
            )
            logger.info(f"Created consumer group: {self.consumer_group}")

        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group already exists: {self.consumer_group}")
            else:
                logger.error(f"Failed to create consumer group: {e}")
                raise
        except Exception as e:
            logger.error(f"Error ensuring consumer group: {e}")
            raise

    def start(self):
        """
        Start consuming audio messages from Redis.

        This is a blocking call that runs until stop() is called or an error occurs.
        """
        self.running = True
        logger.info("Starting Redis audio consumer...")
        logger.info(f"Reading from stream: {self.input_stream}")
        logger.info(f"Writing to stream: {self.output_stream}")

        message_count = 0

        try:
            while self.running:
                try:
                    # Read messages from stream
                    messages = self.redis_client.xreadgroup(
                        groupname=self.consumer_group,
                        consumername=self.consumer_name,
                        streams={self.input_stream: '>'},
                        count=self.batch_size,
                        block=self.block_time_ms
                    )

                    if not messages:
                        # No messages received (timeout)
                        continue

                    # Process each message
                    for stream_name, message_list in messages:
                        for message_id, message_data in message_list:
                            message_count += 1
                            logger.info(f"Processing message {message_count}: {message_id.decode()}")

                            try:
                                # Process the audio message
                                self._process_message(message_id, message_data)

                                # Acknowledge message
                                self.redis_client.xack(
                                    self.input_stream,
                                    self.consumer_group,
                                    message_id
                                )
                                logger.debug(f"Acknowledged message: {message_id.decode()}")

                            except Exception as e:
                                logger.error(f"Failed to process message {message_id.decode()}: {e}")
                                logger.error(traceback.format_exc())
                                # Message will remain in pending list for retry

                except redis.ConnectionError as e:
                    logger.error(f"Redis connection error: {e}")
                    logger.info("Attempting to reconnect...")
                    time.sleep(5)
                    self._connect_redis()
                    self._ensure_consumer_group()

                except Exception as e:
                    logger.error(f"Error reading from Redis: {e}")
                    logger.error(traceback.format_exc())
                    time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            logger.info(f"Consumer stopped. Processed {message_count} messages")
            self.running = False

    def stop(self):
        """Stop the consumer."""
        logger.info("Stopping consumer...")
        self.running = False

    def _process_message(self, message_id: bytes, message_data: Dict[bytes, bytes]):
        """
        Process a single audio message.

        Args:
            message_id: Redis message ID
            message_data: Message payload with audio data and metadata
        """
        start_time = time.time()

        # Extract message fields
        audio_data = message_data.get(b'audio_data')
        metadata_json = message_data.get(b'metadata', b'{}')
        request_id = message_data.get(b'request_id', message_id).decode()

        if not audio_data:
            logger.error(f"[{request_id}] Missing audio_data field")
            return

        # Parse metadata
        try:
            metadata = json.loads(metadata_json.decode())
        except Exception as e:
            logger.warning(f"[{request_id}] Failed to parse metadata: {e}")
            metadata = {}

        logger.info(f"[{request_id}] Audio size: {len(audio_data)} bytes")
        logger.info(f"[{request_id}] Metadata: {metadata}")

        # Convert audio bytes to numpy array
        try:
            # Assuming 16-bit PCM audio
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0

            logger.info(f"[{request_id}] Audio samples: {len(audio_array)}")

        except Exception as e:
            logger.error(f"[{request_id}] Failed to convert audio data: {e}")
            self._publish_error(request_id, f"Audio conversion error: {e}")
            return

        # Transcribe audio
        try:
            language = metadata.get('language')
            task = metadata.get('task', 'transcribe')

            logger.info(f"[{request_id}] Transcribing (language={language}, task={task})...")

            result = self.engine.transcribe(
                audio=audio_float,
                language=language,
                task=task,
                word_timestamps=True
            )

            processing_time_ms = (time.time() - start_time) * 1000

            logger.info(f"[{request_id}] Transcription completed in {processing_time_ms:.2f}ms")
            logger.info(f"[{request_id}] Result: {len(result.segments)} segments, "
                       f"language: {result.language}")

            # Publish result to output stream
            self._publish_result(request_id, result, processing_time_ms, metadata)

        except Exception as e:
            logger.error(f"[{request_id}] Transcription failed: {e}")
            logger.error(traceback.format_exc())
            self._publish_error(request_id, str(e))

    def _publish_result(
        self,
        request_id: str,
        result: TranscriptionResult,
        processing_time_ms: float,
        metadata: Dict[str, Any]
    ):
        """
        Publish transcription result to Redis output stream.

        Args:
            request_id: Request identifier
            result: Transcription result from WhisperRTXEngine
            processing_time_ms: Processing time in milliseconds
            metadata: Original request metadata
        """
        try:
            # Build segments data
            segments_data = []
            for seg in result.segments:
                segments_data.append({
                    'text': seg.text,
                    'start': seg.start,
                    'end': seg.end,
                    'confidence': seg.confidence
                })

            # Build result payload
            payload = {
                'request_id': request_id,
                'text': result.text,
                'segments': segments_data,
                'language': result.language,
                'duration': result.duration,
                'processing_time_ms': processing_time_ms,
                'timestamp': time.time(),
                'status': 'success',
                'metadata': metadata  # Echo original metadata
            }

            # Publish to output stream
            message_id = self.redis_client.xadd(
                self.output_stream,
                {
                    'request_id': request_id,
                    'payload': json.dumps(payload)
                }
            )

            logger.info(f"[{request_id}] Published result to {self.output_stream}: {message_id.decode()}")

        except Exception as e:
            logger.error(f"[{request_id}] Failed to publish result: {e}")
            logger.error(traceback.format_exc())

    def _publish_error(self, request_id: str, error_message: str):
        """
        Publish error to Redis output stream.

        Args:
            request_id: Request identifier
            error_message: Error description
        """
        try:
            payload = {
                'request_id': request_id,
                'text': '',
                'segments': [],
                'language': '',
                'duration': 0.0,
                'processing_time_ms': 0.0,
                'timestamp': time.time(),
                'status': 'error',
                'error': error_message
            }

            message_id = self.redis_client.xadd(
                self.output_stream,
                {
                    'request_id': request_id,
                    'payload': json.dumps(payload)
                }
            )

            logger.info(f"[{request_id}] Published error to {self.output_stream}: {message_id.decode()}")

        except Exception as e:
            logger.error(f"[{request_id}] Failed to publish error: {e}")

    def get_pending_messages(self) -> List[Dict]:
        """
        Get pending messages for this consumer.

        Returns:
            List of pending message info dicts
        """
        try:
            pending = self.redis_client.xpending_range(
                name=self.input_stream,
                groupname=self.consumer_group,
                min='-',
                max='+',
                count=100,
                consumername=self.consumer_name
            )
            return pending

        except Exception as e:
            logger.error(f"Failed to get pending messages: {e}")
            return []

    def __del__(self):
        """Cleanup on deletion."""
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception:
                pass


def run_consumer(
    redis_host: str = "localhost",
    redis_port: int = 6379,
    model_name: str = "large-v3",
    device: str = "cuda",
    compute_type: str = "float16",
    **kwargs
):
    """
    Convenience function to create and run a Redis audio consumer.

    Args:
        redis_host: Redis server host
        redis_port: Redis server port
        model_name: Whisper model name
        device: Device to use
        compute_type: Computation precision
        **kwargs: Additional arguments for RedisAudioConsumer
    """
    consumer = RedisAudioConsumer(
        redis_host=redis_host,
        redis_port=redis_port,
        model_name=model_name,
        device=device,
        compute_type=compute_type,
        **kwargs
    )

    consumer.start()


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="Redis STT Audio Consumer")
    parser.add_argument("--redis-host", type=str, default="localhost", help="Redis host")
    parser.add_argument("--redis-port", type=int, default=6379, help="Redis port")
    parser.add_argument("--redis-db", type=int, default=0, help="Redis database")
    parser.add_argument("--redis-password", type=str, default=None, help="Redis password")
    parser.add_argument("--input-stream", type=str, default="audio:input", help="Input stream name")
    parser.add_argument("--output-stream", type=str, default="transcription:output", help="Output stream")
    parser.add_argument("--consumer-group", type=str, default="stt-workers", help="Consumer group")
    parser.add_argument("--consumer-name", type=str, default=None, help="Consumer name")
    parser.add_argument("--model", type=str, default="large-v3", help="Whisper model name")
    parser.add_argument("--device", type=str, default="cuda", help="Device (cuda/cpu)")
    parser.add_argument("--compute-type", type=str, default="float16", help="Compute type")

    args = parser.parse_args()

    run_consumer(
        redis_host=args.redis_host,
        redis_port=args.redis_port,
        redis_db=args.redis_db,
        redis_password=args.redis_password,
        input_stream=args.input_stream,
        output_stream=args.output_stream,
        consumer_group=args.consumer_group,
        consumer_name=args.consumer_name,
        model_name=args.model,
        device=args.device,
        compute_type=args.compute_type
    )
