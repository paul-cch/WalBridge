import pathlib
import os
import subprocess
import unittest
from unittest.mock import MagicMock, patch

# Make wcsync importable from repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
WCSYNC_ROOT = REPO_ROOT / "configs" / "wallpaper-colors"
import sys

sys.path.insert(0, str(WCSYNC_ROOT))

from wcsync import reloaders
from wcsync.config import Config


class ReloadersTests(unittest.TestCase):
    def test_reload_borders_sets_active_and_inactive_colors(self):
        proc = MagicMock()
        cfg = Config(border_opacity=0xB3, border_inactive_opacity=0x66)
        scheme = {"border_accent": (7, 8, 9), "border_inactive": (20, 30, 40), "grey": (50, 60, 70)}

        with (
            patch("wcsync.reloaders._find_bin", return_value="/usr/bin/borders"),
            patch("wcsync.reloaders.subprocess.Popen", return_value=proc) as popen_mock,
        ):
            result = reloaders.reload_borders(scheme, cfg)

        self.assertEqual(result, proc)
        popen_mock.assert_called_once_with(
            [
                "/usr/bin/borders",
                "width=3.0",
                "active_color=0xb3070809",
                "inactive_color=0x66141e28",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def test_reload_tmux_skips_when_no_session(self):
        with (
            patch("wcsync.reloaders._find_bin", return_value="/usr/bin/tmux"),
            patch(
                "wcsync.reloaders.subprocess.run",
                return_value=subprocess.CompletedProcess(args=[], returncode=1),
            ),
            patch("wcsync.reloaders.subprocess.Popen") as popen_mock,
        ):
            procs = reloaders.reload_tmux()

        self.assertEqual(procs, [])
        popen_mock.assert_not_called()

    def test_reload_tmux_sources_theme_when_session_exists(self):
        fake_proc = MagicMock()
        with (
            patch("wcsync.reloaders._find_bin", return_value="/usr/bin/tmux"),
            patch(
                "wcsync.reloaders.subprocess.run",
                return_value=subprocess.CompletedProcess(args=[], returncode=0),
            ),
            patch("wcsync.writers.tmux.output_path", return_value="/tmp/wallpaper.conf"),
            patch("wcsync.reloaders.subprocess.Popen", return_value=fake_proc) as popen_mock,
        ):
            procs = reloaders.reload_tmux()

        self.assertEqual(procs, [fake_proc])
        popen_mock.assert_called_once_with(
            ["/usr/bin/tmux", "source-file", "/tmp/wallpaper.conf"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def test_reload_kitty_uses_writer_output_path(self):
        p1 = MagicMock()
        p2 = MagicMock()
        with (
            patch("wcsync.reloaders.glob.glob", return_value=["/tmp/kitty-sock-a", "/tmp/kitty-sock-b"]),
            patch("wcsync.reloaders._find_bin", return_value="/usr/bin/kitten"),
            patch("wcsync.writers.kitty.output_path", return_value="/tmp/wallpaper.conf"),
            patch("wcsync.reloaders.subprocess.Popen", side_effect=[p1, p2]) as popen_mock,
        ):
            procs = reloaders.reload_kitty()

        self.assertEqual(procs, [p1, p2])
        self.assertEqual(popen_mock.call_count, 2)
        first_cmd = popen_mock.call_args_list[0].args[0]
        self.assertEqual(first_cmd[0], "/usr/bin/kitten")
        self.assertEqual(first_cmd[-1], "/tmp/wallpaper.conf")

    def test_reload_nvim_uses_discovered_sockets(self):
        proc = MagicMock()
        with (
            patch.dict(os.environ, {"USER": "alice"}, clear=False),
            patch("wcsync.reloaders.tempfile.gettempdir", return_value="/tmp"),
            patch("wcsync.reloaders.glob.glob", return_value=["/tmp/nvim.alice/x/nvim.123.0"]),
            patch("wcsync.reloaders._find_bin", return_value="/usr/bin/nvim"),
            patch("wcsync.reloaders.subprocess.Popen", return_value=proc) as popen_mock,
        ):
            procs = reloaders.reload_nvim()

        self.assertEqual(procs, [proc])
        cmd = popen_mock.call_args.args[0]
        self.assertEqual(cmd[0], "/usr/bin/nvim")
        self.assertEqual(cmd[1:3], ["--server", "/tmp/nvim.alice/x/nvim.123.0"])

    def test_reload_all_respects_targets_and_kills_timeout(self):
        cfg = Config()
        cfg.targets = {k: False for k in cfg.targets}
        cfg.targets.update({"sketchybar": True, "kitty": True})

        fast_proc = MagicMock()
        fast_proc.args = ["sketchybar"]
        slow_proc = MagicMock()
        slow_proc.args = ["kitten"]
        slow_proc.wait.side_effect = subprocess.TimeoutExpired(cmd="kitten", timeout=5)

        with (
            patch("wcsync.reloaders.reload_sketchybar", return_value=fast_proc) as sketch_mock,
            patch("wcsync.reloaders.reload_kitty", return_value=[slow_proc]) as kitty_mock,
            patch("wcsync.reloaders.reload_nvim") as nvim_mock,
            patch("wcsync.reloaders.reload_tmux") as tmux_mock,
            patch("wcsync.reloaders.reload_borders") as borders_mock,
            patch("wcsync.reloaders.log") as log_mock,
        ):
            reloaders.reload_all({"border_accent": (1, 2, 3)}, cfg)

        sketch_mock.assert_called_once()
        kitty_mock.assert_called_once()
        nvim_mock.assert_not_called()
        tmux_mock.assert_not_called()
        borders_mock.assert_not_called()
        fast_proc.wait.assert_called_once_with(timeout=5)
        slow_proc.kill.assert_called_once()
        self.assertTrue(any("timed out" in c.args[0] for c in log_mock.call_args_list if c.args))

    def test_reload_all_triggers_neovim_and_borders(self):
        cfg = Config()
        cfg.targets = {k: False for k in cfg.targets}
        cfg.targets.update({"neovim": True, "borders": True})

        nvim_proc = MagicMock()
        nvim_proc.args = ["nvim"]
        borders_proc = MagicMock()
        borders_proc.args = ["borders"]

        with (
            patch("wcsync.reloaders.reload_nvim", return_value=[nvim_proc]) as nvim_mock,
            patch("wcsync.reloaders.reload_borders", return_value=borders_proc) as borders_mock,
        ):
            reloaders.reload_all({"border_accent": (1, 2, 3)}, cfg)

        nvim_mock.assert_called_once()
        borders_mock.assert_called_once_with({"border_accent": (1, 2, 3)}, cfg)
        nvim_proc.wait.assert_called_once_with(timeout=5)
        borders_proc.wait.assert_called_once_with(timeout=5)

    def test_reload_all_logs_and_skips_missing_binary(self):
        cfg = Config()
        cfg.targets = {k: False for k in cfg.targets}
        cfg.targets["sketchybar"] = True

        with (
            patch("wcsync.reloaders.reload_sketchybar", side_effect=FileNotFoundError("missing")),
            patch("wcsync.reloaders.log") as log_mock,
        ):
            reloaders.reload_all({"border_accent": (1, 2, 3)}, cfg)

        self.assertTrue(
            any("Skipping sketchybar reload" in c.args[0] for c in log_mock.call_args_list if c.args)
        )


if __name__ == "__main__":
    unittest.main()
