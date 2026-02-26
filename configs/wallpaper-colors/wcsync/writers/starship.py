"""Starship prompt config writer."""

import os

from ..utils import atomic_write, hex6, log, safe_home_path

DEFAULT_OUTPUT_PATH = "~/.config/starship.toml"
DEFAULT_FALLBACK_PATH = "~/.config/wallpaper-colors/starship.toml"


def _output_path():
    return safe_home_path(
        os.environ.get("WALLPAPER_STARSHIP_OUTPUT_PATH"),
        DEFAULT_OUTPUT_PATH,
        "WALLPAPER_STARSHIP_OUTPUT_PATH",
    )


def _fallback_path():
    return safe_home_path(
        os.environ.get("WALLPAPER_STARSHIP_FALLBACK_PATH"),
        DEFAULT_FALLBACK_PATH,
        "WALLPAPER_STARSHIP_FALLBACK_PATH",
    )


def write(scheme, config=None):
    accent = hex6(*scheme["accent"])

    content = f"""# Auto-generated from wallpaper — do not edit manually
# Regenerate: python3 ~/.config/wallpaper-colors/wallpaper_colors.py

add_newline = true
command_timeout = 200
format = "[$directory$git_branch$git_status]($style)$character"

[character]
error_symbol = "[✗](bold {accent})"
success_symbol = "[❯](bold {accent})"

[directory]
truncation_length = 3
truncation_symbol = "…/"
style = "bold {accent}"

[git_branch]
format = "[$branch]($style) "
style = "italic {accent}"

[git_status]
format = '[$all_status]($style)'
style = "{accent}"
ahead = "⇡${{count}} "
diverged = "⇕⇡${{ahead_count}}⇣${{behind_count}} "
behind = "⇣${{count}} "
conflicted = " "
up_to_date = " "
untracked = "? "
modified = " "
stashed = ""
staged = ""
renamed = ""
deleted = ""
"""
    # Don't overwrite user's custom starship config
    target = _output_path()
    if os.path.isfile(target):
        try:
            with open(target, "r", encoding="utf-8") as f:
                if "Auto-generated from wallpaper" not in f.readline():
                    alt = _fallback_path()
                    atomic_write(alt, content)
                    log(f"Starship: user config detected, wrote to {alt}")
                    return
        except OSError:
            pass
    atomic_write(target, content)
