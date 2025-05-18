from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .action_registry import ActionRegistry


class ActionProvider(ABC):

    @abstractmethod
    def register(self, registry: "ActionRegistry"):
        """Register all actions in the given registry."""
