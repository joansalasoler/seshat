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

import json, re, locale
import asyncio, aiohttp
from locale import gettext as _
from datetime import datetime

from seshat import RESOURCES_DIR
from .action_registry import ActionRegistry
from .action_provider import ActionProvider

# Find JSON matches on a text
JSON_REGEX = re.compile(r'({.*?})', flags=re.DOTALL)


class ChatProvider(ActionProvider):
    """Generative AI action provider"""

    def __init__(self) -> None:
        self._base_prompt: str = self._read_base_prompt()
        self._response_format: dict = self._get_response_format()
        self._base_url = "http://localhost:11434"
        self._default_model = "gemma3:4b"
        self._user_context = {}

    def set_default_model(self, model: str) -> None:
        """Set the default model name."""

        self._default_model = model

    def set_base_url(self, url: str) -> None:
        """Set the base URL for ollama."""

        self._base_url = url

    def set_user_context(self, context: dict) -> None:
        """Set the user context data."""

        self._user_context = context

    def register(self, registry: ActionRegistry) -> None:
        """Register generative AI actions."""

        registry.register("ai:query", self.query_model)

    async def query_model(self, query: str, text: str) -> str:
        """Queries the AI model with a task and selected text."""

        try:
            messages = self._build_messages(query, text)
            response = await self._post_chat(messages)
            content = self._extract_json(response)
            self._raise_for_error(content)
            return content["answers"]
        except asyncio.CancelledError:
            raise
        except json.JSONDecodeError:
            raise ValueError(_("Invalid response from model"))
        except Exception as e:
            raise RuntimeError(e)

    async def _post_chat(self, messages: list) -> str:
        """Sends a chat messages and returns the response"""

        url = f"{self._base_url}/api/chat"

        payload = {
            "model": self._default_model,
            "format": self._response_format,
            "messages": messages,
            "stream": False
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload) as response:
                    self._raise_for_status(response)
                    data = await response.json()
                    return data["message"]["content"]
            except aiohttp.ClientConnectorError:
                raise ValueError(_(
                    "Cannot connect to AI service at '%s'. "
                    "Please check if the service is running."
                    ) % self._base_url
                )

    def _read_base_prompt(self) -> str:
        """Reads the base prompt from the resources directory."""

        with open(RESOURCES_DIR / "prompt.ai", "r") as f:
            return f.read()

    def _build_messages(self, query: str, text: str) -> list:
        """Constructs the messages for the AI model."""

        return [{
            "role": "system",
            "content": self._build_system_prompt()
        }, {
            "role": "user",
            "content": json.dumps({
                "task": query,
                "selected_text": text
            })
        }]

    def _build_system_prompt(self) -> str:
        """Builds the system prompt with context information."""

        prompt = self._base_prompt
        context = self._get_system_context()
        context.update(self._user_context)
        prompt += self._format_context(context)

        return prompt

    def _format_context(self, context: dict) -> str:
        """Formats context dictionary as a string for the prompt."""

        return '\n'.join(
            f"* {key}: {value}"
            for key, value in context.items() if value is not None
        )

    def _extract_json(self, text: str) -> dict:
        """Extracts the first valid JSON object from a string."""

        matches = JSON_REGEX.findall(text)

        for match in matches:
            try:
                content = json.loads(match)
                return self._normalize_response(content)
            except json.JSONDecodeError:
                pass

        raise ValueError(_("No response could be generated."))

    def _raise_for_error(self, content: dict) -> None:
        """Raises ValueError if the response status is 'error'."""

        if content.get("status") == "error":
            message = content.get("error_message", _("Unknown error"))
            raise ValueError(message)

        if content.get("answers") is None:
            raise ValueError(_("No response could be generated."))

    def _raise_for_status(self, response) -> None:
        """Raises ValueError if the response status is 'error'."""

        if response.status == 404:
            raise ValueError(
                _("Model or API endpoint not found: '%s' at '%s'") % (
                    self._default_model, self._base_url)
            )

        response.raise_for_status()

    def _normalize_response(self, content: dict) -> dict:
        """Normalizes the model response to ensure it is valid."""

        answers = content.get("answers")

        if answers is not None:
            if isinstance(answers, str):
                content["answers"] = [answers]
            elif isinstance(answers, list):
                content["answers"] = [str(a) for a in answers]
            else:
                content["answers"] = [str(answers)]

        return content

    def _get_system_context(self) -> dict:
        """Returns a dictionary with current system context."""

        now = datetime.now()
        today = now.date()

        return {
            "User language": locale.getdefaultlocale()[0],
            "Current date": today.isoformat(),
            "Current time": now.strftime("%H:%M"),
            "Current day name": now.strftime("%A"),
            "Current day number": now.day,
            "Current month name": now.strftime("%B"),
            "Current month number": now.month,
            "Current year": now.year,
            "Current timezone": str(now.astimezone().tzinfo),
        }

    def _get_response_format(self) -> dict:
        """Returns the expected response format for the AI model."""

        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["success", "error"]
                },
                "answers": {
                    "type": "array",
                    "items": { "type": "string" },
                    "minItems": 1
                },
                "error_message": { "type": "string" }
            },
            "required": ["status", "answers", "error_message"]
        }
