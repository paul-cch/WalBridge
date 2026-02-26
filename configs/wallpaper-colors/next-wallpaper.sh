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

resolve_python_bin() {
    local raw="${WALLPAPER_PYTHON:-}"
    local candidate=""

    if [[ -n "$raw" ]]; then
        if [[ "$raw" == */* ]]; then
            candidate="$raw"
        elif command -v "$raw" >/dev/null 2>&1; then
            candidate="$(command -v "$raw")"
        fi

        if [[ -n "$candidate" && -x "$candidate" && "$(basename "$candidate")" == python* ]]; then
            printf '%s\n' "$candidate"
            return
        fi
        echo "WARN: ignoring invalid WALLPAPER_PYTHON=$raw" >&2
    fi

    command -v python3 || true
}

PYTHON="$(resolve_python_bin)"
if [[ -z "$PYTHON" ]]; then
    echo "ERROR: python3 not found" >&2
    exit 1
fi

bash "$SCRIPT_DIR/wallpaper_cycle.sh"
sleep 0.5
"$PYTHON" "$SCRIPT_DIR/wallpaper_colors.py" --force
