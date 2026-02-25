#!/usr/bin/env python3
"""Wallpaper Color Sync

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

import os
import subprocess
import sys

from PIL import Image

from wcsync.capture import DESKTOPPR, load_wallpaper
from wcsync.colors import build_scheme, extract_palette, image_hash, sat, lum
from wcsync.config import Config
from wcsync.reloaders import reload_all
from wcsync.utils import atomic_write, hexc, log
from wcsync.writers import write_all

CACHE_FILE = os.path.expanduser("~/.config/wallpaper-colors/.last_hash")
LAST_WP_FILE = os.path.expanduser("~/.config/wallpaper-colors/.last_wp_path")


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    force = "--force" in sys.argv or "-f" in sys.argv

    config = Config.load()
    log("Triggered")

    # 1. Load wallpaper image
    img, wp_path = load_wallpaper(config)
    if img is None:
        log("ERROR: Could not load wallpaper")
        sys.exit(1)
    if verbose:
        log(f"Loaded wallpaper: {img.size[0]}x{img.size[1]} ({wp_path or 'capture'})")

    # Resize once for all downstream processing
    small = img.resize((200, 200), Image.Resampling.LANCZOS)

    # 2. Check if wallpaper actually changed (skip if identical)
    current_hash = image_hash(small)
    if not force and os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            if f.read().strip() == current_hash:
                log("Unchanged, skipping")
                return

    # 2b. Propagate wallpaper to all spaces (fixes Unsplash per-space bug)
    if wp_path:
        subprocess.run([DESKTOPPR, wp_path], capture_output=True)
        if verbose:
            log(f"Propagated wallpaper to all spaces: {wp_path}")

    # 3. Extract & build scheme
    palette = extract_palette(small, n_colors=config.n_colors)
    scheme = build_scheme(palette, config)

    if verbose:
        print("Palette:")
        for c in palette:
            print(
                f"  #{c[0]:02x}{c[1]:02x}{c[2]:02x}  sat={sat(*c):.2f} lum={lum(*c):.0f}"
            )
        print(f"Accent:    {hexc(*scheme['accent'])}")
        print(f"Secondary: {hexc(*scheme['secondary'])}")
        print(f"Dark:      {hexc(*scheme['dark'])}")
        print(f"Light:     {hexc(*scheme['light'])}")

    # 4. Write configs
    write_all(scheme, config)

    # 5. Save hash + wallpaper path
    atomic_write(CACHE_FILE, current_hash)
    if wp_path:
        atomic_write(LAST_WP_FILE, wp_path)

    # 6. Reload all services in parallel
    reload_all(scheme, config)

    ba = hexc(*scheme["border_accent"])
    bs = hexc(*scheme["border_secondary"])
    log(f"Synced: border={ba}→{bs} bar_accent={hexc(*scheme['accent'])}")


if __name__ == "__main__":
    main()
