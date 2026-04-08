from __future__ import annotations

import math
from typing import Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.color import Color
from textual.widget import Widget
from textual.widgets import RichLog

class MainTextArea(Widget):
    """Scrollable log widget with support for loading shimmer."""

    can_focus = False
    DEFAULT_CSS = """
    MainTextArea {
        height: 1fr;
        layout: vertical;
    }
    MainTextArea > RichLog {
        height: 1fr;
        padding: 0 1;
        margin: 1 0;
        scrollbar-gutter: stable;
        overflow-y: auto;
    }
    """

    def __init__(
            self,
            id,
            shimmer_base_color: str = "#888888",
            shimmer_speed: float = 0.1,
    ) -> None:
        super().__init__(id=id)
        self._shimmer_speed = shimmer_speed
        self._shimmer_base_color = shimmer_base_color
        self._shimmer_frame: int = 0
        self._shimmer_active: bool = False
        self._loading_message: str = ""
        self._timer = None

        # Our source of truth: list of Rich Text objects
        self._lines: list[Text] = []

    def compose(self) -> ComposeResult:
        log =  RichLog(id="inner-log", wrap=True, markup=False)
        log.can_focus = False
        yield log

    def _log(self) -> RichLog:
        return self.query_one("#inner-log", RichLog)

    def write(self, content: str | Text) -> None:
        """Append a line. Accepts Rich markup strings or Text objects."""
        if isinstance(content, str):
            content = Text.from_markup(content)
        self._lines.append(content)
        self._flush()

    def start_loading(self, message: str = "Loading…") -> None:
        """Append a new shimmer line and start animating it."""
        self._loading_message = message
        self._shimmer_frame = 0
        self._shimmer_active = True
        self._flush()
        self._timer = self.set_interval(self._shimmer_speed, self._tick_shimmer)

    def stop_loading(self, final_message: Optional[str] = None) -> None:
        """Stop shimmer and commit the line as final text."""
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

        msg = final_message if final_message is not None else self._loading_message
        if msg:
            self._lines.append(Text.from_markup(msg))

        self._loading_message = ""
        self._shimmer_active = False
        self._flush()


    def _tick_shimmer(self) -> None:
        self._shimmer_frame += 1
        self._flush()

    def _flush(self) -> None:
        log = self._log()
        log.clear()

        # Write committed lines
        for line in self._lines:
            log.write(line)

        # Add shimmer line if active
        if self._shimmer_active and self._loading_message:
            shimmer_line = self._build_shimmer_line(
                self._loading_message,
                self._shimmer_frame,
            )
            log.write(shimmer_line)

        log.scroll_end(animate=False)

    def _build_shimmer_line(self, message: str, frame: int) -> Text:
        """Sweep a bright spot across the message text."""
        if not message:
            return Text("")

        n = len(message)
        spot = (frame * 4) % (n + 20) - 10

        base = Color.parse(self._shimmer_base_color)
        rich_text = Text()

        for i, ch in enumerate(message):
            dist = abs(i - spot)
            brightness = math.exp(-0.15 * dist * dist)
            brightness = 0.65 + brightness * 0.75

            r = int(base.r * brightness)
            g = int(base.g * brightness)
            b = int(base.b * brightness)
            rich_text.append(ch, style=f"#{r:02x}{g:02x}{b:02x}")

        return rich_text