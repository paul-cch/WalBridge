"""Alacritty theme writer."""

import os

from ..utils import atomic_write, hex6, safe_home_path

DEFAULT_OUTPUT_PATH = "~/.config/alacritty/themes/wallpaper.toml"


def _output_path():
    override = os.environ.get("WALLPAPER_ALACRITTY_OUTPUT_PATH")
    return safe_home_path(override, DEFAULT_OUTPUT_PATH, "WALLPAPER_ALACRITTY_OUTPUT_PATH")


def write(scheme, config=None):
    dark = hex6(*scheme["dark"])
    light = hex6(*scheme["light"])
    accent = hex6(*scheme["accent"])
    secondary = hex6(*scheme["secondary"])
    red = hex6(*scheme["red"])
    green = hex6(*scheme["green"])
    yellow = hex6(*scheme["yellow"])
    blue = accent
    purple = hex6(*scheme["purple"])
    cyan = hex6(*scheme["cyan"])
    grey = hex6(*scheme["grey"])
    orange = hex6(*scheme["orange"])
    pink = hex6(*scheme["pink"])

    content = f"""# Auto-generated from wallpaper — do not edit manually
# Regenerate: python3 ~/.config/wallpaper-colors/wallpaper_colors.py

[colors.primary]
background = "{dark}"
foreground = "{light}"

[colors.normal]
black = "{dark}"
red = "{red}"
green = "{green}"
yellow = "{yellow}"
blue = "{blue}"
magenta = "{purple}"
cyan = "{cyan}"
white = "{light}"

[colors.bright]
black = "{grey}"
red = "{red}"
green = "{green}"
yellow = "{orange}"
blue = "{blue}"
magenta = "{pink}"
cyan = "{secondary}"
white = "{light}"

[colors.cursor]
text = "{dark}"
cursor = "{accent}"

[colors.selection]
text = "{light}"
background = "{secondary}"
"""
    atomic_write(_output_path(), content)
