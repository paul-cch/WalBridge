# Contributing to Wallpaper Theme Sync

## Quick Start

1. Clone the repo
2. Install dependencies: `pip3 install -r requirements.txt`
3. Install external tools: `brew install desktoppr`
4. Run manually: `python3 configs/wallpaper-colors/wallpaper_colors.py -v`

## Adding a New Target App

The project uses a writer/reloader registry pattern. Adding support for a new app takes 4 steps:

### 1. Create a writer module

Create `configs/wallpaper-colors/wcsync/writers/myapp.py`:

```python
"""MyApp theme writer."""

import os

from ..utils import atomic_write, hex6

OUTPUT_PATH = os.path.expanduser("~/.config/myapp/theme.conf")


def write(scheme, config=None):
    content = f"""# Auto-generated from wallpaper — do not edit manually
accent = {hex6(*scheme["accent"])}
background = {hex6(*scheme["dark"])}
foreground = {hex6(*scheme["light"])}
"""
    atomic_write(OUTPUT_PATH, content)
```

### 2. Register the writer

In `configs/wallpaper-colors/wcsync/writers/__init__.py`, add:

```python
from . import myapp

_WRITERS = {
    ...
    "myapp": myapp,
}
```

### 3. Add a reload function (optional)

If the app supports hot-reload, add to `configs/wallpaper-colors/wcsync/reloaders.py`:

```python
def reload_myapp():
    return subprocess.Popen(
        [_find_bin("myapp"), "--reload"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
```

And register it in `reload_all()`.

### 4. Add a config toggle

In `configs/wallpaper-colors/wcsync/config.py`, add to `_DEFAULT_TARGETS`:

```python
_DEFAULT_TARGETS = {
    ...
    "myapp": True,
}
```

## Project Structure

```
configs/wallpaper-colors/
├── wallpaper_colors.py      # Entry point
├── wcsync/
│   ├── utils.py             # atomic_write, color format helpers
│   ├── capture.py           # Wallpaper image capture
│   ├── colors.py            # Palette extraction + scheme generation
│   ├── config.py            # Config dataclass + TOML loading
│   ├── writers/             # Per-app config writers (registry pattern)
│   └── reloaders.py         # Per-app reload functions
tools/
├── wallpaper-faded.swift    # Persistent transition daemon
└── wallpaper-fade.swift     # One-shot transition CLI
```

## Code Style

- Python: follow existing style — clean, minimal, no type annotations on internal functions
- Shell: `set -euo pipefail` in every script
- All config file writes **must** use `atomic_write()` from `wcsync/utils.py`
- Color formats: `hexc()` for `0xAARRGGBB`, `hex6()` for `#rrggbb`
- Binary lookups: use `_find_bin()` in reloaders, `shutil.which()` in modules

## Color Scheme

The `scheme` dict passed to all writers contains:

| Key | Type | Description |
|-----|------|-------------|
| `accent` | `(r, g, b)` | Primary accent from wallpaper |
| `secondary` | `(r, g, b)` | Most hue-distant palette color |
| `border_accent` | `(r, g, b)` | Vivified accent for borders |
| `border_secondary` | `(r, g, b)` | Vivified secondary for borders |
| `dark` | `(r, g, b)` | Darkest palette color |
| `light` | `(r, g, b)` | Lightest palette color |
| `bar_bg` | `(r, g, b)` | Bar background (= dark) |
| `item_bg` | `(r, g, b)` | Item background (slightly lighter) |
| `grey` | `(r, g, b)` | Muted grey |
| `red`, `green`, `yellow`, `cyan`, `purple`, `orange`, `pink` | `(r, g, b)` | Named colors harmonized toward accent |

## Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/). A git hook enforces the format — set it up with:

```bash
git config core.hooksPath .githooks
```

Examples:

```
feat: add multi-monitor support
fix(capture): retry on CGWindowListCreateImage failure
refactor: modularize wallpaper_colors.py into wcsync package
```
