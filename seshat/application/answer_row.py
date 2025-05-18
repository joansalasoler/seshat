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

from gi.repository import Gtk, GObject
from seshat import RESOURCES_DIR
from .command import Command


@Gtk.Template(filename=RESOURCES_DIR / "answer_row.ui")
class AnswerRow(Gtk.ListBoxRow):
    """A row in the answers list."""

    __gtype_name__ = "AnswerRow"

    __gsignals__ = {
        "row-modified": (
            GObject.SIGNAL_RUN_LAST, None, ()),
    }

    _label = Gtk.Template.Child("label")

    def __init__(self, command: Command):
        super().__init__()
        self._command = command
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

        label_text = self._get_label_text()
        self._label.set_text(label_text)

    def _get_label_text(self) -> str:
        """Return the text to display in the label."""

        return self._ellipsis(self._command.label)

    def _ellipsis(self, text: str, max_length: int = 240) -> str:
        """Truncate the text to the given length."""

        return (
            text if len(text) <= max_length else
            f"{text[:max_length - 1]}…"
        )
