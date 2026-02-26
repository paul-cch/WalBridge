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


class _WriterModule:
    def __init__(self, name, fn):
        self.__name__ = name
        self._fn = fn

    def write(self, scheme, config):
        self._fn(scheme, config)


class WritersRegistryTests(unittest.TestCase):
    def test_write_all_respects_target_toggles(self):
        called = []
        mod_a = _WriterModule("wcsync.writers.a", lambda *_: called.append("a"))
        mod_b = _WriterModule("wcsync.writers.b", lambda *_: called.append("b"))
        cfg = Config(targets={"a": True, "b": False})

        with patch.object(writers, "_WRITERS", {"a": mod_a, "b": mod_b}):
            failed = writers.write_all({"accent": (1, 2, 3)}, cfg)

        self.assertEqual(called, ["a"])
        self.assertEqual(failed, [])

    def test_write_all_continues_when_writer_fails(self):
        called = []

        def fail(*_):
            raise RuntimeError("bad writer")

        mod_bad = _WriterModule("wcsync.writers.bad", fail)
        mod_ok = _WriterModule("wcsync.writers.ok", lambda *_: called.append("ok"))
        cfg = Config(targets={"bad": True, "ok": True})

        with (
            patch.object(writers, "_WRITERS", {"bad": mod_bad, "ok": mod_ok}),
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
