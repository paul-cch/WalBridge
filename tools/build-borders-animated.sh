#!/bin/bash
set -euo pipefail
# Build borders-animated from source.
#
# This script intentionally builds from a pinned git ref for reproducibility.
# For gradient support, point --repo/--ref at your gradient-enabled fork and
# optionally pass a patch via --patch-file.
#
# Usage:
#   bash tools/build-borders-animated.sh
#   bash tools/build-borders-animated.sh --repo <git-url> --ref <tag-or-sha>
#   bash tools/build-borders-animated.sh --patch-file ./gradient.patch
#   bash tools/build-borders-animated.sh --out ./borders-animated

REPO_URL="https://github.com/FelixKratz/JankyBorders.git"
REF="v1.8.4"
OUT_PATH="$(pwd)/borders-animated"
PATCH_FILE=""

info() { printf '→ %s\n' "$*"; }
err() { printf 'ERROR: %s\n' "$*" >&2; }

usage() {
    cat <<'USAGE'
Usage:
  bash tools/build-borders-animated.sh [options]

Options:
  --repo URL         Git repository URL (default: FelixKratz/JankyBorders)
  --ref REF          Git tag or commit to build (default: v1.8.4)
  --patch-file PATH  Optional patch to apply with `git apply` before build
  --out PATH         Output binary path (default: ./borders-animated)
  -h, --help         Show this help
USAGE
}

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --repo)
                REPO_URL="$2"
                shift 2
                ;;
            --ref)
                REF="$2"
                shift 2
                ;;
            --patch-file)
                PATCH_FILE="$2"
                shift 2
                ;;
            --out)
                OUT_PATH="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                err "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        err "Missing required command: $1"
        exit 1
    fi
}

main() {
    parse_args "$@"

    require_cmd git
    require_cmd make
    require_cmd shasum

    local workdir src
    workdir="$(mktemp -d)"
    src="$workdir/src"
    trap 'rm -rf "$workdir"' EXIT

    info "Cloning $REPO_URL"
    git clone "$REPO_URL" "$src" >/dev/null 2>&1
    cd "$src"

    info "Checking out $REF"
    git checkout "$REF" >/dev/null 2>&1

    if [ -n "$PATCH_FILE" ]; then
        if [ ! -f "$PATCH_FILE" ]; then
            err "Patch file not found: $PATCH_FILE"
            exit 1
        fi
        info "Applying patch: $PATCH_FILE"
        git apply "$PATCH_FILE"
    fi

    info "Building with make"
    make

    if [ ! -f "bin/borders" ]; then
        err "Build did not produce bin/borders"
        exit 1
    fi

    mkdir -p "$(dirname "$OUT_PATH")"
    cp "bin/borders" "$OUT_PATH"
    chmod +x "$OUT_PATH"

    # Ad-hoc codesign avoids runtime warnings on macOS local builds.
    if command -v codesign >/dev/null 2>&1; then
        codesign --force -s - "$OUT_PATH" >/dev/null 2>&1 || true
    fi

    info "Built binary: $OUT_PATH"
    info "SHA256: $(shasum -a 256 "$OUT_PATH" | awk '{print $1}')"
}

main "$@"
