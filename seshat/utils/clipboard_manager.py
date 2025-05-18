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

import os
import time
import shutil
import logging
from typing import Any, Callable
from collections.abc import Iterable

from gi.repository import GLib
from gi.repository.Gdk import Clipboard, Display
from gi.repository.Gdk import ContentProvider

_logger = logging.getLogger(__name__)


class ClipboardManager:
    """Read and write from the clipboards."""

    def __init__(self) -> None:
        display: Display = Display.get_default()
        self._selection: Clipboard = display.get_primary_clipboard()
        self._clipboard: Clipboard = display.get_clipboard()
        self._xdotool_path = shutil.which("xdotool")
        self._paste_keybinding = "shift+Insert"
        self._paste_delay = 0.3

    def set_paste_delay(self, delay: float) -> None:
        """Set the delay for the paste keystroke.

        Args:
            delay: The delay in seconds
        """

        self._paste_delay = delay

    def set_paste_keybinding(self, keybinding: str) -> None:
        """Set the keybinding for the paste keystroke.

        Args:
            keybinding: The keybinding for the paste keystroke
        """

        self._paste_keybinding = keybinding

    def read_selection(self, callback: Callable) -> None:
        """Read text from the primary clipboard (selection).

        Args:
            callback: Invoked when the text is available
        """

        self._read_async(self._selection, callback)

    def read_clipboard(self, callback: Callable) -> None:
        """Read text from the system clipboard.

        Args:
            callback: Invoked when the text is available
        """

        self._read_async(self._clipboard, callback)

    def set_clipboard(self, text: str) -> None:
        """Set text to the system clipboard.

        Args:
            text: The text to set in the clipboard
        """

        ctype = "text/plain;charset=utf-8"
        value = GLib.Bytes.new(text.encode('utf-8'))
        provider = ContentProvider.new_for_bytes(ctype, value)
        self._clipboard.set_content(provider)

    def set_and_paste(self, content: str) -> None:
        """Set content to the system clipboard and paste it.

        This method converts the content to a string, stores it on the
        clipboard, and then simulates a paste keystroke.

        Args:
            content: The content to paste
        """

        self.set_clipboard(content)
        self.simulate_paste()

    def simulate_paste(self) -> None:
        """Simulate a paste from clipboard keystroke."""

        time.sleep(self._paste_delay)
        keybinding = self._paste_keybinding
        os.system(f"{self._xdotool_path} key {keybinding}")

    def _read_async(self, clipboard: Clipboard, callback: Callable) -> None:
        """Read text from a clipboard asynchronously."""

        def on_text_ready(clipboard, result):
            try:
                callback(clipboard.read_text_finish(result))
            except GLib.Error as e:
                _logger.warning("Cannot read selection: %s", e)
                callback(str())

        clipboard.read_text_async(None, on_text_ready)
