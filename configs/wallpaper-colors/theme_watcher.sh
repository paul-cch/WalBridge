#!/bin/bash
set -uo pipefail
# theme_watcher.sh — Poll macOS appearance every 5s and trigger wallpaper
# switch when dark/light mode changes. Runs as a persistent launchd daemon.

STATE_DIR="$HOME/.config/wallpaper-colors"
THEME_FILE="$STATE_DIR/.last_theme"
CYCLE_SCRIPT="$HOME/.config/wallpaper-colors/wallpaper_cycle.sh"
PYTHON="${WALLPAPER_PYTHON:-$(command -v python3 || true)}"
COLORS_SCRIPT="$HOME/.config/wallpaper-colors/wallpaper_colors.py"

mkdir -p "$STATE_DIR"

get_theme() {
    if defaults read -g AppleInterfaceStyle &>/dev/null; then
        echo "dark"
    else
        echo "light"
    fi
}

LAST=$(cat "$THEME_FILE" 2>/dev/null || echo "")

while true; do
    CURRENT=$(get_theme)
    if [[ "$CURRENT" != "$LAST" ]]; then
        echo "[$(date +%H:%M:%S)] Theme changed: ${LAST:-unknown} → $CURRENT"
        echo "$CURRENT" > "$THEME_FILE"
        LAST="$CURRENT"

        # Switch wallpaper to matching folder.
        if ! bash "$CYCLE_SCRIPT"; then
            echo "[$(date +%H:%M:%S)] WARN: wallpaper cycle failed" >&2
        fi

        # Re-sync colors to the new wallpaper.
        sleep 1
        if [[ -z "$PYTHON" ]]; then
            echo "[$(date +%H:%M:%S)] WARN: python3 not found, skipping color sync" >&2
        elif ! "$PYTHON" "$COLORS_SCRIPT" --force; then
            echo "[$(date +%H:%M:%S)] WARN: color sync failed" >&2
        fi
    fi
    sleep 5
done
