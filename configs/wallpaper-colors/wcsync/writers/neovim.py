"""Neovim highlight overrides + lualine theme writer."""

import os

from ..colors import darken, lighten, vivify
from ..utils import atomic_write, hex6, safe_home_path

DEFAULT_NVIM_COLORS_PATH = "~/.config/wallpaper-colors/nvim_colors.lua"
DEFAULT_LUALINE_PATH = "~/.config/nvim/lua/lualine/themes/wallpaper.lua"


def _nvim_colors_path():
    return safe_home_path(
        os.environ.get("WALLPAPER_NVIM_COLORS_PATH"),
        DEFAULT_NVIM_COLORS_PATH,
        "WALLPAPER_NVIM_COLORS_PATH",
    )


def _lualine_path():
    return safe_home_path(
        os.environ.get("WALLPAPER_LUALINE_PATH"),
        DEFAULT_LUALINE_PATH,
        "WALLPAPER_LUALINE_PATH",
    )


def write(scheme, config=None):
    _write_nvim_colors(scheme)
    _write_lualine_theme(scheme)


def _write_nvim_colors(scheme):
    """Write Neovim highlight overrides synced to wallpaper.

    Syntax colors get a gentle brightness floor (min value 0.65) so they
    stay readable on transparent dark backgrounds without going neon.
    UI elements (borders, selection, statusline) use raw palette values.
    """
    fg = hex6(*scheme["light"])
    grey = hex6(*scheme["grey"])
    sel_bg = hex6(*scheme["item_bg"])
    border = hex6(*scheme["border_accent"])

    # Syntax colors — same hue/saturation as kitty, gentle brightness lift
    accent = hex6(*vivify(scheme["accent"], min_sat=0.35, min_val=0.65))
    red = hex6(*vivify(scheme["red"], min_sat=0.35, min_val=0.65))
    green = hex6(*vivify(scheme["green"], min_sat=0.35, min_val=0.65))
    yellow = hex6(*vivify(scheme["yellow"], min_sat=0.35, min_val=0.65))
    cyan = hex6(*vivify(scheme["cyan"], min_sat=0.35, min_val=0.65))
    purple = hex6(*vivify(scheme["purple"], min_sat=0.35, min_val=0.65))
    orange = hex6(*vivify(scheme["orange"], min_sat=0.35, min_val=0.65))
    pink = hex6(*vivify(scheme["pink"], min_sat=0.35, min_val=0.65))

    # Bright variants for emphasis
    br_accent = hex6(*lighten(scheme["accent"], 0.2))

    # Subtle bg tints for diff/diagnostic virtual text
    add_bg = hex6(*darken(scheme["green"], 0.15))
    change_bg = hex6(*darken(scheme["yellow"], 0.15))
    del_bg = hex6(*darken(scheme["red"], 0.15))

    content = f"""-- Auto-generated from wallpaper — do not edit manually
local M = {{}}

function M.apply()
  local hi = vim.api.nvim_set_hl

  -- Syntax — core vim groups
  hi(0, "Comment", {{ fg = "{grey}", italic = true }})
  hi(0, "String", {{ fg = "{green}" }})
  hi(0, "Character", {{ fg = "{green}" }})
  hi(0, "Keyword", {{ fg = "{accent}", bold = true }})
  hi(0, "Statement", {{ fg = "{accent}" }})
  hi(0, "Conditional", {{ fg = "{accent}" }})
  hi(0, "Repeat", {{ fg = "{accent}" }})
  hi(0, "Label", {{ fg = "{accent}" }})
  hi(0, "Exception", {{ fg = "{red}" }})
  hi(0, "Function", {{ fg = "{cyan}" }})
  hi(0, "Identifier", {{ fg = "{fg}" }})
  hi(0, "Type", {{ fg = "{purple}" }})
  hi(0, "StorageClass", {{ fg = "{accent}" }})
  hi(0, "Structure", {{ fg = "{purple}" }})
  hi(0, "Typedef", {{ fg = "{purple}" }})
  hi(0, "Constant", {{ fg = "{orange}" }})
  hi(0, "Number", {{ fg = "{orange}" }})
  hi(0, "Float", {{ fg = "{orange}" }})
  hi(0, "Boolean", {{ fg = "{orange}" }})
  hi(0, "Operator", {{ fg = "{pink}" }})
  hi(0, "Delimiter", {{ fg = "{grey}" }})
  hi(0, "PreProc", {{ fg = "{yellow}" }})
  hi(0, "Include", {{ fg = "{accent}" }})
  hi(0, "Define", {{ fg = "{accent}" }})
  hi(0, "Macro", {{ fg = "{yellow}" }})
  hi(0, "Special", {{ fg = "{yellow}" }})
  hi(0, "SpecialChar", {{ fg = "{orange}" }})
  hi(0, "Tag", {{ fg = "{accent}" }})
  hi(0, "Todo", {{ fg = "{yellow}", bold = true }})
  hi(0, "Error", {{ fg = "{red}" }})
  hi(0, "Underlined", {{ fg = "{accent}", underline = true }})

  -- Treesitter
  hi(0, "@variable", {{ fg = "{fg}" }})
  hi(0, "@variable.builtin", {{ fg = "{red}", italic = true }})
  hi(0, "@variable.parameter", {{ fg = "{fg}", italic = true }})
  hi(0, "@variable.member", {{ fg = "{fg}" }})
  hi(0, "@property", {{ fg = "{fg}" }})
  hi(0, "@constant", {{ fg = "{orange}" }})
  hi(0, "@constant.builtin", {{ fg = "{orange}", italic = true }})
  hi(0, "@module", {{ fg = "{accent}" }})
  hi(0, "@string", {{ fg = "{green}" }})
  hi(0, "@string.escape", {{ fg = "{orange}" }})
  hi(0, "@string.special", {{ fg = "{green}" }})
  hi(0, "@string.regex", {{ fg = "{orange}" }})
  hi(0, "@character", {{ fg = "{green}" }})
  hi(0, "@number", {{ fg = "{orange}" }})
  hi(0, "@boolean", {{ fg = "{orange}" }})
  hi(0, "@float", {{ fg = "{orange}" }})
  hi(0, "@function", {{ fg = "{cyan}" }})
  hi(0, "@function.call", {{ fg = "{cyan}" }})
  hi(0, "@function.builtin", {{ fg = "{cyan}", italic = true }})
  hi(0, "@function.method", {{ fg = "{cyan}" }})
  hi(0, "@function.method.call", {{ fg = "{cyan}" }})
  hi(0, "@constructor", {{ fg = "{yellow}" }})
  hi(0, "@keyword", {{ fg = "{accent}", bold = true }})
  hi(0, "@keyword.function", {{ fg = "{accent}" }})
  hi(0, "@keyword.return", {{ fg = "{accent}" }})
  hi(0, "@keyword.conditional", {{ fg = "{accent}" }})
  hi(0, "@keyword.repeat", {{ fg = "{accent}" }})
  hi(0, "@keyword.operator", {{ fg = "{pink}" }})
  hi(0, "@keyword.import", {{ fg = "{accent}" }})
  hi(0, "@keyword.exception", {{ fg = "{red}" }})
  hi(0, "@operator", {{ fg = "{pink}" }})
  hi(0, "@punctuation", {{ fg = "{grey}" }})
  hi(0, "@punctuation.bracket", {{ fg = "{grey}" }})
  hi(0, "@punctuation.delimiter", {{ fg = "{grey}" }})
  hi(0, "@punctuation.special", {{ fg = "{yellow}" }})
  hi(0, "@type", {{ fg = "{purple}" }})
  hi(0, "@type.builtin", {{ fg = "{purple}", italic = true }})
  hi(0, "@type.definition", {{ fg = "{purple}" }})
  hi(0, "@attribute", {{ fg = "{yellow}" }})
  hi(0, "@tag", {{ fg = "{accent}" }})
  hi(0, "@tag.attribute", {{ fg = "{orange}" }})
  hi(0, "@tag.delimiter", {{ fg = "{grey}" }})
  hi(0, "@comment", {{ fg = "{grey}", italic = true }})
  hi(0, "@comment.todo", {{ fg = "{yellow}", bold = true }})
  hi(0, "@comment.note", {{ fg = "{cyan}", bold = true }})
  hi(0, "@comment.error", {{ fg = "{red}", bold = true }})
  hi(0, "@comment.warning", {{ fg = "{yellow}", bold = true }})
  hi(0, "@markup.heading", {{ fg = "{accent}", bold = true }})
  hi(0, "@markup.italic", {{ italic = true }})
  hi(0, "@markup.strong", {{ bold = true }})
  hi(0, "@markup.link", {{ fg = "{accent}", underline = true }})
  hi(0, "@markup.link.url", {{ fg = "{cyan}", underline = true }})
  hi(0, "@markup.raw", {{ fg = "{green}" }})
  hi(0, "@markup.list", {{ fg = "{accent}" }})
  hi(0, "@diff.plus", {{ fg = "{green}" }})
  hi(0, "@diff.minus", {{ fg = "{red}" }})
  hi(0, "@diff.delta", {{ fg = "{yellow}" }})

  -- LSP semantic tokens
  hi(0, "@lsp.type.function", {{ fg = "{cyan}" }})
  hi(0, "@lsp.type.method", {{ fg = "{cyan}" }})
  hi(0, "@lsp.type.property", {{ fg = "{fg}" }})
  hi(0, "@lsp.type.variable", {{ fg = "{fg}" }})
  hi(0, "@lsp.type.parameter", {{ fg = "{fg}", italic = true }})
  hi(0, "@lsp.type.type", {{ fg = "{purple}" }})
  hi(0, "@lsp.type.interface", {{ fg = "{purple}" }})
  hi(0, "@lsp.type.namespace", {{ fg = "{accent}" }})
  hi(0, "@lsp.type.enum", {{ fg = "{purple}" }})
  hi(0, "@lsp.type.enumMember", {{ fg = "{orange}" }})
  hi(0, "@lsp.type.decorator", {{ fg = "{yellow}" }})
  hi(0, "@lsp.mod.deprecated", {{ strikethrough = true }})

  -- UI — editor chrome
  hi(0, "Normal", {{ fg = "{fg}", bg = "NONE" }})
  hi(0, "NormalNC", {{ fg = "{fg}", bg = "NONE" }})
  hi(0, "NormalFloat", {{ fg = "{fg}", bg = "NONE" }})
  hi(0, "Visual", {{ bg = "{sel_bg}" }})
  hi(0, "Search", {{ fg = "#000000", bg = "{yellow}" }})
  hi(0, "IncSearch", {{ fg = "#000000", bg = "{orange}" }})
  hi(0, "CurSearch", {{ fg = "#000000", bg = "{accent}" }})
  hi(0, "Substitute", {{ fg = "#000000", bg = "{red}" }})
  hi(0, "CursorLine", {{ bg = "{sel_bg}" }})
  hi(0, "CursorColumn", {{ bg = "{sel_bg}" }})
  hi(0, "ColorColumn", {{ bg = "{sel_bg}" }})
  hi(0, "LineNr", {{ fg = "{grey}", bg = "NONE" }})
  hi(0, "CursorLineNr", {{ fg = "{accent}", bg = "NONE", bold = true }})
  hi(0, "SignColumn", {{ bg = "NONE" }})
  hi(0, "FoldColumn", {{ fg = "{grey}", bg = "NONE" }})
  hi(0, "Folded", {{ fg = "{grey}", bg = "{sel_bg}" }})
  hi(0, "VertSplit", {{ fg = "{border}" }})
  hi(0, "WinSeparator", {{ fg = "{border}" }})
  hi(0, "FloatBorder", {{ fg = "{border}" }})
  hi(0, "FloatTitle", {{ fg = "{accent}", bold = true }})
  hi(0, "StatusLine", {{ fg = "{fg}", bg = "{sel_bg}" }})
  hi(0, "StatusLineNC", {{ fg = "{grey}", bg = "{sel_bg}" }})
  hi(0, "WinBar", {{ fg = "{fg}", bg = "NONE" }})
  hi(0, "WinBarNC", {{ fg = "{grey}", bg = "NONE" }})
  hi(0, "TabLine", {{ fg = "{grey}", bg = "{sel_bg}" }})
  hi(0, "TabLineSel", {{ fg = "{fg}", bg = "{sel_bg}", bold = true }})
  hi(0, "TabLineFill", {{ bg = "NONE" }})
  hi(0, "Title", {{ fg = "{accent}", bold = true }})
  hi(0, "Directory", {{ fg = "{accent}" }})
  hi(0, "MatchParen", {{ fg = "{yellow}", bold = true }})
  hi(0, "NonText", {{ fg = "{grey}" }})
  hi(0, "SpecialKey", {{ fg = "{grey}" }})
  hi(0, "Conceal", {{ fg = "{grey}" }})
  hi(0, "EndOfBuffer", {{ fg = "{grey}", bg = "NONE" }})
  hi(0, "Pmenu", {{ fg = "{fg}", bg = "{sel_bg}" }})
  hi(0, "PmenuSel", {{ fg = "#000000", bg = "{accent}" }})
  hi(0, "PmenuSbar", {{ bg = "{sel_bg}" }})
  hi(0, "PmenuThumb", {{ bg = "{grey}" }})
  hi(0, "ModeMsg", {{ fg = "{accent}", bold = true }})
  hi(0, "MoreMsg", {{ fg = "{green}" }})
  hi(0, "Question", {{ fg = "{green}" }})
  hi(0, "WarningMsg", {{ fg = "{yellow}" }})
  hi(0, "ErrorMsg", {{ fg = "{red}" }})

  -- Diagnostics
  hi(0, "DiagnosticError", {{ fg = "{red}" }})
  hi(0, "DiagnosticWarn", {{ fg = "{yellow}" }})
  hi(0, "DiagnosticInfo", {{ fg = "{accent}" }})
  hi(0, "DiagnosticHint", {{ fg = "{cyan}" }})
  hi(0, "DiagnosticUnderlineError", {{ undercurl = true, sp = "{red}" }})
  hi(0, "DiagnosticUnderlineWarn", {{ undercurl = true, sp = "{yellow}" }})
  hi(0, "DiagnosticUnderlineInfo", {{ undercurl = true, sp = "{accent}" }})
  hi(0, "DiagnosticUnderlineHint", {{ undercurl = true, sp = "{cyan}" }})
  hi(0, "DiagnosticVirtualTextError", {{ fg = "{red}", bg = "{del_bg}" }})
  hi(0, "DiagnosticVirtualTextWarn", {{ fg = "{yellow}", bg = "{change_bg}" }})
  hi(0, "DiagnosticVirtualTextInfo", {{ fg = "{accent}" }})
  hi(0, "DiagnosticVirtualTextHint", {{ fg = "{cyan}" }})

  -- Git / Diff
  hi(0, "DiffAdd", {{ bg = "{add_bg}" }})
  hi(0, "DiffChange", {{ bg = "{change_bg}" }})
  hi(0, "DiffDelete", {{ bg = "{del_bg}" }})
  hi(0, "DiffText", {{ fg = "#000000", bg = "{yellow}" }})
  hi(0, "Added", {{ fg = "{green}" }})
  hi(0, "Changed", {{ fg = "{yellow}" }})
  hi(0, "Removed", {{ fg = "{red}" }})

  -- GitSigns
  hi(0, "GitSignsAdd", {{ fg = "{green}", bg = "NONE" }})
  hi(0, "GitSignsChange", {{ fg = "{yellow}", bg = "NONE" }})
  hi(0, "GitSignsDelete", {{ fg = "{red}", bg = "NONE" }})
  hi(0, "GitSignsCurrentLineBlame", {{ fg = "{grey}", italic = true }})

  -- Telescope
  hi(0, "TelescopeBorder", {{ fg = "{border}" }})
  hi(0, "TelescopePromptBorder", {{ fg = "{border}" }})
  hi(0, "TelescopeResultsBorder", {{ fg = "{border}" }})
  hi(0, "TelescopePreviewBorder", {{ fg = "{border}" }})
  hi(0, "TelescopeTitle", {{ fg = "{accent}", bold = true }})
  hi(0, "TelescopePromptTitle", {{ fg = "{accent}", bold = true }})
  hi(0, "TelescopeResultsTitle", {{ fg = "{accent}", bold = true }})
  hi(0, "TelescopePreviewTitle", {{ fg = "{accent}", bold = true }})
  hi(0, "TelescopeMatching", {{ fg = "{yellow}", bold = true }})
  hi(0, "TelescopeSelection", {{ bg = "{sel_bg}" }})
  hi(0, "TelescopeNormal", {{ bg = "NONE" }})

  -- Cmp (completion)
  hi(0, "CmpItemAbbr", {{ fg = "{fg}" }})
  hi(0, "CmpItemAbbrMatch", {{ fg = "{accent}", bold = true }})
  hi(0, "CmpItemAbbrMatchFuzzy", {{ fg = "{accent}" }})
  hi(0, "CmpItemKind", {{ fg = "{purple}" }})
  hi(0, "CmpItemKindFunction", {{ fg = "{cyan}" }})
  hi(0, "CmpItemKindMethod", {{ fg = "{cyan}" }})
  hi(0, "CmpItemKindVariable", {{ fg = "{fg}" }})
  hi(0, "CmpItemKindKeyword", {{ fg = "{accent}" }})
  hi(0, "CmpItemKindSnippet", {{ fg = "{yellow}" }})
  hi(0, "CmpItemKindText", {{ fg = "{grey}" }})
  hi(0, "CmpItemMenu", {{ fg = "{grey}" }})

  -- Indent guides
  hi(0, "IblIndent", {{ fg = "{sel_bg}" }})
  hi(0, "IblScope", {{ fg = "{grey}" }})
  hi(0, "IndentBlanklineChar", {{ fg = "{sel_bg}" }})

  -- WhichKey
  hi(0, "WhichKey", {{ fg = "{accent}" }})
  hi(0, "WhichKeyGroup", {{ fg = "{cyan}" }})
  hi(0, "WhichKeyDesc", {{ fg = "{fg}" }})
  hi(0, "WhichKeySeparator", {{ fg = "{grey}" }})
  hi(0, "WhichKeyBorder", {{ fg = "{border}" }})

  -- Neo-tree
  hi(0, "NeoTreeNormal", {{ bg = "NONE" }})
  hi(0, "NeoTreeNormalNC", {{ bg = "NONE" }})
  hi(0, "NeoTreeDirectoryName", {{ fg = "{accent}" }})
  hi(0, "NeoTreeDirectoryIcon", {{ fg = "{accent}" }})
  hi(0, "NeoTreeRootName", {{ fg = "{accent}", bold = true }})
  hi(0, "NeoTreeFileName", {{ fg = "{fg}" }})
  hi(0, "NeoTreeGitAdded", {{ fg = "{green}" }})
  hi(0, "NeoTreeGitModified", {{ fg = "{yellow}" }})
  hi(0, "NeoTreeGitDeleted", {{ fg = "{red}" }})
  hi(0, "NeoTreeGitUntracked", {{ fg = "{orange}" }})

  -- Notify / Noice
  hi(0, "NotifyINFOBorder", {{ fg = "{green}" }})
  hi(0, "NotifyWARNBorder", {{ fg = "{yellow}" }})
  hi(0, "NotifyERRORBorder", {{ fg = "{red}" }})
  hi(0, "NotifyINFOTitle", {{ fg = "{green}" }})
  hi(0, "NotifyWARNTitle", {{ fg = "{yellow}" }})
  hi(0, "NotifyERRORTitle", {{ fg = "{red}" }})
  hi(0, "NoiceCmdline", {{ fg = "{fg}" }})
  hi(0, "NoiceCmdlineBorder", {{ fg = "{border}" }})
  hi(0, "NoicePopup", {{ bg = "NONE" }})
  hi(0, "NoicePopupBorder", {{ fg = "{border}" }})

  -- Lazy
  hi(0, "LazyButton", {{ fg = "{fg}", bg = "{sel_bg}" }})
  hi(0, "LazyButtonActive", {{ fg = "#000000", bg = "{accent}" }})
  hi(0, "LazyH1", {{ fg = "#000000", bg = "{accent}", bold = true }})

  -- Flash (leap/hop)
  hi(0, "FlashLabel", {{ fg = "#000000", bg = "{yellow}", bold = true }})
  hi(0, "FlashMatch", {{ fg = "{br_accent}" }})

  -- Snacks (lazyvim notifications)
  hi(0, "SnacksNotifierBorderInfo", {{ fg = "{green}" }})
  hi(0, "SnacksNotifierBorderWarn", {{ fg = "{yellow}" }})
  hi(0, "SnacksNotifierBorderError", {{ fg = "{red}" }})
  hi(0, "SnacksNotifierTitleInfo", {{ fg = "{green}" }})
  hi(0, "SnacksNotifierTitleWarn", {{ fg = "{yellow}" }})
  hi(0, "SnacksNotifierTitleError", {{ fg = "{red}" }})
  hi(0, "SnacksDashboardHeader", {{ fg = "{accent}" }})
  hi(0, "SnacksDashboardKey", {{ fg = "{yellow}" }})
  hi(0, "SnacksDashboardDesc", {{ fg = "{fg}" }})
  hi(0, "SnacksDashboardIcon", {{ fg = "{accent}" }})

  -- LspReferenceText / Read / Write (word highlight under cursor)
  hi(0, "LspReferenceText", {{ bg = "{sel_bg}" }})
  hi(0, "LspReferenceRead", {{ bg = "{sel_bg}" }})
  hi(0, "LspReferenceWrite", {{ bg = "{sel_bg}" }})
  hi(0, "LspSignatureActiveParameter", {{ fg = "{yellow}", bold = true }})

  -- Refresh lualine theme (picks up new wallpaper.lua)
  pcall(function()
    package.loaded["lualine.themes.wallpaper"] = nil
    local theme = require("lualine.themes.wallpaper")
    require("lualine.highlight").create_highlight_groups(theme)
    vim.cmd("redrawstatus")
  end)
end

return M
"""
    atomic_write(_nvim_colors_path(), content)


def _write_lualine_theme(scheme):
    """Write lualine statusline theme synced to wallpaper."""
    fg = hex6(*scheme["light"])
    accent = hex6(*scheme["accent"])
    green = hex6(*scheme["green"])
    red = hex6(*scheme["red"])
    yellow = hex6(*scheme["yellow"])
    purple = hex6(*scheme["purple"])
    grey = hex6(*scheme["grey"])
    sel_bg = hex6(*scheme["item_bg"])

    content = f"""-- Auto-generated from wallpaper — do not edit manually
return {{
  normal = {{
    a = {{ bg = "{accent}", fg = "{fg}", gui = "bold" }},
    b = {{ bg = "{sel_bg}", fg = "{accent}" }},
    c = {{ bg = "{sel_bg}", fg = "{grey}" }},
  }},
  insert = {{
    a = {{ bg = "{green}", fg = "{fg}", gui = "bold" }},
    b = {{ bg = "{sel_bg}", fg = "{green}" }},
  }},
  visual = {{
    a = {{ bg = "{purple}", fg = "{fg}", gui = "bold" }},
    b = {{ bg = "{sel_bg}", fg = "{purple}" }},
  }},
  replace = {{
    a = {{ bg = "{red}", fg = "{fg}", gui = "bold" }},
    b = {{ bg = "{sel_bg}", fg = "{red}" }},
  }},
  command = {{
    a = {{ bg = "{yellow}", fg = "{fg}", gui = "bold" }},
    b = {{ bg = "{sel_bg}", fg = "{yellow}" }},
  }},
  terminal = {{
    a = {{ bg = "{green}", fg = "{fg}", gui = "bold" }},
    b = {{ bg = "{sel_bg}", fg = "{green}" }},
  }},
  inactive = {{
    a = {{ bg = "{sel_bg}", fg = "{grey}" }},
    b = {{ bg = "{sel_bg}", fg = "{grey}" }},
    c = {{ bg = "{sel_bg}", fg = "{grey}" }},
  }},
}}
"""
    atomic_write(_lualine_path(), content)
