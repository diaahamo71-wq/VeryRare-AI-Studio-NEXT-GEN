"""Safe, explicit VST3 discovery and smoke-test reporting."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from app.vst3_host import scan_vst3_paths, inspect_plugin


def scan_and_test(extra_paths: list[str] | None = None) -> list[dict[str, Any]]:
    results = []
    for path in scan_vst3_paths(extra_paths):
        row: dict[str, Any] = {"path": path, "discovered": True, "loaded": False}
        try:
            row.update(inspect_plugin(path))
        except Exception as exc:
            # Keep the scanner alive if a plugin fails to load. For true crash
            # isolation, move each smoke test into a dedicated worker process.
            row["error"] = f"{type(exc).__name__}: {exc}"
        results.append(row)
    return results
