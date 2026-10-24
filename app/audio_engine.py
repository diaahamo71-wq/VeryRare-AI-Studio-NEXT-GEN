"""Deterministic offline mix engine for user-supplied vocal and instrumental WAVs.

This MVP deliberately avoids voice conversion, source separation, cloud APIs, and
arbitrary model-generated code. It provides conservative, repeatable DSP which
can be reviewed and extended by the agent planner later.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json

import numpy as np
import soundfile as sf
from scipy import signal


@dataclass
class MixSettings:
    """Safe starting settings; values are intentionally modest."""
    vocal_gain_db: float = 0.0
    instrumental_gain_db: float = -3.0
    vocal_highpass_hz: float = 80.0
    vocal_presence_db: float = 1.5
    presence_hz: float = 3200.0
    compression_ratio: float = 2.0
    compression_threshold_db: float = -18.0
    reverb_mix: float = 0.08
    delay_mix: float = 0.0
    delay_ms: float = 260.0
    master_peak_dbfs: float = -1.0


def _db_to_gain(db: float) -> float:
    return float(10.0 ** (db / 20.0))


def _validate_audio(audio: np.ndarray, label: str) -> np.ndarray:
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim == 1:
        audio = audio[:, None]
    if audio.ndim != 2 or audio.shape[0] < 2:
        raise ValueError(f"{label} must contain at least two audio frames.")
    if not np.isfinite(audio).all():
        raise ValueError(f"{label} contains NaN or infinite samples.")
    return audio


def _stereo(audio: np.ndarray) -> np.ndarray:
    if audio.shape[1] == 1:
        return np.repeat(audio, 2, axis=1)
    if audio.shape[1] >= 2:
        return audio[:, :2]
    raise ValueError("Unsupported channel count.")


def _biquad(audio: np.ndarray, sos: np.ndarray) -> np.ndarray:
    # Use second-order sections for numerical stability.
    return signal.sosfilt(sos, audio, axis=0).astype(np.float32)


def _presence_eq(audio: np.ndarray, sample_rate: int, center_hz: float, gain_db: float) -> np.ndarray:
    if abs(gain_db) < 1e-6:
        return audio
    # A gentle peaking EQ: narrow band-pass mixed into the original signal.
    q = 1.0
    w0 = 2.0 * np.pi * min(center_hz, sample_rate * 0.45) / sample_rate
    alpha = np.sin(w0) / (2.0 * q)
    A = 10 ** (gain_db / 40.0)
    b0 = 1 + alpha * A
    b1 = -2 * np.cos(w0)
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * np.cos(w0)
    a2 = 1 - alpha / A
    sos = np.array([[b0/a0, b1/a0, b2/a0, 1.0, a1/a0, a2/a0]], dtype=np.float64)
    return _biquad(audio, sos)


def _compress(audio: np.ndarray, sample_rate: int, threshold_db: float, ratio: float) -> np.ndarray:
    """Simple linked-channel feed-forward compressor with smoothed envelope."""
    if ratio <= 1.0:
        return audio
    peak = np.max(np.abs(audio), axis=1)
    attack = max(1, int(sample_rate * 0.010))
    release = max(1, int(sample_rate * 0.100))
    env = np.empty_like(peak)
    a_a = np.exp(-1.0 / attack)
    a_r = np.exp(-1.0 / release)
    state = 0.0
    for i, value in enumerate(peak):
        coeff = a_a if value > state else a_r
        state = coeff * state + (1.0 - coeff) * float(value)
        env[i] = state
    env_db = 20.0 * np.log10(np.maximum(env, 1e-8))
    over = np.maximum(env_db - threshold_db, 0.0)
    reduction_db = over * (1.0 - 1.0 / ratio)
    gain = (10.0 ** (-reduction_db / 20.0)).astype(np.float32)
    return audio * gain[:, None]


def _reverb(audio: np.ndarray, sample_rate: int, mix: float) -> np.ndarray:
    """Small deterministic stereo room from filtered, decaying delay taps."""
    mix = float(np.clip(mix, 0.0, 0.35))
    if mix <= 0:
        return audio
    wet = np.zeros_like(audio)
    # Short taps keep the vocal intimate rather than washing it out.
    taps_ms = (29, 43, 61, 79, 97, 127)
    gains = (0.45, 0.34, 0.27, 0.20, 0.14, 0.10)
    for channel in range(audio.shape[1]):
        for tap_ms, gain in zip(taps_ms, gains):
            delay = max(1, int(sample_rate * tap_ms / 1000))
            if delay < len(audio):
                wet[delay:, channel] += audio[:-delay, channel] * gain
    # Gentle low-pass on the wet return reduces brittle tails.
    sos = signal.butter(2, min(7000, sample_rate * 0.45), fs=sample_rate,
                        btype="lowpass", output="sos")
    wet = _biquad(wet, sos)
    return audio * (1.0 - mix) + wet * mix


def _delay(audio: np.ndarray, sample_rate: int, mix: float, delay_ms: float) -> np.ndarray:
    mix = float(np.clip(mix, 0.0, 0.30))
    if mix <= 0:
        return audio
    delay = max(1, int(sample_rate * float(np.clip(delay_ms, 60, 700)) / 1000))
    wet = np.zeros_like(audio)
    if delay < len(audio):
        wet[delay:] = audio[:-delay] * 0.45
        if delay * 2 < len(audio):
            wet[delay * 2:] += audio[:-delay * 2] * 0.20
    return audio * (1.0 - mix) + wet * mix


def analyze_file(path: str | Path) -> dict[str, Any]:
    """Return basic objective measurements; no subjective quality claims."""
    path = Path(path)
    audio, sr = sf.read(str(path), dtype="float32", always_2d=True)
    audio = _validate_audio(audio, path.name)
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(np.square(audio, dtype=np.float64))))
    return {
        "file": path.name,
        "sample_rate_hz": int(sr),
        "channels": int(audio.shape[1]),
        "duration_seconds": round(len(audio) / sr, 3),
        "peak_dbfs": round(20 * np.log10(max(peak, 1e-9)), 2),
        "rms_dbfs": round(20 * np.log10(max(rms, 1e-9)), 2),
        "clipped_sample_count": int(np.count_nonzero(np.abs(audio) >= 0.9999)),
    }


def mix_tracks(
    vocal_path: str | Path,
    instrumental_path: str | Path,
    output_path: str | Path,
    settings: MixSettings | None = None,
) -> dict[str, Any]:
    """Mix vocal WAV + instrumental WAV to a 24-bit PCM WAV and JSON report.

    Tracks are aligned at time zero and the shorter track is zero-padded to the
    longer duration. This is explicit and deterministic; it does not time-stretch
    or infer musical alignment.
    """
    settings = settings or MixSettings()
    vocal_path, instrumental_path, output_path = map(Path, (vocal_path, instrumental_path, output_path))
    if not vocal_path.is_file():
        raise FileNotFoundError(f"Vocal file not found: {vocal_path}")
    if not instrumental_path.is_file():
        raise FileNotFoundError(f"Instrumental file not found: {instrumental_path}")
    vocal, vocal_sr = sf.read(str(vocal_path), dtype="float32", always_2d=True)
    instrumental, instrumental_sr = sf.read(str(instrumental_path), dtype="float32", always_2d=True)
    vocal = _stereo(_validate_audio(vocal, "Vocal"))
    instrumental = _stereo(_validate_audio(instrumental, "Instrumental"))
    if vocal_sr != instrumental_sr:
        raise ValueError(
            f"Sample rates differ ({vocal_sr} vs {instrumental_sr} Hz). "
            "Convert both files to the same sample rate before mixing."
        )

    sr = int(vocal_sr)
    if not 8000 <= sr <= 192000:
        raise ValueError(f"Unsupported sample rate: {sr}")
    length = max(len(vocal), len(instrumental))
    def pad(x: np.ndarray) -> np.ndarray:
        if len(x) == length:
            return x
        return np.pad(x, ((0, length - len(x)), (0, 0)))
    vocal, instrumental = pad(vocal), pad(instrumental)

    hp = float(np.clip(settings.vocal_highpass_hz, 20, min(500, sr * 0.2)))
    sos = signal.butter(2, hp, fs=sr, btype="highpass", output="sos")
    processed_vocal = _biquad(vocal, sos)
    processed_vocal = _presence_eq(processed_vocal, sr, settings.presence_hz,
                                    float(np.clip(settings.vocal_presence_db, -6, 6)))
    processed_vocal = _compress(
        processed_vocal, sr,
        float(np.clip(settings.compression_threshold_db, -36, -6)),
        float(np.clip(settings.compression_ratio, 1, 6)),
    )
    processed_vocal = _reverb(processed_vocal, sr, settings.reverb_mix)
    processed_vocal = _delay(processed_vocal, sr, settings.delay_mix, settings.delay_ms)
    processed_vocal *= _db_to_gain(float(np.clip(settings.vocal_gain_db, -18, 12)))
    processed_instrumental = instrumental * _db_to_gain(
        float(np.clip(settings.instrumental_gain_db, -18, 12))
    )
    mix = processed_vocal + processed_instrumental

    # Conservative peak ceiling; no claim of LUFS normalization.
    ceiling = _db_to_gain(float(np.clip(settings.master_peak_dbfs, -3, -0.1)))
    peak_before = float(np.max(np.abs(mix)))
    master_gain = min(1.0, ceiling / max(peak_before, 1e-12))
    mix *= master_gain
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), np.clip(mix, -1.0, 1.0), sr, subtype="PCM_24")

    report = {
        "engine": "VeryRare deterministic DSP MVP",
        "status": "rendered",
        "note": "Peak-limited mix; loudness is measured but not LUFS-normalized. Listen and A/B before release.",
        "inputs": {
            "vocal": analyze_file(vocal_path),
            "instrumental": analyze_file(instrumental_path),
        },
        "output": analyze_file(output_path),
        "settings": asdict(settings),
        "master_peak_gain_db": round(20 * np.log10(max(master_gain, 1e-12)), 2),
        "checks": {
            "sample_rates_match": True,
            "output_is_finite": bool(np.isfinite(mix).all()),
            "output_peak_below_ceiling": bool(float(np.max(np.abs(mix))) <= ceiling + 1e-5),
            "manual_listening_required": True,
        },
    }
    report_path = output_path.with_suffix(".report.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
