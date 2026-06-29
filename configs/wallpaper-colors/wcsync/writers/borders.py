"""JankyBorders border_colors writer."""

from ..target_writing import ColorMaterial
from ..utils import hexc


def render(scheme, app, config=None):
    accent = hexc(*scheme["border_accent"])
    inactive_rgb = scheme.get("border_inactive") or scheme.get("grey", scheme["border_accent"])
    inactive = hexc(*inactive_rgb)
    return ColorMaterial(f"active_color={accent}\ninactive_color={inactive}\n")
