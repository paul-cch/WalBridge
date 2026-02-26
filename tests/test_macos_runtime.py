import pathlib
import sys
import importlib
import unittest

# Make wcsync importable from repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
WCSYNC_ROOT = REPO_ROOT / "configs" / "wallpaper-colors"
sys.path.insert(0, str(WCSYNC_ROOT))


class MacOSRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "darwin", "macOS-only runtime validation")
    def test_quartz_runtime_available(self):
        sys.modules.pop("Quartz", None)
        import Quartz
        import wcsync.capture as capture_module

        self.assertIsNotNone(Quartz)
        capture_module = importlib.reload(capture_module)
        self.assertGreaterEqual(capture_module.get_display_count(), 0)


if __name__ == "__main__":
    unittest.main()
