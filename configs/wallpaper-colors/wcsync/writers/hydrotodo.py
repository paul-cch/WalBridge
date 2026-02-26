"""HydroToDo TUI theme writer."""

import json
import os

from ..utils import atomic_write, safe_home_path

DEFAULT_OUTPUT_PATH = "~/.config/wallpaper-colors/hydrotodo_colors.json"


def _output_path():
    return safe_home_path(
        os.environ.get("WALLPAPER_HYDROTODO_OUTPUT_PATH"),
        DEFAULT_OUTPUT_PATH,
        "WALLPAPER_HYDROTODO_OUTPUT_PATH",
    )


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
    atomic_write(_output_path(), json.dumps(theme) + "\n")
