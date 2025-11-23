"""
SpeakerDiarization for identifying and segmenting speakers in audio files.

This module provides functionality to perform speaker diarization using
pyannote-audio, identifying "who spoke when" in audio recordings.
"""

import logging
from typing import List, Dict, Optional, Union, Tuple
from pathlib import Path
import warnings

try:
    from pyannote.audio import Pipeline
    import torch
except ImportError as e:
    raise ImportError(
        "pyannote-audio and torch are required. "
        "Install with: pip install pyannote-audio torch"
    ) from e


logger = logging.getLogger(__name__)


class SpeakerSegment:
    """
    Represents a speaker segment in an audio file.

    Attributes:
        start (float): Start time in seconds
        end (float): End time in seconds
        speaker (str): Speaker label (e.g., "SPEAKER_00")
        duration (float): Duration of the segment in seconds
    """

    def __init__(self, start: float, end: float, speaker: str):
        """
        Initialize a speaker segment.

        Args:
            start: Start time in seconds
            end: End time in seconds
            speaker: Speaker label
        """
        self.start = start
        self.end = end
        self.speaker = speaker
        self.duration = end - start

    def __repr__(self) -> str:
        return f"SpeakerSegment(start={self.start:.2f}s, end={self.end:.2f}s, speaker={self.speaker}, duration={self.duration:.2f}s)"

    def to_dict(self) -> Dict:
        """Convert segment to dictionary representation."""
        return {
            "start": self.start,
            "end": self.end,
            "speaker": self.speaker,
            "duration": self.duration
        }

    def overlaps_with(self, other: "SpeakerSegment") -> bool:
        """
        Check if this segment overlaps with another segment.

        Args:
            other: Another SpeakerSegment

        Returns:
            True if segments overlap, False otherwise
        """
        return not (self.end <= other.start or self.start >= other.end)


class SpeakerDiarization:
    """
    Perform speaker diarization on audio files using pyannote-audio.

    This class uses pre-trained models to identify different speakers and
    segment audio based on speaker turns.

    Attributes:
        pipeline: Initialized pyannote Pipeline instance
        use_auth_token: HuggingFace authentication token for model access
        device: Device to run inference on (cuda/cpu)
    """

    # Default model from pyannote (requires HuggingFace token)
    DEFAULT_MODEL = "pyannote/speaker-diarization-3.1"

    def __init__(
        self,
        use_auth_token: Optional[str] = None,
        model_name: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        Initialize the SpeakerDiarization pipeline.

        Args:
            use_auth_token: HuggingFace authentication token.
                           Required for accessing pyannote models.
                           Get token at: https://huggingface.co/settings/tokens
            model_name: Name of the diarization model to use.
                       Defaults to "pyannote/speaker-diarization-3.1"
            device: Device to run on ("cuda", "cpu", or None for auto-detect)

        Raises:
            RuntimeError: If model loading fails
            ValueError: If auth token is missing when required

        Note:
            You must accept the user conditions for pyannote models at:
            https://huggingface.co/pyannote/speaker-diarization-3.1
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.use_auth_token = use_auth_token

        # Auto-detect device if not specified
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        logger.info(f"Initializing SpeakerDiarization with model: {self.model_name}")
        logger.info(f"Using device: {self.device}")

        try:
            # Load the diarization pipeline
            # Note: This will download the model on first use
            self.pipeline = Pipeline.from_pretrained(
                self.model_name,
                use_auth_token=self.use_auth_token
            )

            # Move to specified device
            if self.device == "cuda" and torch.cuda.is_available():
                self.pipeline = self.pipeline.to(torch.device("cuda"))
                logger.info("Pipeline moved to CUDA")
            else:
                logger.info("Pipeline running on CPU")

            logger.info(f"Successfully loaded model: {self.model_name}")

        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            if "401" in str(e) or "authentication" in str(e).lower():
                raise ValueError(
                    "Authentication failed. Please provide a valid HuggingFace token. "
                    "Get your token at: https://huggingface.co/settings/tokens"
                ) from e
            raise RuntimeError(f"Model initialization failed: {e}") from e

    def diarize(
        self,
        audio_path: Union[str, Path],
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None
    ) -> List[SpeakerSegment]:
        """
        Perform speaker diarization on an audio file.

        Args:
            audio_path: Path to the audio file (supports WAV, MP3, etc.)
            num_speakers: Exact number of speakers (if known)
            min_speakers: Minimum number of speakers
            max_speakers: Maximum number of speakers

        Returns:
            List of SpeakerSegment objects representing speaker turns

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If diarization fails

        Example:
            >>> diarizer = SpeakerDiarization(use_auth_token="your_token")
            >>> segments = diarizer.diarize("meeting.wav", num_speakers=3)
            >>> for seg in segments:
            ...     print(f"{seg.speaker}: {seg.start:.1f}s - {seg.end:.1f}s")
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Processing audio file: {audio_path}")

        try:
            # Prepare pipeline parameters
            params = {}
            if num_speakers is not None:
                params["num_speakers"] = num_speakers
            if min_speakers is not None:
                params["min_speakers"] = min_speakers
            if max_speakers is not None:
                params["max_speakers"] = max_speakers

            # Run diarization
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")  # Suppress model warnings
                diarization = self.pipeline(str(audio_path), **params)

            # Convert pyannote output to SpeakerSegment objects
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segment = SpeakerSegment(
                    start=turn.start,
                    end=turn.end,
                    speaker=speaker
                )
                segments.append(segment)

            logger.info(f"Diarization complete: {len(segments)} segments identified")

            # Log speaker statistics
            speakers = set(seg.speaker for seg in segments)
            logger.info(f"Number of speakers detected: {len(speakers)}")

            return segments

        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            raise RuntimeError(f"Failed to diarize audio: {e}") from e

    def get_speaker_statistics(
        self,
        segments: List[SpeakerSegment]
    ) -> Dict[str, Dict]:
        """
        Calculate statistics for each speaker from diarization segments.

        Args:
            segments: List of SpeakerSegment objects

        Returns:
            Dictionary mapping speaker labels to their statistics

        Example:
            >>> stats = diarizer.get_speaker_statistics(segments)
            >>> for speaker, data in stats.items():
            ...     print(f"{speaker}: {data['total_time']:.1f}s, {data['num_turns']} turns")
        """
        stats = {}

        for segment in segments:
            speaker = segment.speaker

            if speaker not in stats:
                stats[speaker] = {
                    "num_turns": 0,
                    "total_time": 0.0,
                    "segments": []
                }

            stats[speaker]["num_turns"] += 1
            stats[speaker]["total_time"] += segment.duration
            stats[speaker]["segments"].append(segment.to_dict())

        # Calculate average turn duration
        for speaker in stats:
            avg_duration = stats[speaker]["total_time"] / stats[speaker]["num_turns"]
            stats[speaker]["avg_turn_duration"] = avg_duration

        return stats

    def merge_short_segments(
        self,
        segments: List[SpeakerSegment],
        min_duration: float = 0.5
    ) -> List[SpeakerSegment]:
        """
        Merge very short segments with adjacent segments from the same speaker.

        Args:
            segments: List of SpeakerSegment objects
            min_duration: Minimum duration threshold in seconds

        Returns:
            List of merged SpeakerSegment objects
        """
        if not segments:
            return []

        merged = []
        current = segments[0]

        for next_seg in segments[1:]:
            # Check if segments are from same speaker and close together
            if (current.speaker == next_seg.speaker and
                (next_seg.start - current.end) < 0.5):  # Gap threshold
                # Merge segments
                current = SpeakerSegment(
                    start=current.start,
                    end=next_seg.end,
                    speaker=current.speaker
                )
            else:
                # Only add if meets minimum duration
                if current.duration >= min_duration:
                    merged.append(current)
                current = next_seg

        # Add final segment
        if current.duration >= min_duration:
            merged.append(current)

        logger.info(f"Merged segments: {len(segments)} -> {len(merged)}")
        return merged

    def export_segments_to_rttm(
        self,
        segments: List[SpeakerSegment],
        output_path: Union[str, Path],
        audio_filename: str = "audio"
    ) -> None:
        """
        Export segments to RTTM format (Rich Transcription Time Marked).

        Args:
            segments: List of SpeakerSegment objects
            output_path: Path to output RTTM file
            audio_filename: Name of the audio file (for RTTM format)
        """
        output_path = Path(output_path)

        with open(output_path, "w") as f:
            for segment in segments:
                # RTTM format: SPEAKER <filename> 1 <start> <duration> <NA> <NA> <speaker> <NA> <NA>
                line = (
                    f"SPEAKER {audio_filename} 1 {segment.start:.3f} "
                    f"{segment.duration:.3f} <NA> <NA> {segment.speaker} <NA> <NA>\n"
                )
                f.write(line)

        logger.info(f"Exported {len(segments)} segments to {output_path}")

    def get_model_info(self) -> Dict:
        """
        Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
            "model_type": "PyAnnote Speaker Diarization"
        }


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("SpeakerDiarization Module - Testing")
    print("=" * 70)

    # Note: Actual usage requires HuggingFace token and audio file
    print("\nTo use this module, you need:")
    print("1. HuggingFace account and token from: https://huggingface.co/settings/tokens")
    print("2. Accept model conditions at: https://huggingface.co/pyannote/speaker-diarization-3.1")
    print("3. Audio file for processing")

    print("\nExample usage:")
    print("""
    from speaker_diarization import SpeakerDiarization

    # Initialize with your HuggingFace token
    diarizer = SpeakerDiarization(use_auth_token="your_hf_token_here")

    # Process audio file
    segments = diarizer.diarize("path/to/audio.wav", num_speakers=2)

    # Display results
    for seg in segments:
        print(f"{seg.speaker}: {seg.start:.2f}s - {seg.end:.2f}s ({seg.duration:.2f}s)")

    # Get speaker statistics
    stats = diarizer.get_speaker_statistics(segments)
    for speaker, data in stats.items():
        print(f"{speaker}: {data['total_time']:.1f}s total, {data['num_turns']} turns")
    """)

    # Test SpeakerSegment class
    print("\nTesting SpeakerSegment class:")
    seg1 = SpeakerSegment(0.0, 5.5, "SPEAKER_00")
    seg2 = SpeakerSegment(5.0, 10.0, "SPEAKER_01")

    print(f"Segment 1: {seg1}")
    print(f"Segment 2: {seg2}")
    print(f"Overlap: {seg1.overlaps_with(seg2)}")
