"""SketchyBar colors.sh writer."""

from ..target_apps import target_path
from ..utils import atomic_write, hexc

def _output_path():
    return target_path("sketchybar")


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
