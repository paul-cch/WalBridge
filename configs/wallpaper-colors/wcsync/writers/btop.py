"""btop theme writer."""

from ..target_apps import target_name, target_path
from ..utils import atomic_write, hex6

def _theme_name():
    return target_name("btop", "theme")


def _output_path():
    return target_path("btop")


def write(scheme, config=None):
    dark = hex6(*scheme["dark"])
    light = hex6(*scheme["light"])
    accent = hex6(*scheme["accent"])
    secondary = hex6(*scheme["secondary"])
    item_bg = hex6(*scheme["item_bg"])
    grey = hex6(*scheme["grey"])
    red = hex6(*scheme["red"])
    green = hex6(*scheme["green"])
    yellow = hex6(*scheme["yellow"])
    cyan = hex6(*scheme["cyan"])
    purple = hex6(*scheme["purple"])
    orange = hex6(*scheme["orange"])
    pink = hex6(*scheme["pink"])

    content = f"""# Auto-generated from wallpaper — do not edit manually
# Regenerate: python3 ~/.config/wallpaper-colors/wallpaper_colors.py

theme[main_bg]="{dark}"
theme[main_fg]="{light}"
theme[title]="{accent}"
theme[hi_fg]="{accent}"
theme[selected_bg]="{item_bg}"
theme[selected_fg]="{light}"
theme[inactive_fg]="{grey}"
theme[graph_text]="{accent}"
theme[meter_bg]="{item_bg}"
theme[proc_misc]="{secondary}"
theme[cpu_box]="{accent}"
theme[mem_box]="{secondary}"
theme[net_box]="{cyan}"
theme[proc_box]="{purple}"
theme[div_line]="{grey}"
theme[temp_start]="{green}"
theme[temp_mid]="{yellow}"
theme[temp_end]="{red}"
theme[cpu_start]="{green}"
theme[cpu_mid]="{yellow}"
theme[cpu_end]="{red}"
theme[free_end]="{green}"
theme[free_mid]="{yellow}"
theme[free_start]="{red}"
theme[cached_start]="{green}"
theme[cached_mid]="{yellow}"
theme[cached_end]="{red}"
theme[available_start]="{red}"
theme[available_mid]="{yellow}"
theme[available_end]="{green}"
theme[used_start]="{green}"
theme[used_mid]="{yellow}"
theme[used_end]="{red}"
theme[download_start]="{cyan}"
theme[download_mid]="{accent}"
theme[download_end]="{purple}"
theme[upload_start]="{green}"
theme[upload_mid]="{orange}"
theme[upload_end]="{red}"
theme[process_start]="{accent}"
theme[process_mid]="{secondary}"
theme[process_end]="{pink}"
"""
    atomic_write(_output_path(), content)
