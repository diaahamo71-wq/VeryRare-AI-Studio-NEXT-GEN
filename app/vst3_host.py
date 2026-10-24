"""Offline VST3 hosting adapter using Spotify Pedalboard.

This module only loads plugins explicitly selected by the user/approved plan.
It does not download, install, or execute arbitrary code. Test each third-party
plugin before production use; some plugins may hang or crash the host process.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
import json
import os

import numpy as np
import soundfile as sf

try:
    from pedalboard import load_plugin
except ImportError:  # keeps the rest of the app usable before optional install
    load_plugin = None


def _plugin_path(path: str | Path) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"VST3 plugin path does not exist: {p}")
    # Pedalboard accepts a VST3 bundle/file path. Do not assume every plugin
    # has the same on-disk layout.
    if p.suffix.lower() != ".vst3" and not p.is_dir():
        raise ValueError("Expected a .vst3 plugin bundle/path.")
    return p


def scan_vst3_paths(extra_paths: list[str] | None = None) -> list[str]:
    """Return existing VST3 bundle paths from standard Windows folders.

    This is path discovery, not proof that a plugin loads or is compatible.
    User-supplied extra paths are supported; no recursive full-drive scan.
    """
    candidates: list[Path] = []
    env_paths = os.environ.get("VERYRARE_VST3_PATHS", "")
    raw = list(extra_paths or []) + [x for x in env_paths.split(os.pathsep) if x]
    for raw_path in raw:
        candidates.append(Path(raw_path).expanduser())
    if os.name == "nt":
        candidates.extend([
            Path(os.environ.get("CommonProgramFiles", r"C:\Program Files\Common Files")) / "VST3",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Common" / "VST3",
        ])
    found: set[str] = set()
    for root in candidates:
        if not root.exists():
            continue
        if root.suffix.lower() == ".vst3":
            found.add(str(root.resolve()))
            continue
        try:
            for item in root.iterdir():
                if item.suffix.lower() == ".vst3" or (item.is_dir() and item.name.lower().endswith(".vst3")):
                    found.add(str(item.resolve()))
        except OSError:
            continue
    return sorted(found, key=str.casefold)


def inspect_plugin(plugin_path: str | Path) -> dict[str, Any]:
    """Attempt to load a plugin and return its exposed parameter names.

    A successful load is a smoke test only, not an audio-quality certification.
    """
    if load_plugin is None:
        raise RuntimeError("Pedalboard is not installed. Run: python -m pip install pedalboard")
    path = _plugin_path(plugin_path)
    plugin = load_plugin(str(path))
    params = getattr(plugin, "parameters", {})
    parameter_names = sorted(str(k) for k in params.keys()) if hasattr(params, "keys") else []
    return {
        "path": str(path),
        "loaded": True,
        "plugin_type": type(plugin).__name__,
        "parameters": parameter_names,
        "note": "Loaded successfully; verify the rendered audio and plugin license separately.",
    }


def render_vst3(
    input_wav: str | Path,
    output_wav: str | Path,
    plugin_path: str | Path,
    parameter_values: Mapping[str, float] | None = None,
    wet: float = 1.0,
    block_size: int = 8192,
) -> dict[str, Any]:
    """Render one WAV through one VST3 effect offline.

    Parameter names must match the plugin's exposed Pedalboard parameter keys.
    Values are checked against discovered ranges where range metadata exists.
    A dry/wet mix is applied after processing; this is not a plugin's own mix
    control and is not suitable for every latency/time-varying plugin.
    """
    if load_plugin is None:
        raise RuntimeError("Pedalboard is not installed. Run: python -m pip install pedalboard")
    src, dst = Path(input_wav), Path(output_wav)
    if not src.is_file():
        raise FileNotFoundError(f"Input WAV not found: {src}")
    plugin_file = _plugin_path(plugin_path)
    wet = float(wet)
    if not 0.0 <= wet <= 1.0:
        raise ValueError("wet must be between 0.0 and 1.0")
    audio, sr = sf.read(str(src), dtype="float32", always_2d=True)
    if len(audio) < 2 or not np.isfinite(audio).all():
        raise ValueError("Input WAV must contain finite audio samples.")
    plugin = load_plugin(str(plugin_file))
    applied: dict[str, float] = {}
    requested = dict(parameter_values or {})
    exposed = getattr(plugin, "parameters", {})
    for name, value in requested.items():
        if name not in exposed:
            raise ValueError(
                f"Unknown parameter {name!r}. Exposed parameters: {sorted(str(k) for k in exposed.keys())}"
            )
        param = exposed[name]
        value = float(value)
        lo, hi = getattr(param, "range", (None, None))
        if lo is not None and value < lo or hi is not None and value > hi:
            raise ValueError(f"Parameter {name!r}={value} is outside its plugin range {param.range}.")
        setattr(plugin, name, value)
        applied[name] = value

    # Pedalboard expects channel-first float audio (channels, frames).
    dry = audio.T.copy()
    wet_audio = np.asarray(plugin(dry, sample_rate=int(sr), buffer_size=int(block_size)), dtype=np.float32)
    if wet_audio.ndim == 1:
        wet_audio = wet_audio[None, :]
    if wet_audio.shape != dry.shape:
        raise RuntimeError(
            f"Plugin changed audio shape from {dry.shape} to {wet_audio.shape}; "
            "this adapter currently requires equal-length effect processing."
        )
    mixed = (dry * (1.0 - wet) + wet_audio * wet).T
    peak_before = float(np.max(np.abs(audio)))
    peak_after = float(np.max(np.abs(mixed)))
    dst.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(dst), mixed, int(sr), subtype="PCM_24")
    report = {
        "input": str(src),
        "output": str(dst),
        "plugin_path": str(plugin_file),
        "plugin_type": type(plugin).__name__,
        "sample_rate_hz": int(sr),
        "channels": int(audio.shape[1]),
        "frames_in": int(len(audio)),
        "frames_out": int(len(mixed)),
        "wet": wet,
        "parameters_applied": applied,
        "peak_dbfs_before": round(20 * np.log10(max(peak_before, 1e-9)), 2),
        "peak_dbfs_after": round(20 * np.log10(max(peak_after, 1e-9)), 2),
        "rendered": True,
        "warnings": [
            "This is offline processing; plugin compatibility and sound quality require listening tests.",
            "The plugin was not sandboxed in a separate process. Use only trusted plugins.",
        ],
    }
    dst.with_suffix(".vst3-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
