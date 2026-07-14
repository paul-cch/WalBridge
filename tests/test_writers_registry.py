import pathlib
import tempfile
import types
import unittest
from unittest.mock import patch

# Make wcsync importable from repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
WCSYNC_ROOT = REPO_ROOT / "configs" / "wallpaper-colors"
import sys

sys.path.insert(0, str(WCSYNC_ROOT))

from wcsync.config import Config
from wcsync import target_writing


class _TargetApp:
    def __init__(self, name):
        self.name = name


class _PathApp:
    name = "demo"
    writer_module = "demo"

    def __init__(self, paths):
        self.paths = paths

    def path(self, key="output"):
        return str(self.paths[key])


class TargetWritingTests(unittest.TestCase):
    def test_write_all_respects_target_toggles(self):
        called = []
        app_a = _TargetApp("a")
        cfg = Config(targets={"a": True})

        def fake_write(app, *_):
            called.append(app.name)
            return ["/tmp/a"]

        with (
            patch.object(target_writing, "enabled_target_apps", return_value=[app_a]),
            patch.object(target_writing, "write_target_app", side_effect=fake_write),
        ):
            failed = target_writing.write_all({"accent": (1, 2, 3)}, cfg)

        self.assertEqual(called, ["a"])
        self.assertEqual(failed, [])

    def test_write_all_continues_when_writer_fails(self):
        called = []

        app_bad = _TargetApp("bad")
        app_ok = _TargetApp("ok")
        cfg = Config(targets={"bad": True, "ok": True})

        def fake_write(app, *_):
            if app.name == "bad":
                raise RuntimeError("bad writer")
            called.append(app.name)
            return ["/tmp/ok"]

        with (
            patch.object(target_writing, "enabled_target_apps", return_value=[app_bad, app_ok]),
            patch.object(target_writing, "write_target_app", side_effect=fake_write),
            patch("wcsync.target_writing.log") as log_mock,
        ):
            failed = target_writing.write_all({"accent": (1, 2, 3)}, cfg)

        self.assertEqual(called, ["ok"])
        self.assertEqual(failed, ["bad"])
        self.assertTrue(
            any("Writer bad failed" in call.args[0] for call in log_mock.call_args_list if call.args)
        )

    def test_write_target_app_uses_fallback_for_user_owned_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            output = root / "starship.toml"
            fallback = root / "wallpaper-colors" / "starship.toml"
            output.write_text("[character]\nsuccess_symbol='>'\n", encoding="utf-8")
            app = _PathApp({"output": output, "fallback": fallback})
            material = target_writing.ColorMaterial(
                "# Auto-generated from wallpaper\n",
                fallback_key="fallback",
                owned_marker="# Auto-generated from wallpaper",
            )
            adapter = types.SimpleNamespace(render=lambda *_: material)

            with patch.object(target_writing, "_adapter_module", return_value=adapter):
                target_writing.write_target_app(app, {}, None)

            self.assertIn("success_symbol", output.read_text(encoding="utf-8"))
            self.assertTrue(fallback.is_file())
            self.assertIn("Auto-generated", fallback.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
