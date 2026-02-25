#!/bin/bash
set -euo pipefail

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Next Wallpaper
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🖼️
# @raycast.packageName Wallpaper

# Cycle to next wallpaper, then force a full color sync.
# Works standalone or as a Raycast Script Command.

SCRIPT_DIR="$HOME/.config/wallpaper-colors"
PYTHON="${WALLPAPER_PYTHON:-$(command -v python3)}"

bash "$SCRIPT_DIR/wallpaper_cycle.sh"
sleep 0.5
"$PYTHON" "$SCRIPT_DIR/wallpaper_colors.py" --force
