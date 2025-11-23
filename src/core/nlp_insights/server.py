"""
NLP Service Server - Long-running service mode

Runs the NLP Service in production mode (non-test mode).
Keeps the service alive to process transcription data from Redis streams.

Author: ML Team (ONDATA 2)
Date: 2025-11-22
"""

import logging
import signal
import sys
import time
import os
from typing import Optional

from .nlp_service import NLPService, NLPServiceConfig
from src.shared.grpc_health_server import GRPCHealthServer
from src.shared.secrets import get_hf_token, get_redis_password

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NLPServer:
    """Server wrapper for NLP Service."""

    def __init__(
        self,
        config: Optional[NLPServiceConfig] = None,
        enable_diarization: bool = False,  # Disabled by default for stability
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        hf_token: Optional[str] = None
    ):
        """
        Initialize NLP Server.

        Args:
            config: NLPServiceConfig instance
            enable_diarization: Enable speaker diarization (requires HF token)
            redis_host: Redis host (overrides config)
            redis_port: Redis port (overrides config)
            hf_token: HuggingFace token for diarization models
        """
        self.service = None
        self.grpc_health_server = None
        self.running = False

        logger.info("="*70)
        logger.info("NLP Service Server - Starting")
        logger.info("="*70)

        try:
            # Initialize service
            self.service = NLPService(
                config=config,
                enable_diarization=enable_diarization,
                redis_host=redis_host,
                redis_port=redis_port,
                diarization_token=hf_token
            )

            logger.info(f"Service initialized: {self.service}")

            # Perform health check
            health = self.service.health_check()
            logger.info(f"Health check: {health['status']}")

            if health['status'] == 'unhealthy':
                logger.error("Service unhealthy at startup!")
                raise RuntimeError(f"Unhealthy service: {health}")

            logger.info("NLP Service ready to process requests")

        except Exception as e:
            logger.error(f"Failed to initialize NLP Service: {e}")
            raise

    def start(self):
        """Start the server and keep it running."""
        self.running = True

        # Start gRPC health server
        try:
            self.grpc_health_server = GRPCHealthServer(port=50052, service_name="nlp.NLPService")
            self.grpc_health_server.start()
        except Exception as e:
            logger.error(f"Failed to start gRPC health server: {e}")

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("NLP Service is now running (press Ctrl+C to stop)")
        logger.info("Waiting for transcription data from Redis streams...")

        try:
            # Keep server alive - service processes Redis streams in background
            while self.running:
                time.sleep(10)  # Sleep and check health periodically

                # Periodic health check
                try:
                    health = self.service.health_check()
                    if health['status'] != 'healthy':
                        logger.warning(f"Health check degraded: {health}")
                except Exception as e:
                    logger.error(f"Health check failed: {e}")

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")

        finally:
            self.stop()

    def stop(self):
        """Stop the server gracefully."""
        logger.info("Shutting down NLP Service...")
        self.running = False

        # Stop gRPC health server
        if self.grpc_health_server:
            try:
                self.grpc_health_server.stop()
            except Exception as e:
                logger.error(f"Error stopping gRPC health server: {e}")

        if self.service:
            try:
                # Get final metrics
                metrics = self.service.get_metrics()
                logger.info(f"Final metrics: Processed {metrics['total_processed']} requests")

                # Close service
                self.service.close()
                logger.info("NLP Service closed successfully")

            except Exception as e:
                logger.error(f"Error during shutdown: {e}")

        logger.info("NLP Service Server stopped")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        self.running = False


def main():
    """Main entry point for NLP Service Server."""
    # Read configuration from environment
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    # Read secrets from Docker secrets or environment variables
    hf_token = get_hf_token(required=False)
    redis_password = get_redis_password(default="")

    enable_diarization = os.getenv("ENABLE_DIARIZATION", "false").lower() == "true"

    logger.info(f"Configuration:")
    logger.info(f"  Redis: {redis_host}:{redis_port}")
    logger.info(f"  Diarization: {'enabled' if enable_diarization else 'disabled'}")

    # Create and start server
    try:
        server = NLPServer(
            redis_host=redis_host,
            redis_port=redis_port,
            enable_diarization=enable_diarization,
            hf_token=hf_token
        )

        server.start()

    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
