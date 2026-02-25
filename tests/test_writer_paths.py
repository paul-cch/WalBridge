import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

# Make wcsync importable from repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
WCSYNC_ROOT = REPO_ROOT / "configs" / "wallpaper-colors"
import sys

sys.path.insert(0, str(WCSYNC_ROOT))

from wcsync.writers import borders, yazi


SCHEME = {
    "accent": (1, 2, 3),
    "secondary": (4, 5, 6),
    "border_accent": (7, 8, 9),
    "border_secondary": (10, 11, 12),
    "dark": (13, 14, 15),
    "light": (220, 221, 222),
    "bar_bg": (16, 17, 18),
    "item_bg": (19, 20, 21),
    "grey": (22, 23, 24),
    "red": (25, 26, 27),
    "green": (28, 29, 30),
    "yellow": (31, 32, 33),
    "cyan": (34, 35, 36),
    "purple": (37, 38, 39),
    "orange": (40, 41, 42),
    "pink": (43, 44, 45),
}


class WriterPathOverrideTests(unittest.TestCase):
    def test_borders_writer_respects_output_override(self):
        with tempfile.TemporaryDirectory() as td:
            out_path = pathlib.Path(td) / "custom" / "border_colors"
            with patch.dict(os.environ, {"WALLPAPER_BORDER_COLORS_FILE": str(out_path)}):
                borders.write(SCHEME)

            self.assertTrue(out_path.is_file())
            text = out_path.read_text(encoding="utf-8")
            self.assertIn("0xff070809", text)
            self.assertIn("0xff0a0b0c", text)

    def test_yazi_writer_respects_explicit_output_override(self):
        with tempfile.TemporaryDirectory() as td:
            out_path = pathlib.Path(td) / "yazi" / "flavor.toml"
            with patch.dict(os.environ, {"WALLPAPER_YAZI_OUTPUT_PATH": str(out_path)}):
                yazi.write(SCHEME)

            self.assertTrue(out_path.is_file())
            text = out_path.read_text(encoding="utf-8")
            self.assertIn('[mgr]', text)

    def test_yazi_writer_uses_flavor_name_for_default_path(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            expected = home / ".config" / "yazi" / "flavors" / "sunset.yazi" / "flavor.toml"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_YAZI_FLAVOR_NAME": "sunset",
                },
                clear=False,
            ):
                yazi.write(SCHEME)

            self.assertTrue(expected.is_file())


if __name__ == "__main__":
    unittest.main()
