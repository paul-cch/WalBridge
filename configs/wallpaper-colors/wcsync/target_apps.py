"""Target App module and policy.

This module is the single source of truth for apps WalBridge can generate
Color Material for: defaults, adapter module names, hot reload capability, and
environment-derived path/name policy.
"""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass, field
from typing import Callable

from .utils import safe_home_path, sanitize_filename, sanitize_name


@dataclass(frozen=True)
class NamePolicy:
    default: str
    env_var: str
    sanitizer: Callable[[str | None, str, str | None], str] = sanitize_name

    def resolve(self) -> str:
        return self.sanitizer(os.environ.get(self.env_var), self.default, self.env_var)

    @property
    def env_vars(self) -> tuple[str, ...]:
        return (self.env_var,)


@dataclass(frozen=True)
class BoolPolicy:
    default: bool
    env_var: str

    def resolve(self) -> bool:
        raw = os.environ.get(self.env_var)
        if raw is None:
            return self.default
        return raw.strip().lower() not in {"0", "false", "no", "off"}

    @property
    def env_vars(self) -> tuple[str, ...]:
        return (self.env_var,)


@dataclass(frozen=True)
class PathPolicy:
    default_path: str | Callable[[], str]
    env_var: str | None = None

    def resolve(self) -> str:
        default = self.default_path() if callable(self.default_path) else self.default_path
        override = os.environ.get(self.env_var) if self.env_var else None
        return safe_home_path(override, default, self.env_var)

    @property
    def env_vars(self) -> tuple[str, ...]:
        return (self.env_var,) if self.env_var else ()


@dataclass(frozen=True)
class TargetApp:
    name: str
    writer_module: str
    default_enabled: bool = True
    reload_function: str | None = None
    paths: dict[str, PathPolicy] = field(default_factory=dict)
    names: dict[str, NamePolicy] = field(default_factory=dict)
    bools: dict[str, BoolPolicy] = field(default_factory=dict)

    def reload(self, scheme, config=None):
        if not self.reload_function:
            return []
        reloaders = importlib.import_module(f"{__package__}.reloaders")
        result = getattr(reloaders, self.reload_function)(scheme, config)
        if result is None:
            return []
        return result if isinstance(result, list) else [result]

    def path(self, key: str = "output") -> str:
        return self.paths[key].resolve()

    def target_name(self, key: str = "name") -> str:
        return self.names[key].resolve()

    def flag(self, key: str) -> bool:
        return self.bools[key].resolve()

    @property
    def env_vars(self) -> tuple[str, ...]:
        env_vars: list[str] = []
        for policy in self.paths.values():
            env_vars.extend(policy.env_vars)
        for policy in self.names.values():
            env_vars.extend(policy.env_vars)
        for policy in self.bools.values():
            env_vars.extend(policy.env_vars)
        return tuple(env_vars)


def _named_path(app: str, name_key: str, template: str) -> Callable[[], str]:
    return lambda: template.format(name=target_name(app, name_key))


TARGET_APPS: tuple[TargetApp, ...] = (
    TargetApp(
        "sketchybar",
        "sketchybar",
        reload_function="reload_sketchybar",
        paths={
            "output": PathPolicy(
                "~/.config/sketchybar/colors.sh",
                "WALLPAPER_SKETCHYBAR_OUTPUT_PATH",
            )
        },
    ),
    TargetApp(
        "borders",
        "borders",
        reload_function="reload_borders",
        paths={
            "output": PathPolicy(
                "~/.config/wallpaper-colors/border_colors",
                "WALLPAPER_BORDER_COLORS_FILE",
            )
        },
    ),
    TargetApp(
        "kitty",
        "kitty",
        reload_function="reload_kitty",
        paths={
            "output": PathPolicy(
                "~/.config/kitty/themes/wallpaper.conf",
                "WALLPAPER_KITTY_OUTPUT_PATH",
            )
        },
    ),
    TargetApp(
        "wezterm",
        "wezterm",
        names={"scheme": NamePolicy("wallpaper", "WALLPAPER_WEZTERM_SCHEME_NAME")},
        paths={
            "output": PathPolicy(
                _named_path("wezterm", "scheme", "~/.config/wezterm/colors/{name}.toml"),
                "WALLPAPER_WEZTERM_OUTPUT_PATH",
            )
        },
    ),
    TargetApp(
        "alacritty",
        "alacritty",
        paths={
            "output": PathPolicy(
                "~/.config/alacritty/themes/wallpaper.toml",
                "WALLPAPER_ALACRITTY_OUTPUT_PATH",
            )
        },
    ),
    TargetApp(
        "ghostty",
        "ghostty",
        names={
            "theme_file": NamePolicy(
                "wallpaper.conf",
                "WALLPAPER_GHOSTTY_THEME_FILE",
                sanitize_filename,
            )
        },
        paths={
            "output": PathPolicy(
                _named_path("ghostty", "theme_file", "~/.config/ghostty/themes/{name}"),
                "WALLPAPER_GHOSTTY_OUTPUT_PATH",
            )
        },
    ),
    TargetApp(
        "iterm2",
        "iterm2",
        names={"preset": NamePolicy("wallpaper", "WALLPAPER_ITERM_PRESET_NAME")},
        paths={
            "output": PathPolicy(
                _named_path("iterm2", "preset", "~/.config/iterm2/colors/{name}.itermcolors"),
                "WALLPAPER_ITERM_OUTPUT_PATH",
            )
        },
    ),
    TargetApp(
        "tmux",
        "tmux",
        reload_function="reload_tmux",
        paths={
            "output": PathPolicy(
                "~/.config/tmux/themes/wallpaper.conf",
                "WALLPAPER_TMUX_OUTPUT_PATH",
            )
        },
    ),
    TargetApp(
        "btop",
        "btop",
        names={"theme": NamePolicy("wallpaper", "WALLPAPER_BTOP_THEME_NAME")},
        paths={
            "output": PathPolicy(
                _named_path("btop", "theme", "~/.config/btop/themes/{name}.theme"),
                "WALLPAPER_BTOP_OUTPUT_PATH",
            )
        },
    ),
    TargetApp(
        "neovim",
        "neovim",
        reload_function="reload_nvim",
        paths={
            "nvim_colors": PathPolicy(
                "~/.config/wallpaper-colors/nvim_colors.lua",
                "WALLPAPER_NVIM_COLORS_PATH",
            ),
            "lualine": PathPolicy(
                "~/.config/nvim/lua/lualine/themes/wallpaper.lua",
                "WALLPAPER_LUALINE_PATH",
            ),
        },
    ),
    TargetApp(
        "yazi",
        "yazi",
        names={"flavor": NamePolicy("wallpaper", "WALLPAPER_YAZI_FLAVOR_NAME")},
        bools={"write_theme_selector": BoolPolicy(True, "WALLPAPER_YAZI_WRITE_THEME_SELECTOR")},
        paths={
            "output": PathPolicy(
                _named_path("yazi", "flavor", "~/.config/yazi/flavors/{name}.yazi/flavor.toml"),
                "WALLPAPER_YAZI_OUTPUT_PATH",
            ),
            "theme": PathPolicy(
                "~/.config/yazi/theme.toml",
                "WALLPAPER_YAZI_THEME_PATH",
            ),
            "theme_fallback": PathPolicy("~/.config/wallpaper-colors/yazi.theme.toml"),
        },
    ),
    TargetApp(
        "starship",
        "starship",
        paths={
            "output": PathPolicy("~/.config/starship.toml", "WALLPAPER_STARSHIP_OUTPUT_PATH"),
            "fallback": PathPolicy(
                "~/.config/wallpaper-colors/starship.toml",
                "WALLPAPER_STARSHIP_FALLBACK_PATH",
            ),
        },
    ),
    TargetApp(
        "opencode",
        "opencode",
        paths={
            "output": PathPolicy(
                "~/.config/opencode/themes/wallpaper.json",
                "WALLPAPER_OPENCODE_OUTPUT_PATH",
            )
        },
    ),
    TargetApp(
        "hydrotodo",
        "hydrotodo",
        paths={
            "output": PathPolicy(
                "~/.config/wallpaper-colors/hydrotodo_colors.json",
                "WALLPAPER_HYDROTODO_OUTPUT_PATH",
            )
        },
    ),
    TargetApp(
        "vscode",
        "vscode",
        default_enabled=False,
        paths={
            "settings": PathPolicy(
                "~/Library/Application Support/Code/User/settings.json",
                "WALLPAPER_VSCODE_SETTINGS_PATH",
            )
        },
    ),
)

_TARGET_APP_BY_NAME = {app.name: app for app in TARGET_APPS}


def all_target_apps() -> tuple[TargetApp, ...]:
    return TARGET_APPS


def target_app(name: str) -> TargetApp:
    return _TARGET_APP_BY_NAME[name]


def target_defaults() -> dict[str, bool]:
    return {app.name: app.default_enabled for app in TARGET_APPS}


def enabled_target_apps(config) -> list[TargetApp]:
    targets = getattr(config, "targets", {}) or {}
    return [app for app in TARGET_APPS if targets.get(app.name, app.default_enabled)]


def target_path(app_name: str, key: str = "output") -> str:
    return target_app(app_name).path(key)


def target_name(app_name: str, key: str = "name") -> str:
    return target_app(app_name).target_name(key)


def target_flag(app_name: str, key: str) -> bool:
    return target_app(app_name).flag(key)


def target_env_vars() -> tuple[str, ...]:
    env_vars: list[str] = []
    for app in TARGET_APPS:
        env_vars.extend(app.env_vars)
    return tuple(dict.fromkeys(env_vars))


def target_env_material(environ=None) -> dict[str, str]:
    environ = os.environ if environ is None else environ
    return {key: environ[key] for key in target_env_vars() if key in environ}
