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

from wcsync.writers import alacritty, borders, btop, ghostty, iterm2, tmux, wezterm, yazi
from wcsync.writers import hydrotodo, kitty, neovim, opencode, sketchybar, starship


SCHEME = {
    "accent": (1, 2, 3),
    "secondary": (4, 5, 6),
    "border_accent": (7, 8, 9),
    "border_inactive": (10, 11, 12),
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
    def test_sketchybar_writer_respects_output_override(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            out_path = home / "sketchybar" / "colors.sh"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_SKETCHYBAR_OUTPUT_PATH": str(out_path),
                },
                clear=False,
            ):
                sketchybar.write(SCHEME)

            self.assertTrue(out_path.is_file())
            self.assertIn("export BLUE=", out_path.read_text(encoding="utf-8"))

    def test_kitty_writer_respects_output_override(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            out_path = home / "kitty" / "wallpaper.conf"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_KITTY_OUTPUT_PATH": str(out_path),
                },
                clear=False,
            ):
                kitty.write(SCHEME)

            self.assertTrue(out_path.is_file())
            self.assertIn("background #", out_path.read_text(encoding="utf-8"))

    def test_neovim_writer_respects_output_overrides(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            colors_path = home / "nvim" / "nvim_colors.lua"
            lualine_path = home / "nvim" / "wallpaper.lua"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_NVIM_COLORS_PATH": str(colors_path),
                    "WALLPAPER_LUALINE_PATH": str(lualine_path),
                },
                clear=False,
            ):
                neovim.write(SCHEME)

            self.assertTrue(colors_path.is_file())
            self.assertTrue(lualine_path.is_file())
            self.assertIn("function M.apply()", colors_path.read_text(encoding="utf-8"))
            self.assertIn("return {", lualine_path.read_text(encoding="utf-8"))

    def test_starship_writer_respects_output_override(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            out_path = home / "starship" / "starship.toml"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_STARSHIP_OUTPUT_PATH": str(out_path),
                },
                clear=False,
            ):
                starship.write(SCHEME)

            self.assertTrue(out_path.is_file())
            self.assertIn("Auto-generated from wallpaper", out_path.read_text(encoding="utf-8"))

    def test_starship_writer_respects_fallback_override(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            target = home / "starship" / "starship.toml"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("[character]\nsuccess_symbol='>'\n", encoding="utf-8")
            fallback = home / "wallpaper-colors" / "starship.generated.toml"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_STARSHIP_OUTPUT_PATH": str(target),
                    "WALLPAPER_STARSHIP_FALLBACK_PATH": str(fallback),
                },
                clear=False,
            ):
                starship.write(SCHEME)

            self.assertTrue(target.is_file())
            self.assertIn("success_symbol='>'", target.read_text(encoding="utf-8"))
            self.assertTrue(fallback.is_file())
            self.assertIn("Auto-generated from wallpaper", fallback.read_text(encoding="utf-8"))

    def test_opencode_writer_respects_output_override(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            out_path = home / "opencode" / "wallpaper.json"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_OPENCODE_OUTPUT_PATH": str(out_path),
                },
                clear=False,
            ):
                opencode.write(SCHEME)

            self.assertTrue(out_path.is_file())
            self.assertIn('"$schema"', out_path.read_text(encoding="utf-8"))

    def test_hydrotodo_writer_respects_output_override(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            out_path = home / "hydrotodo" / "colors.json"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_HYDROTODO_OUTPUT_PATH": str(out_path),
                },
                clear=False,
            ):
                hydrotodo.write(SCHEME)

            self.assertTrue(out_path.is_file())
            self.assertIn('"accent"', out_path.read_text(encoding="utf-8"))

    def test_borders_writer_respects_output_override(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            out_path = home / "custom" / "border_colors"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_BORDER_COLORS_FILE": str(out_path),
                },
                clear=False,
            ):
                borders.write(SCHEME)

            self.assertTrue(out_path.is_file())
            text = out_path.read_text(encoding="utf-8")
            self.assertIn("active_color=0xff070809", text)
            self.assertIn("inactive_color=0xff0a0b0c", text)

    def test_yazi_writer_respects_explicit_output_override(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            out_path = home / "yazi" / "flavor.toml"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_YAZI_OUTPUT_PATH": str(out_path),
                    "WALLPAPER_YAZI_WRITE_THEME_SELECTOR": "0",
                },
                clear=False,
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
            home = pathlib.Path(td)
            out_path = home / "alacritty" / "wallpaper.toml"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_ALACRITTY_OUTPUT_PATH": str(out_path),
                },
                clear=False,
            ):
                alacritty.write(SCHEME)

            self.assertTrue(out_path.is_file())
            self.assertIn("[colors.primary]", out_path.read_text(encoding="utf-8"))

    def test_ghostty_writer_respects_output_override(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            out_path = home / "ghostty" / "wallpaper.conf"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_GHOSTTY_OUTPUT_PATH": str(out_path),
                },
                clear=False,
            ):
                ghostty.write(SCHEME)

            self.assertTrue(out_path.is_file())
            text = out_path.read_text(encoding="utf-8")
            self.assertIn("palette = 0=", text)
            self.assertIn("background =", text)

    def test_iterm2_writer_respects_output_override(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            out_path = home / "iterm2" / "wallpaper.itermcolors"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_ITERM_OUTPUT_PATH": str(out_path),
                },
                clear=False,
            ):
                iterm2.write(SCHEME)

            self.assertTrue(out_path.is_file())
            text = out_path.read_text(encoding="utf-8")
            self.assertIn("<key>Background Color</key>", text)
            self.assertIn("<key>Ansi 15 Color</key>", text)

    def test_tmux_writer_respects_output_override(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            out_path = home / "tmux" / "wallpaper.conf"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_TMUX_OUTPUT_PATH": str(out_path),
                },
                clear=False,
            ):
                tmux.write(SCHEME)

            self.assertTrue(out_path.is_file())
            text = out_path.read_text(encoding="utf-8")
            self.assertIn('set -g status-style "fg=', text)
            self.assertIn("source-file ~/.config/tmux/themes/wallpaper.conf", text)

    def test_btop_writer_uses_theme_name_for_default_path(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            expected = home / ".config" / "btop" / "themes" / "sunset.theme"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_BTOP_THEME_NAME": "sunset",
                },
                clear=False,
            ):
                btop.write(SCHEME)

            self.assertTrue(expected.is_file())
            self.assertIn('theme[main_bg]="#', expected.read_text(encoding="utf-8"))

    def test_borders_writer_rejects_output_path_outside_home(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
            home = pathlib.Path(td)
            outside_path = pathlib.Path(outside) / "border_colors"
            expected = home / ".config" / "wallpaper-colors" / "border_colors"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_BORDER_COLORS_FILE": str(outside_path),
                },
                clear=False,
            ):
                borders.write(SCHEME)

            self.assertFalse(outside_path.exists())
            self.assertTrue(expected.is_file())

    def test_btop_writer_sanitizes_invalid_theme_name(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            expected = home / ".config" / "btop" / "themes" / "wallpaper.theme"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_BTOP_THEME_NAME": "../evil",
                },
                clear=False,
            ):
                btop.write(SCHEME)

            self.assertTrue(expected.is_file())

    def test_yazi_writer_sanitizes_invalid_flavor_name(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            expected = home / ".config" / "yazi" / "flavors" / "wallpaper.yazi" / "flavor.toml"
            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "WALLPAPER_YAZI_FLAVOR_NAME": "../sunset",
                    "WALLPAPER_YAZI_WRITE_THEME_SELECTOR": "0",
                },
                clear=False,
            ):
                yazi.write(SCHEME)

            self.assertTrue(expected.is_file())


if __name__ == "__main__":
    unittest.main()
