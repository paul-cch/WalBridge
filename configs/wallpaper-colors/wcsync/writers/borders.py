"""JankyBorders border_colors writer."""

import os

from ..utils import atomic_write, hexc

OUTPUT_PATH = os.path.expanduser("~/.config/wallpaper-colors/border_colors")


def write(scheme, config=None):
    accent = hexc(*scheme["border_accent"])
    secondary = hexc(*scheme["border_secondary"])
    atomic_write(OUTPUT_PATH, f"{accent}\n{secondary}\n")
