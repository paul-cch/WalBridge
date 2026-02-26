"""Shared utilities for wallpaper color sync."""

import os
import re
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


def safe_home_path(path, default_path, env_var=None):
    """Resolve a path, forcing it to remain under the current user's home."""
    home = os.path.realpath(os.path.expanduser("~"))
    fallback = os.path.realpath(os.path.abspath(os.path.expanduser(default_path)))

    raw = path if path is not None else default_path
    resolved = os.path.realpath(os.path.abspath(os.path.expanduser(raw)))

    if resolved == home or resolved.startswith(home + os.sep):
        return resolved

    if env_var and path is not None:
        log(f"Ignoring {env_var}: path must stay within {home}")
    return fallback


_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_SAFE_FILE_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def sanitize_name(value, default, env_var=None):
    """Allow only [A-Za-z0-9_-] for generated file/theme names."""
    if isinstance(value, str):
        name = value.strip()
        if _SAFE_NAME_RE.fullmatch(name):
            return name
    if env_var and value is not None:
        log(f"Ignoring {env_var}: expected [A-Za-z0-9_-]+")
    return default


def sanitize_filename(value, default, env_var=None):
    """Allow only basename-like file names (no path separators)."""
    if isinstance(value, str):
        name = value.strip()
        if _SAFE_FILE_RE.fullmatch(name):
            return name
    if env_var and value is not None:
        log(f"Ignoring {env_var}: invalid filename")
    return default


# --- Color Format Helpers ---


def clamp(v, lo=0, hi=255):
    return max(lo, min(hi, int(v)))


def hexc(r, g, b, a=0xFF):
    """Format as 0xAARRGGBB (SketchyBar / JankyBorders)."""
    return f"0x{a:02x}{r:02x}{g:02x}{b:02x}"


def hex6(r, g, b):
    """Format as #rrggbb (Kitty / Neovim / Yazi / Starship)."""
    return f"#{r:02x}{g:02x}{b:02x}"
