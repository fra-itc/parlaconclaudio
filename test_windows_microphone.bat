@echo off
REM Windows Microphone Test Script
REM Tests real microphone input with the RTSTT system

REM Change to the script's directory (project root)
cd /d "%~dp0"

echo ======================================================================
echo   RTSTT Windows Microphone Test
echo   Real-time Speech Recognition with Live Microphone
echo ======================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

REM Check if PyAudio is installed
python -c "import pyaudio" >nul 2>&1
if %errorlevel% neq 0 (
    echo PyAudio not installed. Installing now...
    pip install pyaudio
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install PyAudio
        echo Try manual install: pip install pyaudio
        pause
        exit /b 1
    )
)

REM Check if websockets is installed
python -c "import websockets" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing websockets...
    pip install websockets
)

echo.
echo [1/3] Checking available microphones...
echo.
python -c "from src.core.audio_capture.audio_factory import create_audio_capture; driver = create_audio_capture(driver='portaudio'); devices = driver.list_devices(); print(f'\nFound {len(devices)} microphone(s):'); [print(f'  [{i}] {d.name} {\"(DEFAULT)\" if d.is_default else \"\"}') for i, d in enumerate(devices)]"

echo.
echo [2/3] Checking backend status...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Backend not responding on port 8000
    echo Make sure Docker containers are running: docker-compose up -d
    echo.
    pause
)

echo Backend is ready!
echo.
echo [3/3] Starting live microphone test...
echo.
echo ==================================================
echo   SPEAK INTO YOUR MICROPHONE NOW
echo   Test will run for 30 seconds
echo   Transcriptions will appear in real-time
echo ==================================================
echo.

python -m src.host_audio_bridge.main --driver portaudio --test-duration 30 --log-level INFO

echo.
echo ======================================================================
echo Test complete! Check the output above for transcriptions.
echo ======================================================================
pause
