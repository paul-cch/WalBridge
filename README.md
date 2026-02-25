# Wallpaper Theme Sync

Automatically syncs SketchyBar, JankyBorders, Kitty, Neovim, Yazi, Starship, OpenCode, and HydroToDo colors to match the current macOS wallpaper — with animated transitions between wallpapers (fade, slide, wipe, grow), theme-aware wallpaper cycling, and multi-monitor support.

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
└─────────────────────┘     │ wallpaper_colors│───▶│  nvim_colors.lua │──▶ Neovim
                            │ .py + wcsync/   │    │  flavor.toml     │──▶ Yazi
  WatchPaths trigger ──────▶│                 │    │  starship.toml   │──▶ Starship
                            └────────────────┘    │  wallpaper.json  │──▶ OpenCode
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
6. **Reload**: SketchyBar (`--reload`), JankyBorders (IPC via homebrew `borders`), Kitty (`kitten @ set-colors`), Neovim (`--remote-send` to all instances). Yazi and Starship apply on next launch/prompt.
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

# Optional: install prebuilt borders-animated binary (checksum verified)
bash install.sh --install-prebuilt-borders

# Optional: customize launchd label prefix
WTS_AGENT_PREFIX=com.yourname.wallpaper-sync bash install.sh
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
vivify_sat = 0.45     # Border color saturation floor
vivify_val = 0.65     # Border color brightness floor
opacity = 179         # Border opacity (0–255)

[targets]              # Enable/disable individual apps
sketchybar = true
borders = true
kitty = true
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

### `borders-animated`

Pre-built custom fork of [JankyBorders](https://github.com/FelixKratz/JankyBorders) that adds animated gradient border support. The included binary is a **Mach-O arm64 executable** — Apple Silicon only (no x86_64 support).

**Provenance**: Forked from FelixKratz/JankyBorders with a single addition: `gradient()` support in the `active_color` parameter. The fork patches the border rendering to interpolate between two colors diagonally. The upstream project does not support gradients.

**Gradient syntax**:
```
active_color=gradient(top_left=0xffCOLOR1,bottom_right=0xffCOLOR2)
```

**IPC**: Live color updates use the homebrew `borders` binary for IPC — both share the same mach bootstrap port (`borders`), so the lightweight homebrew binary can send gradient config to the running `borders-animated` process without spawning a heavyweight duplicate.

**Install behavior**:
- `install.sh` skips the checked-in binary by default.
- To install it, run `bash install.sh --install-prebuilt-borders`.
- Installer validates `checksums/borders-animated.sha256` before copying.

**Limitations**:
- arm64 only (Apple Silicon). No universal binary or x86_64 build.
- No automated build pipeline — the binary is checked into the repo as a pre-built artifact.
- Upstream JankyBorders changes must be manually cherry-picked into the fork.

### Target apps

| App | Config generated | Reload method |
|---|---|---|
| **SketchyBar** | `~/.config/sketchybar/colors.sh` | `sketchybar --reload` |
| **JankyBorders** | `~/.config/wallpaper-colors/border_colors` | IPC via homebrew `borders` binary |
| **Kitty** | `~/.config/kitty/themes/wallpaper.conf` | `kitten @ set-colors` via unix socket |
| **Neovim** | `~/.config/wallpaper-colors/nvim_colors.lua` + lualine theme | `nvim --remote-send` to all instances |
| **Yazi** | `~/.config/yazi/flavors/wallpaper.yazi/flavor.toml` | Applied on next yazi launch |
| **Starship** | `~/.config/starship.toml` | Applied on next prompt render |
| **OpenCode** | `~/.config/opencode/themes/wallpaper.json` | Applied on next launch |
| **HydroToDo** | `~/.config/wallpaper-colors/hydrotodo_colors.json` | Hot-reload via file watch |

### SketchyBar optional widgets

The example `configs/sketchybar/sketchybarrc` keeps private/personal integrations disabled by default. Enable them only if you use those tools:

```bash
SKETCHYBAR_ENABLE_LIVE_ACTIVITY=1 \
SKETCHYBAR_ENABLE_AIRPODS=1 \
SKETCHYBAR_ENABLE_IRIS=1 \
SKETCHYBAR_ENABLE_TWINGATE=1 \
SKETCHYBAR_ENABLE_SUPERCHARGE=1 \
~/.config/sketchybar/sketchybarrc
```

### Neovim details

Generates a Lua module with highlight groups for syntax, UI, diagnostics, and git. Syntax colors are vivified (brightness boosted) so they stay readable on dark/transparent backgrounds. Reloaded three ways:
- **Immediate**: `nvim --server` pushes to all running instances
- **On focus**: `FocusGained` autocmd re-sources the file
- **On theme change**: `ColorScheme` autocmd reapplies overrides

Requires `~/.config/nvim/lua/config/wallpaper-sync.lua`.

### Yazi details

Generates a complete yazi flavor at `~/.config/yazi/flavors/wallpaper.yazi/flavor.toml` with all UI elements themed: manager, tabs, mode indicators, status bar, file type colors, borders, picker, input, and notifications. Yazi does not hot-reload flavors — the new theme applies on next launch.

Set in `~/.config/yazi/theme.toml`:
```toml
[flavor]
dark  = "wallpaper"
light = "wallpaper"
```

### `wallpaper_cycle.sh`

Theme-aware wallpaper cycler. Detects macOS dark/light mode and picks the next wallpaper from the corresponding folder. Shuffles through all wallpapers in a folder before repeating (shuffle order and position tracked in state files).

```bash
# Manual cycle
bash ~/.config/wallpaper-colors/wallpaper_cycle.sh
```

### Launchd agents

| Agent | Purpose |
|---|---|
| `com.wallpaper-theme-sync.wallpaper-cycle` | Runs `wallpaper_cycle.sh` every 30 min + at login |
| `com.wallpaper-theme-sync.wallpaper-colors` | Triggers `wallpaper_colors.py` via WatchPaths + 2-min poll |
| `com.wallpaper-theme-sync.wallpaper-faded` | Persistent transition daemon (`KeepAlive`) |
| `com.wallpaper-theme-sync.borders-animated` | Runs `borders-animated` with `KeepAlive` |
| `com.wallpaper-theme-sync.theme-watcher` | Polls dark/light mode changes and triggers cycle + sync |

`WTS_AGENT_PREFIX` can override `com.wallpaper-theme-sync` during install/uninstall.

## File locations

### Project

```
wallpaper-theme-sync/
├── README.md
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
│   ├── wallpaper_cycle.sh       # Theme-aware wallpaper cycler
│   └── borders-cycle.sh         # Borders startup with fixed gradient
├── launchd/
│   ├── wallpaper-cycle.plist
│   ├── wallpaper-colors.plist
│   ├── wallpaper-faded.plist
│   ├── borders-animated.plist
│   └── theme-watcher.plist
└── borders-animated             # Custom JankyBorders fork binary (arm64)
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
├── wallpaper_cycle.sh           # Deployed cycle script
├── borders-cycle.sh             # Borders startup
├── nvim_colors.lua              # Auto-generated Neovim highlights
├── border_colors                # Accent + secondary hex values
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
└── borders-animated             # Custom JankyBorders fork (arm64)

~/Library/LaunchAgents/
├── com.wallpaper-theme-sync.wallpaper-cycle.plist
├── com.wallpaper-theme-sync.wallpaper-colors.plist
├── com.wallpaper-theme-sync.wallpaper-faded.plist
├── com.wallpaper-theme-sync.borders-animated.plist
└── com.wallpaper-theme-sync.theme-watcher.plist
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
- **JankyBorders** (`brew install borders`) — homebrew binary used for IPC to running `borders-animated`
- **borders-animated** (custom JankyBorders fork with gradient support, optional install via `--install-prebuilt-borders`, arm64 only)
- **Kitty** with `allow_remote_control yes` and `listen_on unix:/tmp/kitty-sock-*`
- **Neovim** with `wallpaper-sync.lua` config
- **Yazi** — flavor applied on launch, no extra config needed
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

**Transitions** (`wallpaper-faded`):
- Persistent daemon with `DispatchSource` file watcher on the same wallpaper store
- Reacts within ~100ms of wallpaper change
- `KeepAlive` launchd agent ensures it's always running
