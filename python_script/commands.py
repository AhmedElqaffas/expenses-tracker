from dataclasses import dataclass, field

@dataclass
class ArgSpec:
    name: str # display name, e.g. "message"
    suggestions: list[str] = field(default_factory=list)  # empty = free text

# Slash command registry
SLASH_COMMANDS = {
    "print": {
        "usage": "/print <level> <message>",
        "description": "Print a message with a log level",
        "args": [
            ArgSpec("log_level", suggestions=["info", "warning", "error"]),
            ArgSpec("message"),  # free text, no suggestions
        ],
    },
    "clear": {
        "usage": "/clear",
        "description": "Clear the output area",
        "args": [],
    },
}