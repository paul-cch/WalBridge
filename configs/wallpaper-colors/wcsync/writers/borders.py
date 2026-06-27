"""JankyBorders border_colors writer."""

from ..target_apps import target_path
from ..utils import atomic_write, hexc

def _output_path():
    return target_path("borders")


def write(scheme, config=None):
    accent = hexc(*scheme["border_accent"])
    inactive_rgb = scheme.get("border_inactive") or scheme.get("grey", scheme["border_accent"])
    inactive = hexc(*inactive_rgb)
    atomic_write(
        _output_path(),
        f"active_color={accent}\ninactive_color={inactive}\n",
    )
