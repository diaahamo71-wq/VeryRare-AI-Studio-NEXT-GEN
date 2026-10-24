"""Capability catalog for real audio processors.

The catalog distinguishes built-in DSP from external VST3/CLAP plugins that
must be installed and hosted. It never claims an external plugin is active
unless a future scanner/host verifies it.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal

Status = Literal["implemented_builtin", "external_plugin_required", "planned"]


@dataclass(frozen=True)
class Capability:
    id: str
    name: str
    category: str
    purpose: str
    status: Status
    safety_notes: str
    prompt_terms: tuple[str, ...]


CAPABILITIES: tuple[Capability, ...] = (
    Capability("gain_balance", "Track gain and balance", "mixing",
               "Set vocal and instrumental levels without clipping.",
               "implemented_builtin", "Always check peaks and listen in context.",
               ("balance", "vocal louder", "beat quieter", "sit in the mix")),
    Capability("highpass_eq", "High-pass filtering", "equalization",
               "Reduce rumble and unwanted low-frequency handling noise.",
               "implemented_builtin", "Avoid thinning the voice with excessive cutoff.",
               ("muddy", "rumble", "low end", "clean vocal")),
    Capability("presence_eq", "Presence EQ", "equalization",
               "Gently adjust intelligibility and forwardness.",
               "implemented_builtin", "Large boosts can sound harsh or expose artifacts.",
               ("clear", "presence", "intelligible", "forward vocal")),
    Capability("compression", "Vocal compression", "dynamics",
               "Reduce level variation with a conservative feed-forward compressor.",
               "implemented_builtin", "Not a substitute for listening or clip gain.",
               ("consistent", "controlled", "compressed", "upfront")),
    Capability("room_reverb", "Short room reverb", "spatial",
               "Add a restrained early-reflection-like space.",
               "implemented_builtin", "Current built-in reverb is a simple tap model, not a convolution room.",
               ("intimate", "room", "space", "soft ambience")),
    Capability("delay", "Tempo-unsynced delay", "spatial",
               "Add short repeated echoes.",
               "implemented_builtin", "Current implementation does not infer tempo or automate throws.",
               ("echo", "delay", "dreamy", "throw")),
    Capability("pitch_correction", "Pitch correction / Auto-Tune", "pitch",
               "Correct notes toward a selected key and scale, preserving intended slides.",
               "external_plugin_required", "Must select key/scale or explicitly enable chromatic mode; never silently tune.",
               ("autotune", "pitch correction", "in tune", "hard tune", "natural tuning")),
    Capability("harmony", "Pitch-aware harmonizer", "vocal layers",
               "Generate scale-aware harmony voices with independent level and formant settings.",
               "external_plugin_required", "Harmony depends on key/chords; synthetic copies can create phase and intelligibility issues.",
               ("harmonies", "backing vocals", "vocal stack", "choir", "octave")),
    Capability("doubler", "Vocal doubler", "vocal layers",
               "Create controlled width using short offsets, modulation, or pitch micro-shifts.",
               "planned", "Keep a mono compatibility check and avoid uncontrolled phase cancellation.",
               ("double track", "wider vocal", "thicker", "stereo vocal")),
    Capability("deesser", "De-esser", "dynamics",
               "Reduce excessive sibilance dynamically.",
               "external_plugin_required", "Detect sibilance before choosing a band; avoid dulling all consonants.",
               ("sibilant", "harsh s", "ess", "sharp consonants")),
    Capability("derverb", "Dereverb / room reduction", "restoration",
               "Reduce room tails already baked into the vocal recording.",
               "external_plugin_required", "Source separation / dereverb can create watery artifacts; keep a bypass comparison.",
               ("remove room", "dry vocal", "dereverb", "roomy recording")),
    Capability("denoise", "Noise reduction", "restoration",
               "Reduce steady background noise when it is actually present.",
               "external_plugin_required", "Do not denoise clean vocals; aggressive settings damage breaths and tails.",
               ("hiss", "noise", "hum", "background noise")),
    Capability("declip", "Declipping", "restoration",
               "Attempt to reconstruct clipped waveform peaks.",
               "external_plugin_required", "Cannot guarantee recovery of destroyed information.",
               ("clipping", "clipped vocal", "distortion from clipping")),
    Capability("transient_control", "Transient shaping", "dynamics",
               "Control sharp consonant or percussive attacks.",
               "external_plugin_required", "Over-processing can blunt articulation.",
               ("sharp attacks", "too punchy", "transients")),
    Capability("saturation", "Tape / tube saturation", "tone",
               "Add controlled harmonic density and soften peaks.",
               "planned", "Oversampling and gain-matched bypass are desirable.",
               ("warm", "tape", "analog", "grit", "thicker")),
    Capability("stereo_width", "Stereo image control", "spatial",
               "Manage width and mono compatibility.",
               "planned", "Check mono fold-down and phase correlation.",
               ("wide", "stereo", "spacious", "narrow")),
    Capability("sidechain_ducking", "Vocal-aware instrumental ducking", "mixing",
               "Gently reduce beat level while vocal energy is present.",
               "planned", "Use smooth attack/release; avoid audible pumping unless requested.",
               ("vocal clarity", "beat masks vocal", "duck the beat")),
    Capability("automation", "Section-aware effect automation", "automation",
               "Apply different effect amounts to intro, verse, chorus, bridge and outro.",
               "planned", "Requires section markers or user-confirmed timeline regions.",
               ("delay throws", "chorus wider", "intro", "bridge", "outro")),
    Capability("limiting", "True-peak-aware limiting", "mastering",
               "Control final peaks with oversampling and a measured loudness target.",
               "external_plugin_required", "The current built-in peak ceiling is not a true-peak limiter or LUFS mastering.",
               ("louder", "master", "streaming master", "true peak")),
    Capability("loudness_metering", "Loudness and true-peak metering", "analysis",
               "Measure integrated LUFS, loudness range and true peak where supported.",
               "planned", "Do not normalize to a target without checking genre and dynamics.",
               ("LUFS", "loudness", "streaming", "mastering level")),
)


def list_capabilities() -> list[dict]:
    """Return a serializable inventory; external/planned items are not activated."""
    return [asdict(item) for item in CAPABILITIES]


def search_capabilities(prompt: str) -> list[dict]:
    """Rank possible processing capabilities by explicit prompt-term matches."""
    text = prompt.casefold()
    ranked = []
    for item in CAPABILITIES:
        hits = [term for term in item.prompt_terms if term.casefold() in text]
        if hits:
            ranked.append({
                **asdict(item),
                "matched_terms": hits,
                "is_available_now": item.status == "implemented_builtin",
            })
    return sorted(ranked, key=lambda x: (not x["is_available_now"], -len(x["matched_terms"]), x["category"], x["id"]))
