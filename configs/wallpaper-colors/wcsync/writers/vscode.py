"""VS Code syntax highlighting writer.

Writes editor.tokenColorCustomizations into VS Code's settings.json.
VS Code watches this file and applies changes instantly — no reload needed.
"""

import colorsys
import json
import os
import re

from ..colors import lighten
from ..utils import atomic_write, clamp, hex6, log, safe_home_path

DEFAULT_SETTINGS_PATH = "~/Library/Application Support/Code/User/settings.json"


def _syntax(rgb, max_sat=0.60, min_val=0.70, max_val=0.92):
    """Process a scheme color for readable syntax highlighting.

    Unlike vivify (floors only), this CAPS saturation to prevent neon
    on vibrant wallpapers while keeping colors distinct and readable.
    """
    h, s, v = colorsys.rgb_to_hsv(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)
    s = max(0.20, min(s, max_sat))
    v = max(min_val, min(v, max_val))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (clamp(r * 255), clamp(g * 255), clamp(b * 255))


def _settings_path():
    return safe_home_path(
        os.environ.get("WALLPAPER_VSCODE_SETTINGS_PATH"),
        DEFAULT_SETTINGS_PATH,
        "WALLPAPER_VSCODE_SETTINGS_PATH",
    )


def _strip_jsonc(text):
    """Strip comments and trailing commas so JSONC can be parsed as JSON."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"(?m)//.*$", "", text)
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return text


def _read_settings():
    """Read and parse VS Code settings.json, handling JSONC."""
    path = _settings_path()
    if not os.path.isfile(path):
        return None, path

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    except OSError:
        return None, path

    for text in (raw, _strip_jsonc(raw)):
        try:
            return json.loads(text), path
        except json.JSONDecodeError:
            continue

    return None, path


def _update_settings(token_customizations):
    """Merge syntax color overrides into VS Code settings.json.

    Only touches editor.tokenColorCustomizations — workbench colors are left
    to the user (vibrancy, transparency, etc.).
    """
    settings, path = _read_settings()
    if settings is None:
        if os.path.isfile(path):
            log("VS Code: could not parse settings.json, skipping")
        return

    tcc = settings.setdefault("editor.tokenColorCustomizations", {})
    if isinstance(tcc, dict):
        tcc["textMateRules"] = token_customizations

    atomic_write(path, json.dumps(settings, indent=4) + "\n")


def write(scheme, config=None):
    fg = hex6(*scheme["light"])
    grey = hex6(*scheme["grey"])
    # Brighter grey for punctuation — brackets/braces need to stay readable
    # on vibrancy backgrounds where the base grey can disappear.
    punct = hex6(*lighten(scheme["grey"], 0.30))

    # Per-role tuning: (max_sat, min_val, max_val)
    # Higher min_val than typical dark themes because vibrancy makes
    # the background lighter/noisier — syntax needs to punch through.
    accent = hex6(*_syntax(scheme["accent"], max_sat=0.52, min_val=0.80))
    red = hex6(*_syntax(scheme["red"], max_sat=0.55, min_val=0.80))
    green = hex6(*_syntax(scheme["green"], max_sat=0.45, min_val=0.78, max_val=0.92))
    yellow = hex6(*_syntax(scheme["yellow"], max_sat=0.48, min_val=0.80, max_val=0.92))
    cyan = hex6(*_syntax(scheme["cyan"], max_sat=0.48, min_val=0.78))
    purple = hex6(*_syntax(scheme["purple"], max_sat=0.48, min_val=0.78))
    orange = hex6(*_syntax(scheme["orange"], max_sat=0.50, min_val=0.80, max_val=0.92))
    pink = hex6(*_syntax(scheme["pink"], max_sat=0.40, min_val=0.78))

    token_rules = [
        {
            "scope": ["comment", "punctuation.definition.comment"],
            "settings": {"foreground": grey, "fontStyle": "italic"},
        },
        {
            "scope": ["string", "string.quoted", "string.template"],
            "settings": {"foreground": green},
        },
        {
            "scope": ["constant.character.escape", "string.regexp"],
            "settings": {"foreground": orange},
        },
        {
            "scope": [
                "keyword",
                "keyword.control",
                "keyword.operator.new",
                "keyword.operator.expression",
                "keyword.operator.logical",
                "storage",
                "storage.type",
                "storage.modifier",
            ],
            "settings": {"foreground": accent, "fontStyle": "bold"},
        },
        {
            "scope": [
                "entity.name.function",
                "support.function",
                "meta.function-call entity.name.function",
            ],
            "settings": {"foreground": cyan},
        },
        {
            "scope": [
                "entity.name.type",
                "entity.name.class",
                "support.type",
                "support.class",
                "entity.other.inherited-class",
                "entity.name.type.interface",
            ],
            "settings": {"foreground": purple},
        },
        {
            "scope": ["variable", "variable.other"],
            "settings": {"foreground": fg},
        },
        {
            "scope": ["variable.language", "variable.parameter"],
            "settings": {"foreground": fg, "fontStyle": "italic"},
        },
        {
            "scope": [
                "constant",
                "constant.numeric",
                "constant.language",
                "support.constant",
                "variable.other.enummember",
            ],
            "settings": {"foreground": orange},
        },
        {
            "scope": ["keyword.operator", "punctuation.accessor"],
            "settings": {"foreground": pink},
        },
        {
            "scope": [
                "punctuation",
                "punctuation.definition",
                "punctuation.separator",
                "punctuation.terminator",
                "meta.brace",
            ],
            "settings": {"foreground": punct},
        },
        {"scope": ["entity.name.tag"], "settings": {"foreground": accent}},
        {
            "scope": ["entity.other.attribute-name"],
            "settings": {"foreground": orange, "fontStyle": "italic"},
        },
        {
            "scope": [
                "meta.decorator",
                "punctuation.decorator",
                "entity.name.function.decorator",
            ],
            "settings": {"foreground": yellow},
        },
        {
            "scope": [
                "entity.name.import",
                "entity.name.namespace",
                "support.module",
            ],
            "settings": {"foreground": accent},
        },
        {
            "scope": ["meta.preprocessor", "entity.name.function.preprocessor"],
            "settings": {"foreground": yellow},
        },
        {
            "scope": ["support.type.property-name.css"],
            "settings": {"foreground": cyan},
        },
        {
            "scope": ["support.constant.property-value.css"],
            "settings": {"foreground": orange},
        },
        {
            "scope": ["markup.heading", "entity.name.section"],
            "settings": {"foreground": accent, "fontStyle": "bold"},
        },
        {"scope": ["markup.bold"], "settings": {"fontStyle": "bold"}},
        {"scope": ["markup.italic"], "settings": {"fontStyle": "italic"}},
        {
            "scope": ["markup.underline.link"],
            "settings": {"foreground": cyan, "fontStyle": "underline"},
        },
        {
            "scope": ["markup.inline.raw", "markup.fenced_code"],
            "settings": {"foreground": green},
        },
        {"scope": ["markup.list"], "settings": {"foreground": accent}},
        {"scope": ["markup.inserted"], "settings": {"foreground": green}},
        {"scope": ["markup.deleted"], "settings": {"foreground": red}},
        {"scope": ["markup.changed"], "settings": {"foreground": yellow}},
        {"scope": ["invalid"], "settings": {"foreground": red}},
        {
            "scope": ["invalid.deprecated"],
            "settings": {"foreground": orange, "fontStyle": "strikethrough"},
        },
    ]

    _update_settings(token_rules)
