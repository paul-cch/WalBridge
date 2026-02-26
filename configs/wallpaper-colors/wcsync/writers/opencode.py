"""OpenCode TUI theme writer."""

import json
import os

from ..colors import darken, vivify
from ..utils import atomic_write, hex6, safe_home_path

DEFAULT_OUTPUT_PATH = "~/.config/opencode/themes/wallpaper.json"


def _output_path():
    return safe_home_path(
        os.environ.get("WALLPAPER_OPENCODE_OUTPUT_PATH"),
        DEFAULT_OUTPUT_PATH,
        "WALLPAPER_OPENCODE_OUTPUT_PATH",
    )


def write(scheme, config=None):
    fg = hex6(*scheme["light"])
    grey = hex6(*scheme["grey"])
    sel_bg = hex6(*scheme["item_bg"])
    border = hex6(*scheme["border_accent"])

    # Syntax colors — gentle brightness lift for readability
    accent = hex6(*vivify(scheme["accent"], min_sat=0.35, min_val=0.65))
    red = hex6(*vivify(scheme["red"], min_sat=0.35, min_val=0.65))
    green = hex6(*vivify(scheme["green"], min_sat=0.35, min_val=0.65))
    yellow = hex6(*vivify(scheme["yellow"], min_sat=0.35, min_val=0.65))
    cyan = hex6(*vivify(scheme["cyan"], min_sat=0.35, min_val=0.65))
    purple = hex6(*vivify(scheme["purple"], min_sat=0.35, min_val=0.65))
    orange = hex6(*vivify(scheme["orange"], min_sat=0.35, min_val=0.65))
    pink = hex6(*vivify(scheme["pink"], min_sat=0.35, min_val=0.65))

    # Diff background tints
    add_bg = hex6(*darken(scheme["green"], 0.15))
    del_bg = hex6(*darken(scheme["red"], 0.15))

    theme = {
        "$schema": "https://opencode.ai/theme.json",
        "theme": {
            "primary": accent,
            "secondary": hex6(*scheme["secondary"]),
            "accent": border,
            "error": red,
            "warning": orange,
            "success": green,
            "info": cyan,
            "text": fg,
            "textMuted": grey,
            "background": hex6(*scheme["dark"]),
            "backgroundPanel": sel_bg,
            "backgroundElement": sel_bg,
            "border": grey,
            "borderActive": border,
            "borderSubtle": hex6(*darken(scheme["grey"], 0.7)),
            "diffAdded": green,
            "diffRemoved": red,
            "diffContext": grey,
            "diffHunkHeader": grey,
            "diffHighlightAdded": green,
            "diffHighlightRemoved": red,
            "diffAddedBg": add_bg,
            "diffRemovedBg": del_bg,
            "diffContextBg": sel_bg,
            "diffLineNumber": grey,
            "diffAddedLineNumberBg": add_bg,
            "diffRemovedLineNumberBg": del_bg,
            "markdownText": fg,
            "markdownHeading": accent,
            "markdownLink": cyan,
            "markdownLinkText": accent,
            "markdownCode": green,
            "markdownBlockQuote": grey,
            "markdownEmph": orange,
            "markdownStrong": yellow,
            "markdownHorizontalRule": grey,
            "markdownListItem": accent,
            "markdownListEnumeration": cyan,
            "markdownImage": purple,
            "markdownImageText": accent,
            "markdownCodeBlock": fg,
            "syntaxComment": grey,
            "syntaxKeyword": accent,
            "syntaxFunction": cyan,
            "syntaxVariable": fg,
            "syntaxString": green,
            "syntaxNumber": orange,
            "syntaxType": purple,
            "syntaxOperator": pink,
            "syntaxPunctuation": grey,
        },
    }
    atomic_write(_output_path(), json.dumps(theme, indent=2) + "\n")
