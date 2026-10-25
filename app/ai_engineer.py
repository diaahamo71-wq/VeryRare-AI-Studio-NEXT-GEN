"""Prompt-driven, guarded local AI mix planner.

The local language model interprets the user's creative brief and objective audio
measurements, then proposes bounded settings for the real built-in DSP engine.
It does not receive raw audio samples and must not be described as having listened
to the song. No heuristic fallback is used when the model is unavailable.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from app.audio_engine import analyze_file

_SETTINGS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "vocal_gain_db": {"type": "number"},
        "instrumental_gain_db": {"type": "number"},
        "vocal_highpass_hz": {"type": "number"},
        "vocal_presence_db": {"type": "number"},
        "compression_ratio": {"type": "number"},
        "compression_threshold_db": {"type": "number"},
        "reverb_mix": {"type": "number"},
        "delay_mix": {"type": "number"},
        "delay_ms": {"type": "number"},
        "master_peak_dbfs": {"type": "number"},
        "decisions": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "summary", "vocal_gain_db", "instrumental_gain_db",
        "vocal_highpass_hz", "vocal_presence_db", "compression_ratio",
        "compression_threshold_db", "reverb_mix", "delay_mix", "delay_ms",
        "master_peak_dbfs", "decisions", "warnings",
    ],
    "additionalProperties": False,
}

_BOUNDS = {
    "vocal_gain_db": (-18.0, 12.0),
    "instrumental_gain_db": (-18.0, 12.0),
    "vocal_highpass_hz": (20.0, 250.0),
    "vocal_presence_db": (-6.0, 6.0),
    "compression_ratio": (1.0, 6.0),
    "compression_threshold_db": (-36.0, -6.0),
    "reverb_mix": (0.0, 0.35),
    "delay_mix": (0.0, 0.30),
    "delay_ms": (60.0, 700.0),
    "master_peak_dbfs": (-3.0, -0.1),
}


def _bounded_settings(candidate: dict[str, Any]) -> dict[str, float]:
    settings: dict[str, float] = {}
    for key, (low, high) in _BOUNDS.items():
        value = candidate.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"AI response has a missing or invalid numeric setting: {key}")
        number = float(value)
        if not low <= number <= high:
            raise ValueError(f"AI response proposed {key}={number}, outside the safe range {low}..{high}.")
        settings[key] = number
    return settings


def plan_ai_mix(vocal_path: str | Path, beat_path: str | Path, brief: str) -> dict[str, Any]:
    """Use a locally installed Ollama model to plan a mix from brief + measurements."""
    model = os.environ.get("VERYRARE_LOCAL_MODEL", "qwen3:4b-instruct")
    base_url = os.environ.get("VERYRARE_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    measurements = {
        "vocal": analyze_file(vocal_path),
        "instrumental": analyze_file(beat_path),
    }
    system_prompt = (
        "You are the cautious mix engineer for VeryRare Studio. Interpret the user's "
        "creative brief and the supplied objective WAV measurements. Return only the "
        "requested JSON schema. Choose settings that fit the brief; do not blindly add "
        "effects. Keep intimate vocals intelligible and avoid extreme processing. "
        "Dreamcore/otherworldly may justify subtle ambience or delay, but only if the "
        "brief asks for it. Natural/dry means little or no ambience. Preserve the "
        "performer's identity: do not propose pitch/formant changes or voice conversion. "
        "The available DSP controls are gain, high-pass, presence EQ, simple compression, "
        "short-tap reverb, delay, and sample-peak ceiling. Do not claim these controls "
        "can repair artifacts, restore lost source effects, align timing, or perform "
        "true-peak/LUFS mastering. Measurements are not a substitute for listening. "
        "Use conservative values and explain each decision briefly. All numeric values "
        "must remain within the JSON schema ranges described by the tool."
    )
    payload = {
        "model": model,
        "stream": False,
        "format": _SETTINGS_SCHEMA,
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({
                "creative_brief": brief.strip(),
                "objective_measurements": measurements,
                "task": "Plan the best conservative starting mix for these tracks.",
            }, ensure_ascii=False)},
        ],
    }
    request = urllib.request.Request(
        base_url + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Local AI is unavailable. Install/start Ollama and download model '{model}'. "
            "No heuristic substitute was used."
        ) from exc
    except TimeoutError as exc:
        raise RuntimeError("The local AI timed out while planning. Try again or use a smaller model.") from exc

    message = raw.get("message", {}).get("content", "")
    try:
        candidate = json.loads(message)
    except (TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("The local AI returned invalid structured output; no mix settings were applied.") from exc
    if not isinstance(candidate, dict):
        raise RuntimeError("The local AI response was not a settings object.")
    settings = _bounded_settings(candidate)
    return {
        "mode": "local_pretrained_llm",
        "model": model,
        "summary": str(candidate.get("summary", "AI mix plan")),
        "settings": settings,
        "decisions": [str(item) for item in candidate.get("decisions", [])][:12],
        "warnings": [str(item) for item in candidate.get("warnings", [])][:12],
        "measurements": measurements,
        "executed": False,
        "execution_note": (
            "The AI has planned and validated settings. The app must pass these settings "
            "to the real DSP renderer; the model itself does not process audio samples."
        ),
    }


def plan_ai_mix_cloud(vocal_path: str | Path, beat_path: str | Path, brief: str) -> dict[str, Any]:
    """Use OpenRouter to plan a mix from the brief and measurements; audio bytes stay local."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("Cloud AI needs OPENROUTER_API_KEY set in the environment; the key is never stored in the repository.")
    model = os.environ.get("VERYRARE_CLOUD_MIX_MODEL", "openrouter/free")
    measurements = {
        "vocal": analyze_file(vocal_path),
        "instrumental": analyze_file(beat_path),
    }
    system_prompt = (
        "You are the cautious mix engineer for VeryRare Studio. Use only the creative brief "
        "and objective WAV measurements provided. You have NOT heard the audio. Return one JSON "
        "object matching the supplied schema. Choose conservative settings, preserve an intimate "
        "natural vocal, and do not add effects unless requested. Dreamcore may justify subtle "
        "ambience. Available DSP: gain, high-pass, presence EQ, simple compression, short-tap "
        "reverb, delay and sample-peak ceiling. Do not claim to fix artifacts, restore source "
        "effects, align timing or perform true-peak/LUFS mastering. Explain decisions briefly."
    )
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({
                "creative_brief": brief.strip(),
                "objective_measurements": measurements,
                "task": "Plan a conservative starting mix for the actual local DSP renderer.",
            }, ensure_ascii=False)},
        ],
        "temperature": 0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "veryrare_mix_plan",
                "strict": True,
                "schema": _SETTINGS_SCHEMA,
            },
        },
    }
    url = "https://openrouter.ai/api/v1/chat/completions"
    request = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "https://github.com/diaahamo71-wq/VeryRare-AI-Studio-NEXT-GEN",
            "X-Title": "VeryRare AI Studio",
        }, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"OpenRouter cloud AI request failed with HTTP {exc.code}; check API key, model access and quota. {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Could not reach the cloud AI service. Check internet access and try again.") from exc
    try:
        candidate = json.loads(raw["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Cloud AI returned invalid structured output; no mix settings were applied.") from exc
    if not isinstance(candidate, dict):
        raise RuntimeError("Cloud AI response was not a settings object.")
    settings = _bounded_settings(candidate)
    return {
        "mode": "cloud_pretrained_llm",
        "model": model,
        "summary": str(candidate.get("summary", "Cloud AI mix plan")),
        "settings": settings,
        "decisions": [str(item) for item in candidate.get("decisions", [])][:12],
        "warnings": [str(item) for item in candidate.get("warnings", [])][:12],
        "measurements": measurements,
        "executed": False,
        "execution_note": (
            "Only the brief and numeric measurements were sent to OpenRouter; audio files remained local. "
            "The validated settings are applied by the local DSP renderer. The cloud model did not hear the tracks."
        ),
    }
