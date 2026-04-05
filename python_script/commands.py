from abc import ABC, abstractmethod
from enum import StrEnum
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ArgSpec:
    name: str # display name, e.g. "amount"
    suggestions_supplier: Callable[[any], list[str]] | None = None  # empty = free text

@dataclass
class CommandSpec:
    name: str
    description: str
    args: list[ArgSpec] = field(default_factory=list)

class Commands(StrEnum):
    PRINT = "print"
    ADD_CATEGORY = "add_category"
    REMOVE_CATEGORY = "remove_category"

# Slash command registry
SLASH_COMMANDS = {
    Commands.PRINT: {
        "usage": "/print <level> <message>",
        "description": "Print a message with a log level",
        "args": [
            ArgSpec("log_level", lambda x : ["info", "warning", "error"]),
            ArgSpec("message"),  # free text, no suggestions
        ],
    },
}

class CommandService(ABC):
    """Base class for all command services. Each service registers its own commands."""

    @abstractmethod
    def get_commands(self) -> list[CommandSpec]:
        """Return all commands this service handles."""
        ...

    @abstractmethod
    async def execute(self, command: str, args: dict[str, str], app) -> None:
        """Execute a command with the given parsed args."""
        ...