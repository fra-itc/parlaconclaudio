"""
WASAPI Audio Capture Example

Demonstrates complete audio capture workflow:
1. Device enumeration
2. Audio capture with callbacks
3. Format conversion
4. Real-time statistics

Author: ORCHIDEA Agent System
Created: 2025-11-21
"""

import sys
import time
import numpy as np
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.audio_capture import (
    WASAPICapture,
    list_audio_devices,
    get_default_device,
    convert_to_mono,
    normalize_audio,
    get_audio_stats,
    convert_int16_to_float32
)


def example_list_devices():
    """Example 1: List all available audio devices"""
    print("=" * 60)
    print("Example 1: Device Enumeration")
    print("=" * 60)

    # List all devices
    devices = list_audio_devices('all')
    print(f"\nFound {len(devices)} audio devices:")

    for i, device in enumerate(devices):
        default_str = " [DEFAULT]" if device.is_default else ""
        print(f"{i+1}. {device.name}")
        print(f"   Type: {device.device_type}{default_str}")
        print(f"   ID: {device.device_id}")
        print(f"   Channels: {device.max_channels}")
        print(f"   Sample rates: {device.supported_sample_rates}")
        print()

    # Get default device
    default = get_default_device()
    if default:
        print(f"Default device: {default.name}")
    else:
        print("No default device found")


def example_basic_capture():
    """Example 2: Basic audio capture"""
    print("\n" + "=" * 60)
    print("Example 2: Basic Audio Capture")
    print("=" * 60)

    chunk_count = 0
    total_samples = 0

    def audio_callback(audio_data):
        """Process each audio chunk"""
        nonlocal chunk_count, total_samples

        chunk_count += 1
        total_samples += len(audio_data)

        # Calculate statistics
        stats = get_audio_stats(audio_data)

        if chunk_count % 10 == 0:  # Print every 10th chunk
            print(f"Chunk {chunk_count:3d}: "
                  f"{stats['samples']:5d} samples, "
                  f"RMS: {stats['rms_db']:6.1f} dB, "
                  f"Peak: {stats['peak_db']:6.1f} dB")

    # Initialize capture
    capture = WASAPICapture(
        sample_rate=16000,
        channels=1,
        chunk_duration_ms=100
    )

    print(f"\nCapture config:")
    print(f"  Sample rate: {capture.sample_rate} Hz")
    print(f"  Channels: {capture.channels}")
    print(f"  Chunk size: {capture.chunk_size} samples")
    print(f"  Chunk duration: {capture.chunk_duration_ms} ms")

    print("\nStarting capture... (5 seconds)")
    capture.start(audio_callback)

    # Capture for 5 seconds
    time.sleep(5)

    # Stop capture
    capture.stop()

    # Print final statistics
    stats = capture.get_stats()
    print(f"\nCapture statistics:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Total samples: {stats['total_samples']}")
    print(f"  Duration: {stats['duration_seconds']:.2f} seconds")
    print(f"  Latency: {stats['latency_ms']:.1f} ms")
    print(f"  Errors: {stats['error_count']}")


def example_format_conversion():
    """Example 3: Audio format conversion"""
    print("\n" + "=" * 60)
    print("Example 3: Format Conversion")
    print("=" * 60)

    collected_audio = []

    def audio_callback(audio_data):
        """Collect audio chunks"""
        collected_audio.append(audio_data)

    # Capture stereo audio
    capture = WASAPICapture(
        sample_rate=48000,
        channels=2,
        chunk_duration_ms=100
    )

    print("\nCapturing 2 seconds of audio...")
    capture.start(audio_callback)
    time.sleep(2)
    capture.stop()

    # Concatenate all chunks
    audio = np.concatenate(collected_audio)
    print(f"\nCaptured audio shape: {audio.shape}")

    # Convert to mono
    print("\nConverting to mono...")
    mono = convert_to_mono(audio)
    print(f"Mono audio shape: {mono.shape}")

    # Convert from int16 to float32
    print("\nConverting to float32...")
    audio_float = convert_int16_to_float32(mono)
    print(f"Float32 audio dtype: {audio_float.dtype}")
    print(f"Float32 range: [{audio_float.min():.3f}, {audio_float.max():.3f}]")

    # Normalize
    print("\nNormalizing to -20 dB...")
    normalized = normalize_audio(audio_float, target_level=-20.0)

    # Compare statistics
    print("\nAudio statistics comparison:")

    stats_original = get_audio_stats(audio_float)
    stats_normalized = get_audio_stats(normalized)

    print(f"Original:")
    print(f"  RMS: {stats_original['rms_db']:.1f} dB")
    print(f"  Peak: {stats_original['peak_db']:.1f} dB")

    print(f"Normalized:")
    print(f"  RMS: {stats_normalized['rms_db']:.1f} dB")
    print(f"  Peak: {stats_normalized['peak_db']:.1f} dB")


def example_context_manager():
    """Example 4: Using context manager"""
    print("\n" + "=" * 60)
    print("Example 4: Context Manager Usage")
    print("=" * 60)

    chunk_count = 0

    def audio_callback(audio_data):
        """Process audio"""
        nonlocal chunk_count
        chunk_count += 1

    print("\nUsing context manager (auto cleanup)...")

    with WASAPICapture(sample_rate=16000, channels=1) as capture:
        capture.start(audio_callback)
        print("Capturing for 2 seconds...")
        time.sleep(2)
        # Automatically stops on exit

    print(f"Processed {chunk_count} chunks")
    print("Capture stopped automatically")


def example_statistics():
    """Example 5: Real-time statistics monitoring"""
    print("\n" + "=" * 60)
    print("Example 5: Real-time Statistics")
    print("=" * 60)

    def audio_callback(audio_data):
        """Minimal callback"""
        pass

    capture = WASAPICapture(
        sample_rate=16000,
        channels=1,
        chunk_duration_ms=50
    )

    print("\nMonitoring capture statistics...")
    capture.start(audio_callback)

    # Monitor for 5 seconds
    for i in range(10):
        time.sleep(0.5)
        stats = capture.get_stats()

        print(f"[{i+1}] Chunks: {stats['total_chunks']:3d}, "
              f"Samples: {stats['total_samples']:6d}, "
              f"Latency: {stats['latency_ms']:5.1f} ms, "
              f"Running: {stats['running']}")

    capture.stop()


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("WASAPI Audio Capture Examples")
    print("=" * 60)

    try:
        # Example 1: List devices
        example_list_devices()

        # Example 2: Basic capture
        example_basic_capture()

        # Example 3: Format conversion
        example_format_conversion()

        # Example 4: Context manager
        example_context_manager()

        # Example 5: Statistics
        example_statistics()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
