#!/bin/bash
set -euo pipefail
# install.sh — Deploy wallpaper-theme-sync to your Mac.
#
# Usage:
#   bash install.sh                         # Install / update
#   bash install.sh --uninstall             # Remove launchd agents
#   bash install.sh --install-prebuilt-borders  # Install checked-in borders-animated binary

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="$HOME/.config/wallpaper-colors"
BIN_DIR="$HOME/.local/bin"
LAUNCH_DIR="$HOME/Library/LaunchAgents"
CHECKSUM_DIR="$REPO_DIR/checksums"
AGENT_PREFIX="${WTS_AGENT_PREFIX:-com.wallpaper-theme-sync}"
INSTALL_PREBUILT_BORDERS=false
UNINSTALL=false

info()  { printf '→ %s\n' "$*"; }
error() { printf 'ERROR: %s\n' "$*" >&2; }

usage() {
    cat <<'USAGE'
Usage:
  bash install.sh [--install-prebuilt-borders]
  bash install.sh --uninstall

Options:
  --install-prebuilt-borders  Install checked-in borders-animated after checksum validation
  --uninstall                 Unload and remove launchd agents for current prefix

Environment:
  WTS_AGENT_PREFIX            launchd label/file prefix (default: com.wallpaper-theme-sync)
USAGE
}

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --uninstall)
                UNINSTALL=true
                ;;
            --install-prebuilt-borders)
                INSTALL_PREBUILT_BORDERS=true
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
        shift
    done
}

validate_agent_prefix() {
    if ! printf '%s' "$AGENT_PREFIX" | grep -Eq '^[A-Za-z0-9][A-Za-z0-9.-]*$'; then
        error "Invalid WTS_AGENT_PREFIX: $AGENT_PREFIX"
        error "Allowed pattern: ^[A-Za-z0-9][A-Za-z0-9.-]*$"
        exit 1
    fi
}

plist_dest_path() {
    local source_name="$1"
    echo "$LAUNCH_DIR/$AGENT_PREFIX.$source_name"
}

verify_sha256() {
    local file="$1"
    local checksum_file="$2"
    local expected actual

    if [ ! -f "$checksum_file" ]; then
        error "Checksum file missing: $checksum_file"
        return 1
    fi

    expected=$(awk '{print $1}' "$checksum_file")
    actual=$(shasum -a 256 "$file" | awk '{print $1}')

    if [ "$expected" != "$actual" ]; then
        error "Checksum mismatch for $(basename "$file")"
        error "Expected: $expected"
        error "Actual:   $actual"
        return 1
    fi

    return 0
}

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------
check_deps() {
    local ok=true

    if ! command -v python3 >/dev/null 2>&1; then
        error "python3 not found"; ok=false
    elif ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null; then
        error "Python 3.11+ required (found $(python3 --version 2>&1))"; ok=false
    fi

    python3 -c "import PIL" 2>/dev/null    || { error "Pillow not installed (pip3 install Pillow)"; ok=false; }
    python3 -c "import Quartz" 2>/dev/null  || { error "PyObjC not installed (pip3 install pyobjc-framework-Quartz)"; ok=false; }
    command -v desktoppr >/dev/null 2>&1    || { error "desktoppr not found (brew install desktoppr)"; ok=false; }
    command -v swiftc >/dev/null 2>&1       || { error "swiftc not found (install Xcode Command Line Tools)"; ok=false; }

    if [ "$ok" = false ]; then
        echo ""
        echo "Install missing dependencies and re-run."
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Find the right Python interpreter (must have Pillow)
# ---------------------------------------------------------------------------
detect_python() {
    local py
    for py in \
        "$(command -v python3 2>/dev/null || true)" \
        /usr/local/bin/python3 \
        /Library/Frameworks/Python.framework/Versions/Current/bin/python3; do
        [ -n "$py" ] && [ -x "$py" ] && "$py" -c "import PIL" 2>/dev/null && { echo "$py"; return; }
    done
    echo "python3"
}

# ---------------------------------------------------------------------------
# Deploy sync package
# ---------------------------------------------------------------------------
deploy_configs() {
    info "Deploying sync package to $CONFIG_DIR/"
    mkdir -p "$CONFIG_DIR"

    cp "$REPO_DIR/configs/wallpaper-colors/wallpaper_colors.py" "$CONFIG_DIR/"
    cp -r "$REPO_DIR/configs/wallpaper-colors/wcsync" "$CONFIG_DIR/"

    for script in wallpaper_cycle.sh borders-cycle.sh theme_watcher.sh next-wallpaper.sh; do
        [ -f "$REPO_DIR/configs/wallpaper-colors/$script" ] && \
            cp "$REPO_DIR/configs/wallpaper-colors/$script" "$CONFIG_DIR/"
    done

    if [ ! -f "$CONFIG_DIR/config.toml" ]; then
        cp "$REPO_DIR/configs/wallpaper-colors/config.toml.example" "$CONFIG_DIR/config.toml"
        info "  Created config.toml from example"
    fi
}

# ---------------------------------------------------------------------------
# Build Swift tools from source
# ---------------------------------------------------------------------------
build_tools() {
    info "Building Swift tools"

    mkdir -p "$BIN_DIR/WallpaperFaded.app/Contents/MacOS"
    mkdir -p "$BIN_DIR/WallpaperFade.app/Contents/MacOS"

    swiftc -O "$REPO_DIR/tools/wallpaper-faded.swift" \
        -o "$BIN_DIR/WallpaperFaded.app/Contents/MacOS/wallpaper-faded" \
        -framework AppKit -framework QuartzCore
    info "  Built wallpaper-faded"

    swiftc -O "$REPO_DIR/tools/wallpaper-fade.swift" \
        -o "$BIN_DIR/WallpaperFade.app/Contents/MacOS/wallpaper-fade" \
        -framework AppKit -framework QuartzCore -framework ScreenCaptureKit
    info "  Built wallpaper-fade"

    # LSUIElement plist (no Dock icon)
    for app in WallpaperFaded WallpaperFade; do
        cat > "$BIN_DIR/$app.app/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>LSUIElement</key><true/></dict></plist>
PLIST
    done

    # Copy borders-animated only when explicitly requested.
    if [ -f "$REPO_DIR/borders-animated" ]; then
        if [ "$INSTALL_PREBUILT_BORDERS" = true ]; then
            local checksum_file="$CHECKSUM_DIR/borders-animated.sha256"
            verify_sha256 "$REPO_DIR/borders-animated" "$checksum_file"
            cp "$REPO_DIR/borders-animated" "$BIN_DIR/"
            info "  Installed borders-animated (checksum verified)"
        else
            info "  Skipped prebuilt borders-animated (pass --install-prebuilt-borders to install it)"
        fi
    else
        info "  borders-animated not found in repo — build from source or download separately"
    fi
}

# ---------------------------------------------------------------------------
# Install launchd agents (substitute __HOME__, __PYTHON__, __AGENT_PREFIX__)
# ---------------------------------------------------------------------------
install_agents() {
    local PYTHON
    PYTHON=$(detect_python)
    info "Installing launchd agents (Python: $PYTHON)"

    mkdir -p "$LAUNCH_DIR"
    for plist in "$REPO_DIR"/launchd/*.plist; do
        local name dest
        name=$(basename "$plist")
        dest=$(plist_dest_path "$name")
        sed \
            -e "s|__HOME__|$HOME|g" \
            -e "s|__PYTHON__|$PYTHON|g" \
            -e "s|__AGENT_PREFIX__|$AGENT_PREFIX|g" \
            "$plist" > "$dest"
        info "  $(basename "$dest")"
    done
}

# ---------------------------------------------------------------------------
# Load agents
# ---------------------------------------------------------------------------
load_agents() {
    info "Loading launchd agents"
    for plist in "$LAUNCH_DIR"/"$AGENT_PREFIX".*.plist; do
        [ -f "$plist" ] || continue
        launchctl unload "$plist" 2>/dev/null || true
        launchctl load "$plist"
        info "  Loaded $(basename "$plist")"
    done
}

# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------
uninstall() {
    info "Uninstalling launchd agents for prefix $AGENT_PREFIX"
    for plist in "$LAUNCH_DIR"/"$AGENT_PREFIX".*.plist; do
        [ -f "$plist" ] || continue
        launchctl unload "$plist" 2>/dev/null || true
        rm "$plist"
        info "  Removed $(basename "$plist")"
    done
    echo ""
    echo "Agents removed. Config at $CONFIG_DIR/ left in place."
    echo "Remove manually: rm -rf $CONFIG_DIR"
    exit 0
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
parse_args "$@"
validate_agent_prefix
[ "$UNINSTALL" = true ] && uninstall

echo "wallpaper-theme-sync installer"
echo "==============================="
echo ""
echo "Launchd prefix: $AGENT_PREFIX"
echo ""

check_deps
deploy_configs
build_tools
install_agents
load_agents

echo ""
echo "Done!"
echo "  Config: $CONFIG_DIR/config.toml"
echo "  Test:   python3 $CONFIG_DIR/wallpaper_colors.py -v"
echo "  Logs:   tail -f $CONFIG_DIR/sync.log"
