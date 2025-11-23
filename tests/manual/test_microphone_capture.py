"""
Manual Microphone Capture Test

Interactive test script for real-time microphone audio capture.
Tests live microphone input, audio levels, VAD detection, and saves output for verification.

Usage:
    python -m tests.manual.test_microphone_capture [OPTIONS]

Options:
    --duration SECONDS    Recording duration (default: 5)
    --output FILEPATH     Output WAV file path (default: test_output/mic_test.wav)
    --show-levels         Display real-time audio levels
    --show-vad            Display VAD (Voice Activity Detection) results
    --device-id ID        Specific device ID to use (default: None = default device)
    --sample-rate RATE    Sample rate in Hz (default: 16000)

Author: ORCHIDEA Agent System
Created: 2025-11-23
"""

import argparse
import sys
import time
import numpy as np
from pathlib import Path
from datetime import datetime
import wave

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.audio_capture.wasapi_capture import WASAPICapture
from src.core.audio_capture.vad_silero import SileroVAD


class MicrophoneTester:
    """Interactive microphone capture tester."""

    def __init__(
        self,
        duration: float = 5.0,
        output_file: str = "test_output/mic_test.wav",
        show_levels: bool = True,
        show_vad: bool = True,
        device_id: str = None,
        sample_rate: int = 16000
    ):
        """
        Initialize microphone tester.

        Args:
            duration: Recording duration in seconds
            output_file: Output WAV file path
            show_levels: Display real-time audio levels
            show_vad: Display VAD detection results
            device_id: Specific device ID (None = default device)
            sample_rate: Sample rate in Hz
        """
        self.duration = duration
        self.output_file = Path(output_file)
        self.show_levels = show_levels
        self.show_vad = show_vad
        self.device_id = device_id
        self.sample_rate = sample_rate

        # Storage for recorded audio
        self.recorded_chunks = []
        self.total_samples = 0
        self.speech_samples = 0
        self.start_time = None

        # Initialize components
        self.capture = None
        self.vad = None

    def setup(self):
        """Set up audio capture and VAD."""
        print("=" * 60)
        print("RTSTT Microphone Capture Test")
        print("=" * 60)
        print(f"Duration: {self.duration}s")
        print(f"Sample Rate: {self.sample_rate} Hz")
        print(f"Output File: {self.output_file}")
        print(f"Show Levels: {self.show_levels}")
        print(f"Show VAD: {self.show_vad}")
        print("-" * 60)

        # Create output directory
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize audio capture
        print("Initializing audio capture...")
        self.capture = WASAPICapture(
            device_id=self.device_id,
            sample_rate=self.sample_rate,
            channels=1,
            chunk_duration_ms=100
        )

        # Initialize VAD if requested
        if self.show_vad:
            print("Loading Silero VAD model...")
            try:
                self.vad = SileroVAD(
                    threshold=0.5,
                    sample_rate=self.sample_rate
                )
                print("✓ VAD model loaded")
            except Exception as e:
                print(f"⚠ Warning: Could not load VAD: {e}")
                self.show_vad = False
                self.vad = None

        print("✓ Setup complete")
        print("-" * 60)

    def audio_callback(self, audio_chunk: np.ndarray):
        """
        Callback for audio chunks.

        Args:
            audio_chunk: Audio data as numpy array
        """
        # Store chunk
        self.recorded_chunks.append(audio_chunk.copy())
        self.total_samples += len(audio_chunk)

        # Calculate audio levels
        if self.show_levels:
            rms = np.sqrt(np.mean(audio_chunk ** 2))
            peak = np.max(np.abs(audio_chunk))

            # Create visual level meter (0-50 chars)
            level_chars = int(rms * 50)
            level_bar = "█" * level_chars + "░" * (50 - level_chars)

            print(f"\rLevel: {level_bar} RMS: {rms:.3f} Peak: {peak:.3f}", end="")

        # VAD detection
        if self.show_vad and self.vad is not None:
            try:
                is_speech, confidence = self.vad.process_chunk(audio_chunk)

                if is_speech:
                    self.speech_samples += len(audio_chunk)

                # Visual VAD indicator
                vad_status = "🎤 SPEECH" if is_speech else "   silence"
                vad_bar = "█" * int(confidence * 20) + "░" * (20 - int(confidence * 20))

                if self.show_levels:
                    print(f" | VAD: {vad_bar} {confidence:.2f} {vad_status}", end="")
                else:
                    print(f"\rVAD: {vad_bar} {confidence:.2f} {vad_status}", end="")

            except Exception as e:
                if self.show_levels:
                    print(f" | VAD: Error - {e}", end="")

        # Check if duration exceeded
        elapsed = time.time() - self.start_time
        if elapsed >= self.duration:
            self.capture.stop()

    def run(self):
        """Run the microphone capture test."""
        print("\nStarting audio capture...")
        print("Speak into your microphone!")
        print("(Recording will stop automatically after duration)")
        print("-" * 60)

        # Start capture
        self.start_time = time.time()
        self.capture.start(callback=self.audio_callback)

        # Wait for completion
        while self.capture.is_running():
            time.sleep(0.1)

        print("\n" + "-" * 60)
        print("✓ Recording complete")

    def save_results(self):
        """Save recorded audio to file."""
        if not self.recorded_chunks:
            print("⚠ No audio recorded!")
            return

        # Concatenate all chunks
        audio_data = np.concatenate(self.recorded_chunks)

        # Convert to int16
        audio_int16 = np.int16(audio_data * 32767)

        # Save to WAV
        print(f"\nSaving audio to: {self.output_file}")
        with wave.open(str(self.output_file), 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        print(f"✓ Audio saved: {len(audio_data)} samples ({len(audio_data) / self.sample_rate:.2f}s)")

    def show_statistics(self):
        """Display capture statistics."""
        print("\n" + "=" * 60)
        print("CAPTURE STATISTICS")
        print("=" * 60)

        duration = self.total_samples / self.sample_rate
        print(f"Total Duration: {duration:.2f}s")
        print(f"Total Samples: {self.total_samples}")
        print(f"Sample Rate: {self.sample_rate} Hz")

        if self.show_vad and self.speech_samples > 0:
            speech_duration = self.speech_samples / self.sample_rate
            speech_percentage = (self.speech_samples / self.total_samples) * 100
            print(f"\nVAD Detection:")
            print(f"  Speech Duration: {speech_duration:.2f}s ({speech_percentage:.1f}%)")
            print(f"  Silence Duration: {duration - speech_duration:.2f}s")

        # Audio quality metrics
        if self.recorded_chunks:
            audio_data = np.concatenate(self.recorded_chunks)
            rms = np.sqrt(np.mean(audio_data ** 2))
            peak = np.max(np.abs(audio_data))

            print(f"\nAudio Quality:")
            print(f"  RMS Level: {rms:.4f}")
            print(f"  Peak Level: {peak:.4f}")

            if peak < 0.01:
                print("  ⚠ Warning: Very low audio levels - check microphone!")
            elif peak > 0.95:
                print("  ⚠ Warning: Audio may be clipping - reduce input level!")
            else:
                print("  ✓ Audio levels look good")

        print("=" * 60)

    def cleanup(self):
        """Clean up resources."""
        if self.capture and self.capture.is_running():
            self.capture.stop()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive microphone capture test for RTSTT"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Recording duration in seconds (default: 5)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="test_output/mic_test.wav",
        help="Output WAV file path (default: test_output/mic_test.wav)"
    )
    parser.add_argument(
        "--show-levels",
        action="store_true",
        default=True,
        help="Display real-time audio levels (default: True)"
    )
    parser.add_argument(
        "--show-vad",
        action="store_true",
        default=True,
        help="Display VAD detection results (default: True)"
    )
    parser.add_argument(
        "--device-id",
        type=str,
        default=None,
        help="Specific device ID to use (default: None = default device)"
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Sample rate in Hz (default: 16000)"
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio devices and exit"
    )

    args = parser.parse_args()

    # List devices if requested
    if args.list_devices:
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            print("Available Audio Devices:")
            print("-" * 60)
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                print(f"Device {i}: {info['name']}")
                print(f"  Max Input Channels: {info['maxInputChannels']}")
                print(f"  Default Sample Rate: {info['defaultSampleRate']}")
                print()
            p.terminate()
        except Exception as e:
            print(f"Error listing devices: {e}")
        return

    # Create tester
    tester = MicrophoneTester(
        duration=args.duration,
        output_file=args.output,
        show_levels=args.show_levels,
        show_vad=args.show_vad,
        device_id=args.device_id,
        sample_rate=args.sample_rate
    )

    try:
        # Run test
        tester.setup()
        tester.run()
        tester.save_results()
        tester.show_statistics()

        print("\n✓ Test completed successfully!")

    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
