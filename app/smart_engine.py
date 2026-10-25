"""Transparent, local-first starting-point recommendations for vocal mixing.

These are conservative heuristics, not an AI claim or a replacement for listening.
The recommendations are derived from measured WAV statistics and an optional brief.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.audio_engine import MixSettings, analyze_file


def recommend_mix(vocal_path: str | Path, beat_path: str | Path, brief: str = "") -> dict[str, Any]:
    """Return a safe editable mix starting point with an explanation for every choice."""
    vocal_path, beat_path = Path(vocal_path), Path(beat_path)
    vocal = analyze_file(vocal_path)
    beat = analyze_file(beat_path)
    prompt = (brief or "").lower()

    # Start from the studio's restrained default; adapt only when measurements or
    # explicit creative words justify a change.
    settings = MixSettings()
    reasons: list[str] = []

    vocal_rms = float(vocal["rms_dbfs"])
    beat_rms = float(beat["rms_dbfs"])
    vocal_peak = float(vocal["peak_dbfs"])

    if vocal_rms < -30:
        settings.vocal_gain_db = 3.0
        reasons.append("The vocal RMS is very low; a modest +3 dB starting gain may help it sit in the mix.")
    elif vocal_rms > -12:
        settings.vocal_gain_db = -2.0
        reasons.append("The vocal RMS is high; a small level reduction leaves more headroom.")
    else:
        reasons.append("The vocal level is within a broad working range; vocal gain is left at unity.")

    if beat_rms > vocal_rms + 8:
        settings.instrumental_gain_db = -5.0
        reasons.append("The instrumental RMS is substantially above the vocal; the beat is lowered conservatively.")
    elif vocal_rms > beat_rms + 8:
        settings.instrumental_gain_db = -1.0
        reasons.append("The vocal RMS is substantially above the beat; the beat is not attenuated as much.")
    else:
        settings.instrumental_gain_db = -3.0
        reasons.append("The vocal and instrumental RMS levels are not extremely far apart; the beat starts at -3 dB.")

    if vocal_peak > -1.0:
        settings.compression_ratio = 2.5
        settings.compression_threshold_db = -20.0
        reasons.append("The vocal has near-full-scale peaks; moderate compression is suggested, but peak control still needs listening.")
    else:
        settings.compression_ratio = 2.0
        settings.compression_threshold_db = -18.0
        reasons.append("A gentle 2:1 compressor is used as a starting point, not an automatic loudness target.")

    if any(word in prompt for word in ("dreamy", "dreamcore", "ethereal", "otherworldly", "wide", "atmospheric")):
        settings.reverb_mix = 0.12
        settings.delay_mix = 0.06
        reasons.append("Your brief requests an atmospheric space; subtle reverb and delay are enabled for preview.")
    elif any(word in prompt for word in ("dry", "close", "intimate", "natural", "minimal reverb")):
        settings.reverb_mix = 0.035
        settings.delay_mix = 0.0
        reasons.append("Your brief requests an intimate, natural vocal; ambience and delay are kept low.")
    else:
        settings.reverb_mix = 0.08
        settings.delay_mix = 0.0
        reasons.append("No strong space preference was detected; reverb stays subtle and delay remains off.")

    if any(word in prompt for word in ("warm", "soft", "smooth", "less bright")):
        settings.vocal_presence_db = 0.5
        reasons.append("The brief favors warmth and softness, so presence boost is reduced.")
    elif any(word in prompt for word in ("clear", "forward", "intelligible", "cut through")):
        settings.vocal_presence_db = 2.0
        reasons.append("The brief favors clarity, so a modest presence lift is suggested.")
    else:
        settings.vocal_presence_db = 1.0
        reasons.append("A small presence lift is used instead of an aggressive high-frequency boost.")

    # The engine's limiter is a sample-peak ceiling, not true-peak mastering.
    settings.master_peak_dbfs = -1.0
    return {
        "mode": "local_heuristic",
        "summary": "Conservative starting mix based on measured file levels and your brief",
        "executed": False,
        "settings": {
            "vocal_gain_db": settings.vocal_gain_db,
            "instrumental_gain_db": settings.instrumental_gain_db,
            "vocal_highpass_hz": settings.vocal_highpass_hz,
            "vocal_presence_db": settings.vocal_presence_db,
            "compression_ratio": settings.compression_ratio,
            "compression_threshold_db": settings.compression_threshold_db,
            "reverb_mix": settings.reverb_mix,
            "delay_mix": settings.delay_mix,
            "delay_ms": settings.delay_ms,
            "master_peak_dbfs": settings.master_peak_dbfs,
        },
        "measurements": {
            "vocal": vocal,
            "instrumental": beat,
            "rms_difference_db_vocal_minus_instrumental": round(vocal_rms - beat_rms, 2),
        },
        "reasons": reasons,
        "limitations": [
            "This is a transparent local heuristic, not a trained AI listening model.",
            "RMS and peak measurements cannot identify every mix problem or recover original effects.",
            "Preview and adjust by ear before publishing; the peak ceiling is not LUFS or true-peak mastering.",
        ],
    }
