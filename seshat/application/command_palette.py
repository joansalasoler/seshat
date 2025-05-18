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

from typing import Callable
from gi.repository import Gdk, Gtk, GObject
from seshat import RESOURCES_DIR
from .command import Command
from .command_list import CommandList
from .command_row import CommandRow
from .answer_row import AnswerRow


@Gtk.Template(filename=RESOURCES_DIR / "command_palette.ui")
class CommandPalette(Gtk.ApplicationWindow):
    """Main window for the command palette."""

    __gtype_name__ = "CommandPalette"

    __gsignals__ = {
        "search-changed": (
            GObject.SIGNAL_RUN_LAST, None, (str,)),

        "search-stopped": (
            GObject.SIGNAL_RUN_LAST, None, ()),

        "row-activated": (
            GObject.SIGNAL_RUN_LAST, None, (object, str,)),

        "row-modified": (
            GObject.SIGNAL_RUN_LAST, None, (object,)),

        "focus-lost": (
            GObject.SIGNAL_RUN_FIRST, None, ()),

        "key-pressed": (
            GObject.SIGNAL_RUN_FIRST, GObject.TYPE_BOOLEAN, (
                int, int, Gdk.ModifierType
            )),
    }

    _search_entry = Gtk.Template.Child("search_entry")
    _scrolled_window = Gtk.Template.Child("scrolled_window")
    _listbox_container = Gtk.Template.Child("listbox_container")
    _status_box = Gtk.Template.Child("status_box")
    _status_label = Gtk.Template.Child("status_label")
    _progress_bar = Gtk.Template.Child("progress_bar")

    def __init__(self, app: Gtk.Application) -> None:
        super().__init__(application=app)
        self._answer_list = CommandList()
        self._command_list = CommandList()
        self._scrolled_window.set_visible(True)
        self._scrolled_window.set_child(self._command_list)
        self._active_list = self._command_list
        self._focus_event = Gtk.EventControllerFocus()
        self._key_event = Gtk.EventControllerKey()
        self.add_controller(self._focus_event)
        self.add_controller(self._key_event)
        self._connect_signals()

    def _connect_signals(self) -> None:
        """Connect signal handlers to their respective signals."""

        self.connect("map", self._on_window_mapped)
        self._focus_event.connect("leave", self._on_focus_lost)
        self._key_event.connect("key-pressed", self._on_key_pressed)
        self._search_entry.connect("activate", self._on_search_activated)
        self._search_entry.connect("stop-search", self._on_search_stopped)
        self._search_entry.connect("search-changed", self._on_search_changed)
        self._answer_list.connect("row-activated", self._on_row_activated)
        self._command_list.connect("row-activated", self._on_row_activated)

    def get_search_text(self) -> str:
        """Get the search entry text."""

        return self._search_entry.get_text()

    def set_command_filter(self, callback: Callable) -> None:
        """Set the filter function for the command list.

        Args:
            callback: A commamd filtering function
        """

        self._command_list.set_filter_func(callback)

    def set_command_sort(self, callback: Callable) -> None:
        """Set the sort function for the command list.

        Args:
            callback: A commamd sorting function
        """

        self._command_list.set_sort_func(callback)

    def add_answer(self, command: Command) -> None:
        """Add a new command to the answer list.

        Args:
            command: A command to add to the list
        """

        row = AnswerRow(command)
        self._answer_list.append(row)

    def add_command(self, command: Command) -> None:
        """Add a new command to the command list.

        Args:
            command: A command to add to the list
        """

        row = CommandRow(command)
        row.connect("row-modified", self._on_row_modified)
        self._command_list.append(row)

    def show_answers(self):
        """Show the answer list and hide the command list."""

        self._scrolled_window.set_child(self._answer_list)
        self._active_list = self._answer_list

    def show_commands(self):
        """Show the command list and hide the answer list."""

        self._scrolled_window.set_child(self._command_list)
        self._active_list = self._command_list

    def clear_answers(self):
        """Remove all rows from the answer list."""

        self._answer_list.remove_all()

    def navigate_next(self) -> None:
        """Navigate to the next item in the active list."""

        self._active_list.navigate(+1)
        self._search_entry.grab_focus()

    def navigate_previous(self) -> None:
        """Navigate to the previous item in the active list."""

        self._active_list.navigate(-1)
        self._search_entry.grab_focus()

    def update_view(self, query: str = str()) -> None:
        """Refreshes the active list view."""

        self._active_list.update_view(query)
        self._active_list.invalidate_filter()
        self._active_list.invalidate_sort()
        self._active_list.select_first()
        self._search_entry.grab_focus()

    def pulse_progress(self) -> bool:
        """Pulse the progress bar to indicate activity."""

        self._progress_bar.pulse()

    def show_status(self, message: str, style="progress") -> None:
        """Show a status message in the status label."""

        self._progress_bar.set_visible(style == "progress")
        self._status_label.set_label(message)
        self._status_box.set_css_classes([style, "frame", "background"])
        self._status_box.set_visible(True)

    def hide_status(self) -> None:
        """Clear the status message from the status label."""

        self._status_box.set_visible(False)

    def _on_window_mapped(self, window: Gtk.ApplicationWindow) -> None:
        """Handle the window being mapped shown."""

        self._search_entry.set_text(str())
        self.update_view()

    def _on_focus_lost(self, controller: Gtk.EventControllerFocus) -> None:
        """Handle focus leaving the window."""

        self.emit("focus-lost")

    def _on_key_pressed(self, controller: Gtk.EventControllerKey,
        keyval: int, keycode: int, state: Gdk.ModifierType) -> bool:
        """Handle a key being pressed in the window."""

        self.emit("key-pressed", keyval, keycode, state)
        return True

    def _on_search_changed(self, search_entry: Gtk.SearchEntry) -> None:
        """Handle changes to the search entry text."""

        search_text = search_entry.get_text()
        self.emit("search-changed", search_text)

    def _on_search_stopped(self, search_entry: Gtk.SearchEntry) -> None:
        """Handle the Escape key being pressed in the search entry."""

        self.emit("search-stopped")

    def _on_search_activated(self, search_entry: Gtk.SearchEntry) -> None:
        """Handle the Enter key being pressed in the search entry."""

        self._active_list.activate_selected()

    def _on_row_activated(self, listbox: CommandList, row: CommandRow) -> None:
        """Handle a row being activated (clicked or pressed)."""

        search_text = self._search_entry.get_text()
        self.emit("row-activated", row, search_text)

    def _on_row_modified(self, row: CommandRow) -> None:
        """Handle row value changes."""

        self.emit("row-modified", row)
