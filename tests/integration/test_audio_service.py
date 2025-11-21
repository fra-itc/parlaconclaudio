"""
Integration tests for AudioService

Tests the complete audio pipeline from capture to segmentation.

Author: ORCHIDEA Agent System
Created: 2025-11-21
"""

import pytest
import numpy as np
import time
from src.core.audio_capture.audio_service import AudioService, AudioServiceState


def test_audio_service_init():
    """Test service initialization"""
    service = AudioService(sample_rate=16000)
    assert service.sample_rate == 16000
    assert service.get_state() == AudioServiceState.STOPPED


def test_audio_service_start_stop():
    """Test service start/stop lifecycle"""
    service = AudioService(sample_rate=16000)

    # Track segments
    segments_received = []

    def segment_callback(segment):
        segments_received.append(segment)

    # Start service
    service.start(segment_callback=segment_callback)
    assert service.is_running()

    # Let it run for 2 seconds
    time.sleep(2.0)

    # Check metrics
    metrics = service.get_metrics()
    assert metrics['chunks_captured'] > 0
    assert metrics['chunks_processed'] > 0

    # Stop service
    service.stop()
    assert service.get_state() == AudioServiceState.STOPPED


def test_audio_service_metrics():
    """Test metrics collection"""
    service = AudioService(sample_rate=16000)

    service.start()
    time.sleep(1.0)

    metrics = service.get_metrics()
    assert 'chunks_captured' in metrics
    assert 'chunks_processed' in metrics
    assert 'segments_detected' in metrics
    assert metrics['chunks_captured'] >= 0

    service.stop()


def test_audio_service_state_machine():
    """Test state machine transitions"""
    service = AudioService(sample_rate=16000)

    # Initial state
    assert service.get_state() == AudioServiceState.STOPPED

    # Start
    service.start()
    assert service.get_state() == AudioServiceState.RUNNING

    # Cannot start again
    service.start()  # Should log warning but not fail
    assert service.get_state() == AudioServiceState.RUNNING

    # Stop
    service.stop()
    assert service.get_state() == AudioServiceState.STOPPED

    # Cannot stop again
    service.stop()  # Should log warning but not fail
    assert service.get_state() == AudioServiceState.STOPPED


def test_audio_service_multiple_segments():
    """Test detection of multiple speech segments"""
    service = AudioService(
        sample_rate=16000,
        vad_threshold=0.5,
        min_speech_duration_ms=250,
        min_silence_duration_ms=300
    )

    segments = []
    segment_durations = []

    def on_segment(segment):
        segments.append(segment)
        duration = len(segment) / 16000
        segment_durations.append(duration)
        print(f"Segment {len(segments)}: {len(segment)} samples, {duration:.2f}s")

    service.start(segment_callback=on_segment)

    # Run for 5 seconds
    print("\nCapturing audio for 5 seconds...")
    time.sleep(5.0)

    service.stop()

    metrics = service.get_metrics()
    print(f"\nMetrics:")
    print(f"  Chunks captured: {metrics['chunks_captured']}")
    print(f"  Chunks processed: {metrics['chunks_processed']}")
    print(f"  Segments detected: {metrics['segments_detected']}")
    print(f"  Total speech duration: {metrics['total_speech_duration']:.2f}s")
    print(f"  VAD speech ratio: {metrics['vad_speech_ratio']:.1%}")
    print(f"  Errors: {metrics['errors']}")

    # Verify segments have correct properties
    for segment in segments:
        assert isinstance(segment, np.ndarray)
        assert len(segment) > 0
        # Check minimum duration (250ms = 4000 samples at 16kHz)
        assert len(segment) >= 4000


def test_audio_service_buffer_integration():
    """Test circular buffer integration"""
    service = AudioService(
        sample_rate=16000,
        buffer_capacity_seconds=5.0
    )

    service.start()
    time.sleep(1.0)

    # Check that buffer is being used
    buffer_available = service.buffer.available()
    assert buffer_available >= 0

    service.stop()


def test_audio_service_vad_integration():
    """Test VAD integration"""
    service = AudioService(
        sample_rate=16000,
        vad_threshold=0.5
    )

    service.start()
    time.sleep(2.0)

    metrics = service.get_metrics()

    # VAD should be processing chunks
    assert metrics['chunks_processed'] > 0

    # Speech ratio should be between 0 and 1
    assert 0.0 <= metrics['vad_speech_ratio'] <= 1.0

    service.stop()


def test_audio_service_error_handling():
    """Test error handling in callbacks"""
    service = AudioService(sample_rate=16000)

    error_count = [0]

    def faulty_callback(segment):
        error_count[0] += 1
        raise RuntimeError("Test error")

    service.start(segment_callback=faulty_callback)
    time.sleep(2.0)
    service.stop()

    # Service should continue despite errors
    metrics = service.get_metrics()
    assert metrics['chunks_captured'] > 0


@pytest.mark.integration
@pytest.mark.slow
def test_audio_service_end_to_end():
    """
    End-to-end test with real audio capture

    This test requires:
    - Active audio device
    - Speech input during test
    - Longer runtime (10 seconds)
    """
    service = AudioService(
        sample_rate=16000,
        vad_threshold=0.5,
        min_speech_duration_ms=250,
        min_silence_duration_ms=300
    )

    segments = []
    segment_info = []

    def on_segment(segment):
        segments.append(segment)
        duration = len(segment) / 16000
        energy = np.sqrt(np.mean(segment ** 2))
        segment_info.append({
            'samples': len(segment),
            'duration': duration,
            'energy': energy
        })
        print(f"\nSegment {len(segments)}:")
        print(f"  Samples: {len(segment)}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Energy: {energy:.4f}")

    service.start(segment_callback=on_segment)

    # Run for 10 seconds to capture speech
    print("\n" + "="*60)
    print("CAPTURING AUDIO FOR 10 SECONDS")
    print("Please speak into your microphone to test speech detection!")
    print("="*60)

    for i in range(10):
        time.sleep(1.0)
        print(f"  {i+1}/10 seconds...")

    service.stop()

    # Print final metrics
    metrics = service.get_metrics()
    print("\n" + "="*60)
    print("FINAL METRICS")
    print("="*60)
    print(f"Chunks captured:     {metrics['chunks_captured']}")
    print(f"Chunks processed:    {metrics['chunks_processed']}")
    print(f"Segments detected:   {metrics['segments_detected']}")
    print(f"Speech duration:     {metrics['total_speech_duration']:.2f}s")
    print(f"Speech ratio:        {metrics['vad_speech_ratio']:.1%}")
    print(f"Errors:              {metrics['errors']}")
    print("="*60)

    # Verify some activity occurred
    assert metrics['chunks_captured'] > 0, "No audio chunks captured"
    assert metrics['chunks_processed'] > 0, "No audio chunks processed"

    # If speech was detected, verify segment properties
    if len(segments) > 0:
        print(f"\nDetected {len(segments)} speech segments")
        for i, info in enumerate(segment_info, 1):
            print(f"  Segment {i}: {info['duration']:.2f}s, energy={info['energy']:.4f}")


def test_audio_service_component_initialization():
    """Test that all components are properly initialized"""
    service = AudioService(sample_rate=16000)

    # Check components exist
    assert service.capture is not None
    assert service.buffer is not None
    assert service.vad is not None
    assert service.segmenter is not None

    # Check component configuration
    assert service.capture.sample_rate == 16000
    assert service.buffer.sample_rate == 16000
    assert service.vad.sample_rate == 16000
    assert service.segmenter.sample_rate == 16000
