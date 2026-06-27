import pathlib
import unittest
from unittest.mock import patch

# Make wcsync importable from repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
WCSYNC_ROOT = REPO_ROOT / "configs" / "wallpaper-colors"
import sys

sys.path.insert(0, str(WCSYNC_ROOT))

from wcsync.config import Config
from wcsync import writers


class _TargetApp:
    def __init__(self, name, fn):
        self.name = name
        self._fn = fn

    def write(self, scheme, config):
        self._fn(scheme, config)


class WritersRegistryTests(unittest.TestCase):
    def test_write_all_respects_target_toggles(self):
        called = []
        app_a = _TargetApp("a", lambda *_: called.append("a"))
        cfg = Config(targets={"a": True})

        with patch.object(writers, "enabled_target_apps", return_value=[app_a]):
            failed = writers.write_all({"accent": (1, 2, 3)}, cfg)

        self.assertEqual(called, ["a"])
        self.assertEqual(failed, [])

    def test_write_all_continues_when_writer_fails(self):
        called = []

        def fail(*_):
            raise RuntimeError("bad writer")

        app_bad = _TargetApp("bad", fail)
        app_ok = _TargetApp("ok", lambda *_: called.append("ok"))
        cfg = Config(targets={"bad": True, "ok": True})

        with (
            patch.object(writers, "enabled_target_apps", return_value=[app_bad, app_ok]),
            patch("wcsync.writers.log") as log_mock,
        ):
            failed = writers.write_all({"accent": (1, 2, 3)}, cfg)

        self.assertEqual(called, ["ok"])
        self.assertEqual(failed, ["bad"])
        self.assertTrue(
            any("Writer bad failed" in call.args[0] for call in log_mock.call_args_list if call.args)
        )


if __name__ == "__main__":
    unittest.main()
