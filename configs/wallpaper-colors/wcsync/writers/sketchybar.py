"""SketchyBar colors.sh writer."""

from ..target_writing import ColorMaterial
from ..utils import hexc


def render(scheme, app, config=None):
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
    return ColorMaterial(content)
