import os
import pathlib
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

# Make wcsync importable from repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
WCSYNC_ROOT = REPO_ROOT / "configs" / "wallpaper-colors"
import sys

sys.path.insert(0, str(WCSYNC_ROOT))

from wcsync import target_apps


class TargetAppsTests(unittest.TestCase):
    def test_target_defaults_are_single_source_for_config_toggles(self):
        defaults = target_apps.target_defaults()

        self.assertTrue(defaults["kitty"])
        self.assertTrue(defaults["hydrotodo"])
        self.assertFalse(defaults["vscode"])

    def test_enabled_target_apps_respects_config_targets(self):
        cfg = SimpleNamespace(targets={name: False for name in target_apps.target_defaults()})
        cfg.targets.update({"kitty": True, "vscode": True})

        enabled = [app.name for app in target_apps.enabled_target_apps(cfg)]

        self.assertEqual(enabled, ["kitty", "vscode"])

    def test_name_derived_path_uses_target_policy(self):
        with tempfile.TemporaryDirectory() as td:
            home = pathlib.Path(td)
            with patch.dict(
                os.environ,
                {"HOME": str(home), "WALLPAPER_WEZTERM_SCHEME_NAME": "sunset"},
                clear=False,
            ):
                path = target_apps.target_path("wezterm")

        self.assertEqual(
            path,
            os.path.realpath(home / ".config" / "wezterm" / "colors" / "sunset.toml"),
        )

    def test_output_override_stays_inside_home(self):
        with tempfile.TemporaryDirectory() as home_td, tempfile.TemporaryDirectory() as outside_td:
            home = pathlib.Path(home_td)
            outside = pathlib.Path(outside_td) / "border_colors"
            with (
                patch.dict(
                    os.environ,
                    {"HOME": str(home), "WALLPAPER_BORDER_COLORS_FILE": str(outside)},
                    clear=False,
                ),
                patch("wcsync.target_apps.safe_home_path", wraps=target_apps.safe_home_path) as safe_mock,
            ):
                path = target_apps.target_path("borders")

        self.assertEqual(
            path,
            os.path.realpath(home / ".config" / "wallpaper-colors" / "border_colors"),
        )
        safe_mock.assert_called()

    def test_target_bool_policy_handles_yazi_selector_opt_out(self):
        with patch.dict(os.environ, {"WALLPAPER_YAZI_WRITE_THEME_SELECTOR": "off"}, clear=False):
            self.assertFalse(target_apps.target_flag("yazi", "write_theme_selector"))

    def test_target_env_material_only_includes_target_app_env_vars(self):
        material = target_apps.target_env_material(
            {
                "WALLPAPER_KITTY_OUTPUT_PATH": "/tmp/kitty.conf",
                "WALLPAPER_DIR": "/tmp/wallpapers",
                "WALLPAPER_PYTHON": "/usr/bin/python3",
                "OTHER": "ignored",
            }
        )

        self.assertEqual(material, {"WALLPAPER_KITTY_OUTPUT_PATH": "/tmp/kitty.conf"})


if __name__ == "__main__":
    unittest.main()
