"""WezTerm color scheme writer."""

import os

from ..utils import atomic_write, hex6, safe_home_path, sanitize_name

DEFAULT_SCHEME_NAME = "wallpaper"


def _scheme_name():
    return sanitize_name(
        os.environ.get("WALLPAPER_WEZTERM_SCHEME_NAME"),
        DEFAULT_SCHEME_NAME,
        "WALLPAPER_WEZTERM_SCHEME_NAME",
    )


def _output_path():
    default_path = f"~/.config/wezterm/colors/{_scheme_name()}.toml"
    return safe_home_path(
        os.environ.get("WALLPAPER_WEZTERM_OUTPUT_PATH"),
        default_path,
        "WALLPAPER_WEZTERM_OUTPUT_PATH",
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

[metadata]
name = "{_scheme_name()}"

[colors]
foreground = "{light}"
background = "{dark}"
cursor_bg = "{accent}"
cursor_fg = "{dark}"
cursor_border = "{accent}"
selection_fg = "{light}"
selection_bg = "{secondary}"
ansi = [
  "{dark}",
  "{red}",
  "{green}",
  "{yellow}",
  "{blue}",
  "{purple}",
  "{cyan}",
  "{light}",
]
brights = [
  "{grey}",
  "{red}",
  "{green}",
  "{orange}",
  "{blue}",
  "{pink}",
  "{secondary}",
  "{light}",
]
"""
    atomic_write(_output_path(), content)
