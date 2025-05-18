# -*- coding: utf-8 -*-

# Seshat: AI powered command palette
# Copyright (C) 2025 Joan Sala <contact@joansala.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
import logging
from threading import Thread, Event
from typing import Callable, List, Set
from evdev import InputDevice, categorize, ecodes
from evdev.events import KeyEvent

_logger = logging.getLogger(__name__)


class HotkeyListener(Thread):
    """A thread-based listener for keyboard hotkeys.

    This class monitors keyboard events from an input device and
    triggers callbacks when hotkey combinations are detected.
    """

    def __init__(self, device_path: str) -> None:
        super().__init__(daemon=True)

        self._device_path: str = device_path
        self._poll_interval: float = 0.05
        self._modifier_keys: List[str] = ["KEY_LEFTMETA", "KEY_RIGHTMETA"]
        self._trigger_key: str = "KEY_SPACE"
        self._stop_event: Event = Event()
        self._current_modifiers: Set[str] = set()
        self._trigger_pressed: bool = False
        self._callbacks: List[Callable] = list()

    def set_poll_interval(self, value: float) -> None:
        """Set the polling delay interval.

        Args:
            value: The polling delay in seconds
        """

        self._poll_interval = value

    def set_modifier_keys(self, keys: List[str]) -> None:
        """Set the modifier keys.

        Args:
            keys: List of key codes that act as modifiers
        """

        self._modifier_keys = keys

    def set_trigger_key(self, key: str) -> None:
        """Set the trigger key.

        Args:
            key: The key code that acts as the trigger
        """

        self._trigger_key = key

    def add_callback(self, callback: Callable) -> None:
        """Adds a callback to be triggered.

        Args:
            callback: A callable function
        """

        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable) -> None:
        """Remove a previously registered callback.

        Args:
            callback: The callback function to remove
        """

        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def run(self) -> None:
        """Thread entry point that listens for hotkeys."""

        try:
            device = InputDevice(self._device_path)

            while not self._stop_event.is_set():
                for event in device.read_loop():
                    if self._stop_event.is_set():
                        break

                    if event.type == ecodes.EV_KEY:
                        key_event = categorize(event)
                        self._handle_key_event(key_event)
                        time.sleep(self._poll_interval)
        except Exception as e:
            _logger.error("HotkeyListener error: %s", e)

    def shutdown(self) -> None:
        """Stop the hotkey listener thread."""

        self._stop_event.set()
        self.join()

    def _handle_key_event(self, key_event: KeyEvent) -> None:
        """Process a keyboard key event."""

        if key_event.keystate == key_event.key_down:
            self._handle_key_down(key_event)
        elif key_event.keystate == key_event.key_up:
            self._handle_key_up(key_event)

    def _handle_key_down(self, key_event: KeyEvent) -> None:
        """Handle a key press event."""

        if key_event.keycode in self._modifier_keys:
            self._current_modifiers.add(key_event.keycode)

        if key_event.keycode == self._trigger_key:
            self._trigger_pressed = True

        if self._current_modifiers and self._trigger_pressed:
            self._trigger_callbacks()

    def _handle_key_up(self, key_event: KeyEvent) -> None:
        """Handle a key release event."""

        if key_event.keycode in self._modifier_keys:
            self._current_modifiers.discard(key_event.keycode)

        if key_event.keycode == self._trigger_key:
            self._trigger_pressed = False

    def _trigger_callbacks(self) -> None:
        """Queue all registered callbacks."""

        for callback in self._callbacks:
            callback()
