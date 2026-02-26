import pathlib
import os
import tempfile
import unittest
from unittest.mock import patch

# Make wcsync importable from repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
WCSYNC_ROOT = REPO_ROOT / "configs" / "wallpaper-colors"
import sys

sys.path.insert(0, str(WCSYNC_ROOT))

from wcsync import utils


class UtilsTests(unittest.TestCase):
    def test_clamp_hexc_hex6(self):
        self.assertEqual(utils.clamp(300), 255)
        self.assertEqual(utils.clamp(-12), 0)
        self.assertEqual(utils.clamp(12.9), 12)
        self.assertEqual(utils.hexc(1, 2, 3), "0xff010203")
        self.assertEqual(utils.hexc(1, 2, 3, a=0x7F), "0x7f010203")
        self.assertEqual(utils.hex6(1, 2, 3), "#010203")

    def test_atomic_write_creates_parent_and_replaces(self):
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td) / "nested" / "file.txt"
            utils.atomic_write(str(out), "hello")
            self.assertEqual(out.read_text(encoding="utf-8"), "hello")

            utils.atomic_write(str(out), "world")
            self.assertEqual(out.read_text(encoding="utf-8"), "world")

    def test_atomic_write_cleans_temp_file_on_replace_failure(self):
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td) / "x" / "file.txt"
            with patch("wcsync.utils.os.replace", side_effect=RuntimeError("boom")):
                with self.assertRaises(RuntimeError):
                    utils.atomic_write(str(out), "content")

            tmp_files = list((out.parent if out.parent.exists() else pathlib.Path(td)).glob(".tmp_*"))
            self.assertEqual(tmp_files, [])

    def test_safe_home_path_accepts_only_home_descendants(self):
        with tempfile.TemporaryDirectory() as home_td:
            with patch.dict(os.environ, {"HOME": home_td}, clear=False):
                result = utils.safe_home_path(
                    "~/themes/wallpaper.conf",
                    "~/fallback.conf",
                    "WALLPAPER_TEST_PATH",
                )
        self.assertEqual(result, os.path.realpath(os.path.join(home_td, "themes/wallpaper.conf")))

    def test_safe_home_path_rejects_outside_home(self):
        with tempfile.TemporaryDirectory() as home_td, tempfile.TemporaryDirectory() as outside_td:
            with (
                patch.dict(os.environ, {"HOME": home_td}, clear=False),
                patch("wcsync.utils.log") as log_mock,
            ):
                result = utils.safe_home_path(
                    os.path.join(outside_td, "theme.conf"),
                    "~/fallback.conf",
                    "WALLPAPER_TEST_PATH",
                )

        self.assertEqual(result, os.path.realpath(os.path.join(home_td, "fallback.conf")))
        self.assertTrue(
            any("Ignoring WALLPAPER_TEST_PATH" in c.args[0] for c in log_mock.call_args_list if c.args)
        )

    def test_sanitize_name_and_filename(self):
        self.assertEqual(utils.sanitize_name("wallpaper_01", "default", "WALLPAPER_THEME"), "wallpaper_01")
        self.assertEqual(utils.sanitize_filename("theme.toml", "fallback.toml", "WALLPAPER_FILE"), "theme.toml")
        with patch("wcsync.utils.log") as log_mock:
            self.assertEqual(utils.sanitize_name("../../oops", "default", "WALLPAPER_THEME"), "default")
            self.assertEqual(utils.sanitize_filename("../oops.toml", "fallback.toml", "WALLPAPER_FILE"), "fallback.toml")
        self.assertTrue(
            any("WALLPAPER_THEME" in c.args[0] for c in log_mock.call_args_list if c.args)
        )
        self.assertTrue(
            any("WALLPAPER_FILE" in c.args[0] for c in log_mock.call_args_list if c.args)
        )


if __name__ == "__main__":
    unittest.main()
