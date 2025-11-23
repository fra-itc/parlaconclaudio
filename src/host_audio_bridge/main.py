#!/usr/bin/env python3
"""
Audio Bridge Main Entry Point

Run the audio bridge service as a standalone application.

Usage:
    python -m src.host_audio_bridge.main [options]

    # With environment variables
    export RTSTT_WEBSOCKET_URL="ws://localhost:8000/ws"
    export RTSTT_AUDIO_DRIVER="mock"
    python -m src.host_audio_bridge.main

    # With command line args
    python -m src.host_audio_bridge.main --url ws://192.168.1.100:8000/ws --driver pulseaudio
"""

import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.host_audio_bridge.audio_bridge import AudioBridge
from src.host_audio_bridge.config import BridgeConfig
from src.core.audio_capture.platform_detector import detect_platform


def setup_logging(level: str = "INFO", log_file: Path = None) -> None:
    """Setup logging configuration"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=handlers
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="RTSTT Audio Bridge - Stream audio from host to backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect driver and connect to local backend
  python -m src.host_audio_bridge.main

  # Use mock driver for testing
  python -m src.host_audio_bridge.main --driver mock --pattern sine

  # Connect to remote backend
  python -m src.host_audio_bridge.main --url ws://192.168.1.100:8000/ws

  # Test for 10 seconds only
  python -m src.host_audio_bridge.main --test-duration 10

  # Use PulseAudio on Linux
  python -m src.host_audio_bridge.main --driver pulseaudio --sample-rate 44100
        """
    )

    # Connection options
    conn_group = parser.add_argument_group("Connection")
    conn_group.add_argument(
        "--url",
        default=None,
        help="WebSocket URL (default: ws://localhost:8000/ws)"
    )
    conn_group.add_argument(
        "--reconnect-delay",
        type=float,
        default=5.0,
        help="Delay between reconnection attempts in seconds (default: 5.0)"
    )
    conn_group.add_argument(
        "--max-reconnect",
        type=int,
        default=0,
        help="Maximum reconnection attempts, 0 = infinite (default: 0)"
    )

    # Audio options
    audio_group = parser.add_argument_group("Audio")
    audio_group.add_argument(
        "--driver",
        choices=["mock", "wasapi", "pulseaudio", "alsa", "portaudio"],
        default=None,
        help="Audio driver to use (default: auto-detect)"
    )
    audio_group.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        choices=[8000, 16000, 22050, 44100, 48000],
        help="Audio sample rate in Hz (default: 16000)"
    )
    audio_group.add_argument(
        "--channels",
        type=int,
        default=1,
        choices=[1, 2],
        help="Number of audio channels (default: 1 = mono)"
    )
    audio_group.add_argument(
        "--chunk-size",
        type=int,
        default=4096,
        help="Audio chunk size in frames (default: 4096)"
    )
    audio_group.add_argument(
        "--buffer-seconds",
        type=float,
        default=2.0,
        help="Minimum buffer duration before sending (default: 2.0)"
    )
    audio_group.add_argument(
        "--device-id",
        type=int,
        default=None,
        help="Specific audio device ID to use"
    )
    audio_group.add_argument(
        "--pattern",
        choices=["sine", "noise", "silence", "speech"],
        default="sine",
        help="Pattern for mock driver (default: sine)"
    )

    # Logging options
    log_group = parser.add_argument_group("Logging")
    log_group.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    log_group.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Log file path (default: stdout only)"
    )

    # Testing options
    test_group = parser.add_argument_group("Testing")
    test_group.add_argument(
        "--test-duration",
        type=float,
        default=None,
        help="Run for N seconds then exit (default: run forever)"
    )
    test_group.add_argument(
        "--info",
        action="store_true",
        help="Show platform and driver information then exit"
    )

    return parser.parse_args()


def show_platform_info() -> None:
    """Display platform and driver information"""
    from src.core.audio_capture.audio_factory import AudioCaptureFactory

    platform_info = detect_platform()
    platform_details = AudioCaptureFactory.get_platform_info()
    drivers = AudioCaptureFactory.list_available_drivers()

    print("=" * 60)
    print("RTSTT Audio Bridge - Platform Information")
    print("=" * 60)
    print()
    print(f"Platform Type:     {platform_info.platform_type.value}")
    print(f"OS:                {platform_info.os_name} {platform_info.os_version}")
    if platform_info.is_wsl:
        print(f"WSL Version:       {platform_info.wsl_version}")
    print()
    print("Available Audio Subsystems:")
    for subsystem in platform_info.available_subsystems:
        print(f"  - {subsystem.value}")
    print()
    print(f"Recommended Driver: {platform_info.recommended_driver}")
    print()
    print("Registered Drivers:")
    for name, info in drivers.items():
        suitable = "✅" if info["suitable_for_platform"] else "❌"
        print(f"  {suitable} {name:15s} - {info['description']}")
    print()
    print("=" * 60)


async def main_async() -> int:
    """Async main function"""
    args = parse_args()

    # Show info and exit if requested
    if args.info:
        show_platform_info()
        return 0

    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)

    # Show startup banner
    print()
    print("=" * 60)
    print("  RTSTT Audio Bridge Service")
    print("  Host-to-Backend Audio Streaming")
    print("=" * 60)
    print()

    # Create config from args and environment
    config = BridgeConfig.from_env()

    # Override with command line args
    if args.url:
        config.websocket_url = args.url
    if args.reconnect_delay:
        config.reconnect_delay = args.reconnect_delay
    if args.max_reconnect:
        config.max_reconnect_attempts = args.max_reconnect
    if args.driver:
        config.driver = args.driver
    if args.sample_rate:
        config.sample_rate = args.sample_rate
    if args.channels:
        config.channels = args.channels
    if args.chunk_size:
        config.chunk_size = args.chunk_size
    if args.buffer_seconds:
        config.buffer_seconds = args.buffer_seconds
    if args.device_id is not None:
        config.device_id = args.device_id
    if args.pattern:
        config.pattern = args.pattern
    if args.test_duration:
        config.test_duration = args.test_duration
    if args.log_level:
        config.log_level = args.log_level

    # Create and run bridge
    bridge = AudioBridge(config)

    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, stopping...")
        bridge.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await bridge.run()
        return 0

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        bridge.stop()
        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


def main() -> int:
    """Main entry point"""
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main())
