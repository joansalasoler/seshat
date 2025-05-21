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

from gi.repository import Gtk, GLib, GObject
from .command import Command
from seshat import RESOURCES_DIR
from seshat.i18n import normalize_text


@Gtk.Template(filename=RESOURCES_DIR / "command_row.ui")
class CommandRow(Gtk.ListBoxRow):
    """A row in the commands list."""

    __gtype_name__ = "CommandRow"

    __gsignals__ = {
        "row-modified": (
            GObject.SIGNAL_RUN_LAST, None, ()),
    }

    _icon = Gtk.Template.Child("icon")
    _label = Gtk.Template.Child("label")
    _star_button = Gtk.Template.Child("star_button")
    _star_icon = Gtk.Template.Child("star_icon")

    def __init__(self, command: Command):
        super().__init__()
        self._command = command
        self._star_button.connect("toggled", self._on_star_toggled)
        self.update_view()

    def get_command(self) -> Command:
        """Return the command of the row."""

        return self._command

    def get_text(self) -> int:
        """Return the label text of the row."""

        return self._label.get_text()

    def get_total_height(self) -> int:
        """Return the total height of the row including margins."""

        height = self.get_allocated_height()
        height += self.get_margin_bottom()
        height += self.get_margin_top()

        return height

    def update_view(self, query: str = str()) -> None:
        """Update the row's icon and label to match the command."""

        icon_name = self._command.icon_name
        label_text = self._get_label_text()
        is_starred = self._command.is_starred

        self._icon.set_from_icon_name(icon_name)
        self._label.set_text(label_text)

        markup_text = self._markup_text(label_text, query)
        self._label.set_markup(markup_text)

        self._star_button.set_active(is_starred)
        self._update_star_icon()

    def toggle_starred(self) -> None:
        """Toggle the command's starred status."""

        self._star_button.activate()

    def _get_label_text(self) -> str:
        """Return the text to display in the label."""

        return self._ellipsis(
            self._command.answer
            if bool(self._command.answer)
            else self._command.label
        )

    def _ellipsis(self, text: str, max_length: int = 120) -> str:
        """Truncate the text to the given length."""

        return (
            text if len(text) <= max_length else
            f"{text[:max_length - 1]}…"
        )

    def _on_star_toggled(self, button):
        """Update the command's starred status."""

        was_starred = self._command.is_starred
        self._command.is_starred = button.get_active()
        self._update_star_icon()

        if was_starred != self._command.is_starred:
            self.emit("row-modified")

    def _update_star_icon(self):
        """Update the icons for the bookmark toggle"""

        is_starred = self._command.is_starred
        prefix = str() if is_starred else "non-"
        self._star_icon.set_from_icon_name(f"{prefix}starred-symbolic")

    def _markup_text(self, text: str, query: str) -> str:
        """Highlight the query in the label text."""

        if query is None or len(query.strip()) < 1:
            return text

        normalized_text = normalize_text(text)
        normalized_query = normalize_text(query)
        index = normalized_text.find(normalized_query)

        if index == -1:
            return text

        result = text

        start = self._find_start(text, index)
        end = self._find_end(text, start, normalized_query)

        start_text = self._escape_markup(text[:start])
        marked_text = self._escape_markup(text[start:end])
        end_text = self._escape_markup(text[end:])

        result = start_text
        result += f"<span><b>{marked_text}</b></span>"
        result += end_text

        return result

    def _escape_markup(self, text: str) -> str:
        """Escape the markup in the label text."""

        return GLib.markup_escape_text(text)

    def _find_start(self, text: str, index: int) -> int:
        """Map normalized index to original string index."""

        i = 0
        n = 0

        while n < index and i < len(text):
            character = text[i]
            normalized = normalize_text(character)
            n += len(normalized)
            i += 1

        return i

    def _find_end(self, text: str, start: int, query: str) -> int:
        """Map normalized query length to end index in original string."""

        count = 0
        end = start

        while count < len(query) and end < len(text):
            character = text[end]
            count += len(normalize_text(character))
            end += 1

        return end
