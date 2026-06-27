#!/usr/bin/env python3
"""Wallpaper Color Sync CLI adapter.

Extracts dominant colors from the macOS wallpaper and updates:
- SketchyBar colors.sh
- JankyBorders border_colors
- Kitty terminal theme
- Neovim highlight colors + lualine theme
- Yazi file manager flavor
- OpenCode TUI theme
- HydroToDo TUI theme
- Starship prompt palette

Usage:
    python3 wallpaper_colors.py [-v|--verbose] [-f|--force]
"""

import sys

from wcsync.sync_run import SyncRunError, SyncRunOptions, run_sync


def options_from_argv(argv):
    return SyncRunOptions(
        verbose="--verbose" in argv or "-v" in argv,
        force="--force" in argv or "-f" in argv,
    )


def main():
    try:
        run_sync(options_from_argv(sys.argv[1:]))
    except SyncRunError:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
