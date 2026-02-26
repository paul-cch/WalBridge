"""Writer registry — dispatches write_all to individual target writers."""

from concurrent.futures import ThreadPoolExecutor, as_completed

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

    enabled = [(name, mod) for name, mod in _WRITERS.items() if config.targets.get(name, True)]
    written = set()
    failed = []

    if enabled:
        with ThreadPoolExecutor(max_workers=min(8, len(enabled))) as pool:
            futures = {pool.submit(mod.write, scheme, config): (name, mod) for name, mod in enabled}
            for fut in as_completed(futures):
                name, mod = futures[fut]
                try:
                    fut.result()
                except Exception as e:
                    log(f"Writer {name} failed: {e}")
                    failed.append(name)
                    continue
                written.add(mod)

    log(
        f"Wrote configs for: {', '.join(sorted(m.__name__.rsplit('.', 1)[-1] for m in written))}"
    )
    return failed
