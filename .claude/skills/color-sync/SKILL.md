---
name: "Wallpaper Color Sync Pipeline"
description: "Color extraction and theme sync pipeline for wallpaper-theme-sync. Provides context on the extract→scheme→write→reload chain, target app config formats, and reload commands. Use when editing wcsync/ modules, wallpaper_colors.py, shell scripts, Swift transition tools, or any color-related config."
user-invocable: false
---

# Wallpaper Color Sync Pipeline

## Architecture

```
wallpaper_cycle.sh  (launchd timer, every 30 min)
        │ desktoppr
        ▼
wallpaper-faded     (Swift daemon — persistent overlay, animated transitions)
        │
        ▼
wallpaper_colors.py (entry point — CLI + orchestration)
        │
        ├── wcsync/capture.py    → wallpaper image capture (multi-monitor + retry)
        ├── wcsync/colors.py     → palette extraction + scheme generation
        ├── wcsync/config.py     → config.toml loading
        ├── wcsync/utils.py      → atomic_write, log, color format helpers
        ├── wcsync/writers/      → per-app config writers (registry pattern)
        │   ├── sketchybar.py    → colors.sh          → SketchyBar
        │   ├── borders.py       → border_colors      → JankyBorders
        │   ├── kitty.py         → wallpaper.conf     → Kitty
        │   ├── neovim.py        → nvim_colors.lua    → Neovim
        │   ├── lualine.py       → wallpaper.lua      → Neovim lualine theme
        │   ├── yazi.py          → flavor.toml        → Yazi
        │   ├── starship.py      → starship.toml      → Starship prompt
        │   ├── opencode.py      → wallpaper.json     → OpenCode TUI
        │   └── hydrotodo.py     → hydrotodo.json     → HydroToDo
        └── wcsync/reloaders.py  → app-specific reload commands
```

## Package Structure

```
configs/wallpaper-colors/
├── wallpaper_colors.py          # Entry point (~100 lines)
├── config.toml.example          # Config reference
├── wcsync/
│   ├── __init__.py
│   ├── utils.py                 # atomic_write, log, clamp, hexc, hex6
│   ├── config.py                # Config dataclass + TOML loading
│   ├── colors.py                # extract_palette, build_scheme, vivify, pick_secondary
│   ├── capture.py               # get_wallpaper_path, capture_wallpaper (multi-monitor + retry)
│   ├── reloaders.py             # reload_all + per-app reload functions
│   └── writers/
│       ├── __init__.py          # WRITERS registry + write_all dispatch
│       ├── sketchybar.py        # write(scheme, config) → colors.sh
│       ├── borders.py           # write(scheme, config) → border_colors
│       ├── kitty.py             # write(scheme, config) → wallpaper.conf
│       ├── neovim.py            # write(scheme, config) → nvim_colors.lua
│       ├── lualine.py           # write(scheme, config) → wallpaper.lua
│       ├── yazi.py              # write(scheme, config) → flavor.toml
│       ├── starship.py          # write(scheme, config) → starship.toml
│       ├── opencode.py          # write(scheme, config) → wallpaper.json
│       └── hydrotodo.py         # write(scheme, config) → hydrotodo.json
```

## Pipeline Steps

1. **Capture** (`capture.py`) — Read wallpaper path via `desktoppr` (multi-monitor: `desktoppr <display_num>`). Fallback: `CGWindowListCreateImage` with retry (3 attempts, exponential backoff), multiple window name patterns ("Wallpaper-", "Desktop Picture"), and validation (reject < 16px, all-black).
2. **Dedup** (`wallpaper_colors.py`) — Hash 16x16 thumbnail (sha256). Skip if unchanged (~370ms).
3. **Extract** (`colors.py`) — Resize to 200x200, Pillow median-cut quantization → N dominant colors (default 8, configurable via `config.n_colors`).
4. **Scheme** (`colors.py`) — `build_scheme(palette, config)`:
   - `accent` = most vibrant (highest `saturation * weighted_luminance`), or `config.accent_override`
   - `secondary` = most hue-distant palette color from accent
   - `vivify()` = boost sat/val for border colors (configurable floors)
   - Named colors (red, green, cyan, etc.) = fixed hues harmonized toward accent by `config.harmonize_factor`
5. **Write** (`writers/`) — Each writer has `write(scheme, config)`. Registry in `writers/__init__.py` dispatches via `write_all(scheme, config)`. All use `atomic_write()` (temp + rename).
6. **Reload** (`reloaders.py`) — `reload_all(config)` calls per-app reload functions for enabled targets.

## Key Functions by Module

### `wcsync/utils.py`
| Function | Purpose |
|----------|---------|
| `atomic_write(path, content)` | Write via temp file + rename (crash-safe) |
| `log(msg)` | Timestamped log to stdout |
| `clamp(v, lo, hi)` | Numeric clamp |
| `hexc(r, g, b)` | RGB tuple → `#rrggbb` |
| `hex6(r, g, b)` | RGB tuple → `rrggbb` (no #) |

### `wcsync/capture.py`
| Function | Purpose |
|----------|---------|
| `get_wallpaper_path(display)` | desktoppr → file path for given display |
| `capture_wallpaper(display)` | CGWindowListCreateImage fallback with retry + validation |

### `wcsync/colors.py`
| Function | Purpose |
|----------|---------|
| `extract_palette(img, n_colors)` | Pillow median-cut quantization |
| `pick_secondary(palette, accent)` | Most hue-distant color for gradients |
| `vivify(rgb, min_sat, min_val)` | Boost saturation/value for borders |
| `build_scheme(palette, config)` | Master scheme dict from palette + config |

### `wcsync/config.py`
| Function | Purpose |
|----------|---------|
| `Config` dataclass | All tuning parameters with defaults |
| `Config.load()` | Load from `~/.config/wallpaper-colors/config.toml` |

### `wcsync/writers/__init__.py`
| Function | Purpose |
|----------|---------|
| `WRITERS` dict | Registry: name → (module, output_path) |
| `write_all(scheme, config)` | Dispatch to all enabled writers |

### `wcsync/reloaders.py`
| Function | Purpose |
|----------|---------|
| `reload_all(config)` | Reload all enabled target apps |
| `reload_sketchybar()` | `sketchybar --reload` |
| `reload_borders()` | IPC via borders-cycle.sh |
| `reload_kitty()` | `kitten @ set-colors` to all instances |
| `reload_neovim()` | `nvim --server` to all instances |

## Configuration (config.toml)

Loaded by `wcsync/config.py`. Optional — all fields have defaults.

```toml
[general]
display = 1           # Which display (1 = primary)
n_colors = 8          # Palette size

[scheme]
min_saturation = 0.45
min_value = 0.55
harmonize_factor = 0.25
# accent_override = "#3a7bd5"

[borders]
vivify_sat = 0.45
vivify_val = 0.65
opacity = 179

[targets]
sketchybar = true
borders = true
kitty = true
neovim = true
yazi = true
starship = true
opencode = true
hydrotodo = true
```

## Color Formats

| Target | Format | Example |
|--------|--------|---------|
| SketchyBar | `0xAARRGGBB` | `0xff3a7bd5` |
| Kitty | `#rrggbb` | `#3a7bd5` |
| Neovim | `#rrggbb` | `#3a7bd5` |
| Borders | `0xAARRGGBB` | `0xff3a7bd5` |
| Yazi | `#rrggbb` | `#3a7bd5` |
| Starship | `#rrggbb` | `#3a7bd5` |
| OpenCode | `#rrggbb` | `#3a7bd5` |
| HydroToDo | `#rrggbb` | `#3a7bd5` |

## Reload Commands

| App | Method |
|-----|--------|
| SketchyBar | `sketchybar --reload` |
| JankyBorders | `borders` IPC (homebrew) via `borders-cycle.sh` |
| Kitty | `kitten @ set-colors --all --configured <path>` |
| Neovim | `nvim --server <socket> --remote-send` to all instances |
| Yazi | Applies on next launch (no hot-reload) |
| Starship | Applies on next prompt render |
| OpenCode | Applies on next launch |
| HydroToDo | Hot-reload via file watch |

## Config File Paths

| File | Path |
|------|------|
| colors.sh | `~/.config/sketchybar/colors.sh` |
| border_colors | `~/.config/wallpaper-colors/border_colors` |
| wallpaper.conf | `~/.config/kitty/themes/wallpaper.conf` |
| nvim_colors.lua | `~/.config/wallpaper-colors/nvim_colors.lua` |
| wallpaper.lua | `~/.config/nvim/lua/lualine/themes/wallpaper.lua` |
| flavor.toml | `~/.config/yazi/flavors/wallpaper.yazi/flavor.toml` |
| starship.toml | `~/.config/starship.toml` |
| wallpaper.json | `~/.config/opencode/themes/wallpaper.json` |
| hydrotodo.json | `~/.config/wallpaper-colors/hydrotodo_colors.json` |

## Swift Tools

### wallpaper-faded (persistent daemon)
- **Build**: `swiftc -O wallpaper-faded.swift -o wallpaper-faded`
- **Frameworks**: AppKit, QuartzCore
- Keeps overlay window showing current wallpaper; animates away on change

### wallpaper-fade (one-shot)
- **Build**: `swiftc -O wallpaper-fade.swift -o wallpaper-fade`
- **Frameworks**: AppKit, QuartzCore, ScreenCaptureKit
- Sets wallpaper with animated transition

### Transitions
fade, slide-left/right/up/down, wipe-left/right/up/down, grow

## Shell Scripts

| Script | Trigger | Purpose |
|--------|---------|---------|
| `wallpaper_cycle.sh` | launchd timer (30min) | Pick next wallpaper from dark/ or light/ |
| `theme_watcher.sh` | launchd daemon (polls 5s) | Detect dark↔light switch, trigger cycle + colors |
| `borders-cycle.sh` | Called by reloaders.py | Animated gradient startup for JankyBorders |

## Editing Guidelines

- **All config writes MUST use `atomic_write()`** from `wcsync/utils.py` — never write directly.
- **Color scheme dict** is the single source of truth — all `write()` functions in `wcsync/writers/` consume it.
- **Adding a new target app**:
  1. Create `wcsync/writers/newapp.py` with `write(scheme, config)` and `OUTPUT_PATH`
  2. Register in `wcsync/writers/__init__.py` `WRITERS` dict
  3. Add reload function in `wcsync/reloaders.py` if hot-reload is supported
  4. Add toggle to `wcsync/config.py` `_DEFAULT_TARGETS`
- **Named color hues are fixed** (red=0, orange=30, yellow=60, etc.) — only sat/val come from the accent.
- **`vivify()` is for borders only** — bar/item colors stay muted to match wallpaper naturally.
- **Python 3.11+** required for `tomllib` (stdlib TOML parser).
- **Runtime Python**: `/usr/local/bin/python3` (has Pillow + PyObjC). Not `/opt/homebrew/bin/python3`.

## Deployment

```bash
# Deploy sync package
cp configs/wallpaper-colors/wallpaper_colors.py ~/.config/wallpaper-colors/
cp -r configs/wallpaper-colors/wcsync ~/.config/wallpaper-colors/

# Deploy config (first time only)
cp -n configs/wallpaper-colors/config.toml.example ~/.config/wallpaper-colors/config.toml
```
