"""Color extraction and scheme generation."""

import colorsys
import hashlib
from collections import Counter

from PIL import Image

from .utils import clamp


# --- Color Math ---


def lum(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


def sat(r, g, b):
    _, s, _ = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return s


def darken(rgb, factor=0.5):
    return tuple(clamp(c * factor) for c in rgb)


def lighten(rgb, factor=0.5):
    return tuple(clamp(c + (255 - c) * factor) for c in rgb)


def color_at_hue(hue_deg, s, v):
    """Create an RGB tuple at a specific hue."""
    r, g, b = colorsys.hsv_to_rgb(hue_deg / 360, s, v)
    return (clamp(r * 255), clamp(g * 255), clamp(b * 255))


def vivify(rgb, min_sat=0.75, min_val=0.85):
    """Take a color's hue and push saturation/value up so it pops."""
    h, s, v = colorsys.rgb_to_hsv(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)
    s = max(s, min_sat)
    v = max(v, min_val)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (clamp(r * 255), clamp(g * 255), clamp(b * 255))


def harmonize(target_deg, accent_deg, factor=0.25):
    """Shift target hue toward accent hue by *factor* along the shortest arc."""
    diff = accent_deg - target_deg
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360
    return (target_deg + diff * factor) % 360


# --- Extraction ---


def image_hash(img):
    """Quick perceptual hash from a pre-resized PIL Image."""
    thumb = img.resize((16, 16), Image.Resampling.LANCZOS)
    return hashlib.sha256(thumb.tobytes()).hexdigest()


def extract_palette(img, n_colors=8):
    """Extract dominant colors using Pillow quantize (median-cut).

    Expects a pre-resized image (200x200) for performance.
    """
    quantized = img.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT)
    raw_palette = quantized.getpalette()
    if raw_palette is None:
        return [(128, 128, 128)] * n_colors
    palette_data = raw_palette[: n_colors * 3]

    colors = []
    for i in range(0, len(palette_data), 3):
        colors.append((palette_data[i], palette_data[i + 1], palette_data[i + 2]))

    try:
        pixel_data = quantized.get_flattened_data()
    except AttributeError:
        pixel_data = list(quantized.getdata())

    counts = Counter(pixel_data)
    indexed = [(colors[i], counts.get(i, 0)) for i in range(len(colors))]
    indexed.sort(key=lambda x: x[1], reverse=True)
    return [c for c, _ in indexed]


# --- Scheme Generation ---


def _parse_hex(h):
    """Parse '#rrggbb' to (r, g, b) tuple."""
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def pick_secondary(palette, accent):
    """Pick a gradient secondary from the actual palette.

    Finds the palette color that is most distinct from the accent in hue
    while still being reasonably vibrant. Falls back to a lighter/darker
    variant of the accent if the palette is monochromatic.
    """
    ah, _, _ = colorsys.rgb_to_hsv(accent[0] / 255, accent[1] / 255, accent[2] / 255)

    best = None
    best_score = -1

    for c in palette:
        if c == accent:
            continue
        ch, cs, cv = colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)
        hue_dist = min(abs(ch - ah), 1.0 - abs(ch - ah))
        vibrancy = cs * cv
        lum_ok = 0.15 < (lum(*c) / 255) < 0.85
        score = hue_dist * 2.0 + vibrancy * 1.0 + (0.3 if lum_ok else 0.0)
        if score > best_score:
            best_score = score
            best = c

    if best is None or best_score < 0.15:
        return lighten(accent, 0.35)

    ch, cs, cv = colorsys.rgb_to_hsv(best[0] / 255, best[1] / 255, best[2] / 255)
    cs = max(cs, 0.35)
    cv = max(cv, 0.45)
    r, g, b = colorsys.hsv_to_rgb(ch, cs, cv)
    return (clamp(r * 255), clamp(g * 255), clamp(b * 255))


def build_scheme(palette, config=None):
    """Build a full color scheme from the extracted palette.

    Accepts an optional Config to override default tuning parameters.
    """
    from .config import Config

    if config is None:
        config = Config()

    # If user provided an accent override, use it instead of auto-detecting
    if config.accent_override:
        accent = _parse_hex(config.accent_override)
        h, s, v = colorsys.rgb_to_hsv(accent[0] / 255, accent[1] / 255, accent[2] / 255)
        s = max(s, config.min_saturation)
        v = max(v, config.min_value)
    else:
        scored = []
        for c in palette:
            s = sat(*c)
            l = lum(*c) / 255
            score = s * (0.3 + 0.7 * l)
            scored.append((c, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        accent = scored[0][0]

        h, s, v = colorsys.rgb_to_hsv(accent[0] / 255, accent[1] / 255, accent[2] / 255)
        s = max(s, config.min_saturation)
        v = max(v, config.min_value)

    by_lum = sorted(palette, key=lambda c: lum(*c))
    dark = by_lum[0]
    light = by_lum[-1]

    if lum(*dark) > 50:
        dark = darken(dark, 0.3)
    if lum(*light) < 160:
        light = lighten(light, 0.4)
    if lum(*light) < 160:
        light = (201, 209, 217)

    ns = min(s + 0.1, 1.0)
    nv = min(v + 0.05, 1.0)

    secondary = pick_secondary(palette, accent)

    border_accent = vivify(
        accent, min_sat=config.border_vivify_sat, min_val=config.border_vivify_val
    )
    border_secondary = vivify(
        secondary,
        min_sat=max(config.border_vivify_sat - 0.05, 0),
        min_val=max(config.border_vivify_val - 0.05, 0),
    )

    ah = h * 360
    hf = config.harmonize_factor
    return {
        "accent": color_at_hue(ah, s, v),
        "secondary": secondary,
        "border_accent": border_accent,
        "border_secondary": border_secondary,
        "dark": dark,
        "light": light,
        "bar_bg": dark,
        "item_bg": lighten(dark, 0.08),
        "grey": darken(light, 0.55),
        "red": color_at_hue(harmonize(0, ah, hf), ns, nv),
        "green": color_at_hue(harmonize(120, ah, hf), ns, nv),
        "yellow": color_at_hue(harmonize(50, ah, hf), ns, nv),
        "cyan": color_at_hue(harmonize(185, ah, hf), ns, nv),
        "purple": color_at_hue(harmonize(270, ah, hf), ns, nv),
        "orange": color_at_hue(harmonize(25, ah, hf), ns, nv),
        "pink": color_at_hue(harmonize(340, ah, 0.20), ns * 0.85, nv),
    }
