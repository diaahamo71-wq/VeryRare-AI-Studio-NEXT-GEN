"""Guarded agent routing for the VeryRare local-first audio studio.

Agents may propose operations only through an explicit plugin manifest. They
cannot execute shell commands, arbitrary Python, or load paths not approved by
the user. Audio files stay local unless the user explicitly opts into cloud
prompt processing and sends text only.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Literal
import json
import os
import urllib.request
import urllib.error

AgentMode = Literal["local", "cloud", "auto"]


@dataclass
class AgentConfig:
    mode: AgentMode = "auto"
    local_base_url: str = "http://127.0.0.1:11434"
    local_model: str = "gemma3:4b"
    cloud_provider: str = "openrouter"
    cloud_model: str = "openrouter/free"
    cloud_api_key_env: str = "OPENROUTER_API_KEY"
    allow_cloud: bool = False
    timeout_seconds: int = 45


def _local_plan(prompt: str, config: AgentConfig) -> dict[str, Any]:
    """Call a local Ollama model using its native JSON API."""
    body = {
        "model": config.local_model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content":
             "You are the audio engineering planner for VeryRare AI Studio. "
             "Return JSON only with keys summary, operations, needs_user_input. "
             "Each operation must contain track (vocal, instrumental, master), "
             "capability, plugin_name_or_id, parameter_intent, wet (0..1), "
             "reason. Never invent installed plugins. Never claim a plugin ran. "
             "If key/scale or other required info is missing, list it in needs_user_input. "
             "This plan is advisory and must be validated against the installed plugin manifest."},
            {"role": "user", "content": prompt},
        ],
    }
    request = urllib.request.Request(
        config.local_base_url.rstrip("/") + "/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    content = payload.get("message", {}).get("content", "")
    result = json.loads(content)
    result["agent"] = "local"
    return result


def _cloud_plan(prompt: str, config: AgentConfig) -> dict[str, Any]:
    """Optional OpenRouter text API; requires user-provided key and explicit opt-in."""
    if not config.allow_cloud:
        raise PermissionError("Cloud agent disabled. Explicitly enable cloud text planning first.")
    key = os.environ.get(config.cloud_api_key_env)
    if not key:
        raise RuntimeError(f"Missing API key in environment variable {config.cloud_api_key_env}.")
    model = config.cloud_model
    url = "https://openrouter.ai/api/v1/chat/completions"
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content":
             "You plan audio processing for VeryRare AI Studio. Return valid JSON only with keys "
             "summary, operations, needs_user_input. Each operation must have track, capability, "
             "plugin_name_or_id, parameter_intent, wet (0..1), reason. Do not claim plugins ran. "
             "Do not invent installed plugins. Ask for missing key/scale information."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "https://github.com/diaahamo71-wq/VeryRare-AI-Studio-NEXT-GEN",
            "X-Title": "VeryRare AI Studio",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(
            f"OpenRouter cloud planner HTTP error {exc.code}; check API key, model access and quota. {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Could not reach OpenRouter. Check internet access and try again.") from exc
    try:
        content = payload["choices"][0]["message"]["content"]
        result = json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("OpenRouter returned invalid JSON; no plan was accepted.") from exc
    if not isinstance(result, dict):
        raise RuntimeError("OpenRouter response was not a JSON object.")
    result["agent"] = "cloud"
    result["model"] = model
    return result


def plan_with_agent(prompt: str, config: AgentConfig | None = None) -> dict[str, Any]:
    """Prefer local for privacy; optionally fall back to cloud for text-only planning."""
    config = config or AgentConfig()
    if config.mode == "local":
        return _local_plan(prompt, config)
    if config.mode == "cloud":
        return _cloud_plan(prompt, config)
    try:
        return _local_plan(prompt, config)
    except Exception as local_error:
        if not config.allow_cloud:
            return {
                "agent": "local-unavailable",
                "summary": "Local planner is unavailable; cloud fallback is disabled.",
                "operations": [],
                "needs_user_input": [],
                "error": f"{type(local_error).__name__}: {local_error}",
            }
        result = _cloud_plan(prompt, config)
        result["fallback_reason"] = f"{type(local_error).__name__}: {local_error}"
        return result


def save_plan(plan: dict[str, Any], path: str) -> None:
    """Save a reviewable plan; does not execute plugins."""
    with open(path, "w", encoding="utf-8") as file:
        json.dump(plan, file, indent=2, ensure_ascii=False)
