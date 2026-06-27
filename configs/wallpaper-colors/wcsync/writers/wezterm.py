"""WezTerm color scheme writer."""

from ..target_apps import target_name, target_path
from ..utils import atomic_write, hex6

def _scheme_name():
    return target_name("wezterm", "scheme")


def _output_path():
    return target_path("wezterm")


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
