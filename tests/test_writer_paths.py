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

from wcsync.writers import alacritty, borders, ghostty, wezterm, yazi


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
            with patch.dict(
                os.environ,
                {
                    "WALLPAPER_YAZI_OUTPUT_PATH": str(out_path),
                    "WALLPAPER_YAZI_WRITE_THEME_SELECTOR": "0",
                },
            ):
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

    def test_yazi_writer_writes_theme_selector_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            selector = home / ".config" / "yazi" / "theme.toml"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_YAZI_FLAVOR_NAME": "sunset",
                },
                clear=False,
            ):
                yazi.write(SCHEME)

            self.assertTrue(selector.is_file())
            text = selector.read_text(encoding="utf-8")
            self.assertIn('dark = "sunset"', text)
            self.assertIn('light = "sunset"', text)

    def test_yazi_writer_preserves_custom_theme_selector(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            selector = home / ".config" / "yazi" / "theme.toml"
            selector.parent.mkdir(parents=True, exist_ok=True)
            selector.write_text("[flavor]\ndark = \"custom\"\n", encoding="utf-8")

            fallback = home / ".config" / "wallpaper-colors" / "yazi.theme.toml"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_YAZI_FLAVOR_NAME": "sunset",
                },
                clear=False,
            ):
                yazi.write(SCHEME)

            self.assertTrue(selector.is_file())
            self.assertIn("custom", selector.read_text(encoding="utf-8"))
            self.assertTrue(fallback.is_file())
            self.assertIn('dark = "sunset"', fallback.read_text(encoding="utf-8"))

    def test_wezterm_writer_uses_scheme_name_for_default_path(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            expected = home / ".config" / "wezterm" / "colors" / "sunset.toml"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_WEZTERM_SCHEME_NAME": "sunset",
                },
                clear=False,
            ):
                wezterm.write(SCHEME)

            self.assertTrue(expected.is_file())
            self.assertIn('name = "sunset"', expected.read_text(encoding="utf-8"))

    def test_alacritty_writer_respects_output_override(self):
        with tempfile.TemporaryDirectory() as td:
            out_path = pathlib.Path(td) / "alacritty" / "wallpaper.toml"
            with patch.dict(os.environ, {"WALLPAPER_ALACRITTY_OUTPUT_PATH": str(out_path)}):
                alacritty.write(SCHEME)

            self.assertTrue(out_path.is_file())
            self.assertIn("[colors.primary]", out_path.read_text(encoding="utf-8"))

    def test_ghostty_writer_respects_output_override(self):
        with tempfile.TemporaryDirectory() as td:
            out_path = pathlib.Path(td) / "ghostty" / "wallpaper.conf"
            with patch.dict(os.environ, {"WALLPAPER_GHOSTTY_OUTPUT_PATH": str(out_path)}):
                ghostty.write(SCHEME)

            self.assertTrue(out_path.is_file())
            text = out_path.read_text(encoding="utf-8")
            self.assertIn("palette = 0=", text)
            self.assertIn("background =", text)


if __name__ == "__main__":
    unittest.main()
