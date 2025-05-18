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

import dbm, json, logging
from pathlib import Path
from typing import Any
from seshat import RESOURCES_DIR, CONFIG_DIR

_logger = logging.getLogger(__name__)


class ConfigManager:
    """A singleton manager for application configuration."""

    _instance = None
    _usage_fields = ["last_invoked", "is_starred"]

    def __new__(cls, *args, **kwargs) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, '_initialized'):
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            self._defaults_path = RESOURCES_DIR / "config.json"
            self._config_path = CONFIG_DIR / "config.json"
            self._commands_db = self._open_database("commands.dbm")
            self._usage_db = self._open_database("usage.dbm")
            self._commands: dict = {}
            self._config: dict = {}
            self._initialized = True
            self._load_config()

    def __del__(self):
        self.close()

    def get_option(self, key: str, fallback: Any = None) -> Any:
        """Get a configuration value by key."""

        return self._config.get(key, fallback)

    def get_commands(self) -> list:
        """Get a list of commands from the configuration."""

        return self._commands.values()

    def save_command(self, command: dict) -> None:
        """Adds a new command to persistent storage."""

        uuid = command["uuid"]

        try:
            if self._commands_db is not None:
                key = uuid.encode('utf-8')
                values = json.dumps(command)
                self._commands_db[key] = values.encode('utf-8')
                self._commands_db.sync()
        except Exception as e:
            _logger.error("Error saving command: %s", e)
        finally:
            self._commands[uuid] = command

    def save_usage(self, command: dict) -> None:
        """Persist usage statistics for a command."""

        if self._usage_db is None:
            return

        try:
            key = command["uuid"].encode('utf-8')
            values = {k: command[k] for k in self._usage_fields}
            data = json.dumps(values).encode('utf-8')
            self._usage_db[key] = data
            self._usage_db.sync()
        except Exception as e:
            _logger.error("Error saving usage: %s", e)

    def close(self):
        """Close all database connections."""

        try:
            self._clean_up()
            self._usage_db.close()
            self._commands_db.close()
        except Exception as e:
            _logger.error("Error closing databases: %s", e)

    def _load_config(self) -> None:
        """Load the application configuration"""

        self._load_from_json(self._defaults_path)

        if self._config_path.exists():
            self._load_from_json(self._config_path)

        if not self._config_path.exists():
            if self._commands_db is not None:
                self._prefill_user_config()
                self._prefill_saved_commands()

        if self._commands_db is not None:
            self._load_saved_commands()

        if self._usage_db is not None:
            self._load_command_usage()

    def _load_saved_commands(self) -> None:
        """Load saved commands from the database"""

        try:
            for key in self._commands_db.keys():
                uuid = key.decode('utf-8')

                if uuid not in self._commands:
                    value = self._commands_db[key].decode('utf-8')
                    self._commands[uuid] = json.loads(value)
        except Exception as e:
            _logger.error("Error loading saved commands: %s", e)

    def _prefill_saved_commands(self) -> None:
        """Load saved commands from the database"""

        try:
            path = RESOURCES_DIR / "examples.json"

            with path.open('r') as f:
                for command in json.load(f)["commands"]:
                    self.save_command(command)
        except Exception as e:
            _logger.error("Error prefilling saved commands: %s", e)

    def _prefill_user_config(self) -> None:
        """Create a user configuration"""

        with self._config_path.open('w') as f:
            json.dump(self._config, f, indent=4)

    def _load_command_usage(self) -> None:
        """Load command usage from the database"""

        try:
            for key in self._usage_db.keys():
                uuid = key.decode('utf-8')

                if uuid in self._commands:
                    command = self._commands[uuid]
                    data = self._usage_db[key].decode('utf-8')
                    command.update(json.loads(data))
        except Exception as e:
            _logger.error("Error loading usage: %s", e)

    def _load_from_json(self, path: Path) -> dict:
        """Load and parse a JSON file."""

        try:
            with path.open('r') as f:
                config = json.load(f)

                for key, value in config.items():
                    if key != "commands" and value != None:
                        self._config[key] = value

                for command in config.get("commands", []):
                    uuid = command["uuid"]
                    self._commands[uuid] = command
        except Exception as e:
            _logger.error("Error loading config: %s", e)

    def _open_database(self, name: str):
        """Open a database file."""

        try:
            path = CONFIG_DIR / name
            return dbm.open(path, flag="c")
        except Exception as e:
            _logger.error("Error opening database: %s", e)

    def _clean_up(self):
        """Remove expired entries from the databases"""

        def _filter(key):
            uuid = key.decode('utf-8')
            command = self._commands[uuid]
            return not command.get("is_starred", False)

        def _sort(key):
            uuid = key.decode('utf-8')
            command = self._commands[uuid]
            return command.get("last_invoked", 0)

        keys = list(filter(_filter, self._commands_db.keys()))
        max_commands = self.get_option("max_user_commands", 100)

        if len(keys) <= max_commands:
            return

        keys = sorted(keys, key=_sort)
        excess_commands = len(keys) - max_commands

        for key in keys[:excess_commands]:
            del self._commands_db[key]
            del self._usage_db[key]

        self._commands_db.sync()
        self._usage_db.sync()
