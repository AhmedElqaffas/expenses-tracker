from textual.widgets import ListView, ListItem, Label

class CommandSuggestions(ListView):
    """Floating suggestion list that appears above the input."""

    DEFAULT_CSS = """
    CommandSuggestions {
        layer: overlay;
        dock: bottom;
        margin-bottom: 3;
        height: auto;
        max-height: 10;
        background: $surface;
        border: tall $primary;
        display: none;
    }
    CommandSuggestions.visible {
        display: block;
    }
    CommandSuggestions > ListItem {
        padding: 0 1;
    }
    CommandSuggestions > ListItem Label {
        width: 1fr;
    }
    """

    def show_suggestions(self, matches: list[tuple[str, str]]) -> None:
        """Populate and show the suggestion list."""
        self.clear()
        for command, description in matches:
            self.append(ListItem(Label(f"[cyan]/{command}[/cyan]  [dim]{description}[/dim]"), name=command))
        if matches:
            self.add_class("visible")
            self.index = 0
        else:
            self.remove_class("visible")

    def hide(self) -> None:
        self.remove_class("visible")
        self.clear()