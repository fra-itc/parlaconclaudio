"""
System Tray Icon - Voice Bridge control panel.

Animated marble sphere icon that shifts colors:
- Idle: slow mystical rainbow shift
- Recording: pulsing red/magenta
- Transcribing: fast golden shimmer

Right-click menu:
- Whisper Language selector
- TTS Voice Style (Alessia + Claudio presets)
- Sound Pack selector (R2-D2, South Park, American Dad)
- Preview sounds on click
- Exit
"""

import colorsys
import json
import logging
import math
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageDraw, ImageFilter
    import pystray
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    logger.info("pystray/Pillow not available - tray icon disabled")

# === PATHS ===
TTS_CONFIG = Path.home() / ".claude" / "cache" / "tts" / "tts_config.json"
SOUNDS_DIR = Path.home() / ".claude" / "cache" / "tts" / "sounds"

# === QUICK PRESETS (fast selection) ===
VOICE_PRESETS = {
    "Classic (Isabella + Andrew)": {
        "alessia": {"voice": "it-IT-IsabellaNeural", "rate": "-4%", "pitch": "-8Hz"},
        "claudio": {"voice": "en-US-AndrewMultilingualNeural", "rate": "+0%", "pitch": "+0Hz"},
    },
    "Brasileiro (Thalita + Andrew)": {
        "alessia": {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "-2%", "pitch": "-4Hz"},
        "claudio": {"voice": "en-US-AndrewMultilingualNeural", "rate": "+0%", "pitch": "+0Hz"},
    },
    "Full Italian (Isabella + Diego)": {
        "alessia": {"voice": "it-IT-IsabellaNeural", "rate": "-4%", "pitch": "-8Hz"},
        "claudio": {"voice": "it-IT-DiegoNeural", "rate": "+0%", "pitch": "-2Hz"},
    },
    "All English (Emma + Andrew)": {
        "alessia": {"voice": "en-US-EmmaMultilingualNeural", "rate": "+0%", "pitch": "+0Hz"},
        "claudio": {"voice": "en-US-AndrewMultilingualNeural", "rate": "+0%", "pitch": "+0Hz"},
    },
    "Seductive (Seraphina + Brian)": {
        "alessia": {"voice": "en-US-SeraphinaMultilingualNeural", "rate": "-5%", "pitch": "-10Hz"},
        "claudio": {"voice": "en-US-BrianMultilingualNeural", "rate": "-3%", "pitch": "-5Hz"},
    },
}

# === EDGE-TTS VOICES BY LANGUAGE ===
# Organized for individual voice selection in tray menu
EDGE_VOICES = {
    "Italiano": [
        {"name": "Isabella", "id": "it-IT-IsabellaNeural", "gender": "F"},
        {"name": "Elsa", "id": "it-IT-ElsaNeural", "gender": "F"},
        {"name": "Diego", "id": "it-IT-DiegoNeural", "gender": "M"},
        {"name": "Giuseppe ML", "id": "it-IT-GiuseppeMultilingualNeural", "gender": "M"},
    ],
    "English US": [
        {"name": "Ava ML", "id": "en-US-AvaMultilingualNeural", "gender": "F"},
        {"name": "Emma ML", "id": "en-US-EmmaMultilingualNeural", "gender": "F"},
        {"name": "Aria", "id": "en-US-AriaNeural", "gender": "F"},
        {"name": "Jenny", "id": "en-US-JennyNeural", "gender": "F"},
        {"name": "Michelle", "id": "en-US-MichelleNeural", "gender": "F"},
        {"name": "Ana", "id": "en-US-AnaNeural", "gender": "F"},
        {"name": "Seraphina ML", "id": "en-US-SeraphinaMultilingualNeural", "gender": "F"},
        {"name": "Andrew ML", "id": "en-US-AndrewMultilingualNeural", "gender": "M"},
        {"name": "Brian ML", "id": "en-US-BrianMultilingualNeural", "gender": "M"},
        {"name": "Guy", "id": "en-US-GuyNeural", "gender": "M"},
        {"name": "Eric", "id": "en-US-EricNeural", "gender": "M"},
        {"name": "Roger", "id": "en-US-RogerNeural", "gender": "M"},
        {"name": "Steffan", "id": "en-US-SteffanNeural", "gender": "M"},
        {"name": "Christopher", "id": "en-US-ChristopherNeural", "gender": "M"},
    ],
    "English GB": [
        {"name": "Sonia", "id": "en-GB-SoniaNeural", "gender": "F"},
        {"name": "Libby", "id": "en-GB-LibbyNeural", "gender": "F"},
        {"name": "Maisie", "id": "en-GB-MaisieNeural", "gender": "F"},
        {"name": "Ryan", "id": "en-GB-RyanNeural", "gender": "M"},
        {"name": "Thomas", "id": "en-GB-ThomasNeural", "gender": "M"},
    ],
    "Portugues BR": [
        {"name": "Thalita ML", "id": "pt-BR-ThalitaMultilingualNeural", "gender": "F"},
        {"name": "Francisca", "id": "pt-BR-FranciscaNeural", "gender": "F"},
        {"name": "Antonio", "id": "pt-BR-AntonioNeural", "gender": "M"},
    ],
    "Espanol": [
        {"name": "Elvira (ES)", "id": "es-ES-ElviraNeural", "gender": "F"},
        {"name": "Ximena (ES)", "id": "es-ES-XimenaNeural", "gender": "F"},
        {"name": "Dalia (MX)", "id": "es-MX-DaliaNeural", "gender": "F"},
        {"name": "Alvaro (ES)", "id": "es-ES-AlvaroNeural", "gender": "M"},
        {"name": "Jorge (MX)", "id": "es-MX-JorgeNeural", "gender": "M"},
    ],
    "Francais": [
        {"name": "Vivienne ML", "id": "fr-FR-VivienneMultilingualNeural", "gender": "F"},
        {"name": "Denise", "id": "fr-FR-DeniseNeural", "gender": "F"},
        {"name": "Eloise", "id": "fr-FR-EloiseNeural", "gender": "F"},
        {"name": "Remy ML", "id": "fr-FR-RemyMultilingualNeural", "gender": "M"},
        {"name": "Henri", "id": "fr-FR-HenriNeural", "gender": "M"},
    ],
    "Deutsch": [
        {"name": "Seraphina ML", "id": "de-DE-SeraphinaMultilingualNeural", "gender": "F"},
        {"name": "Amala", "id": "de-DE-AmalaNeural", "gender": "F"},
        {"name": "Katja", "id": "de-DE-KatjaNeural", "gender": "F"},
        {"name": "Florian ML", "id": "de-DE-FlorianMultilingualNeural", "gender": "M"},
        {"name": "Conrad", "id": "de-DE-ConradNeural", "gender": "M"},
        {"name": "Killian", "id": "de-DE-KillianNeural", "gender": "M"},
    ],
    "Japanese": [
        {"name": "Nanami", "id": "ja-JP-NanamiNeural", "gender": "F"},
        {"name": "Keita", "id": "ja-JP-KeitaNeural", "gender": "M"},
    ],
}

VOLUME_LEVELS = [50, 75, 100, 125, 150, 200, 250, 300]

WHISPER_LANGUAGES = {
    "Auto-detect": None,
    "Italiano": "it",
    "English": "en",
    "Portugues": "pt",
    "Espanol": "es",
    "Francais": "fr",
    "Deutsch": "de",
    "Japanese": "ja",
}


def _load_config() -> dict:
    try:
        if TTS_CONFIG.is_file():
            return json.loads(TTS_CONFIG.read_text())
    except Exception:
        pass
    return {"sound_pack": "r2d2", "whisper_language": None}


def _save_config(config: dict) -> None:
    try:
        TTS_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        TTS_CONFIG.write_text(json.dumps(config, indent=2))
    except Exception as e:
        logger.error(f"Failed to save config: {e}")


def _play_sound(filepath: str) -> None:
    """Play a sound file for preview at configured volume."""
    config = _load_config()
    volume = str(config.get("volume", 200))
    try:
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
             "-volume", volume, filepath],
            creationflags=CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


# ══════════════════════════════════════════════════
# ANIMATED MARBLE SPHERE ICON
# ══════════════════════════════════════════════════

def _marble_noise(x: float, y: float, t: float) -> float:
    """Generate marble-like noise pattern using layered sine waves."""
    v = math.sin(x * 0.15 + t * 0.7)
    v += 0.5 * math.sin(y * 0.22 - t * 0.5)
    v += 0.3 * math.sin((x + y) * 0.18 + t * 1.1)
    v += 0.2 * math.sin(math.sqrt(x * x + y * y) * 0.12 - t * 0.8)
    return v


def _generate_marble_sphere(
    size: int,
    hue_offset: float,
    hue_range: float = 0.3,
    saturation: float = 0.75,
    brightness: float = 0.95,
    time_val: float = 0.0,
) -> "Image.Image":
    """
    Generate a single frame of an animated marble sphere.

    Args:
        size: Icon size in pixels
        hue_offset: Base hue (0.0-1.0) that shifts for animation
        hue_range: How much hue variation in the marble veins
        saturation: Color saturation (0-1)
        brightness: Base brightness (0-1)
        time_val: Time parameter for marble pattern animation
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = img.load()
    center = size / 2.0
    radius = (size - 6) / 2.0  # Leave small margin

    for y in range(size):
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx * dx + dy * dy)

            if dist > radius:
                continue

            # Normalized distance from center (0 = center, 1 = edge)
            norm_dist = dist / radius

            # 3D sphere lighting: brighter at top-left, darker at bottom-right
            light_x = -0.3  # Light from top-left
            light_y = -0.4
            nx = dx / radius
            ny = dy / radius
            nz = math.sqrt(max(0, 1 - nx * nx - ny * ny))
            light_dot = nx * light_x + ny * light_y + nz * 0.8
            light_factor = max(0.15, min(1.0, 0.5 + light_dot * 0.6))

            # Marble veins pattern
            marble = _marble_noise(x, y, time_val)

            # Hue: base + marble variation
            h = (hue_offset + marble * hue_range * 0.15) % 1.0
            # Saturation: slightly less at edges for depth
            s = saturation * (1.0 - norm_dist * 0.2)
            # Value: sphere shading
            v = brightness * light_factor

            # Specular highlight near top-left
            spec_dist = math.sqrt((nx + 0.35) ** 2 + (ny + 0.35) ** 2)
            if spec_dist < 0.3:
                spec = (1.0 - spec_dist / 0.3) ** 2 * 0.4
                v = min(1.0, v + spec)
                s = max(0.0, s - spec * 0.5)

            # Edge glow (rim lighting)
            if norm_dist > 0.7:
                rim = (norm_dist - 0.7) / 0.3
                rim_glow = rim ** 2 * 0.15
                v = min(1.0, v + rim_glow)

            r, g, b = colorsys.hsv_to_rgb(h, s, v)

            # Alpha: smooth edge falloff
            alpha = 255
            if norm_dist > 0.85:
                alpha = int(255 * (1.0 - (norm_dist - 0.85) / 0.15))

            pixels[x, y] = (int(r * 255), int(g * 255), int(b * 255), alpha)

    return img


# Animation presets per state
_ANIM_PRESETS = {
    "idle": {
        "hue_speed": 0.008,       # Slow rainbow drift
        "hue_range": 0.25,
        "saturation": 0.70,
        "brightness": 0.90,
        "time_speed": 0.3,
        "interval": 0.15,         # 150ms per frame
    },
    "recording": {
        "hue_speed": 0.0,         # Locked to red
        "hue_range": 0.08,
        "saturation": 0.90,
        "brightness": 0.95,
        "time_speed": 1.5,        # Fast marble shift
        "interval": 0.08,         # 80ms per frame (fast pulse)
        "base_hue": 0.0,          # Red
        "pulse": True,
    },
    "transcribing": {
        "hue_speed": 0.02,
        "hue_range": 0.12,
        "saturation": 0.80,
        "brightness": 0.95,
        "time_speed": 1.0,
        "interval": 0.10,
        "base_hue": 0.12,         # Golden/amber
    },
}

ICON_SIZE = 64
NUM_IDLE_FRAMES = 36  # Pre-generated frames for idle animation


class _IconAnimator:
    """Background thread that animates the tray icon."""

    def __init__(self):
        self._state = "idle"
        self._running = False
        self._thread: threading.Thread | None = None
        self._icon_ref = None  # Reference to pystray.Icon
        self._frame_idx = 0
        self._time_val = 0.0
        self._idle_frames: list | None = None  # Pre-generated cache

    def _pregenerate_idle_frames(self):
        """Pre-generate idle animation frames for smooth playback."""
        if self._idle_frames is not None:
            return
        logger.info("Pre-generating marble sphere frames...")
        self._idle_frames = []
        for i in range(NUM_IDLE_FRAMES):
            hue = i / NUM_IDLE_FRAMES
            t = i * 0.5
            frame = _generate_marble_sphere(
                ICON_SIZE, hue,
                hue_range=0.25, saturation=0.70, brightness=0.90,
                time_val=t,
            )
            self._idle_frames.append(frame)
        logger.info(f"Generated {NUM_IDLE_FRAMES} marble sphere frames")

    def set_icon(self, icon):
        self._icon_ref = icon

    def set_state(self, state: str):
        self._state = state
        self._frame_idx = 0

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._animation_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _animation_loop(self):
        """Main animation loop - updates icon at preset intervals."""
        self._pregenerate_idle_frames()
        base_hue = 0.0

        while self._running:
            preset = _ANIM_PRESETS.get(self._state, _ANIM_PRESETS["idle"])
            interval = preset["interval"]

            try:
                if self._state == "idle" and self._idle_frames:
                    # Use pre-generated frames for idle (smooth, low CPU)
                    frame = self._idle_frames[self._frame_idx % NUM_IDLE_FRAMES]
                    self._frame_idx += 1
                else:
                    # Generate on-the-fly for recording/transcribing
                    self._time_val += preset["time_speed"]
                    base_hue = preset.get("base_hue", base_hue + preset["hue_speed"])
                    hue = base_hue % 1.0

                    # Pulse effect for recording: oscillate brightness
                    brightness = preset["brightness"]
                    if preset.get("pulse"):
                        pulse = 0.5 + 0.5 * math.sin(self._time_val * 3.0)
                        brightness = 0.55 + pulse * 0.45

                    frame = _generate_marble_sphere(
                        ICON_SIZE, hue,
                        hue_range=preset["hue_range"],
                        saturation=preset["saturation"],
                        brightness=brightness,
                        time_val=self._time_val,
                    )

                if self._icon_ref:
                    self._icon_ref.icon = frame

            except Exception as e:
                logger.debug(f"Animation frame error: {e}")

            time.sleep(interval)


class TrayIcon:
    """System tray icon with animated marble sphere and settings menu."""

    def __init__(self, on_exit: Callable[[], None] | None = None):
        self._on_exit = on_exit
        self._icon: "pystray.Icon | None" = None
        self._thread: threading.Thread | None = None
        self._animator = _IconAnimator()

    def _voice_display_name(self, voice_id: str) -> str:
        """Get short display name for a voice ID."""
        for voices in EDGE_VOICES.values():
            for v in voices:
                if v["id"] == voice_id:
                    return v["name"]
        # Fallback: extract name from ID (e.g. "it-IT-IsabellaNeural" -> "Isabella")
        parts = voice_id.split("-")
        if len(parts) >= 3:
            return parts[2].replace("Neural", "").replace("Multilingual", " ML")
        return voice_id

    def _build_voice_submenu(self, role: str, current_voice_id: str) -> "pystray.Menu":
        """Build a voice selection submenu organized by language for Alessia or Claudio."""
        lang_submenus = []
        for lang_name, voices in EDGE_VOICES.items():
            voice_items = []
            for v in voices:
                is_current = (v["id"] == current_voice_id)
                gender_icon = "F" if v["gender"] == "F" else "M"
                label = f"{'> ' if is_current else '  '}{v['name']} [{gender_icon}]"
                voice_items.append(pystray.MenuItem(
                    label,
                    self._make_set_individual_voice(role, v["id"]),
                ))
            lang_submenus.append(pystray.MenuItem(
                lang_name,
                pystray.Menu(*voice_items),
            ))
        return pystray.Menu(*lang_submenus)

    def _build_menu(self) -> "pystray.Menu":
        config = _load_config()
        current_pack = config.get("sound_pack", "r2d2")
        current_lang = config.get("whisper_language")
        alessia_voice = config.get("alessia", {}).get("voice", "it-IT-IsabellaNeural")
        claudio_voice = config.get("claudio", {}).get("voice", "en-US-AndrewMultilingualNeural")

        # --- Whisper Language submenu ---
        lang_items = []
        for label, code in WHISPER_LANGUAGES.items():
            checked = (current_lang == code)
            lang_items.append(pystray.MenuItem(
                f"{'> ' if checked else '  '}{label}",
                self._make_set_language(code),
            ))

        # --- Quick Presets submenu ---
        preset_items = []
        for preset_name, preset_data in VOICE_PRESETS.items():
            is_current = (
                preset_data["alessia"]["voice"] == alessia_voice
                and preset_data["claudio"]["voice"] == claudio_voice
            )
            preset_items.append(pystray.MenuItem(
                f"{'> ' if is_current else '  '}{preset_name}",
                self._make_set_voice_preset(preset_name),
            ))

        # --- Alessia individual voice submenu ---
        alessia_display = self._voice_display_name(alessia_voice)
        alessia_submenu = self._build_voice_submenu("alessia", alessia_voice)

        # --- Claudio individual voice submenu ---
        claudio_display = self._voice_display_name(claudio_voice)
        claudio_submenu = self._build_voice_submenu("claudio", claudio_voice)

        # --- Sound Pack submenu ---
        pack_items = []
        if SOUNDS_DIR.is_dir():
            for pack_dir in sorted(SOUNDS_DIR.iterdir()):
                if pack_dir.is_dir():
                    pack_name = pack_dir.name
                    count = len(list(pack_dir.glob("*.mp3")))
                    checked = (pack_name == current_pack)
                    pack_items.append(pystray.MenuItem(
                        f"{'> ' if checked else '  '}{pack_name} ({count})",
                        self._make_set_sound_pack(pack_name),
                    ))

        # --- Volume submenu ---
        current_vol = config.get("volume", 200)
        vol_items = []
        for level in VOLUME_LEVELS:
            checked = (level == current_vol)
            pct = f"{level}%"  # ffplay 100 = normal
            vol_items.append(pystray.MenuItem(
                f"{'> ' if checked else '  '}{pct}",
                self._make_set_volume(level),
            ))

        # --- Preview Sounds submenu ---
        preview_items = []
        pack_dir = SOUNDS_DIR / current_pack
        if pack_dir.is_dir():
            for mp3 in sorted(pack_dir.glob("*.mp3"))[:15]:
                preview_items.append(pystray.MenuItem(
                    f"  {mp3.stem}",
                    self._make_preview_sound(str(mp3)),
                ))

        return pystray.Menu(
            pystray.MenuItem("Voice Bridge v0.3", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Whisper Language", pystray.Menu(*lang_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quick Presets", pystray.Menu(*preset_items)),
            pystray.MenuItem(f"Alessia [{alessia_display}]", alessia_submenu),
            pystray.MenuItem(f"Claudio [{claudio_display}]", claudio_submenu),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f"Volume [{current_vol}%]", pystray.Menu(*vol_items)),
            pystray.MenuItem("Sound Pack", pystray.Menu(*pack_items)),
            pystray.MenuItem(f"Preview [{current_pack}]", pystray.Menu(*preview_items) if preview_items else None),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._exit_clicked),
        )

    def _make_set_language(self, lang_code):
        def handler(icon, item):
            config = _load_config()
            config["whisper_language"] = lang_code
            _save_config(config)
            logger.info(f"Whisper language set to: {lang_code or 'auto'}")
            self._rebuild_menu()
        return handler

    def _make_set_voice_preset(self, preset_name):
        def handler(icon, item):
            config = _load_config()
            preset = VOICE_PRESETS[preset_name]
            config["alessia"] = preset["alessia"]
            config["claudio"] = preset["claudio"]
            _save_config(config)
            logger.info(f"Voice preset set to: {preset_name}")
            self._rebuild_menu()
        return handler

    def _make_set_individual_voice(self, role: str, voice_id: str):
        """Set a single voice for Alessia or Claudio."""
        def handler(icon, item):
            config = _load_config()
            if role not in config:
                config[role] = {}
            config[role]["voice"] = voice_id
            # Set sensible defaults for rate/pitch if missing
            config[role].setdefault("rate", "+0%")
            config[role].setdefault("pitch", "+0Hz")
            _save_config(config)
            name = self._voice_display_name(voice_id)
            logger.info(f"{role.capitalize()} voice set to: {name} ({voice_id})")
            self._rebuild_menu()
        return handler

    def _make_set_volume(self, level: int):
        def handler(icon, item):
            config = _load_config()
            config["volume"] = level
            _save_config(config)
            logger.info(f"Volume set to: {level}%")
            self._rebuild_menu()
        return handler

    def _make_set_sound_pack(self, pack_name):
        def handler(icon, item):
            config = _load_config()
            config["sound_pack"] = pack_name
            _save_config(config)
            logger.info(f"Sound pack set to: {pack_name}")
            self._rebuild_menu()
        return handler

    def _make_preview_sound(self, filepath):
        def handler(icon, item):
            _play_sound(filepath)
        return handler

    def _rebuild_menu(self):
        if self._icon:
            self._icon.menu = self._build_menu()
            self._icon.update_menu()

    def start(self) -> None:
        if not TRAY_AVAILABLE:
            logger.warning("Tray icon not available (install pystray Pillow)")
            return

        # Create initial static icon (animator will replace it immediately)
        initial_img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(initial_img)
        draw.ellipse([4, 4, ICON_SIZE - 4, ICON_SIZE - 4], fill=(0, 200, 100, 255))

        self._icon = pystray.Icon(
            "voice_bridge",
            initial_img,
            "Voice Bridge - Ready",
            self._build_menu(),
        )

        # Start animator
        self._animator.set_icon(self._icon)
        self._animator.set_state("idle")
        self._animator.start()

        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()
        logger.info("Tray icon started with animated marble sphere")

    def set_state(self, state: str) -> None:
        if not self._icon:
            return
        title_map = {
            "idle": "Voice Bridge - Ready",
            "recording": "Voice Bridge - Recording...",
            "transcribing": "Voice Bridge - Transcribing...",
        }
        self._animator.set_state(state)
        self._icon.title = title_map.get(state, f"Voice Bridge - {state}")

    def _exit_clicked(self, icon, item):
        if self._on_exit:
            self._on_exit()
        self.stop()

    def stop(self) -> None:
        self._animator.stop()
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
