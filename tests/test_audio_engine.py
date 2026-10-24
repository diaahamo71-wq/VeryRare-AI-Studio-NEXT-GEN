from pathlib import Path

import numpy as np
import soundfile as sf
import pytest

from app.audio_engine import MixSettings, analyze_file, mix_tracks


def test_mix_renders_pcm24_and_report(tmp_path: Path):
    sr = 16000
    t = np.arange(sr, dtype=np.float32) / sr
    vocal = (0.12 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    beat = (0.08 * np.sin(2 * np.pi * 110 * t)).astype(np.float32)
    vocal_path = tmp_path / "vocal.wav"
    beat_path = tmp_path / "beat.wav"
    output = tmp_path / "mix.wav"
    sf.write(vocal_path, vocal, sr)
    sf.write(beat_path, beat, sr)

    report = mix_tracks(vocal_path, beat_path, output, MixSettings(reverb_mix=0.02))
    audio, out_sr = sf.read(output, always_2d=True)
    assert out_sr == sr
    assert audio.shape == (sr, 2)
    assert np.isfinite(audio).all()
    assert report["status"] == "rendered"
    assert report["checks"]["output_peak_below_ceiling"]
    assert output.with_suffix(".report.json").is_file()
    assert sf.info(output).subtype == "PCM_24"


def test_sample_rate_mismatch_is_rejected(tmp_path: Path):
    vocal_path = tmp_path / "vocal.wav"
    beat_path = tmp_path / "beat.wav"
    sf.write(vocal_path, np.zeros(1000, dtype=np.float32), 16000)
    sf.write(beat_path, np.zeros(1000, dtype=np.float32), 22050)
    with pytest.raises(ValueError, match="Sample rates differ"):
        mix_tracks(vocal_path, beat_path, tmp_path / "mix.wav")


def test_analysis_reports_clipping(tmp_path: Path):
    audio_path = tmp_path / "test.wav"
    sf.write(audio_path, np.array([0.0, 1.0, -1.0, 0.2], dtype=np.float32), 16000)
    result = analyze_file(audio_path)
    assert result["clipped_sample_count"] >= 2
    assert result["duration_seconds"] == 0.0 or result["duration_seconds"] > 0
