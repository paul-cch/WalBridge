import pathlib
import subprocess
import unittest
from unittest.mock import MagicMock, patch

# Make wcsync importable from repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
WCSYNC_ROOT = REPO_ROOT / "configs" / "wallpaper-colors"
import sys

sys.path.insert(0, str(WCSYNC_ROOT))

from wcsync import reloaders


class ReloadersTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
