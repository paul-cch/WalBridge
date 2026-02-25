#!/bin/bash
set -euo pipefail
# borders-cycle.sh — Start borders-animated with a fixed diagonal gradient.
# Colors are read from border_colors (written by wallpaper_colors.py).
# Live updates are pushed directly by wallpaper_colors.py via IPC.

BORDER_COLORS="${WALLPAPER_BORDER_COLORS_FILE:-$HOME/.config/wallpaper-colors/border_colors}"
BORDERS_BIN="${WALLPAPER_BORDERS_BIN:-$HOME/.local/bin/borders-animated}"

if [[ -f "$BORDER_COLORS" ]]; then
    { read -r ACCENT; read -r SECONDARY; } < "$BORDER_COLORS"
fi
ACCENT=${ACCENT:-0xff2774d8}
SECONDARY=${SECONDARY:-0xffd86336}

exec "$BORDERS_BIN" style=round width=3.0 hidpi=on placement=inside \
    "active_color=gradient(top_left=${ACCENT/0xff/0xb3},bottom_right=${SECONDARY/0xff/0xb3})" \
    inactive_color=0x00000000
