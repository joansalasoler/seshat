from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from seshat.application import Command


@dataclass
class TaskContext:
    """Encapsulates context for a task execution."""

    command: "Command" = field()
    query: str = field()
    text: str = field()
    error: str | None = field(default=None)
    result: str | list[str] = field(default=None)
    cancelled: bool = field(default=False)