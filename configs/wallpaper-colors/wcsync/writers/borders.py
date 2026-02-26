"""JankyBorders border_colors writer."""

import os

from ..utils import atomic_write, hexc, safe_home_path

DEFAULT_OUTPUT_PATH = "~/.config/wallpaper-colors/border_colors"


def _output_path():
    return safe_home_path(
        os.environ.get("WALLPAPER_BORDER_COLORS_FILE"),
        DEFAULT_OUTPUT_PATH,
        "WALLPAPER_BORDER_COLORS_FILE",
    )


def write(scheme, config=None):
    accent = hexc(*scheme["border_accent"])
    inactive_rgb = scheme.get("border_inactive") or scheme.get("grey", scheme["border_accent"])
    inactive = hexc(*inactive_rgb)
    atomic_write(
        _output_path(),
        f"active_color={accent}\ninactive_color={inactive}\n",
    )
