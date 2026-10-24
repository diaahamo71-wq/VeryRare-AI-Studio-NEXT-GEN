from pathlib import Path

import pytest
from pydantic import ValidationError

from app import web_app


def test_workspace_file_rejects_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(web_app, "WORKSPACE", tmp_path.resolve())
    with pytest.raises(web_app.HTTPException) as exc:
        web_app._safe_workspace_file("../outside.wav", must_exist=False)
    assert exc.value.status_code == 400


def test_workspace_file_requires_existing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(web_app, "WORKSPACE", tmp_path.resolve())
    with pytest.raises(web_app.HTTPException) as exc:
        web_app._safe_workspace_file("missing.wav", must_exist=True)
    assert exc.value.status_code == 404


def test_workspace_file_accepts_a_file_inside_workspace(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    monkeypatch.setattr(web_app, "WORKSPACE", root)
    audio = root / "vocal.wav"
    audio.write_bytes(b"test")
    assert web_app._safe_workspace_file("vocal.wav") == audio


@pytest.mark.parametrize(
    "kwargs",
    [
        {"vocal_file": "../outside.wav", "beat_file": "beat.wav"},
        {"vocal_file": "vocal.wav", "beat_file": "beat.wav", "reverb_mix": 2.0},
        {"vocal_file": "vocal.wav", "beat_file": "beat.wav", "vocal_gain_db": 99},
        {"vocal_file": "vocal.wav", "beat_file": "beat.wav", "master_peak_dbfs": -10},
    ],
)
def test_mix_request_rejects_out_of_range_settings(kwargs):
    with pytest.raises(ValidationError):
        web_app.MixRequest(**kwargs)


def test_mix_request_accepts_safe_defaults():
    request = web_app.MixRequest(vocal_file="vocal.wav", beat_file="beat.wav")
    assert request.reverb_mix == pytest.approx(0.08)
    assert request.master_peak_dbfs == pytest.approx(-1.0)
