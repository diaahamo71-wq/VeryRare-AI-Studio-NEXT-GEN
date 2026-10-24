"""Allowlisted, sequential VST3 effect-chain renderer.

The plan is data-only JSON. It cannot execute code or choose arbitrary file paths
unless the caller explicitly places those paths in the reviewed chain manifest.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

import numpy as np
import soundfile as sf

try:
    from pedalboard import load_plugin
except ImportError:
    load_plugin = None


def render_chain(input_wav: str | Path, output_wav: str | Path,
                 chain_manifest: str | Path) -> dict[str, Any]:
    if load_plugin is None:
        raise RuntimeError("Pedalboard is not installed. Run: python -m pip install -r requirements.txt")
    source, target, manifest_path = Path(input_wav), Path(output_wav), Path(chain_manifest)
    if not source.is_file():
        raise FileNotFoundError(source)
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    steps = manifest.get("plugins")
    if not isinstance(steps, list) or not steps:
        raise ValueError("Manifest must contain a non-empty 'plugins' array.")
    audio, sr = sf.read(str(source), dtype="float32", always_2d=True)
    if not np.isfinite(audio).all():
        raise ValueError("Input audio contains NaN or infinite samples.")
    current = audio.T.copy()
    executed = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or not step.get("path"):
            raise ValueError(f"Plugin step {index} must contain an explicit 'path'.")
        plugin_path = Path(step["path"]).expanduser().resolve()
        if not plugin_path.exists():
            raise FileNotFoundError(f"Plugin step {index} not found: {plugin_path}")
        wet = float(step.get("wet", 1.0))
        if not 0 <= wet <= 1:
            raise ValueError(f"Plugin step {index}: wet must be between 0 and 1.")
        params = step.get("parameters", {})
        if not isinstance(params, dict):
            raise ValueError(f"Plugin step {index}: parameters must be a JSON object.")
        plugin = load_plugin(str(plugin_path), parameter_values=params)
        if not getattr(plugin, "is_effect", False):
            raise ValueError(f"Plugin step {index} is not an audio effect. MIDI instruments are not supported here.")
        dry = current
        processed = np.asarray(plugin(dry, sample_rate=int(sr)), dtype=np.float32)
        if processed.ndim == 1:
            processed = processed[None, :]
        if processed.shape != dry.shape:
            raise RuntimeError(
                f"Plugin step {index} changed shape {dry.shape} -> {processed.shape}; "
                "latency/buffering compensation is not implemented in this MVP."
            )
        current = dry * (1.0 - wet) + processed * wet
        executed.append({
            "index": index,
            "plugin_path": str(plugin_path),
            "plugin_type": type(plugin).__name__,
            "parameters_requested": params,
            "wet": wet,
            "render_succeeded": True,
        })
    result = current.T
    target.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(target), result, int(sr), subtype="PCM_24")
    report = {
        "input": str(source), "output": str(target), "sample_rate_hz": int(sr),
        "channels": int(audio.shape[1]), "plugin_count": len(executed),
        "executed_plugins": executed, "rendered": True,
        "warning": "Listen and compare against bypass. Plugin loading is not sandboxed; only use trusted plugins.",
    }
    target.with_suffix(".chain-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
