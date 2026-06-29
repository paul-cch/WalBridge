"""WezTerm color scheme writer."""

from ..target_writing import ColorMaterial
from ..utils import hex6


def render(scheme, app, config=None):
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
name = "{app.target_name("scheme")}"

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
    return ColorMaterial(content)
