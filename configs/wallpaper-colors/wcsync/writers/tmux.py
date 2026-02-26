"""tmux theme include writer."""

import os

from ..utils import atomic_write, hex6, safe_home_path

DEFAULT_OUTPUT_PATH = "~/.config/tmux/themes/wallpaper.conf"


def _output_path():
    return safe_home_path(
        os.environ.get("WALLPAPER_TMUX_OUTPUT_PATH"),
        DEFAULT_OUTPUT_PATH,
        "WALLPAPER_TMUX_OUTPUT_PATH",
    )


def output_path():
    return _output_path()


def write(scheme, config=None):
    dark = hex6(*scheme["dark"])
    light = hex6(*scheme["light"])
    accent = hex6(*scheme["accent"])
    secondary = hex6(*scheme["secondary"])
    red = hex6(*scheme["red"])
    yellow = hex6(*scheme["yellow"])
    orange = hex6(*scheme["orange"])
    grey = hex6(*scheme["grey"])

    content = f"""# Auto-generated from wallpaper — do not edit manually
# Regenerate: python3 ~/.config/wallpaper-colors/wallpaper_colors.py
# Include from ~/.tmux.conf:
#   source-file ~/.config/tmux/themes/wallpaper.conf

set -g status-style "fg={light},bg={dark}"
set -g message-style "fg={dark},bg={accent}"
set -g message-command-style "fg={dark},bg={secondary}"

set -g pane-border-style "fg={grey}"
set -g pane-active-border-style "fg={accent}"

set -g mode-style "fg={dark},bg={yellow}"
set -g clock-mode-colour "{accent}"

set -g window-status-style "fg={grey},bg={dark}"
set -g window-status-current-style "bold,fg={light},bg={secondary}"
set -g window-status-activity-style "fg={orange},bg={dark}"
set -g window-status-bell-style "bold,fg={dark},bg={red}"

set -g status-left-style "fg={dark},bg={accent}"
set -g status-right-style "fg={dark},bg={secondary}"
"""
    atomic_write(_output_path(), content)
