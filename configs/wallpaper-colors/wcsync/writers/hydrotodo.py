"""HydroToDo TUI theme writer."""

import json

from ..target_apps import target_path
from ..utils import atomic_write


def _output_path():
    return target_path("hydrotodo")


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
