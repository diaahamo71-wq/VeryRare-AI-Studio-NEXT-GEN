from io import BytesIO

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient
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



def _wav_bytes(frequency: float = 220.0, sample_rate: int = 16000) -> bytes:
    samples = np.arange(1600, dtype=np.float32) / sample_rate
    signal = 0.08 * np.sin(2 * np.pi * frequency * samples)
    buffer = BytesIO()
    sf.write(buffer, signal, sample_rate, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


def test_health_route_reports_local_only():
    response = TestClient(web_app.app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["cloud_audio_upload"] is False


def test_import_and_mix_routes_create_new_wav_files(tmp_path, monkeypatch):
    monkeypatch.setattr(web_app, "WORKSPACE", tmp_path.resolve())
    client = TestClient(web_app.app)
    imported = client.post(
        "/api/import",
        files={
            "vocal": ("vocal.wav", _wav_bytes(220), "audio/wav"),
            "beat": ("beat.wav", _wav_bytes(110), "audio/wav"),
        },
    )
    assert imported.status_code == 200, imported.text
    data = imported.json()
    assert data["vocal"]["analysis"]["sample_rate_hz"] == 16000
    assert data["beat"]["analysis"]["duration_seconds"] == pytest.approx(0.1)
    rendered = client.post(
        "/api/mix",
        json={
            "vocal_file": data["vocal"]["file"],
            "beat_file": data["beat"]["file"],
            "reverb_mix": 0,
            "delay_mix": 0,
        },
    )
    assert rendered.status_code == 200, rendered.text
    result = rendered.json()
    assert result["rendered"] is True
    assert result["output_file"] != data["vocal"]["file"]
    assert result["reference_file"] != result["output_file"]
    preview = client.get(result["audio_url"])
    assert preview.status_code == 200
    assert preview.headers["content-type"].startswith("audio/wav")
