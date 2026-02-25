"""Service reload functions — push new colors to running applications."""

import glob
import os
import subprocess
import shutil
import tempfile

from .config import Config
from .utils import hexc, log

def _find_bin(name):
    """Locate binary on PATH, falling back to common Homebrew locations."""
    path = shutil.which(name)
    if path:
        return path
    for prefix in ("/opt/homebrew/bin", "/usr/local/bin"):
        candidate = os.path.join(prefix, name)
        if os.path.isfile(candidate):
            return candidate
    return name  # let subprocess raise a descriptive FileNotFoundError


def reload_sketchybar():
    """Reload SketchyBar config. Returns Popen for parallel wait."""
    return subprocess.Popen(
        [_find_bin("sketchybar"), "--reload"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def reload_kitty():
    """Live-reload Kitty colors via remote control. Returns list of Popen."""
    from .writers.kitty import OUTPUT_PATH

    procs = []
    for sock in glob.glob("/tmp/kitty-sock-*"):
        procs.append(
            subprocess.Popen(
                [
                    _find_bin("kitten"),
                    "@",
                    "--to",
                    f"unix:{sock}",
                    "set-colors",
                    "-a",
                    "-c",
                    OUTPUT_PATH,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        )
    return procs


def reload_nvim():
    """Live-reload Neovim colors in all running instances. Returns list of Popen."""
    procs = []
    user = os.environ.get("USER", "")
    sock_dir = os.path.join(tempfile.gettempdir(), f"nvim.{user}")
    lua_cmd = "lua package.loaded['nvim_colors'] = nil; require('nvim_colors').apply()"
    for sock in glob.glob(os.path.join(sock_dir, "*/nvim.*.0")):
        procs.append(
            subprocess.Popen(
                [
                    _find_bin("nvim"),
                    "--server",
                    sock,
                    "--remote-expr",
                    f'execute("{lua_cmd}")',
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        )
    return procs


def reload_tmux():
    """Hot-reload tmux theme include when a tmux server is running."""
    from .writers.tmux import output_path

    tmux_bin = _find_bin("tmux")
    has_session = subprocess.run(
        [tmux_bin, "list-sessions"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if has_session.returncode != 0:
        return []

    return [
        subprocess.Popen(
            [tmux_bin, "source-file", output_path()],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    ]


def reload_borders(scheme, config=None):
    """Push new gradient to running borders-animated via IPC. Returns Popen.

    Uses the homebrew borders binary — it shares the same mach port as
    borders-animated so it can send IPC without the heavyweight init
    that caused flicker when spawning a second borders-animated.
    """
    if config is None:
        config = Config()

    opacity = config.border_opacity
    accent = hexc(*scheme["border_accent"], a=opacity)
    secondary = hexc(*scheme["border_secondary"], a=opacity)
    return subprocess.Popen(
        [
            _find_bin("borders"),
            "width=3.0",
            f"active_color=gradient(top_left={accent},bottom_right={secondary})",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def reload_all(scheme, config=None):
    """Reload all enabled services in parallel.

    Returns after all child processes have finished.
    """
    if config is None:
        config = Config()

    targets = config.targets
    procs = []

    reloaders = []
    if targets.get("sketchybar", True):
        reloaders.append(("sketchybar", lambda: [reload_sketchybar()]))
    if targets.get("kitty", True):
        reloaders.append(("kitty", lambda: reload_kitty()))
    if targets.get("neovim", True):
        reloaders.append(("neovim", lambda: reload_nvim()))
    if targets.get("tmux", True):
        reloaders.append(("tmux", lambda: reload_tmux()))
    if targets.get("borders", True):
        reloaders.append(("borders", lambda s=scheme, c=config: [reload_borders(s, c)]))

    for name, fn in reloaders:
        try:
            procs.extend(fn())
        except FileNotFoundError as e:
            log(f"Skipping {name} reload: {e}")

    # Yazi, Starship, OpenCode, HydroTodo, WezTerm, Alacritty, Ghostty,
    # iTerm2, btop — no direct hot-reload here; applied on next
    # launch/reload/prompt. tmux is hot-reloaded when a server exists.
    for p in procs:
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            log(f"Reload process {p.args[0]} timed out, killing")
            p.kill()
