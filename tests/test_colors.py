import colorsys
import pathlib
import unittest

from PIL import Image

# Make wcsync importable from repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
WCSYNC_ROOT = REPO_ROOT / "configs" / "wallpaper-colors"
import sys

sys.path.insert(0, str(WCSYNC_ROOT))

from wcsync.colors import (
    build_scheme,
    darken,
    extract_palette,
    harmonize,
    lighten,
    lum,
    pick_secondary,
    sat,
    vivify,
)
from wcsync.config import Config


class _FakeImage:
    def __init__(self, quantized):
        self._quantized = quantized

    def quantize(self, colors, method):
        self.last_quantize = (colors, method)
        return self._quantized


class _QuantizedWithFlattenedData:
    def __init__(self, palette, pixels):
        self._palette = palette
        self._pixels = pixels

    def getpalette(self):
        return self._palette

    def get_flattened_data(self):
        return self._pixels


class _QuantizedWithoutFlattenedData:
    def __init__(self, palette, pixels):
        self._palette = palette
        self._pixels = pixels

    def getpalette(self):
        return self._palette

    def getdata(self):
        return self._pixels


class _QuantizedWithoutPalette:
    @staticmethod
    def getpalette():
        return None


class ColorMathTests(unittest.TestCase):
    def test_lum_sat_darken_lighten(self):
        self.assertEqual(lum(255, 255, 255), 255.0)
        self.assertEqual(sat(128, 128, 128), 0.0)
        self.assertEqual(sat(255, 0, 0), 1.0)
        self.assertEqual(darken((200, 100, 50), 0.5), (100, 50, 25))
        self.assertEqual(lighten((100, 150, 200), 0.5), (177, 202, 227))

    def test_vivify_enforces_minimum_saturation_and_value(self):
        vivified = vivify((64, 96, 128), min_sat=0.8, min_val=0.9)
        _, s, v = colorsys.rgb_to_hsv(vivified[0] / 255, vivified[1] / 255, vivified[2] / 255)
        self.assertGreaterEqual(s, 0.8)
        # int-clamping can drop one 8-bit step below the requested threshold.
        self.assertGreaterEqual(v, 229 / 255)

    def test_harmonize_wraps_around_color_wheel(self):
        self.assertEqual(harmonize(350, 10, 0.5), 0.0)
        self.assertEqual(harmonize(10, 350, 0.5), 0.0)


class PaletteExtractionTests(unittest.TestCase):
    def test_extract_palette_orders_colors_by_frequency(self):
        quantized = _QuantizedWithFlattenedData(
            palette=[255, 0, 0, 0, 255, 0, 0, 0, 255],
            pixels=[1, 1, 1, 2, 2, 0],
        )
        image = _FakeImage(quantized)

        palette = extract_palette(image, n_colors=3)

        self.assertEqual(
            palette,
            [
                (0, 255, 0),
                (0, 0, 255),
                (255, 0, 0),
            ],
        )
        self.assertEqual(image.last_quantize, (3, Image.Quantize.MEDIANCUT))

    def test_extract_palette_falls_back_to_getdata(self):
        quantized = _QuantizedWithoutFlattenedData(
            palette=[10, 20, 30, 200, 210, 220],
            pixels=[0, 1, 1, 1],
        )
        palette = extract_palette(_FakeImage(quantized), n_colors=2)
        self.assertEqual(palette, [(200, 210, 220), (10, 20, 30)])

    def test_extract_palette_returns_gray_when_palette_missing(self):
        palette = extract_palette(_FakeImage(_QuantizedWithoutPalette()), n_colors=4)
        self.assertEqual(palette, [(128, 128, 128)] * 4)


class SchemeGenerationTests(unittest.TestCase):
    def test_build_scheme_with_accent_override_and_expected_keys(self):
        config = Config(accent_override="#336699")
        palette = [(40, 40, 40), (51, 102, 153), (220, 220, 220)]

        scheme = build_scheme(palette, config=config)

        expected_keys = {
            "accent",
            "secondary",
            "border_accent",
            "border_inactive",
            "dark",
            "light",
            "bar_bg",
            "item_bg",
            "grey",
            "red",
            "green",
            "yellow",
            "cyan",
            "purple",
            "orange",
            "pink",
        }
        self.assertEqual(set(scheme), expected_keys)

        h, s, v = colorsys.rgb_to_hsv(51 / 255, 102 / 255, 153 / 255)
        r, g, b = colorsys.hsv_to_rgb(h, max(s, config.min_saturation), max(v, config.min_value))
        expected_accent = (int(r * 255), int(g * 255), int(b * 255))
        self.assertEqual(scheme["accent"], expected_accent)

    def test_build_scheme_applies_dark_and_light_fallback_adjustments(self):
        scheme = build_scheme([(80, 80, 80), (85, 85, 85), (90, 90, 90)], config=Config())
        self.assertEqual(scheme["dark"], (24, 24, 24))
        self.assertEqual(scheme["light"], (201, 209, 217))
        ah, asat, aval = colorsys.rgb_to_hsv(
            scheme["border_accent"][0] / 255,
            scheme["border_accent"][1] / 255,
            scheme["border_accent"][2] / 255,
        )
        ih, isat, ival = colorsys.rgb_to_hsv(
            scheme["border_inactive"][0] / 255,
            scheme["border_inactive"][1] / 255,
            scheme["border_inactive"][2] / 255,
        )
        self.assertAlmostEqual(ah, ih, places=2)
        self.assertLess(isat, asat)
        self.assertLess(ival, aval)

    def test_pick_secondary_prefers_distinct_vibrant_palette_color(self):
        accent = (220, 60, 40)
        palette = [
            accent,
            (35, 200, 215),
            (80, 80, 80),
        ]

        secondary = pick_secondary(palette, accent)
        fallback = lighten(accent, 0.35)

        self.assertNotEqual(secondary, fallback)
        ah, _, _ = colorsys.rgb_to_hsv(accent[0] / 255, accent[1] / 255, accent[2] / 255)
        sh, ss, sv = colorsys.rgb_to_hsv(secondary[0] / 255, secondary[1] / 255, secondary[2] / 255)
        self.assertGreater(min(abs(sh - ah), 1.0 - abs(sh - ah)), 0.2)
        self.assertGreaterEqual(ss, 0.35)
        self.assertGreaterEqual(sv, 0.45)


if __name__ == "__main__":
    unittest.main()
