"""iTerm2 color preset writer."""

import os

from ..utils import atomic_write

DEFAULT_PRESET_NAME = "wallpaper"


def _preset_name():
    return os.environ.get("WALLPAPER_ITERM_PRESET_NAME", DEFAULT_PRESET_NAME)


def _output_path():
    default_path = f"~/.config/iterm2/colors/{_preset_name()}.itermcolors"
    return os.path.expanduser(os.environ.get("WALLPAPER_ITERM_OUTPUT_PATH", default_path))


def _plist_color(name, rgb, alpha=1.0):
    r, g, b = rgb
    return f"""  <key>{name}</key>
  <dict>
    <key>Alpha Component</key>
    <real>{alpha:.6f}</real>
    <key>Blue Component</key>
    <real>{b / 255.0:.6f}</real>
    <key>Color Space</key>
    <string>sRGB</string>
    <key>Green Component</key>
    <real>{g / 255.0:.6f}</real>
    <key>Red Component</key>
    <real>{r / 255.0:.6f}</real>
  </dict>"""


def write(scheme, config=None):
    dark = scheme["dark"]
    light = scheme["light"]
    accent = scheme["accent"]
    secondary = scheme["secondary"]
    red = scheme["red"]
    green = scheme["green"]
    yellow = scheme["yellow"]
    blue = accent
    purple = scheme["purple"]
    cyan = scheme["cyan"]
    grey = scheme["grey"]
    orange = scheme["orange"]
    pink = scheme["pink"]

    entries = [
        ("Ansi 0 Color", dark, 1.0),
        ("Ansi 1 Color", red, 1.0),
        ("Ansi 2 Color", green, 1.0),
        ("Ansi 3 Color", yellow, 1.0),
        ("Ansi 4 Color", blue, 1.0),
        ("Ansi 5 Color", purple, 1.0),
        ("Ansi 6 Color", cyan, 1.0),
        ("Ansi 7 Color", light, 1.0),
        ("Ansi 8 Color", grey, 1.0),
        ("Ansi 9 Color", red, 1.0),
        ("Ansi 10 Color", green, 1.0),
        ("Ansi 11 Color", orange, 1.0),
        ("Ansi 12 Color", blue, 1.0),
        ("Ansi 13 Color", pink, 1.0),
        ("Ansi 14 Color", secondary, 1.0),
        ("Ansi 15 Color", light, 1.0),
        ("Background Color", dark, 1.0),
        ("Badge Color", accent, 0.5),
        ("Bold Color", light, 1.0),
        ("Cursor Color", accent, 1.0),
        ("Cursor Guide Color", grey, 0.25),
        ("Cursor Text Color", dark, 1.0),
        ("Foreground Color", light, 1.0),
        ("Link Color", cyan, 1.0),
        ("Selected Text Color", light, 1.0),
        ("Selection Color", secondary, 1.0),
        ("Tab Color", dark, 1.0),
    ]

    body = "\n".join(_plist_color(name, rgb, alpha) for name, rgb, alpha in entries)
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
{body}
</dict>
</plist>
"""
    atomic_write(_output_path(), content)
