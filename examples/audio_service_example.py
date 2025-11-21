"""
AudioService Example - Complete Audio Pipeline

This example demonstrates how to use AudioService to capture system audio,
detect speech using VAD, and automatically segment into speech phrases.

Usage:
    python examples/audio_service_example.py

Requirements:
    - PyAudio (for WASAPI capture)
    - PyTorch (for Silero VAD)
    - Active audio output (system audio or microphone)

Author: ORCHIDEA Agent System
Created: 2025-11-21
"""

import time
import numpy as np
import logging
from pathlib import Path
import sys

# Add src to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.audio_capture import AudioService, AudioServiceState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def save_segment_to_wav(segment: np.ndarray, sample_rate: int, output_dir: Path, segment_id: int):
    """
    Save audio segment to WAV file

    Args:
        segment: Audio data as numpy array
        sample_rate: Sample rate in Hz
        output_dir: Output directory path
        segment_id: Segment identifier
    """
    try:
        import wave
        import struct

        # Create output directory if needed
        output_dir.mkdir(parents=True, exist_ok=True)

        # Convert float32 to int16
        audio_int16 = np.clip(segment * 32767, -32768, 32767).astype(np.int16)

        # Save to WAV file
        output_path = output_dir / f"segment_{segment_id:04d}.wav"
        with wave.open(str(output_path), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes for int16
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        logger.info(f"Saved segment {segment_id} to {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error saving segment: {e}")
        return None


def main():
    """Main example function"""

    print("\n" + "="*70)
    print("AudioService Example - Real-time Speech Detection and Segmentation")
    print("="*70)

    # Configuration
    SAMPLE_RATE = 16000  # 16kHz recommended for VAD
    CAPTURE_DURATION = 10  # seconds
    OUTPUT_DIR = Path("output/segments")

    # Create AudioService with custom settings
    service = AudioService(
        sample_rate=SAMPLE_RATE,
        chunk_duration_ms=100,  # 100ms chunks
        vad_threshold=0.5,  # Speech confidence threshold
        min_speech_duration_ms=250,  # Minimum 250ms of speech
        min_silence_duration_ms=300,  # 300ms silence to segment
        buffer_capacity_seconds=10.0  # 10 second buffer
    )

    # Track detected segments
    segments = []
    segment_counter = [0]  # Use list for mutable counter in callback

    def on_segment_detected(segment: np.ndarray):
        """Callback when speech segment is detected"""
        segment_counter[0] += 1
        segments.append(segment)

        duration = len(segment) / SAMPLE_RATE
        energy = np.sqrt(np.mean(segment ** 2))

        print(f"\n[SEGMENT {segment_counter[0]}]")
        print(f"  Duration:  {duration:.2f}s")
        print(f"  Samples:   {len(segment)}")
        print(f"  Energy:    {energy:.4f}")

        # Save segment to file
        save_segment_to_wav(segment, SAMPLE_RATE, OUTPUT_DIR, segment_counter[0])

    # Start service
    print(f"\nStarting AudioService...")
    print(f"  Sample rate:      {SAMPLE_RATE} Hz")
    print(f"  VAD threshold:    0.5")
    print(f"  Min speech:       250ms")
    print(f"  Min silence:      300ms")
    print(f"  Buffer capacity:  10.0s")
    print()

    service.start(segment_callback=on_segment_detected)

    if not service.is_running():
        print("ERROR: Service failed to start!")
        return

    print(f"Service running. Capturing for {CAPTURE_DURATION} seconds...")
    print("Please speak or play audio for speech detection!")
    print()

    # Run for specified duration
    for i in range(CAPTURE_DURATION):
        time.sleep(1.0)
        print(f"  [{i+1}/{CAPTURE_DURATION}s] Listening...", end='\r')

    print(f"\n\nStopping service...")
    service.stop()

    # Print final metrics
    metrics = service.get_metrics()
    print("\n" + "="*70)
    print("FINAL STATISTICS")
    print("="*70)
    print(f"Chunks captured:      {metrics['chunks_captured']}")
    print(f"Chunks processed:     {metrics['chunks_processed']}")
    print(f"Segments detected:    {metrics['segments_detected']}")
    print(f"Total speech:         {metrics['total_speech_duration']:.2f}s")
    print(f"Speech ratio:         {metrics['vad_speech_ratio']:.1%}")
    print(f"Errors:               {metrics['errors']}")
    print("="*70)

    # Summary
    if len(segments) > 0:
        print(f"\nDetected {len(segments)} speech segments:")
        for i, seg in enumerate(segments, 1):
            duration = len(seg) / SAMPLE_RATE
            print(f"  Segment {i}: {duration:.2f}s")

        print(f"\nSegments saved to: {OUTPUT_DIR.absolute()}")
    else:
        print("\nNo speech segments detected.")
        print("Try speaking louder or playing audio with speech content.")

    print("\nExample completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
