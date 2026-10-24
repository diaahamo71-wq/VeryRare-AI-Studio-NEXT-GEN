"""MCP server exposing guarded VeryRare AI Studio audio tools.

Transport defaults to stdio for local MCP clients (e.g. Claude Desktop).
Audio is processed locally. This server does not upload audio or call Gemini.
Only paths inside VERYRARE_AUDIO_ROOT (default: current working directory) are
accepted for audio input/output/manifest files. Only plugins inside standard
VST3 folders or VERYRARE_VST3_PATHS are accepted.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from app.audio_engine import analyze_file
from app.vst3_host import inspect_plugin, render_vst3, scan_vst3_paths
from app.plugin_chain import render_chain
from app.automation_timeline import validate_timeline_json

mcp = FastMCP(
    "VeryRare AI Studio",
    instructions=(
        "You control the local VeryRare AI Studio audio-engine through explicit tools. "
        "Always inspect installed plugins before selecting them. Never claim processing "
        "succeeded unless the tool result says rendered=true. Ask before overwriting files. "
        "Do not assume pitch key/scale; ask if needed. Audio paths are local and must be "
        "inside the configured audio workspace. Only trusted installed plugins may be loaded."
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
    allowed_roots = [Path(p).expanduser().resolve() for p in scan_vst3_paths()]
    # scan_vst3_paths returns discovered bundle paths, so require exact match
    # to a discovered plugin path rather than accepting an arbitrary filesystem path.
    if str(requested) not in {str(Path(p).resolve()) for p in allowed_roots}:
        raise PermissionError(
            "Plugin path is not in the discovered VST3 allowlist. Run scan_vst3_plugins first "
            "and use an exact returned path."
        )
    return requested


@mcp.tool()
def studio_status() -> dict[str, Any]:
    """Return local workspace and availability of the optional Pedalboard host."""
    try:
        import pedalboard  # noqa: F401
        pedalboard_ready = True
        pedalboard_error = None
    except Exception as exc:
        pedalboard_ready = False
        pedalboard_error = f"{type(exc).__name__}: {exc}"
    return {
        "studio": "VeryRare AI Studio",
        "audio_workspace": str(_audio_root()),
        "pedalboard_ready": pedalboard_ready,
        "local_audio_only": True,
        "cloud_audio_upload": False,
        "warning": "VST3 plugins are not sandboxed in this MVP; only load trusted plugins.",
        "pedalboard_error": pedalboard_error,
    }


@mcp.tool()
def scan_vst3_plugins() -> list[dict[str, Any]]:
    """Discover VST3 plugins in standard Windows folders and user-configured paths.

    Discovery is not a guarantee of compatibility. Use inspect_vst3_plugin to smoke-test.
    """
    # Discovery only: loading every installed plugin in this process can crash
    # the MCP server. Smoke-test one explicitly selected plugin via inspect_vst3_plugin.
    return [{"path": path, "discovered": True, "loaded": False,
             "note": "Discovery only; inspect this plugin explicitly before use."}
            for path in scan_vst3_paths()]


@mcp.tool()
def inspect_vst3_plugin(plugin_path: str) -> dict[str, Any]:
    """Load one discovered VST3 plugin and return its actual exposed parameter names."""
    plugin = _safe_plugin_path(plugin_path)
    return inspect_plugin(plugin)


@mcp.tool()
def analyze_audio_wav(audio_path: str) -> dict[str, Any]:
    """Analyze a WAV inside the local audio workspace: duration, sample rate, peak and RMS."""
    return analyze_file(_safe_audio_path(audio_path, must_exist=True))


@mcp.tool()
def render_audio_through_vst3(
    input_wav: str,
    output_wav: str,
    plugin_path: str,
    wet: float = 1.0,
    parameters_json: str = "{}",
) -> dict[str, Any]:
    """Render a local WAV through one installed VST3 effect.

    Inspect the plugin first. parameters_json must be a JSON object with exact parameter
    names and numeric values exposed by that plugin. Output path must not already exist
    unless the user has explicitly approved overwriting it.
    """
    src = _safe_audio_path(input_wav, must_exist=True)
    dst = _safe_audio_path(output_wav)
    if dst.exists():
        raise FileExistsError(f"Output already exists; choose a new name to avoid overwriting: {dst}")
    plugin = _safe_plugin_path(plugin_path)
    parameters = json.loads(parameters_json)
    if not isinstance(parameters, dict) or not all(isinstance(k, str) for k in parameters):
        raise ValueError("parameters_json must be a JSON object with string keys.")
    return render_vst3(src, dst, plugin, parameters, wet)


@mcp.tool()
def render_vst3_effect_chain(
    input_wav: str,
    output_wav: str,
    plugins_json: str,
) -> dict[str, Any]:
    """Render a sequence of installed VST3 effects locally.

    plugins_json is a JSON array; each item has plugin_path, optional parameters object,
    and optional wet value. Every plugin must be discovered by scan_vst3_plugins. Output
    must not already exist. This MVP supports sequential audio effects, not MIDI instruments,
    sidechains, plugin GUI automation, or latency compensation.
    """
    src = _safe_audio_path(input_wav, must_exist=True)
    dst = _safe_audio_path(output_wav)
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
        steps.append({
            "path": str(safe_plugin),
            "parameters": item.get("parameters", {}),
            "wet": item.get("wet", 1.0),
        })
    manifest = _audio_root() / "mcp_effect_chain_manifest.json"
    if manifest.exists():
        # Use a per-call unique name to avoid collisions; only metadata, no audio.
        import uuid
        manifest = _audio_root() / f"mcp_effect_chain_{uuid.uuid4().hex}.json"
    manifest.write_text(json.dumps({"plugins": steps}, indent=2), encoding="utf-8")
    try:
        return render_chain(src, dst, manifest)
    finally:
        try:
            manifest.unlink(missing_ok=True)
        except OSError:
            pass


@mcp.tool()
def validate_automation_timeline(timeline_json: str) -> dict[str, Any]:
    """Validate an AI-proposed effect timeline before rendering.

    This tool checks event timing, unique IDs, supported event kinds, fade lengths,
    and schema safety. It does not render audio or guarantee a plugin is compatible.
    """
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


if __name__ == "__main__":
    mcp.run(transport="stdio")
