from __future__ import annotations

from typing import Optional, override

from rich.text import Text
from textual.color import Color
from textual.reactive import reactive
from textual.widget import Widget


class MainTextArea(Widget):
    """A RichLog-like widget that supports a shimmer loading line."""

    DEFAULT_CSS = """
    MainTextArea {
        height: 1fr;
        overflow-y: auto;
        overflow-x: auto;
        background: $surface;
        margin: 1 0;
        padding: 0 1;
    }
    """

    # Tracks whether shimmer is active
    _shimmer_active: reactive[bool] = reactive(False, layout=False)

    def __init__(
            self,
            *args,
            **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        # Committed (non-shimmer) lines stored as Rich Text objects
        self._lines: list[Text] = []

        # The current loading message text (plain string)
        self._loading_message: str = ""

        # Shimmer animation frame counter
        self._shimmer_frame: int = 0

        # How fast the shimmer moves (seconds per frame)
        self._shimmer_speed = 0.1

        self._shimmer_base_color = "#888888"

        self._timer = None


    def write(self, content: str | Text) -> None:
        """Append a line to the log. Accepts Rich markup strings or Text objects."""
        if isinstance(content, str):
            content = Text.from_markup(content)
        self._lines.append(content)
        self.refresh()

    def start_loading(self, message: str = "Loading…") -> None:
        """Start shimmer on a new line with *message*."""
        self._loading_message = message
        self._shimmer_frame = 0
        self._shimmer_active = True
        # Kick off the animation timer
        self._timer = self.set_interval(self._shimmer_speed, self._tick_shimmer)

    def stop_loading(self, final_message: Optional[str] = None) -> None:
        """Stop the shimmer and commit the loading line as plain text."""
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

        # Commit the (optionally replaced) message as a plain line
        if final_message:
            self._lines.append(Text.from_markup(final_message))

        # self._loading_message = ""
        self._shimmer_active = False
        self.refresh()

    def _tick_shimmer(self) -> None:
        """Called on each timer tick to advance the shimmer frame."""
        self._shimmer_frame += 1
        self.refresh()

    def _build_shimmer_line(self, message: str, frame: int) -> Text:
        """A bright spot sweeps across the text, rest stays dim."""
        import math

        n = len(message)
        # Spot position moves left to right, cycling with the frame
        spot = (frame * 4) % (n + 20) - 10  # overshoot edges for smooth entry/exit

        rich_text = Text()
        for i, ch in enumerate(message):
            dist = abs(i - spot)
            # Gaussian-ish falloff: bright at center, dim further away
            brightness = math.exp(-0.15 * dist * dist)
            brightness = 0.65 + brightness * 0.75  # clamp between 0.25 and 1.0

            base = Color.parse(self._shimmer_base_color)
            r = int(base.r * brightness)
            g = int(base.g * brightness)
            b = int(base.b * brightness)
            rich_text.append(ch, style=f"#{r:02x}{g:02x}{b:02x}")

        return rich_text

    @override
    def render(self) -> Text:
        """Combine committed lines + optional shimmer line into one block."""
        combined = Text()

        for idx, line in enumerate(self._lines):
            if idx:
                combined.append("\n")
            combined.append_text(line)

        if self._shimmer_active and self._loading_message:
            if self._lines:
                combined.append("\n")
            shimmer_line = self._build_shimmer_line(
                self._loading_message, self._shimmer_frame
            )
            combined.append_text(shimmer_line)

        return combined