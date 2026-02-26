"""SketchyBar colors.sh writer."""

import os

from ..utils import atomic_write, hexc, safe_home_path

DEFAULT_OUTPUT_PATH = "~/.config/sketchybar/colors.sh"


def _output_path():
    return safe_home_path(
        os.environ.get("WALLPAPER_SKETCHYBAR_OUTPUT_PATH"),
        DEFAULT_OUTPUT_PATH,
        "WALLPAPER_SKETCHYBAR_OUTPUT_PATH",
    )


def write(scheme, config=None):
    content = f"""#!/bin/bash
# Auto-generated from wallpaper — do not edit manually
# Regenerate: python3 ~/.config/wallpaper-colors/wallpaper_colors.py

export BLACK={hexc(*scheme["dark"])}
export WHITE={hexc(*scheme["light"])}
export BLUE={hexc(*scheme["accent"])}
export CYAN={hexc(*scheme["cyan"])}
export PURPLE={hexc(*scheme["purple"])}
export GREEN={hexc(*scheme["green"])}
export RED={hexc(*scheme["red"])}
export YELLOW={hexc(*scheme["yellow"])}
export ORANGE={hexc(*scheme["orange"])}
export PINK={hexc(*scheme["pink"])}
export GREY={hexc(*scheme["grey"])}
export TRANSPARENT=0x00000000

# Bar colors
export BAR_COLOR={hexc(*scheme["bar_bg"], a=0xE6)}
export ITEM_BG_COLOR={hexc(*scheme["item_bg"])}
export ACCENT_COLOR=$BLUE
export ACTIVE_COLOR=$BLUE
export BLUE_VIVID={hexc(*scheme["border_accent"])}
"""
    atomic_write(_output_path(), content)
