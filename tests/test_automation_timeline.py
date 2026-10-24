import json
import pytest
from pydantic import ValidationError

from app.automation_timeline import AutomationTimeline, validate_timeline_json


def test_valid_timeline_is_marked_validated_not_rendered():
    payload = {
        "version": 1,
        "project_name": "VeryRare demo",
        "duration_seconds": 60,
        "events": [{
            "event_id": "telephone-1",
            "track_id": "vocal",
            "effect_kind": "builtin_telephone",
            "start_seconds": 12.0,
            "end_seconds": 13.2,
            "wet": 0.8,
            "fade_in_seconds": 0.05,
            "fade_out_seconds": 0.1,
        }],
    }
    result = validate_timeline_json(json.dumps(payload))
    assert result["validated"] is True
    assert result["rendered"] is False
    assert result["events"][0]["effect_kind"] == "builtin_telephone"


def test_rejects_duplicate_event_ids():
    payload = {
        "duration_seconds": 10,
        "events": [
            {"event_id": "same", "track_id": "vocal", "effect_kind": "builtin_reverb", "start_seconds": 0, "end_seconds": 2},
            {"event_id": "same", "track_id": "vocal", "effect_kind": "builtin_delay", "start_seconds": 2, "end_seconds": 4},
        ],
    }
    with pytest.raises(ValidationError):
        AutomationTimeline.model_validate(payload)


def test_rejects_event_outside_timeline():
    payload = {
        "duration_seconds": 5,
        "events": [{"event_id": "late", "track_id": "vocal", "effect_kind": "builtin_reverb", "start_seconds": 4, "end_seconds": 6}],
    }
    with pytest.raises(ValidationError):
        AutomationTimeline.model_validate(payload)


def test_vst3_event_requires_plugin_path():
    payload = {
        "duration_seconds": 10,
        "events": [{"event_id": "plugin", "track_id": "vocal", "effect_kind": "vst3", "start_seconds": 1, "end_seconds": 2}],
    }
    with pytest.raises(ValidationError):
        AutomationTimeline.model_validate(payload)


def test_rejects_unknown_fields_instead_of_silently_ignoring_them():
    payload = {"duration_seconds": 10, "events": [], "execute_shell": True}
    with pytest.raises(ValidationError):
        AutomationTimeline.model_validate(payload)
