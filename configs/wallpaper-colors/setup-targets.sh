#!/bin/bash
set -euo pipefail
# setup-targets.sh — one-time target integration for tmux, btop, and iTerm2.
#
# Usage:
#   bash ~/.config/wallpaper-colors/setup-targets.sh
#   bash ~/.config/wallpaper-colors/setup-targets.sh --open-iterm

info()  { printf '→ %s\n' "$*"; }
warn()  { printf 'WARN: %s\n' "$*" >&2; }

resolve_path() {
    python3 -c 'import os,sys; print(os.path.realpath(os.path.abspath(os.path.expanduser(sys.argv[1]))))' "$1"
}

safe_home_path() {
    local raw="$1"
    local default="$2"
    local var_name="$3"
    local home resolved fallback

    home="$(resolve_path "$HOME")"
    resolved="$(resolve_path "$raw")"
    fallback="$(resolve_path "$default")"

    if [[ "$resolved" == "$home" || "$resolved" == "$home/"* ]]; then
        printf '%s\n' "$resolved"
    else
        warn "Ignoring invalid $var_name=$raw (must stay within $home)"
        printf '%s\n' "$fallback"
    fi
}

sanitize_name() {
    local value="$1"
    local default="$2"
    local var_name="$3"
    if [[ "$value" =~ ^[A-Za-z0-9_-]+$ ]]; then
        printf '%s\n' "$value"
    else
        warn "Ignoring invalid $var_name=$value (expected [A-Za-z0-9_-]+)"
        printf '%s\n' "$default"
    fi
}

TMUX_CONF="$(safe_home_path "${WALLPAPER_TMUX_CONF:-$HOME/.tmux.conf}" "$HOME/.tmux.conf" "WALLPAPER_TMUX_CONF")"
TMUX_THEME_PATH="$(safe_home_path "${WALLPAPER_TMUX_OUTPUT_PATH:-$HOME/.config/tmux/themes/wallpaper.conf}" "$HOME/.config/tmux/themes/wallpaper.conf" "WALLPAPER_TMUX_OUTPUT_PATH")"
BTOP_CONF="$(safe_home_path "${WALLPAPER_BTOP_CONF:-$HOME/.config/btop/btop.conf}" "$HOME/.config/btop/btop.conf" "WALLPAPER_BTOP_CONF")"
BTOP_THEME_NAME="$(sanitize_name "${WALLPAPER_BTOP_THEME_NAME:-wallpaper}" "wallpaper" "WALLPAPER_BTOP_THEME_NAME")"
ITERM_PRESET_NAME="$(sanitize_name "${WALLPAPER_ITERM_PRESET_NAME:-wallpaper}" "wallpaper" "WALLPAPER_ITERM_PRESET_NAME")"
ITERM_PRESET_PATH="$(safe_home_path "${WALLPAPER_ITERM_OUTPUT_PATH:-$HOME/.config/iterm2/colors/$ITERM_PRESET_NAME.itermcolors}" "$HOME/.config/iterm2/colors/$ITERM_PRESET_NAME.itermcolors" "WALLPAPER_ITERM_OUTPUT_PATH")"
OPEN_ITERM=false

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
