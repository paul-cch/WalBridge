"""Service reload functions — push new colors to running applications."""

import glob
import os
import subprocess
import tempfile

from .config import Config
from .utils import hexc, log


def reload_sketchybar():
    """Reload SketchyBar config. Returns Popen for parallel wait."""
    return subprocess.Popen(
        ["/opt/homebrew/bin/sketchybar", "--reload"],
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
                    "/opt/homebrew/bin/kitten",
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
                    "/opt/homebrew/bin/nvim",
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
            "/opt/homebrew/bin/borders",
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

    if targets.get("sketchybar", True):
        procs.append(reload_sketchybar())
    if targets.get("kitty", True):
        procs.extend(reload_kitty())
    if targets.get("neovim", True):
        procs.extend(reload_nvim())
    if targets.get("borders", True):
        procs.append(reload_borders(scheme, config))

    # Yazi, Starship, OpenCode, HydroTodo — no hot-reload; applied on next launch/prompt
    for p in procs:
        p.wait()
