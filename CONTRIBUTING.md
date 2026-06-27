# Contributing to WalBridge

## Quick Start

1. Clone the repo
2. Install dependencies: `pip3 install -r requirements.txt`
3. Install external tools: `brew install desktoppr`
4. Enable commit hooks: `git config core.hooksPath .githooks`
5. Run tests: `python3 -m unittest discover -s tests -p 'test_*.py' -v`
6. Run shell syntax checks:
   `bash -n install.sh configs/wallpaper-colors/theme_watcher.sh configs/wallpaper-colors/wallpaper_cycle.sh configs/wallpaper-colors/borders-cycle.sh configs/wallpaper-colors/next-wallpaper.sh configs/wallpaper-colors/setup-targets.sh configs/sketchybar/sketchybarrc configs/sketchybar/plugins/*.sh`
7. Run manually: `python3 configs/wallpaper-colors/wallpaper_colors.py -v`

## Community and Security

- Follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) in all project interactions.
- Report vulnerabilities privately (see [SECURITY.md](SECURITY.md)); do not open public security issues.
- Use GitHub issue templates for bug reports and feature requests.

## Adding a New Target App

`wcsync/target_apps.py` is the single source of truth for Target App defaults,
path policy, writer adapters, and hot reload capability.

### 1. Create a writer module

Create `configs/wallpaper-colors/wcsync/writers/myapp.py`:

```python
"""MyApp theme writer."""

from ..target_apps import target_path
from ..utils import atomic_write, hex6


def write(scheme, config=None):
    content = f"""# Auto-generated from wallpaper — do not edit manually
accent = {hex6(*scheme["accent"])}
background = {hex6(*scheme["dark"])}
foreground = {hex6(*scheme["light"])}
"""
    atomic_write(target_path("myapp"), content)
```

### 2. Add Target App metadata

In `configs/wallpaper-colors/wcsync/target_apps.py`, add:

```python
TargetApp(
    "myapp",
    "myapp",
    paths={
        "output": PathPolicy(
            "~/.config/myapp/theme.conf",
            "WALLPAPER_MYAPP_OUTPUT_PATH",
        )
    },
)
```

### 3. Add a reload function (optional)

If the app supports hot-reload, add to `configs/wallpaper-colors/wcsync/reloaders.py`:

```python
def reload_myapp(scheme=None, config=None):
    return subprocess.Popen(
        [_find_bin("myapp"), "--reload"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
)
```

Then set `reload_function="reload_myapp"` on the Target App metadata.

### 4. Add tests

Add metadata/path coverage in `tests/test_target_apps.py` and writer output
coverage in `tests/test_writer_paths.py`.

## Project Structure

```
configs/wallpaper-colors/
├── wallpaper_colors.py      # Entry point
├── wcsync/
│   ├── utils.py             # atomic_write, color format helpers
│   ├── capture.py           # Wallpaper image capture
│   ├── colors.py            # Palette extraction + scheme generation
│   ├── config.py            # Config dataclass + TOML loading
│   ├── target_apps.py       # Target App defaults, paths, writers, reloaders
│   ├── writers/             # Per-app config writers
│   └── reloaders.py         # Per-app reload functions
tools/
├── wallpaper-faded.swift    # Persistent transition daemon
└── wallpaper-fade.swift     # One-shot transition CLI
```

## Code Style

- Python: follow existing style — clean, minimal, no type annotations on internal functions
- Shell: use strict mode (`set -uo pipefail`, plus `-e` where fail-fast is desired)
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
| `border_inactive` | `(r, g, b)` | Muted accent for inactive borders |
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

For user-visible behavior changes, update `CHANGELOG.md` in the same PR.

## SketchyBar Example Config

`configs/sketchybar/sketchybarrc` is intentionally public-safe by default:

- Keep the example profile generic and dependency-light
- New plugin references must include matching scripts under `configs/sketchybar/plugins/`

## Target Path Overrides

To support different local layouts, these environment variables are supported:

- `WALLPAPER_BORDER_COLORS_FILE` (used by borders writer + `borders-cycle.sh`)
- `WALLPAPER_BORDERS_BIN` (used by `borders-cycle.sh`)
- `WALLPAPER_WEZTERM_SCHEME_NAME` / `WALLPAPER_WEZTERM_OUTPUT_PATH`
- `WALLPAPER_ALACRITTY_OUTPUT_PATH`
- `WALLPAPER_GHOSTTY_THEME_FILE` / `WALLPAPER_GHOSTTY_OUTPUT_PATH`
- `WALLPAPER_ITERM_PRESET_NAME` / `WALLPAPER_ITERM_OUTPUT_PATH`
- `WALLPAPER_TMUX_OUTPUT_PATH`
- `WALLPAPER_BTOP_THEME_NAME` / `WALLPAPER_BTOP_OUTPUT_PATH`
- `WALLPAPER_YAZI_FLAVOR_NAME` (changes default Yazi flavor folder name)
- `WALLPAPER_YAZI_OUTPUT_PATH` (explicit Yazi flavor output path)
- `WALLPAPER_YAZI_THEME_PATH` / `WALLPAPER_YAZI_WRITE_THEME_SELECTOR`
- `WALLPAPER_VSCODE_SETTINGS_PATH` (opt-in VS Code settings.json target)
