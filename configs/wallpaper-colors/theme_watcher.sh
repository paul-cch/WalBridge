#!/bin/bash
set -uo pipefail
# theme_watcher.sh — Poll macOS appearance and trigger wallpaper switch when
# dark/light mode changes. Runs as a persistent launchd daemon.
# Poll interval 15s to limit wakeups; on change we run cycle then one sync.
# Note: -e is intentionally omitted so the daemon loop survives individual
# cycle or sync failures without exiting.

STATE_DIR="$HOME/.config/wallpaper-colors"
THEME_FILE="$STATE_DIR/.last_theme"
CYCLE_SCRIPT="$HOME/.config/wallpaper-colors/wallpaper_cycle.sh"
COLORS_SCRIPT="$HOME/.config/wallpaper-colors/wallpaper_colors.py"

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
        echo "[$(date +%H:%M:%S)] WARN: ignoring invalid WALLPAPER_PYTHON=$raw" >&2
    fi

    command -v python3 || true
}

PYTHON="$(resolve_python_bin)"

mkdir -p "$STATE_DIR"

get_theme() {
    if defaults read -g AppleInterfaceStyle &>/dev/null; then
        echo "dark"
    else
        echo "light"
    fi
}

LAST=$(cat "$THEME_FILE" 2>/dev/null || echo "")

# Track display count so we re-apply wallpaper when a monitor is connected/disconnected.
# desktoppr with no args prints one line per display.
DESKTOPPR_BIN="$(command -v desktoppr 2>/dev/null || echo /opt/homebrew/bin/desktoppr)"
get_display_count() {
    "$DESKTOPPR_BIN" 2>/dev/null | wc -l | tr -d ' '
}
LAST_DISPLAY_COUNT="$(get_display_count)"
CURRENT_WP_FILE="$STATE_DIR/.current_wallpaper"

reapply_wallpaper() {
    local wp
    wp="$(cat "$CURRENT_WP_FILE" 2>/dev/null || true)"
    if [[ -n "$wp" && -f "$wp" ]]; then
        echo "[$(date +%H:%M:%S)] Re-applying wallpaper to all displays: $(basename "$wp")"
        "$DESKTOPPR_BIN" "$wp"
    else
        echo "[$(date +%H:%M:%S)] No saved wallpaper to re-apply, running cycle" >&2
        bash "$CYCLE_SCRIPT" || echo "[$(date +%H:%M:%S)] WARN: wallpaper cycle failed" >&2
    fi
}

run_color_sync() {
    sleep 1
    if [[ -z "$PYTHON" ]]; then
        echo "[$(date +%H:%M:%S)] WARN: python3 not found, skipping color sync" >&2
    elif ! "$PYTHON" "$COLORS_SCRIPT" --force; then
        echo "[$(date +%H:%M:%S)] WARN: color sync failed" >&2
    fi
}

while true; do
    CURRENT=$(get_theme)

    # 1) Theme change → cycle to matching folder + sync colors.
    if [[ "$CURRENT" != "$LAST" ]]; then
        echo "[$(date +%H:%M:%S)] Theme changed: ${LAST:-unknown} → $CURRENT"
        echo "$CURRENT" > "$THEME_FILE"
        LAST="$CURRENT"

        if ! bash "$CYCLE_SCRIPT"; then
            echo "[$(date +%H:%M:%S)] WARN: wallpaper cycle failed" >&2
        fi
        run_color_sync
    fi

    # 2) Display count change → re-apply current wallpaper + sync colors.
    DISPLAY_COUNT="$(get_display_count)"
    if [[ "$DISPLAY_COUNT" != "$LAST_DISPLAY_COUNT" ]]; then
        echo "[$(date +%H:%M:%S)] Display count changed: $LAST_DISPLAY_COUNT → $DISPLAY_COUNT"
        LAST_DISPLAY_COUNT="$DISPLAY_COUNT"
        reapply_wallpaper
        run_color_sync
    fi

    sleep 15
done
