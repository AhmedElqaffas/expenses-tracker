from commands import Command, CommandService


class CommandRegistry:
    """Central registry that aggregates commands from all registered services."""

    def __init__(self):
        self._services: dict[str, CommandService] = {}  # command name -> service
        self._specs: dict[str, Command] = {}        # command name -> spec

    def register(self, service: CommandService) -> None:
        for spec in service.get_commands():
            if spec.name in self._specs:
                raise ValueError(f"Command '{spec.name}' is already registered.")
            self._specs[spec.name] = spec
            self._services[spec.name] = service

    def get_spec(self, command: str) -> Command | None:
        return self._specs.get(command)

    def all_specs(self) -> dict[str, Command]:
        return self._specs

    def all_services(self) -> dict[str, CommandService]:
        return self._services

    async def execute(self, command: str, args: dict[str, str], app) -> None:
        service = self._services.get(command)
        if not service:
            raise KeyError(f"No service registered for command '{command}'.")
        await service.execute(command, args, app)

registry = CommandRegistry()