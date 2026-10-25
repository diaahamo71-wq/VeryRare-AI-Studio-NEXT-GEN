from app.ai_engineer import _bounded_settings


def test_ai_settings_are_rejected_outside_safe_ranges():
    candidate = {
        "vocal_gain_db": 0,
        "instrumental_gain_db": -3,
        "vocal_highpass_hz": 80,
        "vocal_presence_db": 1,
        "compression_ratio": 2,
        "compression_threshold_db": -18,
        "reverb_mix": 0.1,
        "delay_mix": 0.05,
        "delay_ms": 260,
        "master_peak_dbfs": -1,
    }
    assert _bounded_settings(candidate)["reverb_mix"] == 0.1
    candidate["reverb_mix"] = 0.9
    import pytest
    with pytest.raises(ValueError, match="outside the safe range"):
        _bounded_settings(candidate)


def test_ai_settings_reject_missing_or_non_numeric_values():
    import pytest
    with pytest.raises(ValueError, match="invalid numeric setting"):
        _bounded_settings({"vocal_gain_db": "loud"})
