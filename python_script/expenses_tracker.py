import os
import sys
from dataclasses import dataclass, field
from typing import Union

from dotenv import load_dotenv
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Input, Label

from categories_service import CategoriesService
from commands import CommandArg
from commands_registry import CommandRegistry
from spending_service import SpendingService
from suggesstions_list import CommandSuggestions
from text_area import MainTextArea


@dataclass
class InputState:
    command: Union[str, None] = None
    collected_args: dict[str, str] = field(default_factory=dict)
    current_arg_index: int = 0

    def current_arg(self, commands: dict) -> Union[CommandArg, None]:
        if not self.command:
            return None
        args = commands[self.command].args
        if self.current_arg_index < len(args):
            return args[self.current_arg_index]
        return None

    def is_complete(self, commands: dict) -> bool:
        if not self.command:
            return False
        return self.current_arg_index >= len(commands[self.command].args)

    def reset(self) -> None:
        self.command = None
        self.collected_args = {}
        self.current_arg_index = 0


class ExpensesTracker(App):
    """TUI app for managing expenses"""

    DEFAULT_CSS = """
    #input_row {
        height: 3;
        align: left middle;
    }

    #input_prefix {
        height: 3;
        content-align: left middle;
        padding: 0 1;
        color: $text-muted;
        width: auto;
    }

    #input {
        width: 1fr;
        border: none;
    }
    """

    AUTO_FOCUS = "#input"

    categories_service: CategoriesService
    spending_service: SpendingService

    text_area: MainTextArea
    input_field: Input
    suggestions_list: CommandSuggestions
    prefix: Label

    state = InputState()

    def __init__(self, categories_service: CategoriesService,
                 spending_service: SpendingService) -> None:
        super().__init__()
        self._load_env()
        self.categories_service = categories_service
        self.spending_service = spending_service
        categories_service.load_categories()
        self.command_registry = CommandRegistry()
        self.command_registry.register(categories_service)
        self.command_registry.register(spending_service)

    def _load_env(self):
        load_dotenv()
        if getattr(sys, 'frozen', False):  # running from a PyInstaller exe
            basedir = sys._MEIPASS
        else:
            basedir = os.path.dirname(__file__)
        load_dotenv(os.path.join(basedir, ".env"))

    def compose(self) -> ComposeResult:
        self.text_area = MainTextArea(id="output")
        yield self.text_area
        self.suggestions_list = CommandSuggestions(id="suggestions")
        yield self.suggestions_list
        with Horizontal(id="input_row"):
            self.prefix = Label("", id="input_prefix")
            yield self.prefix
            self.input_field = Input(placeholder="Type / for commands", id="input")
            yield self.input_field

    async def on_mount(self) -> None:
        self.text_area.write("\n :wave: [bold]Welcome, spender![/bold]\n\n\n :wave: :wave: [bold]Welcome, spender![/bold] :wave: [bold]Welcome, spender![/bold] :wave: [bold]Welcome, spender![/bold] :wave: [bold]Welcome, spender![/bold] :wave: [bold]Welcome, spender![/bold]\n\n")

    def on_input_changed(self, event: Input.Changed) -> None:
        value = event.value
        specs = self.command_registry.all_specs()

        # Step 1: no command chosen yet — suggest commands on "/"
        if self.state.command is None:
            if value.startswith("/"):
                query = value[1:].lower()
                matches = [
                    (cmd, meta.description)
                    for cmd, meta in specs.items()
                    if cmd.startswith(query)
                ]
                self.suggestions_list.show_suggestions(matches)
            else:
                self.suggestions_list.hide()
            return

        # Step 2+: command chosen, collecting args
        current_arg = self.state.current_arg(specs)
        if current_arg and current_arg.suggestions_supplier:
            matches = [
                (s, current_arg.description)
                for s in current_arg.suggestions_supplier()
                if s.startswith(value.lower())
            ]
            self.suggestions_list.show_suggestions(matches)
        else:
            self.suggestions_list.hide()

    def _update_placeholder(self) -> None:
        specs = self.command_registry.all_specs()
        if self.state.command is None:
            self.input_field.placeholder = "Type / for commands"
            self.prefix.update("")
            return

        # Build prefix from command + collected args so far
        parts = [f"[cyan]/{self.state.command}[/cyan]"]
        for arg_name, arg_value in self.state.collected_args.items():
            parts.append(f"[dim]{arg_name}:[/dim][white]{arg_value}[/white]")
        self.prefix.update(" ".join(parts) + " ")

        # Update placeholder for current arg
        current_arg = self.state.current_arg(specs)
        if current_arg:
            if current_arg.suggestions_supplier and current_arg.suggestions_supplier():
                options = ", ".join(current_arg.suggestions_supplier())
                self.input_field.placeholder = f"{current_arg.name}: {options}"
            else:
                self.input_field.placeholder = f"Enter {current_arg.name}..."
        else:
            self.input_field.placeholder = ""

    def _reset_flow(self) -> None:
        self.state.reset()
        self.input_field.value = ""
        self.prefix.update("")
        self.input_field.placeholder = "Type / for commands"
        self.suggestions_list.hide()

    def on_key(self, event) -> None:
        # Backspace on empty input = undo last step
        if event.key == "backspace" and self.input_field.value == "":
            if self.state.command is not None:
                self._step_back()
                event.stop()
                return

        if "visible" not in self.suggestions_list.classes:
            if event.key == "escape":
                self._reset_flow()
            return



        if event.key == "down":
            self.suggestions_list.action_cursor_down()
            event.stop()
        elif event.key == "up":
            self.suggestions_list.action_cursor_up()
            event.stop()
        elif event.key == "tab":
            self._complete_suggestion()
            event.stop()
        elif event.key == "enter":
            highlighted = self.suggestions_list.highlighted_child
            if highlighted:
                self._complete_suggestion()
                if not self.state.is_complete(self.command_registry.all_specs()):
                    event.prevent_default()  # more args needed, stay in input
                event.stop()
        elif event.key == "escape":
            self.suggestions_list.hide()
            event.stop()

    def _step_back(self) -> None:
        """Undo the last completed step, restoring input to what it was."""
        if self.state.current_arg_index > 0:
            # Undo last collected arg — restore its value to input
            self.state.current_arg_index -= 1
            current_arg = self.state.current_arg(self.command_registry.all_specs())
            last_value = self.state.collected_args.pop(current_arg.name, "")
            self.input_field.value = last_value
        elif self.state.command is not None:
            # Undo command selection — restore "/command" to input
            self.input_field.value = f"/{self.state.command}"
            self.state.command = None

        self._update_placeholder()
        # Move cursor to end of restored value
        self.input_field.cursor_position = len(self.input_field.value)

    def _complete_suggestion(self) -> None:
        highlighted = self.suggestions_list.highlighted_child
        if not highlighted or not highlighted.name:
            return

        name = highlighted.name

        if self.state.command is None:
            # Completing a command — advance to first arg
            self.state.command = name
            self.input_field.value = ""
        else:
            # Completing an arg value
            self._advance_arg(name)

        self.suggestions_list.hide()
        self._update_placeholder()

    def _advance_arg(self, value: str) -> None:
        """Store current arg value and move to the next one."""
        current_arg = self.state.current_arg(self.command_registry.all_specs())
        if current_arg:
            self.state.collected_args[current_arg.name] = value
            self.state.current_arg_index += 1
        self.input_field.value = ""

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        self.suggestions_list.hide()
        raw = event.value.strip()
        specs = self.command_registry.all_specs()

        if self.state.command is None:
            return

        # If already complete (last arg was filled via suggestion), execute immediately
        if self.state.is_complete(specs):
            event.input.clear()
            self._execute_command(self.state.command, self.state.collected_args)
            self._reset_flow()
            return

        # Otherwise collect the current free-text arg from input
        current_arg: CommandArg = self.state.current_arg(specs)
        if current_arg:
            if current_arg.required and not raw:
                self.text_area.write(
                    f"[yellow]Please enter a value for [cyan]{current_arg.name}[/cyan][/yellow]"
                )
                return
            self._advance_arg(raw)

        # Check again after collecting — might now be complete
        if self.state.is_complete(specs):
            event.input.clear()
            self._execute_command(self.state.command, self.state.collected_args)
            self._reset_flow()
        else:
            event.input.clear()
            self._update_placeholder()

    @work()  # for a response UI during database operations (see also: https://textual.textualize.io/guide/workers/)
    async def _execute_command(self, command: str, args: dict[str, str]) -> None:
        await self.command_registry.execute(command, args, self)

if __name__ == "__main__":
    categories_service = CategoriesService()
    app = ExpensesTracker(categories_service, SpendingService(categories_service))
    app.run()
