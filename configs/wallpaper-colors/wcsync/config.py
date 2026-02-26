"""User configuration — loads from ~/.config/wallpaper-colors/config.toml."""

import os
import re
import tomllib
from dataclasses import dataclass, field

from .utils import log

CONFIG_PATH = os.path.expanduser("~/.config/wallpaper-colors/config.toml")

_DEFAULT_TARGETS = {
    "sketchybar": True,
    "borders": True,
    "kitty": True,
    "wezterm": True,
    "alacritty": True,
    "ghostty": True,
    "iterm2": True,
    "tmux": True,
    "btop": True,
    "neovim": True,
    "yazi": True,
    "starship": True,
    "opencode": True,
    "hydrotodo": True,
}


def _as_int(value, default, min_value=None, max_value=None):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    if min_value is not None and parsed < min_value:
        return default
    if max_value is not None and parsed > max_value:
        return default
    return parsed


def _as_float(value, default, min_value=None, max_value=None):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default

    if min_value is not None and parsed < min_value:
        return default
    if max_value is not None and parsed > max_value:
        return default
    return parsed


def _as_hex_color(value):
    if not isinstance(value, str):
        return None

    stripped = value.strip()
    if not re.fullmatch(r"#?[0-9a-fA-F]{6}", stripped):
        return None

    return stripped if stripped.startswith("#") else f"#{stripped}"


@dataclass
class Config:
    """All tunable parameters with sensible defaults."""

    # General
    display: int = 1
    n_colors: int = 8

    # Scheme generation
    min_saturation: float = 0.45
    min_value: float = 0.55
    harmonize_factor: float = 0.25
    accent_override: str | None = None  # e.g. "#3a7bd5"

    # Border vivify
    border_vivify_sat: float = 0.65
    border_vivify_val: float = 0.85
    border_opacity: int = 0xB3
    border_inactive_opacity: int = 0x66

    # Target toggles
    targets: dict = field(default_factory=lambda: dict(_DEFAULT_TARGETS))

    @classmethod
    def load(cls, path=None):
        """Load config from TOML file, falling back to defaults for missing keys."""
        path = path or CONFIG_PATH
        if not os.path.isfile(path):
            return cls()

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            log(f"Config parse error in {path}: {e}; using defaults")
            return cls()
        except OSError as e:
            log(f"Config read error in {path}: {e}; using defaults")
            return cls()

        if not isinstance(data, dict):
            log(f"Config root must be a table in {path}; using defaults")
            return cls()

        general = data.get("general", {})
        scheme = data.get("scheme", {})
        borders = data.get("borders", {})
        targets_raw = data.get("targets", {})

        if not isinstance(general, dict):
            general = {}
        if not isinstance(scheme, dict):
            scheme = {}
        if not isinstance(borders, dict):
            borders = {}
        if not isinstance(targets_raw, dict):
            targets_raw = {}

        targets = dict(_DEFAULT_TARGETS)
        for key in targets:
            if key in targets_raw and isinstance(targets_raw[key], bool):
                targets[key] = targets_raw[key]

        # Parse border opacity — support both 0xB3 and 179 in TOML
        opacity = borders.get("opacity", 0xB3)
        if isinstance(opacity, str):
            try:
                opacity = int(opacity, 0)
            except ValueError:
                opacity = 0xB3
        inactive_opacity = borders.get("inactive_opacity", 0x66)
        if isinstance(inactive_opacity, str):
            try:
                inactive_opacity = int(inactive_opacity, 0)
            except ValueError:
                inactive_opacity = 0x66

        return cls(
            display=_as_int(general.get("display", 1), 1, min_value=1),
            n_colors=_as_int(general.get("n_colors", 8), 8, min_value=1, max_value=256),
            min_saturation=_as_float(
                scheme.get("min_saturation", 0.45), 0.45, min_value=0.0, max_value=1.0
            ),
            min_value=_as_float(scheme.get("min_value", 0.55), 0.55, min_value=0.0, max_value=1.0),
            harmonize_factor=_as_float(
                scheme.get("harmonize_factor", 0.25), 0.25, min_value=0.0, max_value=1.0
            ),
            accent_override=_as_hex_color(scheme.get("accent_override")),
            border_vivify_sat=_as_float(
                borders.get("vivify_sat", 0.65), 0.65, min_value=0.0, max_value=1.0
            ),
            border_vivify_val=_as_float(
                borders.get("vivify_val", 0.85), 0.85, min_value=0.0, max_value=1.0
            ),
            border_opacity=_as_int(opacity, 0xB3, min_value=0, max_value=255),
            border_inactive_opacity=_as_int(inactive_opacity, 0x66, min_value=0, max_value=255),
            targets=targets,
        )
