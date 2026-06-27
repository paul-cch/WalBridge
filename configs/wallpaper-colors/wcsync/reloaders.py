"""Hot reload functions — push new colors to running Target Apps."""

import glob
import os
import subprocess
import shutil
import tempfile

from .config import Config
from .target_apps import enabled_target_apps, target_path
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


def reload_sketchybar(scheme=None, config=None):
    """Reload SketchyBar config. Returns Popen for parallel wait."""
    return subprocess.Popen(
        [_find_bin("sketchybar"), "--reload"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def reload_kitty(scheme=None, config=None):
    """Live-reload Kitty colors via remote control. Returns list of Popen."""
    procs = []
    colors_path = target_path("kitty")
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
                    colors_path,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        )
    return procs


def reload_nvim(scheme=None, config=None):
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


def reload_tmux(scheme=None, config=None):
    """Hot-reload tmux theme include when a tmux server is running."""
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
            [tmux_bin, "source-file", target_path("tmux")],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    ]


def reload_borders(scheme, config=None):
    """Push new active_color to running borders via IPC. Returns Popen."""
    if config is None:
        config = Config()

    accent = hexc(*scheme["border_accent"], a=config.border_opacity)
    inactive_rgb = scheme.get("border_inactive") or scheme.get("grey", scheme["border_accent"])
    inactive = hexc(*inactive_rgb, a=config.border_inactive_opacity)
    return subprocess.Popen(
        [
            _find_bin("borders"),
            "width=3.0",
            f"active_color={accent}",
            f"inactive_color={inactive}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def reload_all(scheme, config=None):
    """Hot-reload all enabled Target Apps in parallel.

    Returns after all child processes have finished.
    """
    if config is None:
        config = Config()

    procs = []
    for app in enabled_target_apps(config):
        try:
            procs.extend(app.reload(scheme, config))
        except FileNotFoundError as e:
            log(f"Skipping {app.name} reload: {e}")

    for p in procs:
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            log(f"Reload process {p.args[0]} timed out, killing")
            p.kill()
