<p align="center">
  <h1 align="center">parlaconclaudio</h1>
  <p align="center"><strong>Talk to Claude with your voice. Dictate, listen, control.</strong></p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows%2011-0078D4?style=flat-square&logo=windows" alt="Windows 11">
  <img src="https://img.shields.io/badge/python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/GPU-NVIDIA%20CUDA-76B900?style=flat-square&logo=nvidia" alt="NVIDIA CUDA">
  <img src="https://img.shields.io/badge/STT-Whisper%20large--v3-FF6F00?style=flat-square" alt="Whisper large-v3">
  <img src="https://img.shields.io/badge/TTS-edge--tts-00A4EF?style=flat-square&logo=microsoft" alt="edge-tts">
  <img src="https://img.shields.io/badge/built%20with-Claude%20Code-7C3AED?style=flat-square" alt="Built with Claude Code">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License">
</p>

---

**[English](#english)** | **[Italiano](#italiano)** | **[Portugues BR](#portugues-br)**

---

# English

## What is parlaconclaudio?

A local voice bridge for **Claude Code** on Windows. Two components:

1. **Voice Bridge (STT)** - Press `Ctrl+Alt+Space`, speak, and your words are transcribed locally on your GPU (Whisper large-v3) and pasted into the active terminal. No cloud, no latency.

2. **TTS Notifications** - A Claude Code hook that announces task completions, permission requests, and status changes with natural voices (edge-tts). Walk away from the screen and still know what Claude is doing.

## Architecture

```
Voice Bridge (STT)
  Ctrl+Alt+Space -> Microphone -> Whisper (GPU) -> Clipboard + Ctrl+V -> Terminal

TTS Notifications
  Claude Code Hook -> notify-tts.py -> Chime + edge-tts voice announcement
```

## Prerequisites

- Windows 10/11
- NVIDIA GPU with CUDA support
- Python 3.11+
- FFmpeg (`ffplay` in PATH)
- Claude Code CLI

## Installation

```bash
git clone https://github.com/fra-itc/parlaconclaudio.git
cd parlaconclaudio

python -m venv venv
.\venv\Scripts\activate

# Core dependencies
pip install faster-whisper pynput pyperclip pyaudio pystray Pillow pywin32

# CUDA support
pip install nvidia-cudnn-cu12 nvidia-cublas-cu12

# TTS
pip install edge-tts
```

## Configure Claude Code Hooks

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [{ "hooks": [{ "type": "command", "command": "python C:/PROJECTS/parlaconclaudio/scripts/notify-tts.py", "timeout": 10 }] }],
    "Notification": [{ "hooks": [{ "type": "command", "command": "python C:/PROJECTS/parlaconclaudio/scripts/notify-tts.py", "timeout": 10 }] }]
  }
}
```

## Launch

```bash
# Option 1: Batch file
.\VoiceBridge.bat

# Option 2: Direct
.\venv\Scripts\python.exe -m src.voice_bridge
```

## Project Structure

```
src/voice_bridge/       # STT Bridge
  bridge.py             # State machine: IDLE -> RECORDING -> TRANSCRIBING -> OUTPUT
  config.py             # Configuration
  hotkey_listener.py    # Ctrl+Alt+Space hotkey
  audio_recorder.py     # Microphone capture (PortAudio)
  transcriber.py        # Whisper wrapper
  output_handler.py     # Clipboard + Win32 paste
  sounds.py             # Audio feedback
  tray_icon.py          # Animated system tray icon + settings menu

src/core/
  stt_engine/
    whisper_rtx.py      # FasterWhisper on CUDA
    model_setup.py      # Model download/cache
  audio_capture/
    drivers/
      portaudio_driver.py

scripts/
  notify-tts.py         # Claude Code TTS hook (standalone)
```

---

# Italiano

## Cos'e parlaconclaudio?

Un bridge vocale locale per **Claude Code** su Windows. Due componenti:

1. **Voice Bridge (STT)** - Premi `Ctrl+Alt+Space`, parla, e le tue parole vengono trascritte localmente sulla GPU (Whisper large-v3) e incollate nel terminale attivo. Nessun cloud, nessuna latenza.

2. **Notifiche TTS** - Un hook di Claude Code che annuncia il completamento dei task, richieste di permesso e cambi di stato con voci naturali (edge-tts). Puoi allontanarti dallo schermo e sapere comunque cosa sta facendo Claude.

## Prerequisiti

- Windows 10/11
- GPU NVIDIA con supporto CUDA
- Python 3.11+
- FFmpeg (`ffplay` nel PATH)
- Claude Code CLI

## Installazione

```bash
git clone https://github.com/fra-itc/parlaconclaudio.git
cd parlaconclaudio

python -m venv venv
.\venv\Scripts\activate

pip install faster-whisper pynput pyperclip pyaudio pystray Pillow pywin32
pip install nvidia-cudnn-cu12 nvidia-cublas-cu12
pip install edge-tts
```

## Avvio

```bash
.\VoiceBridge.bat
# oppure
.\venv\Scripts\python.exe -m src.voice_bridge
```

---

# Portugues BR

## O que e parlaconclaudio?

Um bridge vocal local para o **Claude Code** no Windows. Dois componentes:

1. **Voice Bridge (STT)** - Pressione `Ctrl+Alt+Space`, fale, e suas palavras sao transcritas localmente na GPU (Whisper large-v3) e coladas no terminal ativo. Sem nuvem, sem latencia.

2. **Notificacoes TTS** - Um hook do Claude Code que anuncia conclusoes de tarefas, pedidos de permissao e mudancas de status com vozes naturais (edge-tts).

## Pre-requisitos

- Windows 10/11
- GPU NVIDIA com suporte CUDA
- Python 3.11+
- FFmpeg (`ffplay` no PATH)
- Claude Code CLI

## Instalacao

```bash
git clone https://github.com/fra-itc/parlaconclaudio.git
cd parlaconclaudio

python -m venv venv
.\venv\Scripts\activate

pip install faster-whisper pynput pyperclip pyaudio pystray Pillow pywin32
pip install nvidia-cudnn-cu12 nvidia-cublas-cu12
pip install edge-tts
```

## Executar

```bash
.\VoiceBridge.bat
# ou
.\venv\Scripts\python.exe -m src.voice_bridge
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

Built with **[Claude Code](https://claude.ai/claude-code)** by [Anthropic](https://anthropic.com).
