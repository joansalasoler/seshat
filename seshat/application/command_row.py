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
from seshat import RESOURCES_DIR
from .command import Command


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

    def _markup_text(self, text: str, query: str) -> None:
        """Highlight the query in the label text."""

        result = text
        text_lower = text.lower()

        if query in text_lower and query != str():
            start = text_lower.find(query)
            end = start + len(query)

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
