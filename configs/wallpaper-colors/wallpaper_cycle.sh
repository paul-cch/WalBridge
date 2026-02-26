#!/bin/bash
set -euo pipefail
# wallpaper_cycle.sh — Pick next wallpaper from dark/ or light/ based on system theme.
#
# Detects macOS appearance, shuffles through wallpapers in the matching folder,
# and sets the next one via desktoppr. Tracks position in an index file so it
# cycles through all wallpapers before repeating.

# Override with WALLPAPER_DIR to support non-default folder layouts.
WALLPAPER_DIR="${WALLPAPER_DIR:-$HOME/Pictures/wallpaper}"
STATE_DIR="$HOME/.config/wallpaper-colors"
# Prefer full paths to limit PATH hijack in launchd context
if command -v desktoppr >/dev/null 2>&1; then
    DESKTOPPR="$(command -v desktoppr)"
elif [[ -x /opt/homebrew/bin/desktoppr ]]; then
    DESKTOPPR="/opt/homebrew/bin/desktoppr"
elif [[ -x /usr/local/bin/desktoppr ]]; then
    DESKTOPPR="/usr/local/bin/desktoppr"
else
    echo "[$(date +%H:%M:%S)] desktoppr not found" >&2
    exit 1
fi

# Detect system appearance
if defaults read -g AppleInterfaceStyle &>/dev/null; then
    THEME="dark"
else
    THEME="light"
fi

FOLDER="$WALLPAPER_DIR/$THEME"
INDEX_FILE="$STATE_DIR/.cycle_${THEME}_index"
ORDER_FILE="$STATE_DIR/.cycle_${THEME}_order"

# Fast fail with a clear message when theme folder is missing.
if [[ ! -d "$FOLDER" ]]; then
    echo "[$(date +%H:%M:%S)] Missing wallpaper folder: $FOLDER" >&2
    exit 1
fi

# Build sorted list of wallpapers
ALL_FILES=()
while IFS= read -r f; do
    ALL_FILES+=("$f")
done < <(find "$FOLDER" -maxdepth 1 -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) | sort)

COUNT=${#ALL_FILES[@]}

if [[ $COUNT -eq 0 ]]; then
    echo "[$(date +%H:%M:%S)] No wallpapers in $FOLDER" >&2
    exit 1
fi

# Atomic write (symlink-safe)
atomic_write() {
    local dest="$1"
    local content="$2"
    local dir tmp
    dir="$(dirname "$dest")"
    tmp="$(mktemp "$dir/.__wts_XXXXXX")"
    printf '%s\n' "$content" > "$tmp"
    mv -f "$tmp" "$dest"
}

# Generate shuffled order file
reshuffle() {
    local tmp_order tmp_idx
    tmp_order="$(mktemp "$STATE_DIR/.__order_XXXXXX")"
    tmp_idx="$(mktemp "$STATE_DIR/.__index_XXXXXX")"
    seq 0 $(( COUNT - 1 )) | awk 'BEGIN{srand()}{print rand()"\t"$0}' | sort -n | cut -f2 > "$tmp_order"
    mv -f "$tmp_order" "$ORDER_FILE"
    printf '0' > "$tmp_idx"
    mv -f "$tmp_idx" "$INDEX_FILE"
}

# Reshuffle if order file missing or file count changed
if [[ ! -f "$ORDER_FILE" || ! -f "$INDEX_FILE" ]]; then
    reshuffle
else
    ORDER_COUNT=$(wc -l < "$ORDER_FILE" | tr -d ' ')
    if [[ "$ORDER_COUNT" -ne "$COUNT" ]]; then
        reshuffle
    fi
fi

# Read current position (must be integer >= 0)
POS=$(cat "$INDEX_FILE" 2>/dev/null || true)
POS=${POS:-0}
[[ "$POS" =~ ^[0-9]+$ ]] || POS=0

# Read shuffled order into array; validate all entries are indices
ORDER=()
while IFS= read -r line; do
    [[ "$line" =~ ^[0-9]+$ ]] && (( line >= 0 && line < COUNT )) && ORDER+=("$line") || true
done < "$ORDER_FILE"

# If order is empty or position out of range, reshuffle and retry once
if [[ ${#ORDER[@]} -eq 0 || $POS -ge ${#ORDER[@]} || $POS -lt 0 ]]; then
    reshuffle
    POS=0
    ORDER=()
    while IFS= read -r line; do
        [[ "$line" =~ ^[0-9]+$ ]] && (( line >= 0 && line < COUNT )) && ORDER+=("$line") || true
    done < "$ORDER_FILE"
fi

# Defensive: if still empty (corrupted state), reshuffle and use 0
if [[ ${#ORDER[@]} -eq 0 ]]; then
    reshuffle
    POS=0
    ORDER=()
    while IFS= read -r line; do
        [[ "$line" =~ ^[0-9]+$ ]] && (( line >= 0 && line < COUNT )) && ORDER+=("$line") || true
    done < "$ORDER_FILE"
fi

FILE_IDX=${ORDER[$POS]:--1}
if [[ "$FILE_IDX" -lt 0 || "$FILE_IDX" -ge "$COUNT" ]]; then
    echo "[$(date +%H:%M:%S)] Corrupted cycle state, reshuffling" >&2
    reshuffle
    POS=0
    ORDER=()
    while IFS= read -r line; do
        [[ "$line" =~ ^[0-9]+$ ]] && (( line >= 0 && line < COUNT )) && ORDER+=("$line") || true
    done < "$ORDER_FILE"
    FILE_IDX=${ORDER[0]:--1}
    [[ "$FILE_IDX" -ge 0 && "$FILE_IDX" -lt "$COUNT" ]] || { echo "[$(date +%H:%M:%S)] Reshuffle failed" >&2; exit 1; }
fi
NEXT_WP="${ALL_FILES[$FILE_IDX]}"

# Advance position (atomic)
atomic_write "$INDEX_FILE" "$(( POS + 1 ))"

# Set wallpaper and record current path for display-change re-apply
"$DESKTOPPR" "$NEXT_WP"
atomic_write "$STATE_DIR/.current_wallpaper" "$NEXT_WP"

BASENAME=$(basename "$NEXT_WP")
echo "[$(date +%H:%M:%S)] $THEME: $BASENAME ($(( POS + 1 ))/$COUNT)"
