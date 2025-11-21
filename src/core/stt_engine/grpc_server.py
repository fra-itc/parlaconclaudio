"""
gRPC Server for STT Service

Provides a gRPC interface for real-time speech-to-text transcription
using WhisperRTXEngine on NVIDIA RTX GPUs.
"""

import logging
import time
import traceback
from concurrent import futures
from typing import Optional
import grpc
import numpy as np

from . import stt_service_pb2
from . import stt_service_pb2_grpc
from .whisper_rtx import WhisperRTXEngine, TranscriptionSegment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class STTEngineServicer(stt_service_pb2_grpc.STTServiceServicer):
    """
    gRPC Servicer for STT operations using WhisperRTXEngine.

    Implements the STTService defined in stt_service.proto.
    """

    def __init__(
        self,
        model_name: str = "large-v3",
        device: str = "cuda",
        compute_type: str = "float16",
        **engine_kwargs
    ):
        """
        Initialize STT Engine Servicer.

        Args:
            model_name: Whisper model name (default: "large-v3")
            device: Device to use - "cuda" or "cpu" (default: "cuda")
            compute_type: Computation precision (default: "float16")
            **engine_kwargs: Additional arguments for WhisperRTXEngine
        """
        super().__init__()
        logger.info("Initializing STTEngineServicer...")

        try:
            self.engine = WhisperRTXEngine(
                model_name=model_name,
                device=device,
                compute_type=compute_type,
                **engine_kwargs
            )
            logger.info("STTEngineServicer initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize WhisperRTXEngine: {e}")
            logger.error(traceback.format_exc())
            raise

    def Transcribe(self, request, context):
        """
        Transcribe audio data to text with timing segments.

        Args:
            request: AudioRequest containing audio data and parameters
            context: gRPC context

        Returns:
            TranscriptionResponse: Transcription result with segments
        """
        request_id = request.request_id or f"req_{int(time.time() * 1000)}"
        logger.info(f"[{request_id}] Received transcription request")

        start_time = time.time()

        try:
            # Validate request
            if not request.audio_data:
                logger.error(f"[{request_id}] Empty audio data")
                return self._create_error_response(
                    request_id=request_id,
                    error_code=1,
                    error_message="Empty audio data",
                    error_details="AudioRequest.audio_data is empty"
                )

            # Convert bytes to numpy array
            # Assuming 16-bit PCM audio
            audio_array = np.frombuffer(request.audio_data, dtype=np.int16)

            # Convert to float32 and normalize to [-1.0, 1.0]
            audio_float = audio_array.astype(np.float32) / 32768.0

            logger.info(f"[{request_id}] Audio data: {len(audio_array)} samples, "
                       f"sample_rate: {request.sample_rate or 'default'}, "
                       f"language: {request.language or 'auto'}")

            # Prepare transcription parameters
            language = request.language if request.language else None
            task = request.task if request.task else "transcribe"

            # Transcribe using WhisperRTXEngine
            result = self.engine.transcribe(
                audio=audio_float,
                language=language,
                task=task,
                word_timestamps=True
            )

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            logger.info(f"[{request_id}] Transcription completed in {processing_time_ms:.2f}ms")
            logger.info(f"[{request_id}] Result: {len(result.segments)} segments, "
                       f"language: {result.language}")

            # Build response
            response = stt_service_pb2.TranscriptionResponse(
                text=result.text,
                language=result.language,
                duration=result.duration if result.duration else 0.0,
                processing_time_ms=processing_time_ms,
                request_id=request_id,
                status=stt_service_pb2.Status(
                    code=0,
                    message="Success"
                )
            )

            # Add segments
            for seg in result.segments:
                segment = stt_service_pb2.Segment(
                    text=seg.text,
                    start=seg.start,
                    end=seg.end,
                    confidence=seg.confidence if seg.confidence else 0.0
                )
                response.segments.append(segment)

            return response

        except Exception as e:
            logger.error(f"[{request_id}] Transcription failed: {e}")
            logger.error(traceback.format_exc())

            processing_time_ms = (time.time() - start_time) * 1000

            return self._create_error_response(
                request_id=request_id,
                error_code=2,
                error_message="Transcription failed",
                error_details=str(e),
                processing_time_ms=processing_time_ms
            )

    def TranscribeStream(self, request_iterator, context):
        """
        Stream audio chunks for real-time transcription.

        Args:
            request_iterator: Iterator of AudioChunk messages
            context: gRPC context

        Yields:
            TranscriptionResponse: Streaming transcription results
        """
        logger.info("Received streaming transcription request")

        # Accumulate audio chunks
        audio_chunks = []
        request_id = None

        try:
            for chunk in request_iterator:
                if request_id is None:
                    request_id = chunk.request_id or f"stream_{int(time.time() * 1000)}"
                    logger.info(f"[{request_id}] Starting stream processing")

                audio_chunks.append(chunk.audio_data)
                logger.debug(f"[{request_id}] Received chunk {chunk.sequence}")

                if chunk.is_last:
                    logger.info(f"[{request_id}] Received last chunk, processing...")
                    break

            # Concatenate all chunks
            if not audio_chunks:
                logger.error(f"[{request_id}] No audio chunks received")
                yield self._create_error_response(
                    request_id=request_id,
                    error_code=1,
                    error_message="No audio chunks received"
                )
                return

            audio_data = b''.join(audio_chunks)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0

            # Transcribe
            start_time = time.time()
            result = self.engine.transcribe(audio=audio_float, word_timestamps=True)
            processing_time_ms = (time.time() - start_time) * 1000

            logger.info(f"[{request_id}] Stream transcription completed in {processing_time_ms:.2f}ms")

            # Build and yield response
            response = stt_service_pb2.TranscriptionResponse(
                text=result.text,
                language=result.language,
                duration=result.duration if result.duration else 0.0,
                processing_time_ms=processing_time_ms,
                request_id=request_id,
                status=stt_service_pb2.Status(code=0, message="Success")
            )

            for seg in result.segments:
                segment = stt_service_pb2.Segment(
                    text=seg.text,
                    start=seg.start,
                    end=seg.end,
                    confidence=seg.confidence if seg.confidence else 0.0
                )
                response.segments.append(segment)

            yield response

        except Exception as e:
            logger.error(f"[{request_id}] Stream transcription failed: {e}")
            logger.error(traceback.format_exc())

            yield self._create_error_response(
                request_id=request_id or "unknown",
                error_code=2,
                error_message="Stream transcription failed",
                error_details=str(e)
            )

    def HealthCheck(self, request, context):
        """
        Health check for service availability.

        Args:
            request: HealthCheckRequest
            context: gRPC context

        Returns:
            HealthCheckResponse: Service health status
        """
        logger.info("Health check requested")

        try:
            # Get model info
            model_info = self.engine.get_model_info()

            # Check if model is loaded
            is_serving = model_info.get('is_loaded', False)

            status = (stt_service_pb2.HealthCheckResponse.SERVING
                     if is_serving
                     else stt_service_pb2.HealthCheckResponse.NOT_SERVING)

            response = stt_service_pb2.HealthCheckResponse(
                status=status,
                message="STT service is operational" if is_serving else "Model not loaded",
                model_info=stt_service_pb2.ModelInfo(
                    name=model_info.get('model_name', 'unknown'),
                    device=model_info.get('device', 'unknown'),
                    compute_type=model_info.get('compute_type', 'unknown'),
                    is_loaded=is_serving
                )
            )

            logger.info(f"Health check: {response.message}")
            return response

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return stt_service_pb2.HealthCheckResponse(
                status=stt_service_pb2.HealthCheckResponse.NOT_SERVING,
                message=f"Health check error: {str(e)}"
            )

    def _create_error_response(
        self,
        request_id: str,
        error_code: int,
        error_message: str,
        error_details: str = "",
        processing_time_ms: float = 0.0
    ) -> stt_service_pb2.TranscriptionResponse:
        """
        Create an error response.

        Args:
            request_id: Request identifier
            error_code: Error code (non-zero)
            error_message: Human-readable error message
            error_details: Detailed error information
            processing_time_ms: Processing time before error

        Returns:
            TranscriptionResponse with error status
        """
        return stt_service_pb2.TranscriptionResponse(
            text="",
            language="",
            duration=0.0,
            processing_time_ms=processing_time_ms,
            request_id=request_id,
            status=stt_service_pb2.Status(
                code=error_code,
                message=error_message,
                error_details=error_details
            )
        )


def serve(
    port: int = 50051,
    max_workers: int = 10,
    model_name: str = "large-v3",
    device: str = "cuda",
    compute_type: str = "float16",
    **engine_kwargs
):
    """
    Start the gRPC server.

    Args:
        port: Port to listen on (default: 50051)
        max_workers: Maximum number of worker threads (default: 10)
        model_name: Whisper model name (default: "large-v3")
        device: Device to use (default: "cuda")
        compute_type: Computation precision (default: "float16")
        **engine_kwargs: Additional arguments for WhisperRTXEngine
    """
    logger.info(f"Starting gRPC server on port {port}...")

    # Create server
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=max_workers),
        options=[
            ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100 MB
            ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100 MB
        ]
    )

    # Add servicer
    stt_service_pb2_grpc.add_STTServiceServicer_to_server(
        STTEngineServicer(
            model_name=model_name,
            device=device,
            compute_type=compute_type,
            **engine_kwargs
        ),
        server
    )

    # Bind port and start
    server.add_insecure_port(f'[::]:{port}')
    server.start()

    logger.info(f"gRPC server started successfully on port {port}")
    logger.info(f"Model: {model_name}, Device: {device}, Compute: {compute_type}")
    logger.info("Server is ready to accept requests...")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.stop(0)
        logger.info("Server stopped")


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="STT gRPC Server")
    parser.add_argument("--port", type=int, default=50051, help="Port to listen on")
    parser.add_argument("--model", type=str, default="large-v3", help="Whisper model name")
    parser.add_argument("--device", type=str, default="cuda", help="Device (cuda/cpu)")
    parser.add_argument("--compute-type", type=str, default="float16", help="Compute type")
    parser.add_argument("--workers", type=int, default=10, help="Max worker threads")

    args = parser.parse_args()

    serve(
        port=args.port,
        max_workers=args.workers,
        model_name=args.model,
        device=args.device,
        compute_type=args.compute_type
    )
