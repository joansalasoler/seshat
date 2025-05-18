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

from typing import Callable, List
from .action_registry import ActionRegistry
from .action_provider import ActionProvider


class TextProvider(ActionProvider):
    """Provider for text manipulation actions."""

    def text_upper(self, query: str, text: str) -> str:
        """Convert text to uppercase."""

        return text.upper()

    def text_lower(self, query: str, text: str) -> str:
        """Convert text to lowercase."""

        return text.lower()

    def text_title(self, query: str, text: str) -> str:
        """Convert text to title case."""

        return text.title()

    def text_capitalize(self, query: str, text: str) -> str:
        """Capitalize the first character of each line."""

        callback = lambda line: line.capitalize()
        return "".join(self._for_each_line(text, callback))

    def text_strip(self, query: str, text: str) -> str:
        """Strip whitespace from the beginning and end of each line."""

        callback = lambda line: line.strip()
        return "".join(self._for_each_line(text, callback))

    def line_sort_ascending(self, query: str, text: str) -> str:
        """Sort lines in ascending order."""

        return "".join(sorted(self._split_lines(text)))

    def line_sort_descending(self, query: str, text: str) -> str:
        """Sort lines in descending order."""

        return "".join(sorted(self._split_lines(text), reverse=True))

    def line_reverse(self, query: str, text: str) -> str:
        """Reverse the order of lines."""

        return "".join(reversed(self._split_lines(text)))

    def line_remove_empty(self, query: str, text: str) -> str:
        """Remove empty lines from text."""

        return "".join([
            line for line in self._split_lines(text)
            if len(line.strip()) > 0
        ])

    def line_remove_duplicates(self, query: str, text: str) -> str:
        """Remove duplicate consecutive lines."""

        result = []
        previous = None
        lines = self._split_lines(text)

        for line in lines:
            if line != previous:
                result.append(line)
                previous = line

        return "".join(result)

    def register(self, registry: ActionRegistry) -> None:
        """Register text actions with the action registry."""

        registry.register("text:capitalize", self.text_capitalize)
        registry.register("text:lower", self.text_lower)
        registry.register("text:remove_duplicates", self.line_remove_duplicates)
        registry.register("text:remove_empty", self.line_remove_empty)
        registry.register("text:reverse", self.line_reverse)
        registry.register("text:sort_ascending", self.line_sort_ascending)
        registry.register("text:sort_descending", self.line_sort_descending)
        registry.register("text:strip", self.text_strip)
        registry.register("text:title", self.text_title)
        registry.register("text:upper", self.text_upper)

    def _split_lines(self, text: str) -> List[str]:
        """Split into lines while preserving line endings."""

        return text.splitlines(keepends=True)

    def _preserve_indent(self, text: str, callback: Callable) -> str:
        """Apply a callback while preserving indentation."""

        stripped = text.lstrip(' \t')
        indent_length = len(text) - len(stripped)
        indent = text[:indent_length]
        return indent + callback(stripped)

    def _for_each_line(self, text: str, callback: Callable) -> List[str]:
        """Apply a callback to each individual line."""

        return [
            self._preserve_indent(line, callback)
            for line in self._split_lines(text)
        ]
