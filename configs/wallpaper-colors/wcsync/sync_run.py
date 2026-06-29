"""Sync Run module.

Owns one wallpaper-to-Target-App sync lifecycle. The CLI is an adapter over
this module; tests should exercise this interface directly.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass
from hashlib import sha256

from PIL import Image

from .capture import DESKTOPPR, load_wallpaper
from .colors import build_scheme, extract_palette, image_hash, lum, sat
from .config import Config
from .reloaders import reload_all
from .target_writing import write_all
from .target_apps import target_env_material
from .utils import atomic_write, hexc, log

CACHE_FILE = os.path.expanduser("~/.config/wallpaper-colors/.last_hash")
LAST_WP_FILE = os.path.expanduser("~/.config/wallpaper-colors/.last_wp_path")


@dataclass(frozen=True)
class SyncRunOptions:
    verbose: bool = False
    force: bool = False


@dataclass(frozen=True)
class SyncRunResult:
    skipped: bool
    cache_key: str | None = None
    wallpaper_path: str = ""


class SyncRunError(RuntimeError):
    """Raised when a Sync Run cannot complete."""


def config_signature(config):
    """Hash config and Target App env overrides that affect generated files."""
    payload = {
        "config": asdict(config),
        "env": target_env_material(),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def build_cache_key(wallpaper_hash, config):
    return f"{wallpaper_hash}:{config_signature(config)}"


def _log_verbose_palette(palette, scheme):
    print("Palette:")
    for color in palette:
        print(
            f"  #{color[0]:02x}{color[1]:02x}{color[2]:02x}  "
            f"sat={sat(*color):.2f} lum={lum(*color):.0f}"
        )
    print(f"Accent:    {hexc(*scheme['accent'])}")
    print(f"Secondary: {hexc(*scheme['secondary'])}")
    print(f"Dark:      {hexc(*scheme['dark'])}")
    print(f"Light:     {hexc(*scheme['light'])}")


def run_sync(options=None):
    """Run one wallpaper color sync lifecycle."""
    options = options or SyncRunOptions()

    config = Config.load()
    log("Triggered")

    img, wp_path = load_wallpaper(config)
    if img is None:
        log("ERROR: Could not load wallpaper")
        raise SyncRunError("Could not load wallpaper")
    if options.verbose:
        log(f"Loaded wallpaper: {img.size[0]}x{img.size[1]} ({wp_path or 'capture'})")

    current_hash = image_hash(img)
    current_cache_key = build_cache_key(current_hash, config)
    if not options.force and os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            if f.read().strip() == current_cache_key:
                log("Unchanged, skipping")
                return SyncRunResult(skipped=True, cache_key=current_cache_key, wallpaper_path=wp_path)

    small = img.resize((200, 200), Image.Resampling.LANCZOS)

    if wp_path:
        subprocess.run([DESKTOPPR, wp_path], capture_output=True)
        if options.verbose:
            log(f"Propagated wallpaper to all spaces: {wp_path}")

    palette = extract_palette(small, n_colors=config.n_colors)
    scheme = build_scheme(palette, config)

    if options.verbose:
        _log_verbose_palette(palette, scheme)

    failed_writers = write_all(scheme, config)
    if failed_writers:
        failures = ", ".join(sorted(failed_writers))
        log(f"ERROR: writer failures ({failures}); not caching")
        raise SyncRunError(f"writer failures: {failures}")

    atomic_write(CACHE_FILE, current_cache_key)
    if wp_path:
        atomic_write(LAST_WP_FILE, wp_path)

    reload_all(scheme, config)

    ba = hexc(*scheme["border_accent"])
    bi_rgb = scheme.get("border_inactive") or scheme.get("grey", scheme["border_accent"])
    bi = hexc(*bi_rgb)
    log(f"Synced: border={ba} inactive={bi} bar_accent={hexc(*scheme['accent'])}")
    return SyncRunResult(skipped=False, cache_key=current_cache_key, wallpaper_path=wp_path)
