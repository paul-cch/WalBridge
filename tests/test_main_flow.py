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


class MainFlowTests(unittest.TestCase):
    def test_main_exits_when_wallpaper_load_fails(self):
        with (
            patch("wallpaper_colors.Config.load", return_value=Config()),
            patch("wallpaper_colors.load_wallpaper", return_value=(None, "")),
            patch("wallpaper_colors.write_all") as write_all_mock,
            patch("wallpaper_colors.sys.exit", side_effect=SystemExit(1)),
        ):
            with self.assertRaises(SystemExit):
                wallpaper_colors.main()

        write_all_mock.assert_not_called()

    def test_main_skips_unchanged_before_resize(self):
        img = MagicMock()
        img.size = (3840, 2160)
        with (
            patch("wallpaper_colors.Config.load", return_value=Config()),
            patch("wallpaper_colors.load_wallpaper", return_value=(img, "/tmp/wall.jpg")),
            patch("wallpaper_colors.image_hash", return_value="samehash"),
            patch("wallpaper_colors.os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="samehash")),
            patch("wallpaper_colors.write_all") as write_all_mock,
            patch("wallpaper_colors.reload_all") as reload_all_mock,
            patch("wallpaper_colors.atomic_write") as atomic_write_mock,
            patch("wallpaper_colors.subprocess.run") as run_mock,
        ):
            wallpaper_colors.main()

        img.resize.assert_not_called()
        write_all_mock.assert_not_called()
        reload_all_mock.assert_not_called()
        atomic_write_mock.assert_not_called()
        run_mock.assert_not_called()

    def test_main_force_runs_full_pipeline(self):
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
            patch.object(wallpaper_colors.sys, "argv", ["wallpaper_colors.py", "--force"]),
            patch("wallpaper_colors.Config.load", return_value=cfg),
            patch("wallpaper_colors.load_wallpaper", return_value=(img, "/tmp/wall.jpg")),
            patch("wallpaper_colors.image_hash", return_value="newhash"),
            patch("wallpaper_colors.extract_palette", return_value=[(1, 2, 3)]) as extract_mock,
            patch("wallpaper_colors.build_scheme", return_value=scheme) as build_mock,
            patch("wallpaper_colors.write_all", return_value=[]) as write_all_mock,
            patch("wallpaper_colors.reload_all") as reload_all_mock,
            patch("wallpaper_colors.atomic_write") as atomic_write_mock,
            patch("wallpaper_colors.subprocess.run") as run_mock,
        ):
            wallpaper_colors.main()

        img.resize.assert_called_once_with((200, 200), Image.Resampling.LANCZOS)
        run_mock.assert_called_once_with([wallpaper_colors.DESKTOPPR, "/tmp/wall.jpg"], capture_output=True)
        extract_mock.assert_called_once_with(small, n_colors=cfg.n_colors)
        build_mock.assert_called_once_with([(1, 2, 3)], cfg)
        write_all_mock.assert_called_once_with(scheme, cfg)
        reload_all_mock.assert_called_once_with(scheme, cfg)
        atomic_write_mock.assert_has_calls(
            [
                call(wallpaper_colors.CACHE_FILE, "newhash"),
                call(wallpaper_colors.LAST_WP_FILE, "/tmp/wall.jpg"),
            ],
            any_order=False,
        )

    def test_main_exits_without_cache_when_writer_fails(self):
        img = MagicMock()
        img.size = (1920, 1080)
        img.resize.return_value = MagicMock()
        cfg = Config()

        with (
            patch.object(wallpaper_colors.sys, "argv", ["wallpaper_colors.py", "--force"]),
            patch("wallpaper_colors.Config.load", return_value=cfg),
            patch("wallpaper_colors.load_wallpaper", return_value=(img, "/tmp/wall.jpg")),
            patch("wallpaper_colors.image_hash", return_value="newhash"),
            patch("wallpaper_colors.extract_palette", return_value=[(1, 2, 3)]),
            patch("wallpaper_colors.build_scheme", return_value={"border_accent": (13, 14, 15)}),
            patch("wallpaper_colors.write_all", return_value=["kitty"]),
            patch("wallpaper_colors.reload_all") as reload_all_mock,
            patch("wallpaper_colors.atomic_write") as atomic_write_mock,
            patch("wallpaper_colors.subprocess.run") as run_mock,
            patch("wallpaper_colors.sys.exit", side_effect=SystemExit(1)),
        ):
            with self.assertRaises(SystemExit):
                wallpaper_colors.main()

        atomic_write_mock.assert_not_called()
        reload_all_mock.assert_not_called()
        run_mock.assert_called_once_with([wallpaper_colors.DESKTOPPR, "/tmp/wall.jpg"], capture_output=True)


if __name__ == "__main__":
    unittest.main()
