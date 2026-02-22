"""HydroToDo TUI theme writer."""

import json
import os

from ..utils import atomic_write

OUTPUT_PATH = os.path.expanduser("~/.config/wallpaper-colors/hydrotodo_colors.json")


def write(scheme, config=None):
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
    atomic_write(OUTPUT_PATH, json.dumps(theme) + "\n")
