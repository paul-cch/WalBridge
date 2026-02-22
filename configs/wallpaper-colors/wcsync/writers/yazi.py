"""Yazi file manager flavor writer."""

import os

from ..utils import atomic_write, hex6

OUTPUT_PATH = os.path.expanduser("~/.config/yazi/flavors/wallpaper.yazi/flavor.toml")


def write(scheme, config=None):
    bg = hex6(*scheme["dark"])
    fg = hex6(*scheme["light"])
    accent = hex6(*scheme["accent"])
    green = hex6(*scheme["green"])
    red = hex6(*scheme["red"])
    yellow = hex6(*scheme["yellow"])
    purple = hex6(*scheme["purple"])
    cyan = hex6(*scheme["cyan"])
    orange = hex6(*scheme["orange"])
    pink = hex6(*scheme["pink"])
    grey = hex6(*scheme["grey"])
    sel_bg = hex6(*scheme["item_bg"])
    border_accent = hex6(*scheme["border_accent"])

    content = f"""# Auto-generated from wallpaper — do not edit manually
# Regenerate: python3 ~/.config/wallpaper-colors/wallpaper_colors.py

# : Manager {{{{
[mgr]
cwd = {{ fg = "{accent}" }}

find_keyword  = {{ fg = "{red}", bold = true, italic = true, underline = true }}
find_position = {{ fg = "{purple}", bg = "reset", bold = true, italic = true }}

marker_copied   = {{ fg = "{green}", bg = "{green}" }}
marker_cut      = {{ fg = "{yellow}", bg = "{red}" }}
marker_marked   = {{ fg = "{accent}", bg = "{cyan}" }}
marker_selected = {{ fg = "{yellow}", bg = "{yellow}" }}

count_copied   = {{ fg = "{bg}", bg = "{green}" }}
count_cut      = {{ fg = "{bg}", bg = "{yellow}" }}
count_selected = {{ fg = "{bg}", bg = "{accent}" }}

border_symbol = "│"
border_style  = {{ fg = "{grey}" }}
# : }}}}

# : Tabs {{{{
[tabs]
active   = {{ fg = "{bg}", bg = "{accent}", bold = true }}
inactive = {{ fg = "{accent}", bg = "{sel_bg}" }}
# : }}}}

# : Mode {{{{
[mode]
normal_main = {{ fg = "{bg}", bg = "{accent}", bold = true }}
normal_alt  = {{ fg = "{accent}", bg = "{sel_bg}" }}

select_main = {{ fg = "{bg}", bg = "{green}", bold = true }}
select_alt  = {{ fg = "{accent}", bg = "{sel_bg}" }}

unset_main = {{ fg = "{bg}", bg = "{purple}", bold = true }}
unset_alt  = {{ fg = "{accent}", bg = "{sel_bg}" }}
# : }}}}

# : Status bar {{{{
[status]
overall = {{ fg = "{accent}" }}
sep_left  = {{ open = "", close = "" }}
sep_right = {{ open = "", close = "" }}

progress_label  = {{ fg = "{bg}", bold = true }}
progress_normal = {{ fg = "{accent}", bg = "{sel_bg}" }}
progress_error  = {{ fg = "{red}", bg = "{sel_bg}" }}

perm_sep   = {{ fg = "{accent}" }}
perm_type  = {{ fg = "{green}" }}
perm_read  = {{ fg = "{yellow}" }}
perm_write = {{ fg = "{red}" }}
perm_exec  = {{ fg = "{purple}" }}
# : }}}}

# : Pick {{{{
[pick]
border   = {{ fg = "{border_accent}" }}
active   = {{ fg = "{purple}", bold = true }}
inactive = {{}}
# : }}}}

# : Input {{{{
[input]
border   = {{ fg = "{border_accent}" }}
title    = {{}}
value    = {{}}
selected = {{ reversed = true }}
# : }}}}

# : Completion {{{{
[cmp]
border = {{ fg = "{border_accent}" }}
# : }}}}

# : Tasks {{{{
[tasks]
border  = {{ fg = "{border_accent}" }}
title   = {{}}
hovered = {{ fg = "{purple}", underline = true }}
# : }}}}

# : Which {{{{
[which]
mask            = {{ bg = "{grey}" }}
cand            = {{ fg = "{green}" }}
rest            = {{ fg = "{fg}" }}
desc            = {{ fg = "{purple}" }}
separator       = "  "
separator_style = {{ fg = "{grey}" }}
# : }}}}

# : Help {{{{
[help]
on      = {{ fg = "{green}" }}
run     = {{ fg = "{purple}" }}
hovered = {{ reversed = true, bold = true }}
footer  = {{ fg = "{bg}", bg = "{fg}" }}
# : }}}}

# : Spotter {{{{
[spot]
border   = {{ fg = "{border_accent}" }}
title    = {{ fg = "{accent}" }}
tbl_col  = {{ fg = "{green}" }}
tbl_cell = {{ fg = "{purple}", bg = "{sel_bg}" }}
# : }}}}

# : Notify {{{{
[notify]
title_info  = {{ fg = "{green}" }}
title_warn  = {{ fg = "{red}" }}
title_error = {{ fg = "{yellow}" }}
# : }}}}

# : File-specific styles {{{{
[filetype]
rules = [
  {{ mime = "image/*", fg = "{yellow}" }},
  {{ mime = "video/*", fg = "{red}" }},
  {{ mime = "audio/*", fg = "{red}" }},
  {{ mime = "application/zip",             fg = "{purple}" }},
  {{ mime = "application/x-tar",           fg = "{purple}" }},
  {{ mime = "application/x-bzip*",         fg = "{purple}" }},
  {{ mime = "application/x-bzip2",         fg = "{purple}" }},
  {{ mime = "application/x-7z-compressed", fg = "{purple}" }},
  {{ mime = "application/x-rar",           fg = "{purple}" }},
  {{ mime = "application/x-xz",            fg = "{purple}" }},
  {{ mime = "application/doc",        fg = "{green}" }},
  {{ mime = "application/epub+zip",   fg = "{green}" }},
  {{ mime = "application/pdf",        fg = "{green}" }},
  {{ mime = "application/rtf",        fg = "{green}" }},
  {{ mime = "application/vnd.*",      fg = "{green}" }},
  {{ mime = "*", is = "orphan", fg = "{pink}", bg = "{red}" }},
  {{ mime = "application/*exec*", fg = "{red}" }},
  {{ url = "*", fg = "{fg}" }},
  {{ url = "*/", fg = "{accent}" }},
]
# : }}}}
"""
    atomic_write(OUTPUT_PATH, content)
