"""Shared utilities for wallpaper color sync."""

import os
import tempfile
from datetime import datetime


def atomic_write(path, content):
    """Write content to path atomically via temp file + rename."""
    dirn = os.path.dirname(path)
    os.makedirs(dirn, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dirn, prefix=".tmp_")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp, path)
    except BaseException:  # clean up temp file even on SIGINT/SystemExit
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def log(msg):
    """Always log with timestamp (visible in launchd logs)."""
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


# --- Color Format Helpers ---


def clamp(v, lo=0, hi=255):
    return max(lo, min(hi, int(v)))


def hexc(r, g, b, a=0xFF):
    """Format as 0xAARRGGBB (SketchyBar / JankyBorders)."""
    return f"0x{a:02x}{r:02x}{g:02x}{b:02x}"


def hex6(r, g, b):
    """Format as #rrggbb (Kitty / Neovim / Yazi / Starship)."""
    return f"#{r:02x}{g:02x}{b:02x}"
