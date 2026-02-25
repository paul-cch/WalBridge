"""JankyBorders border_colors writer."""

import os

from ..utils import atomic_write, hexc

DEFAULT_OUTPUT_PATH = "~/.config/wallpaper-colors/border_colors"


def _output_path():
    return os.path.expanduser(
        os.environ.get("WALLPAPER_BORDER_COLORS_FILE", DEFAULT_OUTPUT_PATH)
    )


def write(scheme, config=None):
    accent = hexc(*scheme["border_accent"])
    secondary = hexc(*scheme["border_secondary"])
    atomic_write(_output_path(), f"{accent}\n{secondary}\n")
