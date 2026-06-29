"""HydroToDo TUI theme writer."""

import json

from ..target_writing import ColorMaterial


def render(scheme, app, config=None):
    theme = {
        "accent": list(scheme["accent"]),
        "green": list(scheme["green"]),
        "yellow": list(scheme["yellow"]),
        "red": list(scheme["red"]),
        "purple": list(scheme["purple"]),
        "cyan": list(scheme["cyan"]),
        "orange": list(scheme["orange"]),
        "grey": list(scheme["grey"]),
        "dark": list(scheme["dark"]),
        "light": list(scheme["light"]),
    }
    return ColorMaterial(json.dumps(theme) + "\n")
