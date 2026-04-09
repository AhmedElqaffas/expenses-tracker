import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
    collected_args: dict[str, list[str]] = field(default_factory=dict)
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
        self.text_area.write("\n :wave: [bold]Welcome, spender![/bold]\n\n\n")

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
            already = self.state.collected_args.get(current_arg.name, [])
            matches = [
                (s, current_arg.description)
                for s in current_arg.suggestions_supplier()
                if s.startswith(value.lower()) and s not in already  # ← filter out picked
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
        for arg_name, arg_values in self.state.collected_args.items():
            display = ", ".join(arg_values)
            parts.append(f"[dim]{arg_name}:[/dim][white]{display}[/white]")
        self.prefix.update(" ".join(parts) + " ")

        # Update placeholder for current arg
        current_arg = self.state.current_arg(specs)
        if current_arg:
            if current_arg.multi:
                existing = self.state.collected_args.get(current_arg.name, [])
                if existing:
                    self.input_field.placeholder = f"Add more {current_arg.name}s, or Enter to finish"
                else:
                    if current_arg.suggestions_supplier and current_arg.suggestions_supplier():
                        options = ", ".join(current_arg.suggestions_supplier())
                        self.input_field.placeholder = f"Select {current_arg.name}(s): {options}"
                    else:
                        self.input_field.placeholder = f"Enter {current_arg.name}(s), Enter when done"
            else:
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

    async def on_key(self, event) -> None:
        if event.key == "backspace" and self.input_field.value == "":
            if self.state.command is not None:
                self._step_back()
                event.stop()
                return

        if event.key == "enter":
            event.stop()
            event.prevent_default()
            if "visible" in self.suggestions_list.classes:
                highlighted = self.suggestions_list.highlighted_child
                if highlighted:
                    was_command = self.state.command is None
                    self._complete_suggestion()
                    if was_command:
                        if not self.state.is_complete(self.command_registry.all_specs()):
                            return  # has args, wait for them
                    else:
                        # check if we just completed a multi-arg value
                        specs = self.command_registry.all_specs()
                        current_arg = self.state.current_arg(specs)
                        if current_arg and current_arg.multi:
                            return  # stay on this arg for more values
            await self._handle_submit(self.input_field.value)
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
        elif event.key == "escape":
            self.suggestions_list.hide()
            event.stop()

    def _step_back(self) -> None:
        specs = self.command_registry.all_specs()
        current_arg = self.state.current_arg(specs)

        # If we're on a multi-arg that already has values, just clear them
        if current_arg and current_arg.multi:
            existing = self.state.collected_args.get(current_arg.name, [])
            if existing:
                self.state.collected_args.pop(current_arg.name)
                self.input_field.value = ""
                self._update_placeholder()
                self.input_field.cursor_position = 0
                return

        # Otherwise step back to previous arg as normal
        if self.state.current_arg_index > 0:
            self.state.current_arg_index -= 1
            current_arg = self.state.current_arg(specs)
            last_values = self.state.collected_args.pop(current_arg.name, [])
            if current_arg.multi:
                self.input_field.value = ""
            else:
                self.input_field.value = last_values[0] if last_values else ""
        elif self.state.command is not None:
            self.input_field.value = f"/{self.state.command}"
            self.state.command = None

        self._update_placeholder()
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
        current_arg = self.state.current_arg(self.command_registry.all_specs())
        if current_arg:
            if current_arg.multi:
                self.state.collected_args.setdefault(current_arg.name, []).append(value)
                if current_arg.suggestions_supplier:  # ← only show suggestions if supplier exists
                    already = self.state.collected_args.get(current_arg.name, [])
                    matches = [
                        (s, current_arg.description)
                        for s in current_arg.suggestions_supplier()
                        if s not in already
                    ]
                    self.suggestions_list.show_suggestions(matches)
            else:
                self.state.collected_args[current_arg.name] = [value]
                self.state.current_arg_index += 1

    async def _handle_submit(self, raw_value: str) -> None:
        raw = raw_value.strip()
        specs = self.command_registry.all_specs()

        if self.state.command is None:
            return

        if self.state.is_complete(specs):
            self.suggestions_list.hide()
            self.input_field.clear()
            self._execute_command(self.state.command, self.state.collected_args)
            self._reset_flow()
            return

        current_arg: CommandArg = self.state.current_arg(specs)
        if current_arg:
            if current_arg.multi and not raw:
                existing = self.state.collected_args.get(current_arg.name, [])
                if existing:
                    self.suggestions_list.hide()
                    self.state.current_arg_index += 1
                elif current_arg.required:
                    self.text_area.write(
                        f"[yellow]Please select at least one [cyan]{current_arg.name}[/cyan][/yellow]"
                    )
                    return
                else:
                    self.state.current_arg_index += 1
            elif not raw:
                if current_arg.required:
                    self.text_area.write(
                        f"[yellow]Please enter a value for [cyan]{current_arg.name}[/cyan][/yellow]"
                    )
                    return
                else:
                    self.state.current_arg_index += 1
            elif raw:
                self.suggestions_list.hide()
                self.input_field.value = ""
                self._advance_arg(raw)

        if self.state.is_complete(specs):
            self.input_field.clear()
            self._execute_command(self.state.command, self.state.collected_args)
            self._reset_flow()
        else:
            self.input_field.clear()
            self._update_placeholder()

    @work()  # for a response UI during database operations (see also: https://textual.textualize.io/guide/workers/)
    async def _execute_command(self, command: str, args: dict[str, str]) -> None:
        await self.command_registry.execute(command, args, self)

if __name__ == "__main__":
    categories_service = CategoriesService()
    app = ExpensesTracker(categories_service, SpendingService(categories_service))
    app.run()
