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

from typing import Iterator
from gi.repository import Gtk
from seshat import RESOURCES_DIR
from .answer_row import AnswerRow
from .command_row import CommandRow

CommandRowType = AnswerRow | CommandRow


@Gtk.Template(filename=RESOURCES_DIR / "command_list.ui")
class CommandList(Gtk.ListBox):
    """List widget for displaying command rows."""

    __gtype_name__ = "CommandList"

    def __init__(self) -> None:
        super().__init__()
        self.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.set_focusable(False)

    def select(self, row: CommandRowType) -> None:
        """Select a row and scroll to it.

        Args:
            row: The row to select
        """

        self.select_row(row)
        self.scroll_to_row(row)

    def select_first(self) -> None:
        """Select the first row and scroll to it."""

        rows = self.mapped_rows()
        self.select(next(rows))

    def activate_selected(self) -> None:
        """Activate the selected row."""

        selected_row = self.get_selected_row()
        selected_row.activate()

    def update_view(self, query: str = str()) -> None:
        """Update the view."""

        for row in self.visible_rows():
            row.update_view(query)

    def scroll_to_row(self, row: CommandRowType) -> None:
        """Scroll the view to ensure a row is visible.

        Args:
            row: The row to scroll to
        """

        scrolled_window = self.get_parent()
        adjustment = scrolled_window.get_vadjustment()
        scroll_top = adjustment.get_value()
        page_size = adjustment.get_page_size()

        row_top = self._get_row_top(row)
        row_height = row.get_total_height()
        row_bottom = row_top + row_height

        if row_top < scroll_top:
            adjustment.set_value(row_top)
        elif row_bottom > scroll_top + page_size:
            adjustment.set_value(row_bottom - page_size)

    def visible_rows(self) -> Iterator[CommandRowType]:
        """Get an iterator over all visible rows."""

        row = self.get_first_child()

        while row:
            if row.get_visible():
                yield row
            row = row.get_next_sibling()

    def mapped_rows(self) -> Iterator[CommandRowType]:
        """Get an iterator over all displayed rows."""

        row = self.get_first_child()

        while row:
            if row.get_mapped():
                yield row
            row = row.get_next_sibling()

    def navigate(self, direction: int) -> None:
        """Navigate through the list in the specified direction.

        Args:
            direction: Positive or negative number of rows
        """

        rows = list(self.mapped_rows())
        selected_row = self.get_selected_row()

        if len(rows) < 1:
            return
        elif selected_row not in rows:
            self.select(rows[0])
        else:
            last_index = len(rows) - 1
            selected_index = rows.index(selected_row)
            next_index = selected_index + direction
            index = max(0, min(next_index, last_index))
            self.select(rows[index])

    def _get_row_top(self, row: CommandRowType) -> int:
        """Calculate the vertical position of a row in the list."""

        top = 0

        for current in self.mapped_rows():
            if current == row: break
            top += current.get_total_height()

        return top
