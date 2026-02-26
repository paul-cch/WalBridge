import pathlib
import types
import unittest
from unittest.mock import MagicMock, patch

# Make wcsync importable from repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
WCSYNC_ROOT = REPO_ROOT / "configs" / "wallpaper-colors"
import sys

sys.path.insert(0, str(WCSYNC_ROOT))

# Provide a lightweight Quartz stub for non-macOS test environments.
if "Quartz" not in sys.modules:
    sys.modules["Quartz"] = types.SimpleNamespace()

from wcsync.capture import capture_wallpaper, load_wallpaper
from wcsync.config import Config


def _quartz_for_capture(
    create_image,
    width=16,
    height=16,
    raw_bytes=None,
):
    q = MagicMock()
    q.CGRectNull = 0
    q.kCGWindowListOptionIncludingWindow = 0
    q.kCGWindowImageBoundsIgnoreFraming = 0
    q.CGWindowListCreateImage = MagicMock(side_effect=create_image)
    q.CGImageGetWidth = MagicMock(return_value=width)
    q.CGImageGetHeight = MagicMock(return_value=height)
    q.CGImageGetDataProvider = MagicMock(return_value=object())
    q.CGDataProviderCopyData = MagicMock(
        return_value=raw_bytes if raw_bytes is not None else (b"\xff\xff\xff\xff" * (width * height))
    )
    return q


class CaptureTests(unittest.TestCase):
    def test_capture_wallpaper_retries_when_no_window(self):
        with (
            patch("wcsync.capture._find_wallpaper_window", return_value=None),
            patch("wcsync.capture.time.sleep") as sleep_mock,
            patch("wcsync.capture.log") as log_mock,
        ):
            result = capture_wallpaper(retries=3, retry_delay=0.1)

        self.assertIsNone(result)
        self.assertEqual(sleep_mock.call_count, 2)
        self.assertTrue(
            any("No wallpaper window found" in c.args[0] for c in log_mock.call_args_list if c.args)
        )

    def test_capture_wallpaper_retries_when_cgimage_missing_then_succeeds(self):
        quartz = _quartz_for_capture(create_image=[None, object()])
        with (
            patch("wcsync.capture._find_wallpaper_window", return_value=123),
            patch("wcsync.capture.Quartz", quartz),
            patch("wcsync.capture.time.sleep") as sleep_mock,
        ):
            result = capture_wallpaper(retries=2, retry_delay=0.1)

        self.assertIsNotNone(result)
        self.assertEqual(result.mode, "RGB")
        sleep_mock.assert_called_once_with(0.1)

    def test_capture_wallpaper_retries_on_black_frame_and_then_fails(self):
        black_rgba = b"\x00\x00\x00\xff" * (16 * 16)
        quartz = _quartz_for_capture(create_image=[object(), object()], raw_bytes=black_rgba)
        with (
            patch("wcsync.capture._find_wallpaper_window", return_value=123),
            patch("wcsync.capture.Quartz", quartz),
            patch("wcsync.capture.time.sleep") as sleep_mock,
            patch("wcsync.capture.log") as log_mock,
        ):
            result = capture_wallpaper(retries=2, retry_delay=0.1)

        self.assertIsNone(result)
        sleep_mock.assert_called_once_with(0.1)
        self.assertTrue(
            any("all black" in c.args[0] for c in log_mock.call_args_list if c.args)
        )

    def test_capture_wallpaper_rejects_tiny_image(self):
        quartz = _quartz_for_capture(create_image=[object()], width=8, height=8)
        with (
            patch("wcsync.capture._find_wallpaper_window", return_value=123),
            patch("wcsync.capture.Quartz", quartz),
            patch("wcsync.capture.log") as log_mock,
        ):
            result = capture_wallpaper(retries=1, retry_delay=0.1)

        self.assertIsNone(result)
        self.assertTrue(
            any("too small" in c.args[0] for c in log_mock.call_args_list if c.args)
        )

    def test_load_wallpaper_uses_capture_fallback(self):
        cfg = Config(display=2)
        with (
            patch("wcsync.capture.get_wallpaper_path", return_value="/tmp/wall.jpg"),
            patch("wcsync.capture.load_wallpaper_from_file", return_value=None),
            patch("wcsync.capture.capture_wallpaper", return_value="captured") as capture_mock,
        ):
            img, wp_path = load_wallpaper(cfg)

        self.assertEqual(img, "captured")
        self.assertEqual(wp_path, "")
        capture_mock.assert_called_once_with(display=2)

    def test_load_wallpaper_prefers_desktoppr_file_when_available(self):
        cfg = Config(display=1)
        with (
            patch("wcsync.capture.get_wallpaper_path", return_value="/tmp/wall.jpg"),
            patch("wcsync.capture.load_wallpaper_from_file", return_value="file-image"),
            patch("wcsync.capture.capture_wallpaper") as capture_mock,
        ):
            img, wp_path = load_wallpaper(cfg)

        self.assertEqual(img, "file-image")
        self.assertEqual(wp_path, "/tmp/wall.jpg")
        capture_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
