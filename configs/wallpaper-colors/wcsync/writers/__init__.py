"""Writer registry — dispatches write_all to individual target writers."""

from ..config import Config
from ..utils import log

from . import (
    alacritty,
    btop,
    borders,
    ghostty,
    hydrotodo,
    iterm2,
    kitty,
    neovim,
    opencode,
    sketchybar,
    starship,
    tmux,
    wezterm,
    yazi,
)

# Registry: target name → module (must have a `write(scheme, config)` function)
_WRITERS = {
    "sketchybar": sketchybar,
    "borders": borders,
    "kitty": kitty,
    "wezterm": wezterm,
    "alacritty": alacritty,
    "ghostty": ghostty,
    "iterm2": iterm2,
    "tmux": tmux,
    "btop": btop,
    "neovim": neovim,
    "lualine": neovim,  # lualine is part of the neovim target toggle
    "yazi": yazi,
    "starship": starship,
    "opencode": opencode,
    "hydrotodo": hydrotodo,
}

def write_all(scheme, config=None):
    """Write all enabled config files.

    Each writer module exposes write(scheme, config). The config.targets
    dict controls which targets are enabled.
    """
    if config is None:
        config = Config()

    written = set()
    for name, mod in _WRITERS.items():
        # lualine follows the neovim toggle
        toggle_key = "neovim" if name == "lualine" else name
        if not config.targets.get(toggle_key, True):
            continue
        if mod in written:
            continue
        try:
            mod.write(scheme, config)
        except Exception as e:
            log(f"Writer {name} failed: {e}")
            continue
        written.add(mod)

    log(
        f"Wrote configs for: {', '.join(sorted(m.__name__.rsplit('.', 1)[-1] for m in written))}"
    )
