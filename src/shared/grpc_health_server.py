"""
Simple gRPC Health Server Helper

Provides a minimal gRPC server that only exposes standard health checking.
Useful for services that don't use gRPC for their main functionality but need
to expose health checks for Docker/Kubernetes.
"""

import logging
import grpc
from concurrent import futures
from grpc_health.v1 import health
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc
import threading

logger = logging.getLogger(__name__)


class GRPCHealthServer:
    """
    Standalone gRPC server that only provides health checking.

    Runs in a background thread and can be started/stopped independently.
    """

    def __init__(self, port: int, service_name: str = ""):
        """
        Initialize health server.

        Args:
            port: Port to listen on
            service_name: Name of the service for health checks
        """
        self.port = port
        self.service_name = service_name
        self.server = None
        self.health_servicer = None
        self._server_thread = None
        self._running = False

    def start(self):
        """Start the health server in a background thread."""
        if self._running:
            logger.warning("gRPC health server already running")
            return

        logger.info(f"Starting gRPC health server on port {self.port}...")

        # Create server
        self.server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=2),
            options=[
                ('grpc.max_send_message_length', 1 * 1024 * 1024),  # 1 MB
                ('grpc.max_receive_message_length', 1 * 1024 * 1024),  # 1 MB
            ]
        )

        # Add health checking service
        self.health_servicer = health.HealthServicer()
        health_pb2_grpc.add_HealthServicer_to_server(self.health_servicer, self.server)

        # Set initial status as SERVING
        self.health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
        if self.service_name:
            self.health_servicer.set(self.service_name, health_pb2.HealthCheckResponse.SERVING)

        # Bind port
        self.server.add_insecure_port(f'[::]:{self.port}')

        # Start server in background thread
        self._running = True
        self._server_thread = threading.Thread(target=self._run_server, daemon=True)
        self._server_thread.start()

        logger.info(f"gRPC health server started on port {self.port}")

    def _run_server(self):
        """Internal method to run server in thread."""
        try:
            self.server.start()
            logger.info("gRPC health server ready")
            self.server.wait_for_termination()
        except Exception as e:
            logger.error(f"gRPC health server error: {e}")
            self._running = False

    def stop(self):
        """Stop the health server."""
        if not self._running:
            return

        logger.info("Stopping gRPC health server...")
        self._running = False

        if self.server:
            self.server.stop(grace=5)

        if self._server_thread:
            self._server_thread.join(timeout=10)

        logger.info("gRPC health server stopped")

    def set_serving(self):
        """Set health status to SERVING."""
        if self.health_servicer:
            self.health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
            if self.service_name:
                self.health_servicer.set(self.service_name, health_pb2.HealthCheckResponse.SERVING)
            logger.info("Health status set to SERVING")

    def set_not_serving(self):
        """Set health status to NOT_SERVING."""
        if self.health_servicer:
            self.health_servicer.set("", health_pb2.HealthCheckResponse.NOT_SERVING)
            if self.service_name:
                self.health_servicer.set(self.service_name, health_pb2.HealthCheckResponse.NOT_SERVING)
            logger.info("Health status set to NOT_SERVING")

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running
