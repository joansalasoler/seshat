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

from typing import Callable, Dict, Any, Set, TYPE_CHECKING
from asyncio import iscoroutinefunction

if TYPE_CHECKING:
    from .action_provider import ActionProvider


class ActionRegistry:
    """A singleton registry for managing and executing actions.

    This class provides a centralized registry for actions that can be
    invoked by name throughout the application.
    """

    _instance = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "ActionRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, '_initialized'):
            self._actions: Dict[str, Callable] = {}
            self._providers: Set["ActionProvider"] = set()
            self._initialized = True

    def add_provider(self, provider: "ActionProvider") -> None:
        """Register an action provider and all its actions"""

        if provider not in self._providers:
            self._providers.add(provider)
            provider.register(self)

    def register(self, name: str, callback: Callable) -> None:
        """Register an action with the registry.

        Args:
            name: A unique identifier for the action
            callback: A callable that implements the action
        """

        self._actions[name] = callback

    async def invoke(self, name: str, query: str, selection: str) -> str:
        """Invoke a registered action by name.

        Args:
            name: The identifier of the action to invoke
            query: The query string to pass to the action
            selection: The selected text to pass to the action

        Returns:
            The result of the invoked action
        """

        callback = self._actions[name]

        if iscoroutinefunction(callback):
            return await callback(query, selection)

        return callback(query, selection)
