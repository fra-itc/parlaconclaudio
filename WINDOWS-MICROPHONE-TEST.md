# Windows Microphone Testing Guide

## Quick Start

On your Windows 11 host machine, run:

```cmd
test_windows_microphone.bat
```

This will:

1. Check for Python and install PyAudio if needed
2. List available microphones
3. Check backend connectivity
4. Start a 30-second live microphone test
5. Display real-time transcriptions

## Manual Testing

### Step 1: Install Dependencies (First Time Only)

Open PowerShell or Command Prompt:

```cmd
# Install PyAudio for microphone access
pip install pyaudio websockets

# Verify installation
python -c "import pyaudio; print('PyAudio installed successfully')"
```

### Step 2: Ensure Backend is Running

Make sure Docker containers are running:

```cmd
# In WSL2 or via Docker Desktop
docker-compose up -d

# Wait for services to be healthy (60 seconds)
docker-compose ps
```

You should see all services showing "Up (healthy)".

### Step 3: List Available Microphones

```cmd
python -c "from src.core.audio_capture.audio_factory import create_audio_capture; driver = create_audio_capture(driver='portaudio'); devices = driver.list_devices(); [print(f'{i}: {d.name}') for i, d in enumerate(devices)]"
```

### Step 4: Test with Default Microphone

```cmd
# 30-second test
python -m src.host_audio_bridge.main ^
    --driver portaudio ^
    --test-duration 30 ^
    --log-level INFO
```

**Now speak into your microphone!** You should see:

- ✅ "Connected to backend"
- ✅ "Audio capture started"
- 📝 Real-time transcriptions appearing every few seconds

### Step 5: Test with Specific Microphone

If you have multiple microphones:

```cmd
# Use microphone device ID (from Step 3)
python -m src.host_audio_bridge.main ^
    --driver portaudio ^
    --device-id 1 ^
    --test-duration 30 ^
    --log-level INFO
```

## Advanced Options

### Longer Recording Session

```cmd
# 5-minute session
python -m src.host_audio_bridge.main --driver portaudio --test-duration 300
```

### Continuous Recording (No Time Limit)

```cmd
# Run until Ctrl+C
python -m src.host_audio_bridge.main --driver portaudio
```

### Adjust Audio Settings

```cmd
# Higher quality: 48kHz sample rate
python -m src.host_audio_bridge.main ^
    --driver portaudio ^
    --sample-rate 48000 ^
    --channels 1 ^
    --chunk-size 8192
```

### Debug Mode

```cmd
# Show detailed logs
python -m src.host_audio_bridge.main ^
    --driver portaudio ^
    --log-level DEBUG
```

## Troubleshooting

### Issue: "PyAudio not installed"

**Solution:**

```cmd
pip install pyaudio
```

If that fails on Windows, try:

```cmd
pip install pipwin
pipwin install pyaudio
```

### Issue: "Connection refused on port 8000"

**Solution:**

```cmd
# Check if backend is running
curl http://localhost:8000/health

# If not running, start it
docker-compose up -d backend

# Wait 30 seconds for it to become healthy
docker-compose logs backend
```

### Issue: "No default input device"

**Solution:**

1. Open Windows Sound Settings
2. Go to "Sound Control Panel" → "Recording"
3. Enable your microphone and set it as default
4. Test by speaking in the "Levels" tab

### Issue: "Permission denied" for microphone

**Solution:**

1. Windows Settings → Privacy → Microphone
2. Enable "Allow apps to access your microphone"
3. Enable for Python/Command Prompt

### Issue: Empty transcriptions

**Possible causes:**

- Speaking too quietly → Adjust microphone levels in Windows
- Microphone muted → Check Windows sound settings
- Wrong microphone selected → Use `--device-id` to specify
- Background noise → Test in quieter environment

**Verify microphone is working:**

```cmd
# Windows Sound Recorder test
soundrecorder
```

## What to Expect

### Successful Test Output

```
============================================================
  RTSTT Audio Bridge Service
  Host-to-Backend Audio Streaming
============================================================

2025-11-23 20:00:00 - INFO - AudioBridge initialized: ws://localhost:8000/ws
2025-11-23 20:00:00 - INFO - Starting Audio Bridge
2025-11-23 20:00:00 - INFO -   WebSocket: ws://localhost:8000/ws
2025-11-23 20:00:00 - INFO -   Driver: portaudio
2025-11-23 20:00:00 - INFO -   Sample Rate: 16000Hz
2025-11-23 20:00:00 - INFO -   Channels: 1
2025-11-23 20:00:00 - INFO - Initializing audio capture...
2025-11-23 20:00:00 - INFO - ✅ Audio driver initialized: PortAudioDriver
2025-11-23 20:00:00 - INFO - ✅ Connected to backend
2025-11-23 20:00:00 - INFO - ✅ Audio capture started

[Speak now...]

2025-11-23 20:00:03 - INFO - 📝 Transcription: 'Hello, this is a test of the real-time speech recognition system.' (latency: 287ms)
2025-11-23 20:00:05 - INFO - 📝 Transcription: 'The microphone is working perfectly.' (latency: 265ms)
2025-11-23 20:00:08 - INFO - 📝 Transcription: 'Transcriptions appear in near real-time.' (latency: 311ms)

...

============================================================
Bridge Statistics:
  Uptime: 30.2s
  Chunks sent: 15
  Bytes sent: 983,040
  Throughput: 0.26 Mbps
  Reconnections: 0
  Errors: 0
============================================================
```

### Performance Expectations

- **Latency:** 250-350ms from speech to transcription
- **Accuracy:** 90-95% for clear speech
- **Throughput:** ~0.3 Mbps for 16kHz mono audio
- **Stability:** Zero reconnections for typical sessions

## Architecture

```
Windows Host                    Docker Container (WSL2/Linux)
┌─────────────────┐            ┌──────────────────────────┐
│                 │            │                          │
│  Microphone     │            │  Backend (FastAPI)       │
│      ↓          │            │         ↓                │
│  PortAudio      │  WebSocket │  WebSocket Gateway       │
│      ↓          │───────────→│         ↓                │
│  Audio Bridge   │  ws://8000 │  STT Engine (gRPC)       │
│      ↓          │            │         ↓                │
│  Capture Loop   │            │  NLP Service (gRPC)      │
│      ↓          │            │         ↓                │
│  Send Chunks    │            │  Summary Service (gRPC)  │
│                 │            │         ↓                │
│                 │    ←───────┤  Transcription Response  │
│  Display Result │            │                          │
└─────────────────┘            └──────────────────────────┘
```

## Next Steps

After successful microphone testing:

1. **Test with different speech:**
   
   - Normal conversation
   - Technical terms
   - Different accents
   - Background noise scenarios

2. **Check NLP insights:**
   
   - View backend logs: `docker-compose logs backend | grep "NLP"`
   - Keywords should be extracted from transcriptions

3. **Test summary generation:**
   
   - Speak for 2-3 minutes continuously
   - Check backend logs for summary: `docker-compose logs backend | grep "Summary"`

4. **Frontend integration:**
   
   - Start desktop UI: `cd src/ui/desktop && npm start`
   - See transcriptions in the UI in real-time

5. **Multi-user testing:**
   
   - Open multiple terminals
   - Run audio bridge in each
   - Verify concurrent transcriptions work

## Support

If you encounter issues:

1. Check Docker logs: `docker-compose logs`
2. Verify network connectivity: `curl http://localhost:8000/health`
3. Test with mock driver first: `--driver mock --pattern sine`
4. Review LIVE-TEST-RESULTS.md for known issues

For more details, see:

- `DEPLOYMENT.md` - Full deployment guide
- `WAVE-2-QUICKSTART.md` - Wave 2 features
- `STRATEGIC-ROADMAP-WAVE4.md` - Future enhancements
