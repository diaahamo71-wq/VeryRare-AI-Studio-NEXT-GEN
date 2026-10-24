"""MCP server exposing guarded VeryRare AI Studio audio tools.

Transport defaults to stdio for local MCP clients (e.g. Claude Desktop).
Audio is processed locally. This server does not upload audio or call Gemini.
Only paths inside VERYRARE_AUDIO_ROOT are accepted for audio input/output files.
Only discovered VST3 plugins are accepted.
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from app.audio_engine import analyze_file
from app.vst3_host import inspect_plugin, render_vst3, scan_vst3_paths
from app.plugin_chain import render_chain
from app.automation_timeline import AutomationTimeline, validate_timeline_json
from app.automation_renderer import render_automation_timeline as _render_automation_timeline

mcp = FastMCP(
    "VeryRare AI Studio",
    instructions=(
        "Control the local VeryRare AI Studio audio engine through explicit tools. "
        "Inspect installed plugins before selecting them. Never claim processing succeeded "
        "unless the tool result says rendered=true. Ask before overwriting files. "
        "Do not assume pitch key/scale. Audio stays inside the configured local workspace. "
        "Only trusted installed plugins may be loaded."
    ),
)


def _audio_root() -> Path:
    root = Path(os.environ.get("VERYRARE_AUDIO_ROOT", str(Path.cwd()))).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_audio_path(raw: str, *, must_exist: bool = False) -> Path:
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = _audio_root() / p
    p = p.resolve()
    root = _audio_root()
    if p != root and root not in p.parents:
        raise PermissionError(f"Audio path must be inside configured workspace: {root}")
    if must_exist and not p.is_file():
        raise FileNotFoundError(p)
    return p


def _safe_plugin_path(raw: str) -> Path:
    requested = Path(raw).expanduser().resolve()
    allowed = {str(Path(p).expanduser().resolve()) for p in scan_vst3_paths()}
    if str(requested) not in allowed:
        raise PermissionError(
            "Plugin path is not in the discovered VST3 allowlist. Run scan_vst3_plugins first."
        )
    return requested


@mcp.tool()
def studio_status() -> dict[str, Any]:
    """Return local workspace and availability of the optional Pedalboard host."""
    try:
        import pedalboard  # noqa: F401
        ready, error = True, None
    except Exception as exc:
        ready, error = False, f"{type(exc).__name__}: {exc}"
    return {
        "studio": "VeryRare AI Studio", "audio_workspace": str(_audio_root()),
        "pedalboard_ready": ready, "local_audio_only": True, "cloud_audio_upload": False,
        "warning": "VST3 plugins are not sandboxed; only load trusted plugins.",
        "pedalboard_error": error,
    }


@mcp.tool()
def scan_vst3_plugins() -> list[dict[str, Any]]:
    """Discover VST3 plugins; discovery alone does not guarantee compatibility."""
    return [{"path": path, "discovered": True, "loaded": False,
             "note": "Discovery only; inspect this plugin explicitly before use."}
            for path in scan_vst3_paths()]


@mcp.tool()
def inspect_vst3_plugin(plugin_path: str) -> dict[str, Any]:
    """Load one discovered VST3 plugin and return its actual parameter names."""
    return inspect_plugin(_safe_plugin_path(plugin_path))


@mcp.tool()
def analyze_audio_wav(audio_path: str) -> dict[str, Any]:
    """Analyze a WAV inside the local audio workspace: duration, sample rate, peak and RMS."""
    return analyze_file(_safe_audio_path(audio_path, must_exist=True))


@mcp.tool()
def render_audio_through_vst3(
    input_wav: str, output_wav: str, plugin_path: str,
    wet: float = 1.0, parameters_json: str = "{}",
) -> dict[str, Any]:
    """Render a local WAV through one installed VST3 effect; inspect it first."""
    src, dst = _safe_audio_path(input_wav, must_exist=True), _safe_audio_path(output_wav)
    if dst.exists():
        raise FileExistsError(f"Output already exists; choose a new name: {dst}")
    plugin = _safe_plugin_path(plugin_path)
    parameters = json.loads(parameters_json)
    if not isinstance(parameters, dict) or not all(isinstance(k, str) for k in parameters):
        raise ValueError("parameters_json must be a JSON object with string keys.")
    return render_vst3(src, dst, plugin, parameters, wet)


@mcp.tool()
def render_vst3_effect_chain(input_wav: str, output_wav: str, plugins_json: str) -> dict[str, Any]:
    """Render sequential discovered VST3 effects locally; no instruments or latency compensation."""
    src, dst = _safe_audio_path(input_wav, must_exist=True), _safe_audio_path(output_wav)
    if dst.exists():
        raise FileExistsError(f"Output already exists; choose a new name: {dst}")
    requested = json.loads(plugins_json)
    if not isinstance(requested, list) or not requested:
        raise ValueError("plugins_json must be a non-empty JSON array.")
    steps = []
    for item in requested:
        if not isinstance(item, dict) or "plugin_path" not in item:
            raise ValueError("Each plugin item needs plugin_path.")
        safe_plugin = _safe_plugin_path(item["plugin_path"])
        steps.append({"path": str(safe_plugin), "parameters": item.get("parameters", {}),
                      "wet": item.get("wet", 1.0)})
    manifest = _audio_root() / f"mcp_effect_chain_{uuid.uuid4().hex}.json"
    manifest.write_text(json.dumps({"plugins": steps}, indent=2), encoding="utf-8")
    try:
        return render_chain(src, dst, manifest)
    finally:
        manifest.unlink(missing_ok=True)


@mcp.tool()
def validate_automation_timeline(timeline_json: str) -> dict[str, Any]:
    """Validate timeline timing/schema; this tool does not process audio."""
    result = validate_timeline_json(timeline_json)
    for event in result["events"]:
        if event.get("effect_kind") == "vst3":
            try:
                event["plugin_path"] = str(_safe_plugin_path(event["plugin_path"]))
                event["plugin_discovered"] = True
            except Exception as exc:
                event["plugin_discovered"] = False
                event["plugin_validation_error"] = f"{type(exc).__name__}: {exc}"
    return result


@mcp.tool()
def render_automation_timeline(
    input_wav: str, output_wav: str, timeline_json: str, track_id: str = "vocal",
) -> dict[str, Any]:
    """Render time-local effects on one WAV track using a validated timeline.

    Built-in telephone, reverb, delay, EQ and compressor are supported. VST3 events
    require a discovered and inspected plugin path. All enabled events must target
    track_id; render each track separately. Harmonizer and pitch correction fail
    explicitly because no verified processor is implemented. Input and output must
    be in the local workspace, and output must not already exist.
    """
    src, dst = _safe_audio_path(input_wav, must_exist=True), _safe_audio_path(output_wav)
    if dst.exists():
        raise FileExistsError(f"Output already exists; choose a new name: {dst}")
    timeline = AutomationTimeline.model_validate_json(timeline_json)
    allowed = {str(Path(p).resolve()) for p in scan_vst3_paths()}
    for event in timeline.events:
        if event.enabled and event.effect_kind == "vst3":
            plugin_path = str(Path(event.plugin_path or "").expanduser().resolve())
            if plugin_path not in allowed:
                raise PermissionError(
                    f"Plugin for event {event.event_id!r} is not discovered. "
                    "Run scan_vst3_plugins, then inspect the selected plugin."
                )
            inspect_plugin(Path(plugin_path))
    return _render_automation_timeline(
        src, dst, timeline_json, track_id=track_id, allowed_plugin_paths=allowed
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
