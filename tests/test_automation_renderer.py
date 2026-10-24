import json

import numpy as np
import pytest
import soundfile as sf

from app.automation_renderer import render_automation_timeline


def _write_source(path, duration=1.0, sr=16000):
    t = np.arange(int(duration * sr), dtype=np.float32) / sr
    audio = (0.2 * np.sin(2 * np.pi * 700 * t)).astype(np.float32)
    sf.write(path, audio, sr, subtype="PCM_24")
    return audio, sr


def _timeline(effect="builtin_telephone", **overrides):
    event = {
        "event_id": "event-1",
        "track_id": "vocal",
        "effect_kind": effect,
        "start_seconds": 0.2,
        "end_seconds": 0.8,
        "wet": 1.0,
        "fade_in_seconds": 0.05,
        "fade_out_seconds": 0.05,
        "parameters": {},
    }
    event.update(overrides)
    return json.dumps({
        "version": 1,
        "project_name": "renderer test",
        "duration_seconds": 1.0,
        "events": [event],
    })


def test_renders_time_local_effect_and_preserves_duration(tmp_path):
    source = tmp_path / "source.wav"
    output = tmp_path / "render.wav"
    original, sr = _write_source(source)
    report = render_automation_timeline(
        source, output, _timeline(), track_id="vocal", allowed_plugin_paths=set()
    )
    rendered, output_sr = sf.read(output, dtype="float32")
    assert report["rendered"] is True
    assert report["event_count"] == 1
    assert output_sr == sr
    assert len(rendered) == len(original)
    # The effect only touches its time range; regions outside it remain identical
    # within PCM quantization tolerance.
    assert np.allclose(rendered[:int(0.19 * sr)], original[:int(0.19 * sr)], atol=2e-5)
    assert np.allclose(rendered[int(0.82 * sr):], original[int(0.82 * sr):], atol=2e-5)
    assert np.mean(np.abs(rendered[int(0.3 * sr):int(0.7 * sr)] - original[int(0.3 * sr):int(0.7 * sr)])) > 1e-4


def test_never_overwrites_input_or_existing_output(tmp_path):
    source = tmp_path / "source.wav"
    _write_source(source)
    with pytest.raises(ValueError, match="must not overwrite"):
        render_automation_timeline(source, source, _timeline(), track_id="vocal")
    output = tmp_path / "existing.wav"
    output.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        render_automation_timeline(source, output, _timeline(), track_id="vocal")
    assert output.read_bytes() == b"keep"


def test_unsupported_pitch_correction_fails_without_claiming_render(tmp_path):
    source = tmp_path / "source.wav"
    output = tmp_path / "render.wav"
    _write_source(source)
    with pytest.raises(NotImplementedError, match="not implemented"):
        render_automation_timeline(
            source, output, _timeline("pitch_correction"), track_id="vocal",
            allowed_plugin_paths=set(),
        )
    assert not output.exists()


def test_rejects_events_for_a_different_track(tmp_path):
    source = tmp_path / "source.wav"
    output = tmp_path / "render.wav"
    _write_source(source)
    with pytest.raises(ValueError, match="one track"):
        render_automation_timeline(
            source, output, _timeline(track_id="instrumental"),
            track_id="vocal", allowed_plugin_paths=set(),
        )
    assert not output.exists()


def test_rejects_timeline_longer_than_input(tmp_path):
    source = tmp_path / "source.wav"
    output = tmp_path / "render.wav"
    _write_source(source, duration=0.5)
    with pytest.raises(ValueError, match="exceeds track duration"):
        render_automation_timeline(
            source, output, _timeline(), track_id="vocal", allowed_plugin_paths=set()
        )
    assert not output.exists()
