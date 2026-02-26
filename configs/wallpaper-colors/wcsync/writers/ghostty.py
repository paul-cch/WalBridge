"""Ghostty theme writer."""

import os

from ..utils import atomic_write, hex6, safe_home_path, sanitize_filename

DEFAULT_THEME_FILE = "wallpaper.conf"


def _theme_file():
    return sanitize_filename(
        os.environ.get("WALLPAPER_GHOSTTY_THEME_FILE"),
        DEFAULT_THEME_FILE,
        "WALLPAPER_GHOSTTY_THEME_FILE",
    )


def _output_path():
    default_path = f"~/.config/ghostty/themes/{_theme_file()}"
    return safe_home_path(
        os.environ.get("WALLPAPER_GHOSTTY_OUTPUT_PATH"),
        default_path,
        "WALLPAPER_GHOSTTY_OUTPUT_PATH",
    )


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

background = {dark}
foreground = {light}
cursor-color = {accent}
cursor-text = {dark}
selection-background = {secondary}
selection-foreground = {light}

palette = 0={dark}
palette = 1={red}
palette = 2={green}
palette = 3={yellow}
palette = 4={blue}
palette = 5={purple}
palette = 6={cyan}
palette = 7={light}
palette = 8={grey}
palette = 9={red}
palette = 10={green}
palette = 11={orange}
palette = 12={blue}
palette = 13={pink}
palette = 14={secondary}
palette = 15={light}
"""
    atomic_write(_output_path(), content)
