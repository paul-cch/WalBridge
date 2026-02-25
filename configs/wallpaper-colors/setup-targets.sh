#!/bin/bash
set -euo pipefail
# setup-targets.sh — one-time target integration for tmux, btop, and iTerm2.
#
# Usage:
#   bash ~/.config/wallpaper-colors/setup-targets.sh
#   bash ~/.config/wallpaper-colors/setup-targets.sh --open-iterm

TMUX_CONF="${WALLPAPER_TMUX_CONF:-$HOME/.tmux.conf}"
TMUX_THEME_PATH="${WALLPAPER_TMUX_OUTPUT_PATH:-$HOME/.config/tmux/themes/wallpaper.conf}"
BTOP_CONF="${WALLPAPER_BTOP_CONF:-$HOME/.config/btop/btop.conf}"
BTOP_THEME_NAME="${WALLPAPER_BTOP_THEME_NAME:-wallpaper}"
ITERM_PRESET_NAME="${WALLPAPER_ITERM_PRESET_NAME:-wallpaper}"
ITERM_PRESET_PATH="${WALLPAPER_ITERM_OUTPUT_PATH:-$HOME/.config/iterm2/colors/$ITERM_PRESET_NAME.itermcolors}"
OPEN_ITERM=false

info()  { printf '→ %s\n' "$*"; }
warn()  { printf 'WARN: %s\n' "$*" >&2; }

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --open-iterm)
                OPEN_ITERM=true
                ;;
            -h|--help)
                cat <<'USAGE'
Usage:
  bash setup-targets.sh [--open-iterm]

Options:
  --open-iterm  Open generated .itermcolors preset for import in iTerm2
USAGE
                exit 0
                ;;
            *)
                warn "Unknown option: $1"
                exit 1
                ;;
        esac
        shift
    done
}

ensure_tmux_setup() {
    mkdir -p "$(dirname "$TMUX_CONF")"
    touch "$TMUX_CONF"

    if grep -Fq "source-file $TMUX_THEME_PATH" "$TMUX_CONF"; then
        info "tmux already wired: $TMUX_CONF"
        return
    fi

    cat >>"$TMUX_CONF" <<EOF

# >>> wallpaper-theme-sync (auto-generated include)
source-file $TMUX_THEME_PATH
# <<< wallpaper-theme-sync
EOF
    info "Added tmux include to $TMUX_CONF"
}

ensure_btop_setup() {
    mkdir -p "$(dirname "$BTOP_CONF")"

    if [ ! -f "$BTOP_CONF" ]; then
        cat >"$BTOP_CONF" <<EOF
# btop config (created by wallpaper-theme-sync setup)
color_theme = "$BTOP_THEME_NAME"
EOF
        info "Created $BTOP_CONF with color_theme=\"$BTOP_THEME_NAME\""
        return
    fi

    if grep -Eq '^[[:space:]]*color_theme[[:space:]]*=' "$BTOP_CONF"; then
        local tmp
        tmp="$(mktemp)"
        sed -E 's|^[[:space:]]*color_theme[[:space:]]*=.*$|color_theme = "'"$BTOP_THEME_NAME"'"|' "$BTOP_CONF" >"$tmp"
        mv "$tmp" "$BTOP_CONF"
        info "Updated color_theme in $BTOP_CONF"
    else
        printf '\ncolor_theme = "%s"\n' "$BTOP_THEME_NAME" >>"$BTOP_CONF"
        info "Appended color_theme to $BTOP_CONF"
    fi
}

print_iterm_instructions() {
    info "iTerm2 preset path: $ITERM_PRESET_PATH"
    if [ -f "$ITERM_PRESET_PATH" ]; then
        info "Import in iTerm2: Settings > Profiles > Colors > Color Presets > Import..."
        if [ "$OPEN_ITERM" = true ]; then
            if command -v open >/dev/null 2>&1; then
                open "$ITERM_PRESET_PATH" || warn "Failed to open $ITERM_PRESET_PATH"
            else
                warn "'open' command not available; import manually"
            fi
        fi
    else
        warn "Preset not found yet. Generate it first by running wallpaper_colors.py once."
    fi
}

main() {
    parse_args "$@"
    ensure_tmux_setup
    ensure_btop_setup
    print_iterm_instructions
}

main "$@"
