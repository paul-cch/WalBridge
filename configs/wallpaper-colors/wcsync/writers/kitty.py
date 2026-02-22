"""Kitty terminal theme writer."""

import os

from ..colors import darken, lighten
from ..utils import atomic_write, hex6

OUTPUT_PATH = os.path.expanduser("~/.config/kitty/themes/wallpaper.conf")


def write(scheme, config=None):
    bg = scheme["dark"]
    fg = scheme["light"]
    accent = scheme["accent"]
    sel_bg = scheme["item_bg"]

    content = f"""# Auto-generated from wallpaper — do not edit manually
# Regenerate: python3 ~/.config/wallpaper-colors/wallpaper_colors.py

background {hex6(*bg)}
foreground {hex6(*fg)}
cursor {hex6(*accent)}
selection_background {hex6(*sel_bg)}
selection_foreground {hex6(*bg)}

# Normal colors
color0 {hex6(*bg)}
color1 {hex6(*scheme["red"])}
color2 {hex6(*scheme["green"])}
color3 {hex6(*scheme["yellow"])}
color4 {hex6(*accent)}
color5 {hex6(*scheme["purple"])}
color6 {hex6(*scheme["cyan"])}
color7 {hex6(*fg)}

# Bright colors
color8 {hex6(*scheme["grey"])}
color9 {hex6(*lighten(scheme["red"], 0.2))}
color10 {hex6(*lighten(scheme["green"], 0.2))}
color11 {hex6(*lighten(scheme["yellow"], 0.2))}
color12 {hex6(*lighten(accent, 0.2))}
color13 {hex6(*lighten(scheme["purple"], 0.2))}
color14 {hex6(*lighten(scheme["cyan"], 0.2))}
color15 #ffffff

# Tab bar
active_tab_foreground   {hex6(*fg)}
active_tab_background   {hex6(*sel_bg)}
inactive_tab_foreground {hex6(*scheme["grey"])}
inactive_tab_background {hex6(*darken(bg, 0.7))}
"""
    atomic_write(OUTPUT_PATH, content)
