# Audio Test Fixtures

This directory contains audio samples and fixtures used for testing the real-time audio processing pipeline.

## Directory Structure

```
audio/
├── samples/          # Pre-recorded or manually added test samples
├── generated/        # Programmatically generated audio files
└── README.md         # This file
```

## Audio Format Requirements

All audio files used for testing must conform to the following specifications:

- **Sample Rate:** 16 kHz (16000 Hz)
- **Bit Depth:** 16-bit signed integer (PCM)
- **Channels:** Mono (1 channel)
- **Format:** WAV (uncompressed)
- **Encoding:** Linear PCM

## Fixture Categories

### 1. Speech Samples
Audio containing clear human speech for transcription testing.

**Use cases:**
- STT accuracy validation
- VAD detection with speech
- End-to-end pipeline testing
- Latency benchmarking

**Required samples:**
- `speech_5s.wav` - 5 second clear speech sample
- `speech_multilingual.wav` - Multiple languages for i18n testing
- `speech_with_noise.wav` - Speech with background noise

### 2. Silence Samples
Pure silence for negative testing and VAD validation.

**Use cases:**
- VAD false positive testing
- Buffer handling with no audio
- Timeout and idle state testing

**Required samples:**
- `silence_2s.wav` - 2 second complete silence
- `silence_10s.wav` - 10 second silence for long duration tests

### 3. Noise Samples
Various types of noise for robustness testing.

**Use cases:**
- VAD rejection testing
- Noise filtering validation
- Edge case handling

**Required samples:**
- `noise_3s.wav` - White noise sample
- `noise_pink.wav` - Pink noise for realistic background
- `noise_ambient.wav` - Ambient office/home sounds

### 4. Mixed Content
Audio with alternating speech, silence, and noise.

**Use cases:**
- VAD transition testing
- Real-world scenario simulation
- Buffer management with varying content

**Required samples:**
- `mixed_speech_silence.wav` - Speech → Silence → Speech
- `mixed_conversation.wav` - Simulated multi-turn conversation
- `mixed_realistic.wav` - Natural speech with pauses and background

### 5. Edge Cases
Challenging audio for stress testing.

**Use cases:**
- Error handling validation
- Extreme condition testing
- Security and stability testing

**Samples:**
- `empty_0s.wav` - Zero-length audio file
- `very_quiet.wav` - Extremely low volume speech
- `very_loud.wav` - High amplitude audio (clipping test)
- `rapid_speech.wav` - Fast speech for latency testing

## Generating Fixtures

Use the `tests/utils/audio_generator.py` utility to generate synthetic audio:

```python
from tests.utils.audio_generator import AudioGenerator

gen = AudioGenerator(sample_rate=16000)

# Generate a 5-second sine wave at 440 Hz (test tone)
gen.generate_sine_wave(duration=5.0, frequency=440, filename="test_tone.wav")

# Generate 2 seconds of silence
gen.generate_silence(duration=2.0, filename="silence_2s.wav")

# Generate 3 seconds of white noise
gen.generate_white_noise(duration=3.0, filename="noise_3s.wav")
```

## Loading Fixtures in Tests

Use the `tests/utils/audio_loader.py` utility to load and prepare audio:

```python
from tests.utils.audio_loader import AudioLoader

loader = AudioLoader()

# Load and validate audio file
audio_data = loader.load_wav("samples/speech_5s.wav")

# Convert to required format
audio_data = loader.ensure_format(audio_data, target_rate=16000)

# Normalize audio levels
audio_data = loader.normalize(audio_data)

# Chunk audio for streaming tests (100ms chunks)
chunks = loader.chunk_audio(audio_data, chunk_duration_ms=100)
```

## Adding New Fixtures

When adding new audio fixtures:

1. Ensure audio meets format requirements (16 kHz, 16-bit PCM, mono)
2. Place in appropriate category folder
3. Keep file sizes reasonable (< 10 MB per file)
4. Add entry to this README with description
5. Consider adding both `samples/` (manual) and `generated/` (synthetic) versions

## Fixture Validation

Run fixture validation to ensure all audio meets requirements:

```bash
pytest tests/unit/test_audio_format.py::test_fixture_validation -v
```

## License and Attribution

- Generated audio: Created synthetically, no attribution required
- Sample audio: Ensure proper licensing for any third-party samples
- User recordings: Use only with explicit permission for testing purposes
