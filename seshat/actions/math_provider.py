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

import re
from locale import gettext as _
from collections.abc import Iterable
from functools import lru_cache
from multiprocessing import Process, Queue, queues
from typing import Any, Tuple, Optional
from asteval import Interpreter

from .action_registry import ActionRegistry
from .action_provider import ActionProvider

# Removes operation symbols from the end
CLEAN_REGEX = re.compile(r'[\+\-\*/%&|^]+[\s]*$')


class MathProvider(ActionProvider):
    """Provides math evaluation actions."""

    _process: Optional[Process] = None
    _queue_in: Optional[Queue] = None
    _queue_out: Optional[Queue] = None

    def __init__(self):
        super().__init__()
        self._evaluate = lru_cache()(self._evaluate_expression)

    @classmethod
    def _engage_process(cls) -> None:
        """Spawn a new process if it is not running."""

        if not cls._process or not cls._process.is_alive():
            target = cls._run_loop
            cls._queue_in = Queue()
            cls._queue_out = Queue()
            cls._process = Process(target=target, daemon=True)
            cls._process.start()

    @classmethod
    def _terminate_process(cls) -> None:
        """Terminate the worker process and clean up resources."""

        if cls._process and cls._process.is_alive():
            cls._process.terminate()
            cls._process.join(timeout=1)
            cls._queue_in = None
            cls._queue_out = None
            cls._process = None

    @classmethod
    def _run_loop(cls) -> None:
        """Worker process that evaluates math expressions."""

        process = cls._process
        queue_in = cls._queue_in
        queue_out = cls._queue_out
        asteval = Interpreter(minimal=True)

        while process.is_alive():
            text = queue_in.get()
            result, error = cls._process_task(asteval, text)
            queue_out.put((result, error))

    @classmethod
    def _process_task(cls, asteval: Interpreter, text: str) -> Tuple:
        """Evaluate a math expression and return the result"""

        try:
            result = asteval.eval(text, show_errors=False)

            if len(asteval.error) > 0:
                raise SyntaxError(
                    _("Could not evaluate expression")
                    if len(asteval.error_msg) < 1 else
                    asteval.error_msg
                )

            if callable(result):
                raise ValueError(_("Expression returned a callback."))

            if isinstance(result, Iterable):
                if not isinstance(result, str):
                    result = ", ".join(map(str, result))

            if result is None or str(result).strip() == str():
                raise ValueError(_("Expression evaluates to nothing"))

            return (str(result), None)
        except Exception as e:
            return (None, str(e))

    def _evaluate_expression(self, text: str, timeout: float) -> str:
        """Evaluate a math expression in a separate process."""

        self._engage_process()
        self._queue_in.put(text)

        try:
            result, error = self._queue_out.get(timeout=timeout)
            if error is not None: raise SyntaxError(error)
            return self._to_str(result)
        except queues.Empty:
            self._terminate_process()
            raise TimeoutError(_("Evaluation timed out"))

    def _to_str(self, content: Any) -> str:
        """Convert any content to a string representation."""

        if isinstance(content, str):
            return content

        if isinstance(content, Iterable):
            return "".join([str(value) for value in content])

        return str(content)

    def evaluate_text(self, query: str | None, text: str) -> str:
        """Evaluate text as a math expression."""

        text = CLEAN_REGEX.sub('', text).strip()
        return self._evaluate(text, timeout=10.0)

    def evaluate_query(self, query: str, text: str) -> str:
        """Evaluate a user query as a math expression."""

        query = CLEAN_REGEX.sub('', query).strip()
        return self._evaluate(query, timeout=1.0)

    def register(self, registry: ActionRegistry) -> None:
        """Register math evaluation actions."""

        registry.register("math:evaluate_text", self.evaluate_text)
        registry.register("math:evaluate_query", self.evaluate_query)
