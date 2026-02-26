# WalBridge

Automatically syncs SketchyBar, JankyBorders, Kitty, WezTerm, Alacritty, Ghostty, iTerm2, tmux, btop, Neovim, Yazi, Starship, OpenCode, and HydroToDo colors to match the current macOS wallpaper — with animated transitions between wallpapers (fade, slide, wipe, grow), theme-aware wallpaper cycling, and multi-monitor support.

Formerly: `wallpaper-theme-sync`.

Inspired by Linux theming tools like `pywal`, `wallust`, `wpgtk`, and `Stylix` (NixOS), this project brings similar desktop ricing automation to macOS.

See [CHANGELOG.md](CHANGELOG.md) for release notes.
See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md) for project policies.

## How it works

```
┌─────────────────────┐
│  wallpaper_cycle.sh  │  Timer (every 30 min)
│  dark/ or light/     │  Picks folder based on system appearance
└────────┬────────────┘
         │ desktoppr
         ▼
┌─────────────────────┐                           ┌──────────────────┐
│  wallpaper-faded     │                           │  colors.sh       │──▶ SketchyBar
│  (Swift daemon)      │                           │  border_colors   │──▶ JankyBorders
│  animated transitions│     ┌────────────────┐    │  wallpaper.conf  │──▶ Kitty
└─────────────────────┘     │ wallpaper_colors│───▶│  wallpaper.toml  │──▶ WezTerm
                            │ .py + wcsync/   │    │  wallpaper.toml  │──▶ Alacritty
  WatchPaths trigger ──────▶│                 │    │  wallpaper.conf  │──▶ Ghostty
                            │                 │    │  wallpaper.itermcolors │──▶ iTerm2
                            │                 │    │  wallpaper.conf  │──▶ tmux
                            │                 │    │  wallpaper.theme │──▶ btop
                            └────────────────┘    │  nvim_colors.lua │──▶ Neovim
                                                  │  flavor.toml     │──▶ Yazi
                                                  │  starship.toml   │──▶ Starship
                                                  │  wallpaper.json  │──▶ OpenCode
                                                  │  hydrotodo.json  │──▶ HydroToDo
                                                  └──────────────────┘
```

### Wallpaper cycling

`wallpaper_cycle.sh` detects the macOS system appearance (dark/light mode) and picks the next wallpaper from the matching folder:

```
~/Pictures/wallpaper/
├── dark/     # 34 wallpapers for dark mode
└── light/    # 39 wallpapers for light mode
```

- Override the root with `WALLPAPER_DIR=/path/to/wallpapers` if your folders are elsewhere.
- Shuffles through all wallpapers before repeating (tracked in index files)
- Runs on a 30-minute launchd timer + at login
- When the system appearance changes, the next cycle automatically picks from the correct folder

### Color pipeline

1. **Capture**: Loads the wallpaper image from its file path (via `desktoppr`, with multi-monitor support). Falls back to `CGWindowListCreateImage` for dynamic/system wallpapers, with retry logic, multiple window name patterns, and validation against degenerate captures.
2. **Extract**: Resizes to 200x200, runs Pillow median-cut quantization to get N dominant colors (default 8, configurable).
3. **Scheme**: Picks accent (most vibrant — or manual override via config), dark/light backgrounds, a gradient secondary (most hue-distant palette color), and generates named colors at fixed hues matching the accent's saturation/brightness.
4. **Vivify**: Border colors use the same hues but with configurable saturation/value floors so they pop on screen.
5. **Write**: Regenerates all config files for every enabled target app.
6. **Reload**: SketchyBar (`--reload`), JankyBorders (IPC via homebrew `borders`), Kitty (`kitten @ set-colors`), Neovim (`--remote-send` to all instances), and tmux (`source-file` when a server is running). WezTerm, Alacritty, Ghostty, iTerm2, btop, Yazi, Starship, OpenCode, and HydroToDo apply on next app reload/launch/prompt.
7. **Dedup**: Caches a perceptual hash (sha256 of 16x16 thumbnail) so unchanged wallpapers are skipped in ~370ms.

### Wallpaper transitions

The `wallpaper-faded` daemon keeps a persistent overlay window on top of the desktop showing the current wallpaper. When the real wallpaper changes behind it, the overlay animates away — zero flash. A random transition is picked each time:

| Transition | Effect |
|---|---|
| `fade` | Crossfade to new wallpaper |
| `slide-left/right/up/down` | Slide the old wallpaper off screen |
| `wipe-left/right/up/down` | Reveal new wallpaper with a directional wipe |
| `grow` | Old wallpaper scales up and fades out |

## Install

```bash
# Standard install/update
bash install.sh

# Optional: one-time setup for tmux/btop/iTerm2 integration
bash install.sh --setup-targets

# Optional: customize launchd label prefix
WALBRIDGE_AGENT_PREFIX=com.yourname.wallpaper-sync bash install.sh
```

## Configuration

All tuning parameters are configurable via `~/.config/wallpaper-colors/config.toml`. The file is optional — defaults are used when absent. See `configs/wallpaper-colors/config.toml.example` for the full reference.

Key options:

```toml
[general]
display = 1           # Which display to extract from (1 = primary)
n_colors = 8          # Palette size for median-cut quantization (1-256)

[scheme]
min_saturation = 0.45 # Accent color minimum saturation floor
min_value = 0.55      # Accent color minimum brightness floor
harmonize_factor = 0.25  # Named color hue shift toward accent (0–1)
# accent_override = "#3a7bd5"  # Skip auto-detection, use this color

[borders]
vivify_sat = 0.65     # Border color saturation floor (higher = more pop)
vivify_val = 0.85     # Border color brightness floor (higher = more pop)
opacity = 179         # Active border opacity (0–255)
inactive_opacity = 102 # Inactive border opacity (0–255)

[targets]              # Enable/disable individual apps
sketchybar = true
borders = true
kitty = true
wezterm = true
alacritty = true
ghostty = true
iterm2 = true
tmux = true
btop = true
neovim = true
yazi = true
starship = true
opencode = true
hydrotodo = true
```

### Multi-monitor

Set `display` in config.toml to target a specific display (1 = primary, 2 = secondary, etc.). The color scheme is extracted from that display's wallpaper. All target apps are global — there's no per-display theming since SketchyBar, Kitty, etc. don't support it.

## Components

### `wallpaper_colors.py` + `wcsync/`

The core sync pipeline, organized as a Python package:

```
configs/wallpaper-colors/
├── wallpaper_colors.py          # Entry point (CLI + main orchestration)
├── config.toml.example          # Config reference
├── wcsync/
│   ├── __init__.py
│   ├── utils.py                 # atomic_write, log, color format helpers
│   ├── capture.py               # Wallpaper capture (file + CGWindow + multi-monitor)
│   ├── colors.py                # Color extraction + scheme generation
│   ├── config.py                # Config dataclass + TOML loading
│   ├── writers/
│   │   ├── __init__.py          # write_all dispatch + registry
│   │   ├── sketchybar.py
│   │   ├── borders.py
│   │   ├── kitty.py
│   │   ├── wezterm.py
│   │   ├── alacritty.py
│   │   ├── ghostty.py
│   │   ├── iterm2.py
│   │   ├── tmux.py
│   │   ├── btop.py
│   │   ├── neovim.py           # Also writes lualine theme
│   │   ├── lualine.py          # Re-exports from neovim
│   │   ├── yazi.py
│   │   ├── starship.py
│   │   ├── opencode.py
│   │   └── hydrotodo.py
│   └── reloaders.py             # All reload functions
```

**Adding a new target app**:
1. Create `wcsync/writers/newapp.py` with `write(scheme, config)` and `OUTPUT_PATH`
2. Register in `wcsync/writers/__init__.py`
3. Add reload function in `wcsync/reloaders.py` if hot-reload is supported
4. Add toggle to `config.py` `_DEFAULT_TARGETS`

**Color scheme generation**:
- **Accent** = most vibrant palette color (highest `saturation * weighted_luminance`), or manual override via `accent_override` in config
- **Secondary** = most hue-distant palette color (so gradient uses real wallpaper colors, not arbitrary rotations)
- **Border colors** = `vivify(accent)` and `vivify(secondary)` — same hues with configurable sat/val floors
- **Bar colors** = muted versions matching the wallpaper naturally
- **Named colors** (red, green, cyan, etc.) = fixed hues harmonized toward the accent

**Generated exports** in `colors.sh`:
```bash
BLACK, WHITE, BLUE, CYAN, PURPLE, GREEN, RED, YELLOW, ORANGE, PINK, GREY
TRANSPARENT, BAR_COLOR, ITEM_BG_COLOR, ACCENT_COLOR, ACTIVE_COLOR
BLUE_VIVID  # boosted version for readable text on dark backgrounds
```

### `wallpaper-faded` (transition daemon)

A persistent Swift daemon that provides animated wallpaper transitions. Compiled from `tools/wallpaper-faded.swift` and packaged as `WallpaperFaded.app` (LSUIElement, no Dock icon).

**How it works**:
1. On startup, loads the current wallpaper and creates a full-screen overlay window at desktop level
2. The overlay always shows the current wallpaper — it sits between the real desktop and everything else
3. A `DispatchSource` watches `~/Library/Application Support/com.apple.wallpaper/Store` for changes
4. When a change is detected, the overlay is already covering the screen (no flash)
5. A random animation plays (fade, slide, wipe, or grow) to reveal the new wallpaper behind the overlay
6. After animation completes, the overlay refreshes with the new wallpaper image

**Build**:
```bash
swiftc -O tools/wallpaper-faded.swift -o tools/wallpaper-faded
cp tools/wallpaper-faded ~/.local/bin/WallpaperFaded.app/Contents/MacOS/wallpaper-faded
```

### `wallpaper-fade` (standalone CLI)

A standalone CLI tool for one-shot wallpaper transitions. Useful for manual use or scripting.

```bash
# Set wallpaper with animation
wallpaper-fade ~/Pictures/wallpaper/photo.jpg

# Overlay-only mode (animate existing wallpaper away)
wallpaper-fade --from ~/Pictures/wallpaper/old.jpg
```

### JankyBorders

[JankyBorders](https://github.com/FelixKratz/JankyBorders) (`brew install borders`) draws vivid active borders plus muted inactive borders derived from the wallpaper palette, updated live via IPC whenever the wallpaper changes.

### Target apps

| App | Config generated | Reload method |
|---|---|---|
| **SketchyBar** | `~/.config/sketchybar/colors.sh` | `sketchybar --reload` |
| **JankyBorders** | `~/.config/wallpaper-colors/border_colors` | IPC via homebrew `borders` binary |
| **Kitty** | `~/.config/kitty/themes/wallpaper.conf` | `kitten @ set-colors` via unix socket |
| **WezTerm** | `~/.config/wezterm/colors/wallpaper.toml` | Applied on next WezTerm config reload |
| **Alacritty** | `~/.config/alacritty/themes/wallpaper.toml` | Applied on next Alacritty config reload |
| **Ghostty** | `~/.config/ghostty/themes/wallpaper.conf` | Applied on next Ghostty config reload/restart |
| **iTerm2** | `~/.config/iterm2/colors/wallpaper.itermcolors` | One-time preset import (`Settings > Profiles > Colors > Color Presets`) |
| **tmux** | `~/.config/tmux/themes/wallpaper.conf` | Hot-reloaded automatically if tmux server is running |
| **btop** | `~/.config/btop/themes/wallpaper.theme` | Applied when `color_theme = "wallpaper"` is set in `btop.conf` |
| **Neovim** | `~/.config/wallpaper-colors/nvim_colors.lua` + lualine theme | `nvim --remote-send` to all instances |
| **Yazi** | `~/.config/yazi/flavors/wallpaper.yazi/flavor.toml` | Applied on next yazi launch |
| **Starship** | `~/.config/starship.toml` | Applied on next prompt render |
| **OpenCode** | `~/.config/opencode/themes/wallpaper.json` | Applied on next launch |
| **HydroToDo** | `~/.config/wallpaper-colors/hydrotodo_colors.json` | Hot-reload via file watch |

### One-time target wiring

To wire tmux and btop automatically and set up iTerm2 import guidance:

```bash
# If already installed
bash ~/.config/wallpaper-colors/setup-targets.sh

# Or run during install
bash install.sh --setup-targets
```

This helper:
- Adds `source-file ~/.config/tmux/themes/wallpaper.conf` to `~/.tmux.conf` (if missing)
- Sets `color_theme = "wallpaper"` in `~/.config/btop/btop.conf`
- Prints iTerm2 preset import path (`~/.config/iterm2/colors/wallpaper.itermcolors`)

### Terminal/Borders/Yazi/iTerm2/tmux/btop theming overrides

Defaults are still plug-and-play, but you can customize paths/names when integrating into a different dotfiles layout:

```bash
# WezTerm writer
export WALLPAPER_WEZTERM_SCHEME_NAME="wallpaper"
# Optional explicit path (overrides scheme name path):
# export WALLPAPER_WEZTERM_OUTPUT_PATH="$HOME/.config/wezterm/colors/wallpaper.toml"

# Alacritty writer
export WALLPAPER_ALACRITTY_OUTPUT_PATH="$HOME/.config/alacritty/themes/wallpaper.toml"

# Ghostty writer
export WALLPAPER_GHOSTTY_THEME_FILE="wallpaper.conf"
# Optional explicit path (overrides theme file path):
# export WALLPAPER_GHOSTTY_OUTPUT_PATH="$HOME/.config/ghostty/themes/wallpaper.conf"

# iTerm2 writer
export WALLPAPER_ITERM_PRESET_NAME="wallpaper"
# Optional explicit path (overrides preset name path):
# export WALLPAPER_ITERM_OUTPUT_PATH="$HOME/.config/iterm2/colors/wallpaper.itermcolors"

# tmux writer
export WALLPAPER_TMUX_OUTPUT_PATH="$HOME/.config/tmux/themes/wallpaper.conf"

# btop writer
export WALLPAPER_BTOP_THEME_NAME="wallpaper"
# Optional explicit path (overrides theme name path):
# export WALLPAPER_BTOP_OUTPUT_PATH="$HOME/.config/btop/themes/wallpaper.theme"

# Borders writer + borders-cycle.sh
export WALLPAPER_BORDER_COLORS_FILE="$HOME/.config/wallpaper-colors/border_colors"
# Optional: override path to borders binary (default: 'borders' from PATH)
# export WALLPAPER_BORDERS_BIN="/opt/homebrew/bin/borders"

# Yazi writer
export WALLPAPER_YAZI_FLAVOR_NAME="wallpaper"
# Optional explicit path (overrides flavor name derivation):
# export WALLPAPER_YAZI_OUTPUT_PATH="$HOME/.config/yazi/flavors/wallpaper.yazi/flavor.toml"
# Optional theme selector behavior:
# export WALLPAPER_YAZI_THEME_PATH="$HOME/.config/yazi/theme.toml"
# export WALLPAPER_YAZI_WRITE_THEME_SELECTOR=1
```

### Neovim details

Generates a Lua module with highlight groups for syntax, UI, diagnostics, and git. Syntax colors are vivified (brightness boosted) so they stay readable on dark/transparent backgrounds. Reloaded three ways:
- **Immediate**: `nvim --server` pushes to all running instances
- **On focus**: `FocusGained` autocmd re-sources the file
- **On theme change**: `ColorScheme` autocmd reapplies overrides

Requires `~/.config/nvim/lua/config/wallpaper-sync.lua`.

### Yazi details

Generates a complete yazi flavor at `~/.config/yazi/flavors/wallpaper.yazi/flavor.toml` with all UI elements themed: manager, tabs, mode indicators, status bar, file type colors, borders, picker, input, and notifications.

By default, the writer also manages `~/.config/yazi/theme.toml` with:
```toml
[flavor]
dark = "wallpaper"
light = "wallpaper"
```

If `theme.toml` already exists and is not auto-generated by wallpaper sync, it is left untouched and a helper selector is written to `~/.config/wallpaper-colors/yazi.theme.toml`.

### `wallpaper_cycle.sh`

Theme-aware wallpaper cycler. Detects macOS dark/light mode and picks the next wallpaper from the corresponding folder. Shuffles through all wallpapers in a folder before repeating (shuffle order and position tracked in state files).

```bash
# Manual cycle
bash ~/.config/wallpaper-colors/wallpaper_cycle.sh
```

### Launchd agents

| Agent | Purpose |
|---|---|
| `com.walbridge.wallpaper-cycle` | Runs `wallpaper_cycle.sh` every 30 min + at login |
| `com.walbridge.wallpaper-colors` | Triggers `wallpaper_colors.py` via WatchPaths + 2-min poll |
| `com.walbridge.wallpaper-faded` | Persistent transition daemon (restart on crash, 10s throttle) |
| `com.walbridge.borders` | Runs `borders` (JankyBorders), restart on crash, 10s throttle |
| `com.walbridge.theme-watcher` | Polls dark/light mode changes and triggers cycle + sync (restart on crash) |

`WALBRIDGE_AGENT_PREFIX` can override `com.walbridge` during install/uninstall (`WTS_AGENT_PREFIX` is still accepted as a legacy alias).
All agents are limited to the `Aqua` session type.

## File locations

### Project

```
walbridge/
├── README.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── tools/
│   ├── wallpaper-faded.swift    # Persistent transition daemon source
│   ├── wallpaper-faded          # Compiled binary
│   ├── wallpaper-fade.swift     # Standalone CLI tool source
│   └── wallpaper-fade           # Compiled binary
├── configs/wallpaper-colors/
│   ├── wallpaper_colors.py      # Entry point
│   ├── config.toml.example      # Config reference
│   ├── wcsync/                  # Python package
│   │   ├── utils.py             # Shared utilities
│   │   ├── capture.py           # Wallpaper capture + multi-monitor
│   │   ├── colors.py            # Color extraction + scheme
│   │   ├── config.py            # Config loading
│   │   ├── writers/             # Per-app config writers
│   │   └── reloaders.py         # Service reload functions
│   ├── setup-targets.sh         # One-time target integration helper
│   ├── wallpaper_cycle.sh       # Theme-aware wallpaper cycler
│   └── borders-cycle.sh         # Borders startup (solid accent color)
├── launchd/
│   ├── wallpaper-cycle.plist
│   ├── wallpaper-colors.plist
│   ├── wallpaper-faded.plist
│   ├── borders.plist
│   └── theme-watcher.plist
```

### Deployed

```
~/.config/wallpaper-colors/
├── wallpaper_colors.py          # Deployed entry point
├── wcsync/                      # Deployed package
│   ├── utils.py
│   ├── capture.py
│   ├── colors.py
│   ├── config.py
│   ├── writers/
│   └── reloaders.py
├── config.toml                  # User config (optional)
├── setup-targets.sh             # One-time target integration helper
├── wallpaper_cycle.sh           # Deployed cycle script
├── borders-cycle.sh             # Borders startup
├── nvim_colors.lua              # Auto-generated Neovim highlights
├── border_colors                # active_color + inactive_color
├── hydrotodo_colors.json        # Auto-generated HydroToDo theme
├── .last_hash                   # Perceptual hash cache
├── .last_wp_path                # Last wallpaper file path
├── .cycle_dark_index            # Current position in dark shuffle
├── .cycle_dark_order            # Shuffled order for dark wallpapers
├── .cycle_light_index           # Current position in light shuffle
├── .cycle_light_order           # Shuffled order for light wallpapers
├── faded.log                    # Transition daemon log
├── cycle.log                    # Cycle script log
├── sync.log                     # Sync script stdout
└── sync.err.log                 # Sync script stderr

~/.config/yazi/
├── theme.toml                   # Points to wallpaper flavor
└── flavors/wallpaper.yazi/
    └── flavor.toml              # Auto-generated yazi theme

~/.config/sketchybar/colors.sh   # Auto-generated color scheme
~/.config/borders/bordersrc      # Auto-generated border config
~/.config/kitty/themes/wallpaper.conf  # Auto-generated terminal colors
~/.config/wezterm/colors/wallpaper.toml  # Auto-generated WezTerm scheme
~/.config/alacritty/themes/wallpaper.toml  # Auto-generated Alacritty theme
~/.config/ghostty/themes/wallpaper.conf  # Auto-generated Ghostty theme
~/.config/iterm2/colors/wallpaper.itermcolors  # Auto-generated iTerm2 preset
~/.config/tmux/themes/wallpaper.conf  # Auto-generated tmux include
~/.config/btop/themes/wallpaper.theme  # Auto-generated btop theme
~/.config/nvim/lua/config/wallpaper-sync.lua  # Loads nvim_colors.lua
~/.config/starship.toml          # Auto-generated prompt config
~/.config/opencode/themes/wallpaper.json  # Auto-generated TUI theme

~/.local/bin/
├── WallpaperFaded.app/          # Transition daemon app bundle
│   └── Contents/
│       ├── Info.plist           # LSUIElement=true (no Dock icon)
│       └── MacOS/wallpaper-faded
├── WallpaperFade.app/           # Standalone CLI app bundle
│   └── Contents/
│       ├── Info.plist
│       └── MacOS/wallpaper-fade

~/Library/LaunchAgents/
├── com.walbridge.wallpaper-cycle.plist
├── com.walbridge.wallpaper-colors.plist
├── com.walbridge.wallpaper-faded.plist
├── com.walbridge.borders.plist
└── com.walbridge.theme-watcher.plist
```

## Usage

```bash
# Cycle to next wallpaper (auto-detects dark/light mode)
bash ~/.config/wallpaper-colors/wallpaper_cycle.sh

# Manual sync (verbose, force re-extract)
python3 ~/.config/wallpaper-colors/wallpaper_colors.py -v -f

# Manual wallpaper change (triggers both sync + transition)
desktoppr ~/Pictures/wallpaper/photo.jpg

# Standalone transition (no daemon needed)
~/.local/bin/wallpaper-fade ~/Pictures/wallpaper/photo.jpg

# Tail logs
tail -f ~/.config/wallpaper-colors/cycle.log    # wallpaper cycling
tail -f ~/.config/wallpaper-colors/sync.log     # color sync
tail -f ~/.config/wallpaper-colors/faded.log    # transitions
```

## Build

```bash
# Transition daemon
swiftc -O tools/wallpaper-faded.swift -o tools/wallpaper-faded
cp tools/wallpaper-faded ~/.local/bin/WallpaperFaded.app/Contents/MacOS/wallpaper-faded

# Standalone CLI
swiftc -O tools/wallpaper-fade.swift -o tools/wallpaper-fade
cp tools/wallpaper-fade ~/.local/bin/WallpaperFade.app/Contents/MacOS/wallpaper-fade

# Deploy sync package
cp configs/wallpaper-colors/wallpaper_colors.py ~/.config/wallpaper-colors/
cp -r configs/wallpaper-colors/wcsync ~/.config/wallpaper-colors/

# Deploy config (first time only — won't overwrite existing)
cp -n configs/wallpaper-colors/config.toml.example ~/.config/wallpaper-colors/config.toml

# Deploy launchd agents
cp launchd/*.plist ~/Library/LaunchAgents/
```

For production use, prefer `bash install.sh` (it substitutes `__HOME__`, `__PYTHON__`, and `__AGENT_PREFIX__` placeholders automatically).

## Dependencies

- **Python 3.11+** with Pillow (`pip install Pillow`) — 3.11+ required for `tomllib`
- **PyObjC** (ships with macOS Python or `pip install pyobjc-framework-Quartz`)
- **desktoppr** (`brew install desktoppr`) — wallpaper path detection + multi-space propagation
- **SketchyBar** (`brew install FelixKratz/formulae/sketchybar`)
- **JankyBorders** (`brew install borders`) — wallpaper-synced border around the focused window
- **Kitty** with `allow_remote_control yes` and `listen_on unix:/tmp/kitty-sock-*`
- **WezTerm** (optional) — set `color_scheme = "wallpaper"` in your WezTerm config
- **Alacritty** (optional) — import generated `wallpaper.toml` in `alacritty.toml`
- **Ghostty** (optional) — set `theme = wallpaper.conf` in Ghostty config
- **iTerm2** (optional) — import generated `wallpaper.itermcolors` preset once
- **tmux** (optional) — run `bash ~/.config/wallpaper-colors/setup-targets.sh` once
- **btop** (optional) — run `bash ~/.config/wallpaper-colors/setup-targets.sh` once
- **Neovim** with `wallpaper-sync.lua` config
- **Yazi** — flavor applied on launch; theme selector is auto-managed unless custom `theme.toml` is detected
- **Xcode Command Line Tools** (for `swiftc`)

## Performance

| Metric | Value |
|---|---|
| Full color sync | ~1s |
| No-change skip (hash match) | ~370ms |
| Transition animation | 700ms |
| Transition detection latency | ~100ms |
| CPU at idle (daemon + 2-min poll) | negligible |

All image processing is done in memory — no temp files written to disk. The transition daemon is persistent (no per-change startup cost).

## Trigger mechanism

**Wallpaper cycling** (`wallpaper_cycle.sh`):
- **StartInterval**: every 1800 seconds (30 min)
- **RunAtLoad**: cycles once at login
- Detects `defaults read -g AppleInterfaceStyle` → picks `dark/` or `light/` folder

**Color sync** (`wallpaper_colors.py`):
- **WatchPaths**: fires when `~/Library/Application Support/com.apple.wallpaper/Store` changes
- **StartInterval**: polls every 120 seconds as a safety net for third-party wallpaper apps
- **ThrottleInterval**: 2 seconds minimum between runs
- **Session scope**: `Aqua` only

**Transitions** (`wallpaper-faded`):
- Persistent daemon with `DispatchSource` file watcher on the same wallpaper store
- Reacts within ~100ms of wallpaper change
- Launchd restarts on crash (`KeepAlive.SuccessfulExit=false`) with **ThrottleInterval=10**
