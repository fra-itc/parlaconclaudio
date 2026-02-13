"""
Global Hotkey Listener - Detects push-to-talk key combinations.

Uses pynput for global keyboard hooks on Windows.
Default hotkey: Ctrl+Shift+Space
"""

import logging
import threading
from typing import Callable

from pynput import keyboard

logger = logging.getLogger(__name__)


class HotkeyListener:
    """
    Listens for a global hotkey combination.

    Push-to-talk flow:
    - All modifier keys + trigger key pressed -> on_press callback
    - Trigger key released -> on_release callback
    """

    def __init__(
        self,
        hotkey_str: str = "<ctrl>+<shift>+<space>",
        on_press: Callable[[], None] | None = None,
        on_release: Callable[[], None] | None = None,
    ):
        self._on_press = on_press
        self._on_release = on_release
        self._listener: keyboard.Listener | None = None
        self._hotkey_active = False

        # Parse hotkey string into modifier set + trigger key
        self._modifiers, self._trigger = self._parse_hotkey(hotkey_str)
        self._pressed_keys: set = set()

        logger.info(f"Hotkey configured: {hotkey_str}")

    @staticmethod
    def _parse_hotkey(hotkey_str: str) -> tuple[set, keyboard.Key | keyboard.KeyCode]:
        """Parse '<ctrl>+<shift>+<space>' into (modifier_set, trigger_key)."""
        parts = [p.strip() for p in hotkey_str.split("+")]
        modifiers = set()
        trigger = None

        key_map = {
            "<ctrl>": keyboard.Key.ctrl_l,
            "<shift>": keyboard.Key.shift_l,
            "<alt>": keyboard.Key.alt_l,
            "<space>": keyboard.Key.space,
            "<enter>": keyboard.Key.enter,
            "<tab>": keyboard.Key.tab,
        }

        for part in parts:
            lower = part.lower()
            if lower in ("<ctrl>", "<shift>", "<alt>"):
                modifiers.add(key_map[lower])
            elif lower in key_map:
                trigger = key_map[lower]
            else:
                # Assume it's a character key
                trigger = keyboard.KeyCode.from_char(lower.strip("<>"))

        if trigger is None:
            trigger = keyboard.Key.space  # Fallback

        return modifiers, trigger

    def _normalize_key(self, key) -> keyboard.Key | keyboard.KeyCode:
        """Normalize left/right variants to a single modifier."""
        normalize_map = {
            keyboard.Key.ctrl_r: keyboard.Key.ctrl_l,
            keyboard.Key.shift_r: keyboard.Key.shift_l,
            keyboard.Key.alt_r: keyboard.Key.alt_l,
            keyboard.Key.alt_gr: keyboard.Key.alt_l,
        }
        return normalize_map.get(key, key)

    def _on_key_press(self, key) -> None:
        """Handle key press events."""
        normalized = self._normalize_key(key)
        self._pressed_keys.add(normalized)

        # Check if all modifiers + trigger are pressed
        if not self._hotkey_active:
            mods_pressed = all(m in self._pressed_keys for m in self._modifiers)
            trigger_pressed = normalized == self._trigger or self._trigger in self._pressed_keys

            if mods_pressed and trigger_pressed:
                self._hotkey_active = True
                logger.debug("Hotkey pressed - starting recording")
                if self._on_press:
                    self._on_press()

    def _on_key_release(self, key) -> None:
        """Handle key release events."""
        normalized = self._normalize_key(key)
        self._pressed_keys.discard(normalized)

        # If hotkey was active and trigger key released -> stop
        if self._hotkey_active and normalized == self._trigger:
            self._hotkey_active = False
            logger.debug("Hotkey released - stopping recording")
            if self._on_release:
                self._on_release()

    def start(self) -> None:
        """Start listening for hotkey events (non-blocking)."""
        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._listener.daemon = True
        self._listener.start()
        logger.info("Hotkey listener started")

    def stop(self) -> None:
        """Stop listening."""
        if self._listener:
            self._listener.stop()
            self._listener = None
            logger.info("Hotkey listener stopped")

    @property
    def is_active(self) -> bool:
        """Whether the hotkey is currently being held down."""
        return self._hotkey_active
