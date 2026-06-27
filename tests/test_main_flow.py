import pathlib
import types
import unittest
from unittest.mock import MagicMock, call, mock_open, patch

from PIL import Image

# Make wcsync/wallpaper_colors importable from repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
WCSYNC_ROOT = REPO_ROOT / "configs" / "wallpaper-colors"
import sys

sys.path.insert(0, str(WCSYNC_ROOT))

# Provide a lightweight Quartz stub for non-macOS test environments.
if "Quartz" not in sys.modules:
    sys.modules["Quartz"] = types.SimpleNamespace()

import wallpaper_colors
from wcsync.config import Config
from wcsync import sync_run
from wcsync.sync_run import SyncRunError, SyncRunOptions


class SyncRunTests(unittest.TestCase):
    def test_run_sync_raises_when_wallpaper_load_fails(self):
        with (
            patch("wcsync.sync_run.Config.load", return_value=Config()),
            patch("wcsync.sync_run.load_wallpaper", return_value=(None, "")),
            patch("wcsync.sync_run.write_all") as write_all_mock,
        ):
            with self.assertRaises(SyncRunError):
                sync_run.run_sync()

        write_all_mock.assert_not_called()

    def test_run_sync_skips_unchanged_before_resize(self):
        img = MagicMock()
        img.size = (3840, 2160)
        with (
            patch("wcsync.sync_run.Config.load", return_value=Config()),
            patch("wcsync.sync_run.load_wallpaper", return_value=(img, "/tmp/wall.jpg")),
            patch("wcsync.sync_run.image_hash", return_value="samehash"),
            patch("wcsync.sync_run.config_signature", return_value="sig"),
            patch("wcsync.sync_run.os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="samehash:sig")),
            patch("wcsync.sync_run.write_all") as write_all_mock,
            patch("wcsync.sync_run.reload_all") as reload_all_mock,
            patch("wcsync.sync_run.atomic_write") as atomic_write_mock,
            patch("wcsync.sync_run.subprocess.run") as run_mock,
        ):
            result = sync_run.run_sync()

        self.assertTrue(result.skipped)
        img.resize.assert_not_called()
        write_all_mock.assert_not_called()
        reload_all_mock.assert_not_called()
        atomic_write_mock.assert_not_called()
        run_mock.assert_not_called()

    def test_run_sync_reruns_when_config_signature_changes(self):
        img = MagicMock()
        img.size = (1920, 1080)
        small = MagicMock()
        img.resize.return_value = small
        cfg = Config()
        scheme = {
            "accent": (1, 2, 3),
            "secondary": (4, 5, 6),
            "dark": (7, 8, 9),
            "light": (10, 11, 12),
            "border_accent": (13, 14, 15),
            "border_inactive": (16, 17, 18),
        }

        with (
            patch("wcsync.sync_run.Config.load", return_value=cfg),
            patch("wcsync.sync_run.load_wallpaper", return_value=(img, "/tmp/wall.jpg")),
            patch("wcsync.sync_run.image_hash", return_value="samehash"),
            patch("wcsync.sync_run.config_signature", return_value="new-sig"),
            patch("wcsync.sync_run.os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="samehash:old-sig")),
            patch("wcsync.sync_run.extract_palette", return_value=[(1, 2, 3)]),
            patch("wcsync.sync_run.build_scheme", return_value=scheme),
            patch("wcsync.sync_run.write_all", return_value=[]) as write_all_mock,
            patch("wcsync.sync_run.reload_all") as reload_all_mock,
            patch("wcsync.sync_run.atomic_write") as atomic_write_mock,
            patch("wcsync.sync_run.subprocess.run"),
        ):
            result = sync_run.run_sync()

        self.assertFalse(result.skipped)
        img.resize.assert_called_once_with((200, 200), Image.Resampling.LANCZOS)
        write_all_mock.assert_called_once_with(scheme, cfg)
        reload_all_mock.assert_called_once_with(scheme, cfg)
        atomic_write_mock.assert_any_call(sync_run.CACHE_FILE, "samehash:new-sig")

    def test_run_sync_force_runs_full_lifecycle(self):
        img = MagicMock()
        img.size = (1920, 1080)
        small = MagicMock()
        img.resize.return_value = small
        cfg = Config()
        scheme = {
            "accent": (1, 2, 3),
            "secondary": (4, 5, 6),
            "dark": (7, 8, 9),
            "light": (10, 11, 12),
            "border_accent": (13, 14, 15),
            "border_inactive": (16, 17, 18),
        }

        with (
            patch("wcsync.sync_run.Config.load", return_value=cfg),
            patch("wcsync.sync_run.load_wallpaper", return_value=(img, "/tmp/wall.jpg")),
            patch("wcsync.sync_run.image_hash", return_value="newhash"),
            patch("wcsync.sync_run.config_signature", return_value="sig"),
            patch("wcsync.sync_run.extract_palette", return_value=[(1, 2, 3)]) as extract_mock,
            patch("wcsync.sync_run.build_scheme", return_value=scheme) as build_mock,
            patch("wcsync.sync_run.write_all", return_value=[]) as write_all_mock,
            patch("wcsync.sync_run.reload_all") as reload_all_mock,
            patch("wcsync.sync_run.atomic_write") as atomic_write_mock,
            patch("wcsync.sync_run.subprocess.run") as run_mock,
        ):
            result = sync_run.run_sync(SyncRunOptions(force=True))

        self.assertFalse(result.skipped)
        img.resize.assert_called_once_with((200, 200), Image.Resampling.LANCZOS)
        run_mock.assert_called_once_with([sync_run.DESKTOPPR, "/tmp/wall.jpg"], capture_output=True)
        extract_mock.assert_called_once_with(small, n_colors=cfg.n_colors)
        build_mock.assert_called_once_with([(1, 2, 3)], cfg)
        write_all_mock.assert_called_once_with(scheme, cfg)
        reload_all_mock.assert_called_once_with(scheme, cfg)
        atomic_write_mock.assert_has_calls(
            [
                call(sync_run.CACHE_FILE, "newhash:sig"),
                call(sync_run.LAST_WP_FILE, "/tmp/wall.jpg"),
            ],
            any_order=False,
        )

    def test_run_sync_raises_without_cache_when_writer_fails(self):
        img = MagicMock()
        img.size = (1920, 1080)
        img.resize.return_value = MagicMock()
        cfg = Config()

        with (
            patch("wcsync.sync_run.Config.load", return_value=cfg),
            patch("wcsync.sync_run.load_wallpaper", return_value=(img, "/tmp/wall.jpg")),
            patch("wcsync.sync_run.image_hash", return_value="newhash"),
            patch("wcsync.sync_run.config_signature", return_value="sig"),
            patch("wcsync.sync_run.extract_palette", return_value=[(1, 2, 3)]),
            patch("wcsync.sync_run.build_scheme", return_value={"border_accent": (13, 14, 15)}),
            patch("wcsync.sync_run.write_all", return_value=["kitty"]),
            patch("wcsync.sync_run.reload_all") as reload_all_mock,
            patch("wcsync.sync_run.atomic_write") as atomic_write_mock,
            patch("wcsync.sync_run.subprocess.run") as run_mock,
        ):
            with self.assertRaises(SyncRunError):
                sync_run.run_sync(SyncRunOptions(force=True))

        atomic_write_mock.assert_not_called()
        reload_all_mock.assert_not_called()
        run_mock.assert_called_once_with([sync_run.DESKTOPPR, "/tmp/wall.jpg"], capture_output=True)


class WallpaperColorsCliTests(unittest.TestCase):
    def test_options_from_argv_maps_flags(self):
        self.assertEqual(
            wallpaper_colors.options_from_argv(["--verbose", "-f"]),
            SyncRunOptions(verbose=True, force=True),
        )

    def test_main_returns_zero_when_sync_run_succeeds(self):
        with (
            patch.object(wallpaper_colors.sys, "argv", ["wallpaper_colors.py"]),
            patch("wallpaper_colors.run_sync") as run_mock,
        ):
            result = wallpaper_colors.main()

        self.assertEqual(result, 0)
        run_mock.assert_called_once_with(SyncRunOptions())

    def test_main_returns_one_when_sync_run_fails(self):
        with (
            patch.object(wallpaper_colors.sys, "argv", ["wallpaper_colors.py"]),
            patch("wallpaper_colors.run_sync", side_effect=SyncRunError("bad")),
        ):
            result = wallpaper_colors.main()

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
