"""User configuration — loads from ~/.config/wallpaper-colors/config.toml."""

import os
import tomllib
from dataclasses import dataclass, field

CONFIG_PATH = os.path.expanduser("~/.config/wallpaper-colors/config.toml")

_DEFAULT_TARGETS = {
    "sketchybar": True,
    "borders": True,
    "kitty": True,
    "neovim": True,
    "yazi": True,
    "starship": True,
    "opencode": True,
    "hydrotodo": True,
}


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
    border_vivify_sat: float = 0.45
    border_vivify_val: float = 0.65
    border_opacity: int = 0xB3

    # Target toggles
    targets: dict = field(default_factory=lambda: dict(_DEFAULT_TARGETS))

    @classmethod
    def load(cls, path=None):
        """Load config from TOML file, falling back to defaults for missing keys."""
        path = path or CONFIG_PATH
        if not os.path.isfile(path):
            return cls()

        with open(path, "rb") as f:
            data = tomllib.load(f)

        general = data.get("general", {})
        scheme = data.get("scheme", {})
        borders = data.get("borders", {})
        targets_raw = data.get("targets", {})

        targets = dict(_DEFAULT_TARGETS)
        targets.update(targets_raw)

        # Parse border opacity — support both 0xB3 and 179 in TOML
        opacity = borders.get("opacity", 0xB3)
        if isinstance(opacity, str):
            opacity = int(opacity, 0)

        return cls(
            display=general.get("display", 1),
            n_colors=general.get("n_colors", 8),
            min_saturation=scheme.get("min_saturation", 0.45),
            min_value=scheme.get("min_value", 0.55),
            harmonize_factor=scheme.get("harmonize_factor", 0.25),
            accent_override=scheme.get("accent_override"),
            border_vivify_sat=borders.get("vivify_sat", 0.45),
            border_vivify_val=borders.get("vivify_val", 0.65),
            border_opacity=opacity,
            targets=targets,
        )
