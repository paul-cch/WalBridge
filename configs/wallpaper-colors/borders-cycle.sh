#!/bin/bash
set -euo pipefail
# borders-cycle.sh — Start JankyBorders (brew install borders) with active/inactive colors.
# Colors are read from border_colors (written by wallpaper_colors.py).
# Live updates are pushed directly by wallpaper_colors.py via IPC.

BORDER_COLORS="${WALLPAPER_BORDER_COLORS_FILE:-$HOME/.config/wallpaper-colors/border_colors}"
BORDERS_BIN="${WALLPAPER_BORDERS_BIN:-$(command -v borders 2>/dev/null || echo borders)}"

if [[ -f "$BORDER_COLORS" ]]; then
    while IFS= read -r line; do
        line="${line%%#*}"
        line="${line#"${line%%[![:space:]]*}"}"
        line="${line%"${line##*[![:space:]]}"}"
        [[ -z "$line" ]] && continue
        if [[ "$line" =~ ^active_color= ]]; then
            ACCENT="${line#active_color=}"
            continue
        fi
        if [[ "$line" =~ ^inactive_color= ]]; then
            INACTIVE="${line#inactive_color=}"
            continue
        fi
        # Backward compatibility: legacy single-line accent format.
        if [[ -z "${ACCENT:-}" && "$line" =~ ^0x[0-9A-Fa-f]{8}$ ]]; then
            ACCENT="$line"
        fi
    done < "$BORDER_COLORS"
fi
ACCENT=${ACCENT:-0xffb32774}
INACTIVE=${INACTIVE:-0xff404040}
if [[ ! "$ACCENT" =~ ^0x[0-9A-Fa-f]{8}$ ]]; then
    echo "WARN: invalid ACCENT '$ACCENT'; falling back to 0xffb32774" >&2
    ACCENT="0xffb32774"
fi
if [[ ! "$INACTIVE" =~ ^0x[0-9A-Fa-f]{8}$ ]]; then
    echo "WARN: invalid INACTIVE '$INACTIVE'; falling back to 0xff404040" >&2
    INACTIVE="0xff404040"
fi

exec "$BORDERS_BIN" style=round width=3.0 hidpi=on placement=inside \
    "active_color=${ACCENT/0xff/0xb3}" \
    "inactive_color=${INACTIVE/0xff/0x66}"
