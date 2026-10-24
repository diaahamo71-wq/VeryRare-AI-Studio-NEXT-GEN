"""Offline time-local automation renderer for one WAV track.

Only the event kinds implemented here are rendered. Unsupported AI-style effects
fail loudly rather than being approximated or reported as successful.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from scipy import signal

from app.automation_timeline import AutomationTimeline
from app.audio_engine import _compress, _db_to_gain, _presence_eq

try:
    from pedalboard import Delay, Reverb, load_plugin
except ImportError:  # keep the built-in effects usable without the optional host
    Delay = Reverb = load_plugin = None


IMPLEMENTED_BUILTINS = {
    "builtin_telephone", "builtin_reverb", "builtin_delay",
    "builtin_eq", "builtin_compressor",
}
NOT_IMPLEMENTED = {"harmonizer", "pitch_correction"}


def _finite_number(params: dict[str, Any], key: str, default: float,
                   low: float, high: float) -> float:
    value = params.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Parameter {key!r} must be a number.")
    value = float(value)
    if not np.isfinite(value) or not low <= value <= high:
        raise ValueError(f"Parameter {key!r} must be between {low} and {high}.")
    return value


def _to_stereo(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return np.repeat(audio[:, None], 2, axis=1)
    if audio.shape[1] == 1:
        return np.repeat(audio, 2, axis=1)
    if audio.shape[1] >= 2:
        return audio[:, :2].copy()
    raise ValueError("Audio must have at least one channel.")


def _apply_builtin(kind: str, region: np.ndarray, sr: int,
                   params: dict[str, Any]) -> np.ndarray:
    x = region.astype(np.float32, copy=True)
    nyquist = sr * 0.5

    if kind == "builtin_telephone":
        low = _finite_number(params, "low_cut_hz", 300.0, 80.0, min(1200.0, nyquist * 0.8))
        high = _finite_number(params, "high_cut_hz", 3400.0, max(500.0, low + 50), min(10000.0, nyquist * 0.95))
        if high <= low:
            raise ValueError("Telephone high_cut_hz must exceed low_cut_hz.")
        sos = signal.butter(3, [low, high], btype="bandpass", fs=sr, output="sos")
        y = signal.sosfilt(sos, x, axis=0).astype(np.float32)
        drive = _finite_number(params, "drive", 1.25, 1.0, 5.0)
        return (np.tanh(y * drive) / np.tanh(drive)).astype(np.float32)

    if kind == "builtin_eq":
        hp = _finite_number(params, "highpass_hz", 20.0, 20.0, min(2000.0, nyquist * 0.8))
        lp = _finite_number(params, "lowpass_hz", min(18000.0, nyquist * 0.9), hp + 1.0, nyquist * 0.95)
        gain = _finite_number(params, "presence_db", 0.0, -12.0, 12.0)
        sos = signal.butter(2, hp, btype="highpass", fs=sr, output="sos")
        y = signal.sosfilt(sos, x, axis=0).astype(np.float32)
        sos = signal.butter(2, lp, btype="lowpass", fs=sr, output="sos")
        y = signal.sosfilt(sos, y, axis=0).astype(np.float32)
        center = _finite_number(params, "presence_hz", 3200.0, 100.0, min(16000.0, nyquist * 0.9))
        return _presence_eq(y, sr, center, gain).astype(np.float32)

    if kind == "builtin_compressor":
        threshold = _finite_number(params, "threshold_db", -18.0, -48.0, -3.0)
        ratio = _finite_number(params, "ratio", 3.0, 1.0, 12.0)
        return _compress(x, sr, threshold, ratio).astype(np.float32)

    if kind == "builtin_delay":
        if Delay is None:
            raise RuntimeError("Pedalboard is required for the built-in delay but is not installed.")
        seconds = _finite_number(params, "delay_seconds", 0.28, 0.06, 1.5)
        feedback = _finite_number(params, "feedback", 0.25, 0.0, 0.85)
        # Pedalboard's Delay is a built-in effect already covered by this project's
        # declared dependency; no third-party plugin is downloaded or installed.
        effect = Delay(delay_seconds=seconds, feedback=feedback, mix=1.0)
        y = np.asarray(effect(x.T, sample_rate=sr), dtype=np.float32)
        if y.ndim == 1:
            y = y[None, :]
        if y.T.shape != x.shape:
            raise RuntimeError("Built-in delay changed audio dimensions; render was stopped.")
        return y.T

    if kind == "builtin_reverb":
        if Reverb is None:
            raise RuntimeError("Pedalboard is required for the built-in reverb but is not installed.")
        room = _finite_number(params, "room_size", 0.35, 0.0, 1.0)
        damping = _finite_number(params, "damping", 0.5, 0.0, 1.0)
        width = _finite_number(params, "width", 1.0, 0.0, 1.0)
        effect = Reverb(room_size=room, damping=damping, width=width, wet_level=1.0, dry_level=0.0)
        y = np.asarray(effect(x.T, sample_rate=sr), dtype=np.float32)
        if y.ndim == 1:
            y = y[None, :]
        if y.T.shape != x.shape:
            raise RuntimeError("Built-in reverb changed audio dimensions; render was stopped.")
        return y.T

    raise ValueError(f"Unsupported built-in effect: {kind}")


def render_automation_timeline(
    input_wav: str | Path,
    output_wav: str | Path,
    timeline_json: str,
    *,
    track_id: str,
    allowed_plugin_paths: set[str] | None = None,
) -> dict[str, Any]:
    """Render one track's time-local effects; never overwrites source or output."""
    source, target = Path(input_wav).resolve(), Path(output_wav).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Input WAV not found: {source}")
    if source == target:
        raise ValueError("Output must not overwrite the input file.")
    if target.exists():
        raise FileExistsError(f"Output already exists; choose a new name: {target}")

    try:
        timeline_data = json.loads(timeline_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid timeline JSON at line {exc.lineno}, column {exc.colno}") from exc
    timeline = AutomationTimeline.model_validate(timeline_data)
    enabled_events = [e for e in timeline.events if e.enabled]
    other_tracks = sorted({e.track_id for e in enabled_events if e.track_id != track_id})
    if other_tracks:
        raise ValueError(
            f"This render accepts one track ({track_id!r}); timeline also contains enabled "
            f"events for {other_tracks}. Render each track separately."
        )

    audio, sr = sf.read(str(source), dtype="float32", always_2d=True)
    if audio.ndim != 2 or len(audio) < 2 or not np.isfinite(audio).all():
        raise ValueError("Input must be a finite, non-empty audio WAV.")
    if not 8000 <= int(sr) <= 192000:
        raise ValueError(f"Unsupported sample rate: {sr}")
    audio = _to_stereo(audio)
    duration = len(audio) / sr
    if timeline.duration_seconds > duration + max(1.0 / sr, 0.00051):
        raise ValueError(
            f"Timeline duration ({timeline.duration_seconds:.3f}s) exceeds track duration ({duration:.3f}s)."
        )

    current = audio.copy()
    reports: list[dict[str, Any]] = []
    for event in sorted(enabled_events, key=lambda e: (e.start_seconds, e.end_seconds, e.event_id)):
        start = min(len(current), int(round(event.start_seconds * sr)))
        end = min(len(current), int(round(event.end_seconds * sr)))
        if end <= start:
            raise ValueError(f"Event {event.event_id!r} maps to an empty audio region.")
        dry = current[start:end].copy()
        params = dict(event.parameters)
        if event.effect_kind in NOT_IMPLEMENTED:
            raise NotImplementedError(
                f"{event.effect_kind} is not implemented; no output was written. "
                "Install and verify a suitable dedicated processor before using this event."
            )
        if event.effect_kind == "vst3":
            plugin_path = str(Path(event.plugin_path or "").expanduser().resolve())
            if allowed_plugin_paths is None or plugin_path not in allowed_plugin_paths:
                raise PermissionError("VST3 path must exactly match a discovered, allowlisted plugin.")
            if load_plugin is None:
                raise RuntimeError("Pedalboard VST3 host is unavailable.")
            plugin = load_plugin(plugin_path, parameter_values=params)
            if not getattr(plugin, "is_effect", False):
                raise ValueError(f"Plugin for event {event.event_id!r} is not an audio effect.")
            wet_audio = np.asarray(plugin(dry.T, sample_rate=int(sr)), dtype=np.float32)
            if wet_audio.ndim == 1:
                wet_audio = wet_audio[None, :]
            wet_audio = wet_audio.T
            if wet_audio.shape != dry.shape:
                raise RuntimeError(
                    f"Plugin event {event.event_id!r} changed region shape {dry.shape} -> {wet_audio.shape}; "
                    "latency/buffer compensation is not implemented."
                )
        else:
            wet_audio = _apply_builtin(event.effect_kind, dry, int(sr), params)

        fade = np.ones(end - start, dtype=np.float32)
        fade_in = min(len(fade), int(round(event.fade_in_seconds * sr)))
        fade_out = min(len(fade), int(round(event.fade_out_seconds * sr)))
        if fade_in:
            fade[:fade_in] *= np.linspace(0.0, 1.0, fade_in, endpoint=True, dtype=np.float32)
        if fade_out:
            fade[-fade_out:] *= np.linspace(1.0, 0.0, fade_out, endpoint=True, dtype=np.float32)
        blend = (float(event.wet) * fade)[:, None]
        if not np.isfinite(wet_audio).all():
            raise RuntimeError(f"Effect event {event.event_id!r} produced non-finite samples.")
        current[start:end] = dry * (1.0 - blend) + wet_audio * blend
        reports.append({
            "event_id": event.event_id,
            "track_id": event.track_id,
            "effect_kind": event.effect_kind,
            "start_seconds": event.start_seconds,
            "end_seconds": event.end_seconds,
            "wet": event.wet,
            "fade_in_seconds": event.fade_in_seconds,
            "fade_out_seconds": event.fade_out_seconds,
            "rendered": True,
        })

    target.parent.mkdir(parents=True, exist_ok=True)
    peak_before_ceiling = float(np.max(np.abs(current)))
    # Do not silently normalize: preserve level and report possible clipping.
    sf.write(str(target), current, int(sr), subtype="PCM_24")
    reread, out_sr = sf.read(str(target), dtype="float32", always_2d=True)
    if out_sr != sr or reread.shape != current.shape or not np.isfinite(reread).all():
        target.unlink(missing_ok=True)
        raise RuntimeError("Output verification failed; invalid render was removed.")
    report = {
        "input": str(source),
        "output": str(target),
        "sample_rate_hz": int(sr),
        "channels": int(current.shape[1]),
        "duration_seconds": round(len(current) / sr, 6),
        "track_id": track_id,
        "event_count": len(reports),
        "events": reports,
        "rendered": True,
        "peak_before_write": peak_before_ceiling,
        "may_clip": bool(peak_before_ceiling >= 1.0),
        "notes": [
            "Events are processed in ascending start-time order; overlapping events are sequential.",
            "Effects are confined to their selected regions; reverb/delay tails beyond event end are not extended.",
            "Harmonizer and pitch correction are not implemented by this renderer.",
            "Third-party VST3 plugins are not sandboxed; only use trusted plugins.",
        ],
    }
    target.with_suffix(".automation-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report
