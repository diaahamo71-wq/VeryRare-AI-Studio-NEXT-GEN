from pathlib import Path

import numpy as np
import soundfile as sf

from app.smart_engine import recommend_mix


def test_recommend_mix_returns_editable_conservative_settings(tmp_path: Path):
    sr = 16000
    t = np.arange(sr, dtype=np.float32) / sr
    vocal = 0.05 * np.sin(2 * np.pi * 220 * t)
    beat = 0.08 * np.sin(2 * np.pi * 110 * t)
    vocal_path = tmp_path / "vocal.wav"
    beat_path = tmp_path / "beat.wav"
    sf.write(vocal_path, vocal.astype(np.float32), sr)
    sf.write(beat_path, beat.astype(np.float32), sr)

    result = recommend_mix(vocal_path, beat_path, "warm dreamy dreamcore vocal")

    assert result["mode"] == "local_heuristic"
    assert result["executed"] is False
    assert -18 <= result["settings"]["vocal_gain_db"] <= 12
    assert 0 <= result["settings"]["reverb_mix"] <= 0.35
    assert 0 <= result["settings"]["delay_mix"] <= 0.30
    assert result["settings"]["reverb_mix"] == 0.12
    assert result["settings"]["delay_mix"] == 0.06
    assert result["measurements"]["vocal"]["sample_rate_hz"] == sr
    assert result["reasons"]
    assert result["limitations"]
