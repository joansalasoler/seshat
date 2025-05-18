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

import logging
from typing import List
from collections.abc import Iterable
from gi.repository import Gtk, Gdk, Gio, GLib

from seshat import APP_ID, RESOURCES_DIR
from seshat.tasks import TaskContext, TaskExecutor
from seshat.utils import ClipboardManager, ConfigManager, HotkeyListener
from seshat.actions import ChatProvider, TextProvider, MathProvider
from seshat.actions import ActionRegistry

from .command_palette import CommandPalette
from .command_row import CommandRow
from .command import Command

_logger = logging.getLogger(__name__)


class Application(Gtk.Application):
    """Main application class."""

    _flags = Gio.ApplicationFlags.HANDLES_COMMAND_LINE

    def __init__(self) -> None:
        super().__init__(application_id=APP_ID, flags=self._flags)
        self._executor = TaskExecutor()
        self._hotkey_listener = None
        self._commands: List[Command] = []
        self._is_active: bool = False
        self._input: str = str()
        self._output: str | Iterable | None = None

        # Connect signals
        self.connect('activate', self._on_activate)
        self.connect('shutdown', self._on_shutdown)
        self.connect('command-line', self._on_command_line)

        # Add command line options
        self._add_cli_flag("show-palette", "Activate the palette")
        self._add_cli_option("input-device", "Device to listen for hotkeys")

    def show_palette(self) -> None:
        """Show the command palette"""

        self._clipboard.read_selection(lambda text:
            self._on_activate_palette(self._palette, text))

    def _connect_signals(self) -> None:
        """Connect all required signals for the palette window."""

        self._palette.connect("hide", self._on_deactivate_palette)
        self._palette.connect("row-activated", self._on_row_activated)
        self._palette.connect("row-modified", self._on_row_modified)
        self._palette.connect("search-changed", self._on_search_changed)
        self._palette.connect("search-stopped", self._on_focus_leave)
        self._palette.connect("key-pressed", self._on_key_pressed)
        self._palette.connect("focus-lost", self._on_focus_leave)
        self._executor.connect('on-task-success', self._on_task_success)
        self._executor.connect('on-task-error', self._on_task_error)

    def _on_activate(self, app: Gtk.Application) -> None:
        """Handle application activation."""

        self._config = ConfigManager()
        self._palette = CommandPalette(self)
        self._clipboard = ClipboardManager()
        self._palette.set_command_sort(self._sort_row)
        self._palette.set_command_filter(self._filter_row)
        self._setup_clipboard(self._clipboard)
        self._setup_window_size(self._palette)
        self._setup_window_css(self._palette)
        self._setup_commands(self._palette)
        self._setup_actions(self._config)
        self._connect_signals()
        self._is_active = True

    def _on_shutdown(self, app: Gtk.Application) -> None:
        """Handle application shutdown."""

        self._executor.shutdown()

        if self._hotkey_listener:
            self._hotkey_listener.shutdown()

        if hasattr(self, "_config"):
            app._config.close()

    def _on_activate_palette(self, palette: CommandPalette, text: str) -> None:
        """Handle palette activation."""

        self._output = None
        self._input = text
        palette.hide_status()
        palette.show_commands()
        palette.present()

    def _on_deactivate_palette(self, palette: CommandPalette) -> None:
        """Handle palette deactivation."""

        if self._output is not None:
            text = self._output
            self._clipboard.set_and_paste(text)

    def _on_search_changed(self, palette: CommandPalette, query: str) -> None:
        """Handle search text changes in the palette."""

        palette.hide_status()
        palette.show_commands()
        self._executor.cancel_task()
        self._prefetch_answers(query)
        palette.update_view(query)

    def _on_focus_leave(self, palette: CommandPalette) -> None:
        """Handle focus loss events."""

        self._executor.cancel_task()
        palette.hide()

    def _on_key_pressed(self,
        palette: CommandPalette, keyval: int, keycode: int, state: int) -> bool:
        """Handle key press events in the palette."""

        if keyval == Gdk.KEY_Escape:
            self._executor.cancel_task()
            palette.hide()
            return True
        elif keyval == Gdk.KEY_Down:
            palette.navigate_next()
            return True
        elif keyval == Gdk.KEY_Up:
            palette.navigate_previous()
            return True

        return False

    def _on_row_modified(self,
        palette: CommandPalette, row: CommandRow) -> None:
        """Handle command changes in the palette."""

        command = row.get_command()
        self._config.save_usage(command.to_dict())

    def _on_row_activated(self,
        palette: CommandPalette, row: CommandRow, query: str) -> None:
        """Handle row activation in the palette."""

        def _update_progress():
            self._palette.pulse_progress()
            return self._executor.is_running()

        command = row.get_command()
        self._executor.submit(command, query, self._input)

        palette.show_status("I'm working on it —please hold on.")
        GLib.timeout_add(100, _update_progress)

    def _on_task_success(self, executor: TaskExecutor, task: TaskContext) -> None:
        """Handle successful task completion."""

        if isinstance(task.result, list):
            self._palette.clear_answers()

            for answer in task.result:
                command = Command.from_answer(answer)
                self._palette.add_answer(command)

            self._palette.show_answers()
            self._palette.hide_status()
            self._palette.update_view()
        else:
            self._output = task.result
            self._palette.hide_status()
            self._palette.hide()

        if not task.command.is_answer:
            command_dict = task.command.to_dict()
            self._config.save_usage(command_dict)

        if task.command.is_template:
            self._add_saved_command(task.query, task.command)

    def _on_task_error(self,
        executor: TaskExecutor, task: TaskContext) -> None:
        """Handle task completion with errors."""

        self._output = None
        self._palette.show_status(str(task.error), "error")

    def _on_command_line(self,
        app: Gtk.Application, cli: Gio.ApplicationCommandLine) -> int:
        """Handle command line arguments."""

        options = cli.get_options_dict().end().unpack()

        if not app._is_active:
            app.activate()

        if "show-palette" in options:
            app.show_palette()

        if "input-device" in options:
            device_path = options["input-device"]
            self._setup_hotkey_listener(device_path)

        return 0

    def _filter_row(self, row: CommandRow) -> bool:
        """Filter function for command rows."""

        command = row.get_command()
        search_text = self._palette.get_search_text()
        has_query = len(search_text.strip()) > 0

        if command.is_fallback:
            return has_query

        if command.is_proactive:
            return command.answer is not None

        return (
            has_query is False or
            search_text.lower() in command.label.lower()
        )

    def _sort_row(self, row1: CommandRow, row2: CommandRow) -> int:
        """Sort function for command rows."""

        command1 = row1.get_command()
        command2 = row2.get_command()

        value1 = command1.answer
        value2 = command2.answer

        if value1 is not None and value2 is None:
            return -1

        starred1 = command1.is_starred
        starred2 = command2.is_starred

        if starred1 != starred2:
            return -1 if starred1 else 1

        stamp1 = command1.last_invoked
        stamp2 = command2.last_invoked

        if stamp1 != stamp2:
            return -1 if stamp1 > stamp2 else 1

        label1 = row1.get_text().lower()
        label2 = row2.get_text().lower()

        return -1 if label1 < label2 else 1

    def _prefetch_answers(self, query: str) -> None:
        """Prefetch results for proactive commands."""

        commands = [a for a in self._commands if a.is_proactive]

        for command in commands:
            try:
                command.prefetch(query, self._input)
            except Exception as e:
                _logger.error("Prefetch error: %s", e)

    def _add_saved_command(self, query: str, command: Command) -> None:
        """Add a new command from a template."""

        command = Command.from_template(query, command)
        command_dict = command.to_dict()

        self._config.save_command(command_dict)
        self._config.save_usage(command_dict)
        self._palette.add_command(command)
        self._commands.append(command)

    def _add_cli_flag(self, name: str, description: str) -> None:
        """Add a command line flag option."""

        flags = GLib.OptionFlags.NONE
        args = GLib.OptionArg.NONE
        self.add_main_option(name, 0, flags, args, description, None)

    def _add_cli_option(self, name: str, description: str) -> None:
        """Add a command line string option."""

        flags = GLib.OptionArg.NONE
        args = GLib.OptionArg.STRING
        self.add_main_option(name, 0, flags, args, description, None)

    def _setup_commands(self, palette: CommandPalette) -> None:
        """Initialize available commands from configuration."""

        data = self._config.get_commands()
        self._commands = Command.from_dict_list(data)

        for command in self._commands:
            palette.add_command(command)

    def _setup_actions(self, config: ConfigManager) -> None:
        """Setup actions for the application."""

        base_url = config.get_option("chat_base_url")
        model_name = config.get_option("chat_default_model")
        user_context = config.get_option("chat_user_context")

        registry = ActionRegistry()

        chat_provider = ChatProvider()
        chat_provider.set_base_url(base_url)
        chat_provider.set_default_model(model_name)
        chat_provider.set_user_context(user_context)

        registry.add_provider(chat_provider)
        registry.add_provider(MathProvider())
        registry.add_provider(TextProvider())

    def _setup_window_size(self, window: CommandPalette) -> None:
        """Set the window size from configuration."""

        width = self._config.get_option("window_width")
        height = self._config.get_option("window_height")
        window.set_default_size(width, height)
        window.set_size_request(width, -1)

    def _setup_window_css(self, window: CommandPalette) -> None:
        """Set up CSS styling for the window."""

        path = RESOURCES_DIR / "theme.css"
        display = window.get_display()
        provider = Gtk.CssProvider()
        provider.load_from_path(str(path.resolve()))
        Gtk.StyleContext.add_provider_for_display(
            display, provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    def _setup_clipboard(self, clipboard: ClipboardManager) -> None:
        """Configure the clipboard manager."""

        keybinding = self._config.get_option("paste_keybinding")
        delay = self._config.get_option("paste_delay")
        clipboard.set_paste_keybinding(keybinding)
        clipboard.set_paste_delay(delay)

    def _setup_hotkey_listener(self, device_path: str) -> None:
        """Set up the hotkey listener for palette activation."""

        poll_interval = self._config.get_option("hotkey_poll_interval")
        modifiers_keys = self._config.get_option("hotkey_modifiers")
        trigger_key = self._config.get_option("hotkey_trigger")

        self._hotkey_listener = HotkeyListener(device_path)
        self._hotkey_listener.set_poll_interval(poll_interval)
        self._hotkey_listener.set_modifier_keys(modifiers_keys)
        self._hotkey_listener.set_trigger_key(trigger_key)
        self._hotkey_listener.add_callback(self.show_palette)
        self._hotkey_listener.start()
