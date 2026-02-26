#!/bin/bash
set -euo pipefail
# install.sh — Deploy WalBridge to your Mac.
#
# Usage:
#   bash install.sh                         # Install / update
#   bash install.sh --uninstall             # Remove launchd agents
#   bash install.sh --setup-targets         # Also wire tmux/btop/iTerm2 target setup

detect_home() {
    if [ -n "${WTS_INSTALL_HOME:-}" ]; then
        printf '%s\n' "$WTS_INSTALL_HOME"
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        python3 -c 'import os,pwd; print(pwd.getpwuid(os.getuid()).pw_dir)'
    else
        printf '%s\n' "$HOME"
    fi
}

resolve_path() {
    python3 -c 'import os,sys; print(os.path.realpath(os.path.abspath(os.path.expanduser(sys.argv[1]))))' "$1"
}

REAL_HOME="$(detect_home)"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="$REAL_HOME/.config/wallpaper-colors"
BIN_DIR="$REAL_HOME/.local/bin"
LAUNCH_DIR="$REAL_HOME/Library/LaunchAgents"
CHECKSUM_DIR="$REPO_DIR/checksums"
# Optional: packagers can call verify_sha256 for key files when CHECKSUM_DIR is populated.
AGENT_PREFIX="${WALBRIDGE_AGENT_PREFIX:-${WTS_AGENT_PREFIX:-com.walbridge}}"
UNINSTALL=false
SETUP_TARGETS=false

info()  { printf '→ %s\n' "$*"; }
error() { printf 'ERROR: %s\n' "$*" >&2; }

usage() {
    cat <<'USAGE'
Usage:
  bash install.sh [--setup-targets]
  bash install.sh --uninstall

Options:
  --setup-targets              Run one-time tmux/btop/iTerm2 setup helper
  --uninstall                 Unload and remove launchd agents for current prefix

Environment:
  WALBRIDGE_AGENT_PREFIX      launchd label/file prefix (default: com.walbridge)
  WTS_AGENT_PREFIX            legacy alias for WALBRIDGE_AGENT_PREFIX
USAGE
}

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --uninstall)
                UNINSTALL=true
                ;;
            --setup-targets)
                SETUP_TARGETS=true
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
        error "Invalid launchd prefix from WALBRIDGE_AGENT_PREFIX/WTS_AGENT_PREFIX: $AGENT_PREFIX"
        error "Allowed pattern: ^[A-Za-z0-9][A-Za-z0-9.-]*$"
        exit 1
    fi
}

validate_home() {
    if [ -z "$REAL_HOME" ] || [ ! -d "$REAL_HOME" ]; then
        error "Unable to resolve real home directory"
        exit 1
    fi

    if ! printf '%s' "$REAL_HOME" | grep -Eq '^/'; then
        error "Resolved home is not an absolute path: $REAL_HOME"
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
# Dependency check (uses same interpreter as detect_python to avoid conflicts)
# ---------------------------------------------------------------------------
check_deps() {
    local py ok=true
    py="$(detect_python)"

    if [ -z "$py" ] || [ "$py" = "python3" ]; then
        command -v python3 >/dev/null 2>&1 || { error "python3 not found"; ok=false; }
    fi
    if [ -n "$py" ] && [ -x "$py" ]; then
        "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null ||
            { error "Python 3.11+ required (found $("$py" --version 2>&1))"; ok=false; }
        "$py" -c "import PIL" 2>/dev/null    || { error "Pillow not installed (pip install Pillow)"; ok=false; }
        "$py" -c "import Quartz" 2>/dev/null || { error "PyObjC not installed (pip install pyobjc-framework-Quartz)"; ok=false; }
    else
        error "No suitable Python with Pillow found"; ok=false
    fi

    command -v desktoppr >/dev/null 2>&1 || { error "desktoppr not found (brew install desktoppr)"; ok=false; }
    command -v swiftc >/dev/null 2>&1      || { error "swiftc not found (install Xcode Command Line Tools)"; ok=false; }

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

    for script in wallpaper_cycle.sh borders-cycle.sh theme_watcher.sh next-wallpaper.sh setup-targets.sh; do
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
}

# ---------------------------------------------------------------------------
# Install launchd agents (substitute __HOME__, __PYTHON__, __AGENT_PREFIX__)
# ---------------------------------------------------------------------------
install_agents() {
    local PYTHON
    PYTHON=$(resolve_path "$(detect_python)")
    if [ ! -x "$PYTHON" ]; then
        error "Resolved Python is not executable: $PYTHON"
        exit 1
    fi
    info "Installing launchd agents (Python: $PYTHON)"

    mkdir -p "$LAUNCH_DIR"
    mkdir -p "$REAL_HOME/.local/share/borders"
    for plist in "$REPO_DIR"/launchd/*.plist; do
        local name dest
        name=$(basename "$plist")
        dest=$(plist_dest_path "$name")
        sed \
            -e "s|__HOME__|$REAL_HOME|g" \
            -e "s|__PYTHON__|$PYTHON|g" \
            -e "s|__AGENT_PREFIX__|$AGENT_PREFIX|g" \
            "$plist" > "$dest"
        info "  $(basename "$dest")"
    done
}

bootout_agent() {
    local plist="$1"
    local uid domain label
    uid="$(id -u)"
    domain="gui/$uid"
    label="$(basename "$plist" .plist)"
    launchctl bootout "$domain/$label" 2>/dev/null || launchctl bootout "$domain" "$plist" 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Load agents
# ---------------------------------------------------------------------------
load_agents() {
    local uid domain label
    uid="$(id -u)"
    domain="gui/$uid"

    info "Loading launchd agents"
    for plist in "$LAUNCH_DIR"/"$AGENT_PREFIX".*.plist; do
        [ -f "$plist" ] || continue
        label="$(basename "$plist" .plist)"
        bootout_agent "$plist"
        launchctl bootstrap "$domain" "$plist"
        launchctl enable "$domain/$label" 2>/dev/null || true
        info "  Loaded $(basename "$plist")"
    done
}

# ---------------------------------------------------------------------------
# Optional target setup helper
# ---------------------------------------------------------------------------
setup_targets() {
    if [ "$SETUP_TARGETS" != true ]; then
        return
    fi

    if [ ! -f "$CONFIG_DIR/setup-targets.sh" ]; then
        error "Target setup helper not found: $CONFIG_DIR/setup-targets.sh"
        return
    fi

    info "Running optional target setup (tmux/btop/iTerm2)"
    bash "$CONFIG_DIR/setup-targets.sh"
}

# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------
uninstall() {
    info "Uninstalling launchd agents for prefix $AGENT_PREFIX"
    for plist in "$LAUNCH_DIR"/"$AGENT_PREFIX".*.plist; do
        [ -f "$plist" ] || continue
        bootout_agent "$plist"
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
validate_home
[ "$UNINSTALL" = true ] && uninstall

echo "WalBridge installer"
echo "==============================="
echo ""
echo "Launchd prefix: $AGENT_PREFIX"
echo ""

check_deps
deploy_configs
build_tools
install_agents
load_agents
setup_targets

echo ""
echo "Done!"
echo "  Config: $CONFIG_DIR/config.toml"
echo "  Test:   python3 $CONFIG_DIR/wallpaper_colors.py -v"
echo "  Targets setup (optional): bash install.sh --setup-targets"
echo "  Launchd: agents run in Aqua; persistent daemons auto-restart with throttle"
echo "  Logs:   tail -f $CONFIG_DIR/sync.log"
