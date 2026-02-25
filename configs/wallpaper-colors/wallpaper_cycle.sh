#!/bin/bash
set -euo pipefail
# wallpaper_cycle.sh — Pick next wallpaper from dark/ or light/ based on system theme.
#
# Detects macOS appearance, shuffles through wallpapers in the matching folder,
# and sets the next one via desktoppr. Tracks position in an index file so it
# cycles through all wallpapers before repeating.

WALLPAPER_DIR="$HOME/Pictures/wallpaper"
STATE_DIR="$HOME/.config/wallpaper-colors"
DESKTOPPR=$(command -v desktoppr 2>/dev/null || echo "/usr/local/bin/desktoppr")

# Detect system appearance
if defaults read -g AppleInterfaceStyle &>/dev/null; then
    THEME="dark"
else
    THEME="light"
fi

FOLDER="$WALLPAPER_DIR/$THEME"
INDEX_FILE="$STATE_DIR/.cycle_${THEME}_index"
ORDER_FILE="$STATE_DIR/.cycle_${THEME}_order"

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

# Generate shuffled order file
reshuffle() {
    # Use awk to shuffle indices (works on macOS without shuf/gshuf)
    seq 0 $(( COUNT - 1 )) | awk 'BEGIN{srand()}{print rand()"\t"$0}' | sort -n | cut -f2 > "$ORDER_FILE"
    echo 0 > "$INDEX_FILE"
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

# Read current position
POS=$(cat "$INDEX_FILE" 2>/dev/null || true)
POS=${POS:-0}

# Read shuffled order into array
ORDER=()
while IFS= read -r line; do
    ORDER+=("$line")
done < "$ORDER_FILE"

# Wrap around if we've gone through all wallpapers
if [[ $POS -ge ${#ORDER[@]} ]]; then
    reshuffle
    POS=0
    ORDER=()
    while IFS= read -r line; do
        ORDER+=("$line")
    done < "$ORDER_FILE"
fi

FILE_IDX=${ORDER[$POS]}
NEXT_WP="${ALL_FILES[$FILE_IDX]}"

# Advance position
echo "$(( POS + 1 ))" > "$INDEX_FILE"

# Set wallpaper
"$DESKTOPPR" "$NEXT_WP"

BASENAME=$(basename "$NEXT_WP")
echo "[$(date +%H:%M:%S)] $THEME: $BASENAME ($(( POS + 1 ))/$COUNT)"
