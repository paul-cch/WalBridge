import pathlib
import tempfile
import unittest

# Make wcsync importable from repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
WCSYNC_ROOT = REPO_ROOT / "configs" / "wallpaper-colors"
import sys

sys.path.insert(0, str(WCSYNC_ROOT))

from wcsync.config import Config


class ConfigLoadTests(unittest.TestCase):
    def test_missing_config_uses_defaults(self):
        cfg = Config.load("/tmp/does-not-exist-wallpaper-config.toml")
        self.assertEqual(cfg.display, 1)
        self.assertEqual(cfg.n_colors, 8)

    def test_invalid_toml_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            cfg_path = pathlib.Path(td) / "config.toml"
            cfg_path.write_text("[general\nn_colors = 0\n", encoding="utf-8")
            cfg = Config.load(str(cfg_path))
            self.assertEqual(cfg.n_colors, 8)
            self.assertEqual(cfg.display, 1)

    def test_invalid_values_are_clamped_or_defaulted(self):
        with tempfile.TemporaryDirectory() as td:
            cfg_path = pathlib.Path(td) / "config.toml"
            cfg_path.write_text(
                """
[general]
display = 0
n_colors = 0

[scheme]
min_saturation = -1
min_value = 2
harmonize_factor = 3
accent_override = "not-a-color"

[borders]
vivify_sat = -2
vivify_val = 99
opacity = "0xB3"

[targets]
sketchybar = false
kitty = "yes"
""".strip(),
                encoding="utf-8",
            )
            cfg = Config.load(str(cfg_path))
            self.assertEqual(cfg.display, 1)
            self.assertEqual(cfg.n_colors, 8)
            self.assertEqual(cfg.min_saturation, 0.45)
            self.assertEqual(cfg.min_value, 0.55)
            self.assertEqual(cfg.harmonize_factor, 0.25)
            self.assertIsNone(cfg.accent_override)
            self.assertEqual(cfg.border_vivify_sat, 0.45)
            self.assertEqual(cfg.border_vivify_val, 0.65)
            self.assertEqual(cfg.border_opacity, 0xB3)
            self.assertFalse(cfg.targets["sketchybar"])
            self.assertTrue(cfg.targets["kitty"])

    def test_valid_accent_override_normalized(self):
        with tempfile.TemporaryDirectory() as td:
            cfg_path = pathlib.Path(td) / "config.toml"
            cfg_path.write_text(
                """
[scheme]
accent_override = "a1B2c3"
""".strip(),
                encoding="utf-8",
            )
            cfg = Config.load(str(cfg_path))
            self.assertEqual(cfg.accent_override, "#a1B2c3")


if __name__ == "__main__":
    unittest.main()
