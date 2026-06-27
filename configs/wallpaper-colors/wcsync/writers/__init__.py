"""Dispatch write_all to enabled Target App writer adapters."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from ..config import Config
from ..target_apps import enabled_target_apps
from ..utils import log


def write_all(scheme, config=None):
    """Write all enabled config files.

    Each writer module exposes write(scheme, config). The config.targets
    dict controls which targets are enabled.
    """
    if config is None:
        config = Config()

    enabled = enabled_target_apps(config)
    written = []
    failed = []

    if enabled:
        with ThreadPoolExecutor(max_workers=min(8, len(enabled))) as pool:
            futures = {pool.submit(app.write, scheme, config): app for app in enabled}
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
