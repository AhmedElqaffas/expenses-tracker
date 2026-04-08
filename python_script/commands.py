from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Callable


@dataclass
class CommandArg:
    name: str  # display name, e.g. "amount"
    description: str
    required: bool
    suggestions_supplier: Callable[[], list[str]] | None = None  # None = free text
    multi: bool = False


@dataclass
class Command:
    name: str
    description: str
    args: list[CommandArg] = field(default_factory=list)


class Commands(StrEnum):
    LOAD_CATEGORIES = "load_categories"
    ADD_CATEGORY = "add_category"
    REMOVE_CATEGORY = "remove_category"
    RECORD_SPENDING = "record_spending"


class CommandService(ABC):
    """Base class for all command services. Each service registers its own commands."""

    @abstractmethod
    def get_commands(self) -> list[Command]:
        """Return all commands this service handles."""
        ...

    @abstractmethod
    async def execute(self, command: str, args: dict[str, list[str]], app) -> None:
        """Execute a command with the given parsed args."""
        ...
