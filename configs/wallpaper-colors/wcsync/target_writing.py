"""Target App writing module.

Owns the seam between Target App adapters that render Color Material and the
filesystem writes that publish it.
"""

from __future__ import annotations

import importlib
import os
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from .config import Config
from .target_apps import TargetApp, enabled_target_apps
from .utils import atomic_write, log


@dataclass(frozen=True)
class ColorMaterial:
    content: str
    destination_key: str = "output"
    fallback_key: str | None = None
    owned_marker: str | None = None


def _adapter_module(app: TargetApp):
    return importlib.import_module(f"{__package__}.writers.{app.writer_module}")


def _normalize_materials(materials) -> list[ColorMaterial]:
    if materials is None:
        return []
    if isinstance(materials, ColorMaterial):
        return [materials]
    if isinstance(materials, Iterable) and not isinstance(materials, (str, bytes)):
        return list(materials)
    raise TypeError(f"expected ColorMaterial or iterable, got {type(materials).__name__}")


def _destination_path(app: TargetApp, material: ColorMaterial) -> str:
    path = app.path(material.destination_key)
    if not material.owned_marker or not os.path.isfile(path):
        return path

    try:
        with open(path, "r", encoding="utf-8") as f:
            first_line = f.readline()
    except OSError:
        return path

    if material.owned_marker in first_line:
        return path
    if not material.fallback_key:
        raise RuntimeError(f"{app.name} destination is not WalBridge-owned: {path}")

    fallback = app.path(material.fallback_key)
    log(f"{app.name}: user file detected, using fallback Color Material path {fallback}")
    return fallback


def write_target_app(app: TargetApp, scheme, config=None) -> list[str]:
    module = _adapter_module(app)
    render = getattr(module, "render", None)
    if render is None:
        module.write(scheme, config)
        return [app.name]

    written_paths = []
    for material in _normalize_materials(render(scheme, app, config)):
        path = _destination_path(app, material)
        atomic_write(path, material.content)
        written_paths.append(path)
    return written_paths


def write_all(scheme, config=None):
    """Write Color Material for all enabled Target Apps."""
    if config is None:
        config = Config()

    enabled = enabled_target_apps(config)
    written = []
    failed = []

    if enabled:
        with ThreadPoolExecutor(max_workers=min(8, len(enabled))) as pool:
            futures = {pool.submit(write_target_app, app, scheme, config): app for app in enabled}
            for fut in as_completed(futures):
                app = futures[fut]
                try:
                    fut.result()
                except Exception as e:
                    log(f"Writer {app.name} failed: {e}")
                    failed.append(app.name)
                    continue
                written.append(app.name)

    log(f"Wrote configs for: {', '.join(sorted(written))}")
    return failed
