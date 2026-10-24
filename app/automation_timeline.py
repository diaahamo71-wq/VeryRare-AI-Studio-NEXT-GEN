"""Typed validation for AI-generated audio automation timelines.

Validation is not rendering: callers must keep that distinction explicit.
"""
from __future__ import annotations
import json
import math
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

EffectKind = Literal["builtin_telephone", "builtin_reverb", "builtin_delay", "builtin_eq", "builtin_compressor", "vst3", "harmonizer", "pitch_correction"]

class AutomationEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(min_length=1, max_length=80)
    track_id: str = Field(min_length=1, max_length=80)
    effect_kind: EffectKind
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    wet: float = Field(default=1.0, ge=0, le=1)
    parameters: dict[str, float | str | bool] = Field(default_factory=dict)
    plugin_path: str | None = None
    fade_in_seconds: float = Field(default=0.0, ge=0)
    fade_out_seconds: float = Field(default=0.0, ge=0)
    enabled: bool = True
    decision_source: Literal["user", "ai", "reference_analysis"] = "ai"
    confidence: float | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def check_event(self):
        if self.end_seconds <= self.start_seconds:
            raise ValueError("end_seconds must be greater than start_seconds")
        if self.fade_in_seconds + self.fade_out_seconds > self.end_seconds - self.start_seconds:
            raise ValueError("fade lengths exceed event duration")
        if self.effect_kind == "vst3" and not self.plugin_path:
            raise ValueError("vst3 events require plugin_path")
        if self.effect_kind != "vst3" and self.plugin_path is not None:
            raise ValueError("plugin_path is only valid for vst3 events")
        for key, value in self.parameters.items():
            if not key.strip():
                raise ValueError("parameter names cannot be empty")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(f"parameter {key!r} must be finite")
        return self

class AutomationTimeline(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1] = 1
    project_name: str = Field(default="Untitled", min_length=1, max_length=120)
    duration_seconds: float = Field(gt=0)
    events: list[AutomationEvent] = Field(default_factory=list, max_length=500)
    notes: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def check_timeline(self):
        ids = [event.event_id for event in self.events]
        if len(ids) != len(set(ids)):
            raise ValueError("event_id values must be unique")
        for event in self.events:
            if event.end_seconds > self.duration_seconds:
                raise ValueError(f"event {event.event_id!r} exceeds timeline duration")
        return self

def validate_timeline_json(raw_json: str) -> dict[str, Any]:
    """Return normalized, validated timeline data; does not process audio."""
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON at line {exc.lineno}, column {exc.colno}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Timeline must be a JSON object")
    result = AutomationTimeline.model_validate(payload).model_dump(mode="json")
    result["validated"] = True
    result["rendered"] = False
    result["execution_notice"] = "Schema validation only; no audio was processed."
    return result
