"""Wallpaper capture from macOS desktop.

Supports file-based capture via desktoppr (preferred) and CGWindowListCreateImage
fallback for dynamic/system wallpapers. Multi-monitor aware.
"""

import os
import subprocess
import time

import Quartz
from PIL import Image

from .utils import log

DESKTOPPR = "/usr/local/bin/desktoppr"

# Window name patterns to search for wallpaper windows.
# macOS has used different names across versions.
_WALLPAPER_PREFIXES = ("Wallpaper-", "Desktop Picture")


def get_wallpaper_path(display=1):
    """Get wallpaper file path via desktoppr for a given display.

    Args:
        display: Display number (1 = primary, 2 = secondary, etc.)

    Returns:
        File path string or empty string on failure.
    """
    cmd = [DESKTOPPR, str(display - 1)]  # desktoppr uses 0-based screen index

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        log(f"desktoppr failed for display {display}: {e}")
        return ""


def get_display_count():
    """Return the number of connected displays via Quartz."""
    err, display_ids, count = Quartz.CGGetActiveDisplayList(16, None, None)
    if err != 0:
        return 1
    return count


def _find_wallpaper_window(display=1):
    """Find the best wallpaper window ID, optionally filtered by display.

    Returns:
        (window_id, bounds_dict) or (None, None) if not found.
    """
    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionAll, Quartz.kCGNullWindowID
    )

    # Get target display bounds for filtering when display > 1
    display_bounds = None
    if display > 1:
        err, display_ids, count = Quartz.CGGetActiveDisplayList(16, None, None)
        if err == 0 and display <= count:
            rect = Quartz.CGDisplayBounds(display_ids[display - 1])
            display_bounds = {
                "X": Quartz.CGRectGetMinX(rect),
                "Y": Quartz.CGRectGetMinY(rect),
                "Width": Quartz.CGRectGetWidth(rect),
                "Height": Quartz.CGRectGetHeight(rect),
            }

    best = None
    best_area = 0

    for w in window_list:
        name = w.get("kCGWindowName", "") or ""
        if not any(name.startswith(prefix) for prefix in _WALLPAPER_PREFIXES):
            continue

        bounds = w.get("kCGWindowBounds", {})
        width = float(bounds.get("Width", 0))
        height = float(bounds.get("Height", 0))
        area = width * height

        # Filter by display bounds if targeting a specific display
        if display_bounds is not None:
            wx = float(bounds.get("X", 0))
            wy = float(bounds.get("Y", 0))
            dx, dy = display_bounds["X"], display_bounds["Y"]
            dw, dh = display_bounds["Width"], display_bounds["Height"]
            # Check if window origin falls within display bounds (±10px tolerance)
            if not (dx - 10 <= wx <= dx + dw and dy - 10 <= wy <= dy + dh):
                continue

        if area > best_area:
            best_area = area
            best = w.get("kCGWindowNumber", 0)

    return best


def capture_wallpaper(display=1, retries=3, retry_delay=0.5):
    """Capture the wallpaper window and return a PIL Image directly (no disk I/O).

    Retries on failure with exponential backoff. Validates the captured image
    is not degenerate (all-black, tiny, etc.).

    Args:
        display: Display number to capture (1 = primary).
        retries: Number of retry attempts.
        retry_delay: Base delay between retries (doubled each attempt).

    Returns:
        PIL Image in RGB mode, or None on failure.
    """
    for attempt in range(retries):
        window_id = _find_wallpaper_window(display)
        if window_id is None:
            if attempt < retries - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            log(
                f"No wallpaper window found after {retries} attempts (display={display})"
            )
            return None

        cg_image = Quartz.CGWindowListCreateImage(
            Quartz.CGRectNull,
            Quartz.kCGWindowListOptionIncludingWindow,
            window_id,
            Quartz.kCGWindowImageBoundsIgnoreFraming,
        )
        if not cg_image:
            if attempt < retries - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            log("CGWindowListCreateImage returned None")
            return None

        w = Quartz.CGImageGetWidth(cg_image)
        h = Quartz.CGImageGetHeight(cg_image)

        # Validate dimensions — reject degenerate captures
        if w < 16 or h < 16:
            log(f"Captured image too small ({w}x{h}), retrying")
            if attempt < retries - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            return None

        provider = Quartz.CGImageGetDataProvider(cg_image)
        raw = Quartz.CGDataProviderCopyData(provider)
        img = Image.frombytes("RGBA", (w, h), bytes(raw), "raw", "BGRA")
        result = img.convert("RGB")

        # Validate: reject all-black images (likely capture before render)
        thumb = result.resize((4, 4), Image.Resampling.NEAREST)
        pixels = list(thumb.getdata())
        if all(sum(p) < 15 for p in pixels):
            log("Captured image is all black, retrying")
            if attempt < retries - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            return None

        return result

    return None


def load_wallpaper_from_file(wp_path):
    """Load wallpaper image from file path (avoids Dock render race)."""
    if wp_path and os.path.isfile(wp_path):
        try:
            return Image.open(wp_path).convert("RGB")
        except Exception:
            pass
    return None


def load_wallpaper(config=None):
    """High-level: load wallpaper image using the best available method.

    Prefers file-based loading via desktoppr (instant, no race condition),
    falls back to CGWindowListCreateImage (handles dynamic/system wallpapers).

    Returns:
        (PIL Image in RGB, wallpaper_path_or_None)
    """
    from .config import Config

    if config is None:
        config = Config()

    wp_path = get_wallpaper_path(display=config.display)
    img = load_wallpaper_from_file(wp_path)

    if img is None:
        img = capture_wallpaper(display=config.display)
        wp_path = ""

    return img, wp_path
