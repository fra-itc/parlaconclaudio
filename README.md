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

**[English](#english)** | **[Portugues BR](#portugues-br)** | **[Italiano](#italiano)**

---

# English

## What is parlaconclaudio?

A voice interaction system for **Claude Code** (Anthropic's AI coding CLI) on Windows. It adds two capabilities that transform the coding experience:

1. **Voice Dictation** - Press `Ctrl+Alt+Space`, speak naturally, and your words are transcribed locally on your GPU and pasted into the active terminal. No cloud, no latency, no privacy concerns.

2. **Voice Notifications** - Two AI personas (Alessia & Claudio) announce task completions, permission requests, and status changes with natural-sounding voices. You can walk away from the screen and still know what Claude is doing.

3. **Animated Tray Control** - A mystical marble sphere in your system tray shifts colors based on state. Right-click for full settings: voice selection, language, volume, sound packs.

## Demo

> *Screenshots and demo video coming soon*

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Voice Bridge                          │
│                                                         │
│  Ctrl+Alt+Space ──> Microphone ──> Whisper (GPU)        │
│                                      │                  │
│                                      ▼                  │
│                              Transcribed Text            │
│                                      │                  │
│                                      ▼                  │
│                           Clipboard + Ctrl+V             │
│                           (pasted in terminal)           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  TTS Notifications                       │
│                                                         │
│  Claude Code Hook ──> notify-tts.py                     │
│                          │                              │
│                          ├──> Chime (R2-D2/SouthPark)   │
│                          │                              │
│                          └──> edge-tts Voice             │
│                               Alessia (subtasks)        │
│                               Claudio (main tasks)      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   Tray Icon                              │
│                                                         │
│  Animated marble sphere (PIL + pystray)                 │
│  🟢 Rainbow shift = Idle                                │
│  🔴 Red pulse = Recording                               │
│  🟡 Gold shimmer = Transcribing                         │
│                                                         │
│  Right-click menu:                                      │
│  ├── Whisper Language (Auto/IT/EN/PT/ES/FR/DE/JA)      │
│  ├── Quick Presets (5 voice combos)                     │
│  ├── Alessia Voice [by language] (47 voices)            │
│  ├── Claudio Voice [by language] (47 voices)            │
│  ├── Volume (50-300%)                                   │
│  ├── Sound Pack (R2-D2/South Park/American Dad)         │
│  ├── Preview sounds                                     │
│  └── Exit                                               │
└─────────────────────────────────────────────────────────┘
```

## Local STT Specifications

| Spec | Value |
|------|-------|
| **Model** | Whisper large-v3 |
| **Engine** | faster-whisper (CTranslate2 backend) |
| **GPU** | NVIDIA RTX 5080 (any CUDA GPU works) |
| **VRAM** | ~3 GB (float16) |
| **Inference** | ~1 second for 10-15s audio |
| **VAD** | Silero VAD (removes silence pre-transcription) |
| **Languages** | Auto-detect + IT, EN, PT, ES, FR, DE, JA |
| **Privacy** | 100% local - no audio leaves the machine |
| **Compute type** | float16 (CUDA) |
| **Beam size** | 5 |

## TTS Specifications

| Spec | Value |
|------|-------|
| **Engine** | edge-tts (Microsoft Edge Neural Voices) |
| **Cost** | Free |
| **Voices** | 47 across 8 languages |
| **Caching** | Dynamic MP3 cache by content hash |
| **Latency** | ~500ms first time, instant from cache |
| **Personas** | Alessia (subtasks, Italian) + Claudio (main, English) |

## Prerequisites

- Windows 10/11
- NVIDIA GPU with CUDA support
- Python 3.11+
- FFmpeg (`ffplay` in PATH)
- Claude Code CLI

## Installation

```bash
# Clone
git clone https://github.com/fra-itc/parlaconclaudio.git
cd parlaconclaudio

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install core dependencies
pip install faster-whisper pynput pyperclip pyaudio pystray Pillow

# Install CUDA support (cuDNN for CTranslate2)
pip install nvidia-cudnn-cu12 nvidia-cublas-cu12

# Fix transformers compatibility
pip install "transformers<4.45"

# Install TTS (system Python or venv)
pip install edge-tts
```

### Configure Claude Code Hooks

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python C:/Users/YOUR_USER/.claude/scripts/notify-tts.py",
        "timeout": 10,
        "async": true
      }]
    }],
    "Notification": [{
      "hooks": [{
        "type": "command",
        "command": "python C:/Users/YOUR_USER/.claude/scripts/notify-tts.py",
        "timeout": 10,
        "async": true
      }]
    }],
    "TaskCompleted": [{
      "hooks": [{
        "type": "command",
        "command": "python C:/Users/YOUR_USER/.claude/scripts/notify-tts.py",
        "timeout": 10,
        "async": true
      }]
    }]
  }
}
```

### Launch

```bash
# Option 1: Batch file
.\VoiceBridge.bat

# Option 2: Direct
.\venv\Scripts\python.exe -m src.voice_bridge.bridge
```

## Project Structure

```
src/voice_bridge/
  __init__.py            # NVIDIA DLL PATH setup for CUDA imports
  bridge.py              # State machine: IDLE -> RECORDING -> TRANSCRIBING -> OUTPUT
  config.py              # VoiceBridgeConfig dataclass
  hotkey_listener.py     # Global hotkey (toggle + push-to-talk modes)
  audio_recorder.py      # Microphone capture via PortAudio
  transcriber.py         # Whisper wrapper, reads config for language
  output_handler.py      # Clipboard + Win32 SendInput paste
  sounds.py              # Beep feedback (start/stop/output)
  tray_icon.py           # Animated marble sphere + full settings menu

src/core/
  stt_engine/
    whisper_rtx.py       # WhisperRTXEngine (faster-whisper on CUDA)
  audio_capture/
    drivers/
      portaudio_driver.py  # PortAudio microphone driver

scripts/
  notify-tts.py          # Claude Code hook handler (chime + TTS)
  tts-warmup.py          # Pre-generate common TTS phrases
```

## Tools Used During Development

| Tool | Purpose |
|------|---------|
| **Claude Code** (Anthropic CLI) | AI coding assistant that built this entire project |
| **Claude Opus 4.6** | The AI model powering all development |
| **Python 3.11** | Primary language |
| **faster-whisper** | Local Whisper inference (CTranslate2) |
| **edge-tts** | Microsoft Neural TTS voices (free) |
| **pynput** | Global keyboard hooks |
| **pystray + Pillow** | System tray with animated icon frames |
| **pyperclip** | Cross-platform clipboard |
| **PyAudio / PortAudio** | Microphone capture |
| **ffplay** (FFmpeg) | Audio playback (chimes + TTS) |
| **Win32 SendInput** (ctypes) | Keyboard simulation for auto-paste |
| **nvidia-cudnn-cu12** | CUDA Deep Neural Network library |
| **Git** | Version control on `stage` branch |

---

# Portugues BR

## O que e parlaconclaudio?

Um sistema de interacao por voz para o **Claude Code** (CLI de IA da Anthropic) no Windows. Adiciona duas capacidades que transformam a experiencia de programacao:

1. **Ditado por Voz** - Pressione `Ctrl+Alt+Space`, fale naturalmente, e suas palavras sao transcritas localmente na sua GPU e coladas no terminal ativo. Sem nuvem, sem latencia, sem preocupacoes com privacidade.

2. **Notificacoes por Voz** - Duas personas de IA (Alessia e Claudio) anunciam conclusoes de tarefas, pedidos de permissao e mudancas de status com vozes de som natural. Voce pode se afastar da tela e ainda saber o que o Claude esta fazendo.

3. **Controle no Tray Animado** - Uma esfera de marmore mistica no system tray muda de cor conforme o estado. Clique direito para configuracoes completas: selecao de voz, idioma, volume, pacotes de som.

## Especificacoes STT Local

| Spec | Valor |
|------|-------|
| **Modelo** | Whisper large-v3 |
| **Engine** | faster-whisper (backend CTranslate2) |
| **GPU** | NVIDIA RTX 5080 (qualquer GPU CUDA funciona) |
| **VRAM** | ~3 GB (float16) |
| **Inferencia** | ~1 segundo para 10-15s de audio |
| **VAD** | Silero VAD (remove silencio pre-transcricao) |
| **Idiomas** | Auto-detectar + IT, EN, PT, ES, FR, DE, JA |
| **Privacidade** | 100% local - nenhum audio sai da maquina |

## Especificacoes TTS

| Spec | Valor |
|------|-------|
| **Engine** | edge-tts (Vozes Neurais Microsoft Edge) |
| **Custo** | Gratis |
| **Vozes** | 47 em 8 idiomas |
| **Cache** | Cache dinamico MP3 por hash de conteudo |
| **Personas** | Alessia (subtarefas, italiano) + Claudio (principal, ingles) |

## Pre-requisitos

- Windows 10/11
- GPU NVIDIA com suporte CUDA
- Python 3.11+
- FFmpeg (`ffplay` no PATH)
- Claude Code CLI

## Instalacao

```bash
# Clonar
git clone https://github.com/fra-itc/parlaconclaudio.git
cd parlaconclaudio

# Criar ambiente virtual
python -m venv venv
.\venv\Scripts\activate

# Instalar dependencias principais
pip install faster-whisper pynput pyperclip pyaudio pystray Pillow

# Instalar suporte CUDA
pip install nvidia-cudnn-cu12 nvidia-cublas-cu12

# Corrigir compatibilidade do transformers
pip install "transformers<4.45"

# Instalar TTS
pip install edge-tts
```

### Executar

```bash
# Opcao 1: Arquivo batch
.\VoiceBridge.bat

# Opcao 2: Direto
.\venv\Scripts\python.exe -m src.voice_bridge.bridge
```

## Ferramentas Usadas no Desenvolvimento

| Ferramenta | Funcao |
|------------|--------|
| **Claude Code** (Anthropic CLI) | Assistente de IA que construiu todo o projeto |
| **Claude Opus 4.6** | Modelo de IA por tras de todo o desenvolvimento |
| **Python 3.11** | Linguagem principal |
| **faster-whisper** | Inferencia Whisper local (CTranslate2) |
| **edge-tts** | Vozes Neurais Microsoft (gratis) |
| **pynput** | Hooks de teclado globais |
| **pystray + Pillow** | Tray com icone animado |
| **PyAudio / PortAudio** | Captura de microfone |
| **ffplay** (FFmpeg) | Reproducao de audio |
| **Win32 SendInput** (ctypes) | Simulacao de teclado para auto-paste |
| **nvidia-cudnn-cu12** | Biblioteca CUDA Deep Neural Network |

---

# Italiano

## Cos'e parlaconclaudio?

Un sistema di interazione vocale per **Claude Code** (la CLI di IA di Anthropic) su Windows. Aggiunge due capacita' che trasformano l'esperienza di programmazione:

1. **Dettatura Vocale** - Premi `Ctrl+Alt+Space`, parla naturalmente, e le tue parole vengono trascritte localmente sulla GPU e incollate nel terminale attivo. Nessun cloud, nessuna latenza, nessun problema di privacy.

2. **Notifiche Vocali** - Due personaggi IA (Alessia e Claudio) annunciano il completamento dei task, richieste di permesso e cambi di stato con voci dal suono naturale. Puoi allontanarti dallo schermo e sapere comunque cosa sta facendo Claude.

3. **Controllo Tray Animato** - Una sfera di marmo mistica nel system tray cambia colore in base allo stato. Click destro per tutte le impostazioni: selezione voce, lingua, volume, pacchetti suoni.

## Specifiche STT Locale

| Spec | Valore |
|------|--------|
| **Modello** | Whisper large-v3 |
| **Engine** | faster-whisper (backend CTranslate2) |
| **GPU** | NVIDIA RTX 5080 (qualsiasi GPU CUDA funziona) |
| **VRAM** | ~3 GB (float16) |
| **Inferenza** | ~1 secondo per 10-15s di audio |
| **VAD** | Silero VAD (rimuove silenzio pre-trascrizione) |
| **Lingue** | Auto-detect + IT, EN, PT, ES, FR, DE, JA |
| **Privacy** | 100% locale - nessun audio esce dalla macchina |

## Specifiche TTS

| Spec | Valore |
|------|--------|
| **Engine** | edge-tts (Voci Neurali Microsoft Edge) |
| **Costo** | Gratuito |
| **Voci** | 47 in 8 lingue |
| **Cache** | Cache dinamico MP3 per hash del contenuto |
| **Personaggi** | Alessia (subtask, italiano) + Claudio (task principale, inglese) |

## Prerequisiti

- Windows 10/11
- GPU NVIDIA con supporto CUDA
- Python 3.11+
- FFmpeg (`ffplay` nel PATH)
- Claude Code CLI

## Installazione

```bash
# Clona
git clone https://github.com/fra-itc/parlaconclaudio.git
cd parlaconclaudio

# Crea ambiente virtuale
python -m venv venv
.\venv\Scripts\activate

# Installa dipendenze principali
pip install faster-whisper pynput pyperclip pyaudio pystray Pillow

# Installa supporto CUDA
pip install nvidia-cudnn-cu12 nvidia-cublas-cu12

# Fix compatibilita' transformers
pip install "transformers<4.45"

# Installa TTS
pip install edge-tts
```

### Avvio

```bash
# Opzione 1: File batch
.\VoiceBridge.bat

# Opzione 2: Diretto
.\venv\Scripts\python.exe -m src.voice_bridge.bridge
```

## Menu Tray

```
Voice Bridge v0.3
─────────────────
Whisper Language > Auto / IT / EN / PT / ES / FR / DE / JA
─────────────────
Quick Presets > Classic / Brasileiro / Full Italian / All English / Seductive
Alessia [Isabella] > Italiano > / English US > / English GB > / Portugues BR > / ...
Claudio [Andrew ML] > (stessa struttura - 47 voci per lingua)
─────────────────
Volume [200%] > 50% / 75% / 100% / 125% / 150% / 200% / 250% / 300%
Sound Pack > r2d2 / south-park / american-dad
Preview [r2d2] > (click per ascoltare)
─────────────────
Exit
```

## Strumenti Usati nello Sviluppo

| Strumento | Scopo |
|-----------|-------|
| **Claude Code** (Anthropic CLI) | Assistente IA che ha costruito l'intero progetto |
| **Claude Opus 4.6** | Il modello IA dietro tutto lo sviluppo |
| **Python 3.11** | Linguaggio principale |
| **faster-whisper** | Inferenza Whisper locale (CTranslate2) |
| **edge-tts** | Voci Neurali Microsoft (gratuite) |
| **pynput** | Hook tastiera globali |
| **pystray + Pillow** | Tray con icona animata |
| **PyAudio / PortAudio** | Cattura microfono |
| **ffplay** (FFmpeg) | Riproduzione audio |
| **Win32 SendInput** (ctypes) | Simulazione tastiera per auto-paste |
| **nvidia-cudnn-cu12** | Libreria CUDA Deep Neural Network |

---

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Built entirely with **[Claude Code](https://claude.ai/claude-code)** by [Anthropic](https://anthropic.com), powered by **Claude Opus 4.6**.

The name "parlaconclaudio" means "talk with Claudio" - a nod to both the AI persona Claudio who announces your tasks, and the act of speaking with Claude through voice.

---

<p align="center">
  <sub>Made with voice, code, and a marble sphere that never stops spinning.</sub>
</p>
