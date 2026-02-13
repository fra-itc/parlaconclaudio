"""
System Tray Icon (P1) - Visual indicator for voice bridge state.

Green = idle/ready, Red = recording, Yellow = transcribing.
Uses pystray + Pillow for cross-platform tray support.
"""

import logging
import threading
from typing import Callable

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageDraw
    import pystray
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    logger.info("pystray/Pillow not available - tray icon disabled")


def _create_icon_image(color: str, size: int = 64) -> "Image.Image":
    """Create a simple colored circle icon."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    colors = {
        "green": (0, 200, 0, 255),
        "red": (220, 0, 0, 255),
        "yellow": (220, 200, 0, 255),
        "gray": (128, 128, 128, 255),
    }
    fill = colors.get(color, colors["gray"])
    draw.ellipse([4, 4, size - 4, size - 4], fill=fill)
    return img


class TrayIcon:
    """System tray icon with state-based color changes."""

    def __init__(self, on_exit: Callable[[], None] | None = None):
        self._on_exit = on_exit
        self._icon: "pystray.Icon | None" = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the tray icon in a background thread."""
        if not TRAY_AVAILABLE:
            logger.warning("Tray icon not available (install pystray Pillow)")
            return

        menu = pystray.Menu(
            pystray.MenuItem("Voice Bridge v0.1", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._exit_clicked),
        )

        self._icon = pystray.Icon(
            "voice_bridge",
            _create_icon_image("green"),
            "Voice Bridge - Ready",
            menu,
        )

        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()
        logger.info("Tray icon started")

    def set_state(self, state: str) -> None:
        """Update icon color based on state: idle, recording, transcribing."""
        if not self._icon:
            return
        color_map = {"idle": "green", "recording": "red", "transcribing": "yellow"}
        title_map = {
            "idle": "Voice Bridge - Ready",
            "recording": "Voice Bridge - Recording...",
            "transcribing": "Voice Bridge - Transcribing...",
        }
        color = color_map.get(state, "gray")
        self._icon.icon = _create_icon_image(color)
        self._icon.title = title_map.get(state, f"Voice Bridge - {state}")

    def _exit_clicked(self, icon, item) -> None:
        """Handle exit menu click."""
        if self._on_exit:
            self._on_exit()
        self.stop()

    def stop(self) -> None:
        """Stop the tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
