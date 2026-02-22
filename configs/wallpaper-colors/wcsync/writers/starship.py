"""Starship prompt config writer."""

import os

from ..utils import atomic_write, hex6

OUTPUT_PATH = os.path.expanduser("~/.config/starship.toml")


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
    atomic_write(OUTPUT_PATH, content)
