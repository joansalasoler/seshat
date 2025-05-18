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

import asyncio
from time import time
from typing import List
from uuid import uuid4
from dataclasses import dataclass, asdict, field, fields
from seshat.actions import ActionRegistry

_registry = ActionRegistry()

# Action name for all answer commands
ANSWER_ACTION = "<answer>"

# Default icon for saved actions
SAVED_ACTION_ICON = "insert-text-symbolic"


@dataclass
class Command:
    """A command that can be executed from the palette."""

    uuid: str = field(default_factory=lambda: str(uuid4()))
    label: str = field(default="Action")
    icon_name: str = field(default="edit-paste-symbolic")
    action_name: str = field(default=ANSWER_ACTION)
    last_invoked: float = field(default=0)
    user_query: str | None = field(default=None)
    answer: str | None = field(default=None)
    is_starred: bool = field(default=False)
    is_proactive: bool = field(default=False)
    is_fallback: bool = field(default=False)
    is_template: bool = field(default=False)
    is_builtin: bool = field(default=False)

    @property
    def is_answer(self) -> bool:
        """Check if the command is an answer."""

        return self.action_name == ANSWER_ACTION

    async def invoke(self, query: str, text: str) -> str:
        """Execute the command and return its result.

        Args:
            query: The query string to use for the command
            text: The currently selected text

        Returns:
            The result of the command

        Raises:
            Any exception
        """

        self.last_invoked = time()
        if self.answer is not None: return self.answer
        query = self.user_query if self.user_query else query
        return await _registry.invoke(self.action_name, query, text)

    def prefetch(self, query: str, text: str) -> str:
        """Prefetch the result of this command and store it.

        Args:
            query: The query string to use for the command
            text: The currently selected text

        Returns:
            The result of the command
        """

        try:
            query = self.user_query if self.user_query else query
            coroutine = _registry.invoke(self.action_name, query, text)
            self.answer = str(asyncio.run(coroutine))
        except Exception:
            self.answer = None

        return self.answer

    @classmethod
    def from_answer(cls, answer: str) -> "Command":
        """Create a command from a template.

        Args:
            answer: Predefined command answer

        Returns:
            A new command instance
        """

        return cls.from_dict({
            "label": answer.strip(),
            "action_name": ANSWER_ACTION,
            "icon_name": "edit-paste-symbolic",
            "answer": answer,
        })

    @classmethod
    def from_template(cls,
        query: str, template: "Command") -> "Command":
        """Create a command from a template.

        Args:
            query: User query
            template: Template to use for the command

        Returns:
            A new command instance
        """

        clone = template.to_dict()
        clone.update(label=query)
        clone.update(uuid=str(uuid4()))
        clone.update(icon_name=SAVED_ACTION_ICON)
        clone.update(user_query=query)
        clone.update(is_starred=False)
        clone.update(is_template=False)
        clone.update(is_fallback=False)
        clone.update(is_builtin=False)

        return cls.from_dict(clone)

    @classmethod
    def from_dict(cls, data: dict) -> "Command":
        """Create a command from a dictionary.

        Args:
            data: A dictionary containing command properties

        Returns:
            A new command instance
        """

        return cls(**{
            field.name: data.get(field.name)
            for field in fields(cls)
            if field.name in data
        })

    @classmethod
    def from_dict_list(cls, data: List[dict]) -> "List[Command]":
        """Create commands from a list of dictionaries.

        Args:
            data: A list of dictionaries

        Returns:
            A list of command instances
        """

        return [cls.from_dict(data) for data in data]

    def to_dict(self) -> dict:
        """Convert the command to a dictionary.

        Returns:
            A dictionary representation of the command
        """

        values = asdict(self)
        values.pop("answer")

        return values