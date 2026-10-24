# Technology selection — prompt-driven audio engineering

Research snapshot: 24 October 2026. Recheck versions, model licenses, plugin licenses, and third-party terms before release.

## Product scope (corrected)

The user supplies an **already-converted vocal WAV and its instrumental/beat** (or a full song plus the relevant stems). VeryRare AI Studio does **not** convert voices, train voice models, or separate vocals by default. Its job is professional audio engineering: analyze the supplied files, interpret the user's production prompt, create a deliberate effects/mix/master plan, render the complete song, validate it, and present A/B alternatives.

## Recommended free-first architecture

| Area | Selection | Purpose and caveats |
|---|---|---|
| Agent workflow | [LangGraph](https://github.com/langchain-ai/langgraph) | Stateful specialist workflow, checkpoints, approval gates. The LLM proposes settings; registered tools perform audio processing. |
| Local LLM | [Ollama for Windows](https://ollama.com/download/windows) + configurable Qwen3 4B Q4_K_M candidate | No API fee or automatic upload. About 2.6 GB published for this quantization; CPU speed and reasoning quality must be benchmarked on the target PC. This is a candidate, not a claim of world-class music judgment. |
| File inspection and deterministic renders | [FFmpeg](https://ffmpeg.org/) + `ffprobe` | Decode, align, route, apply supported filters, export, and inspect metadata. Preserve originals. Verify the exact build's license flags. |
| Audio I/O / DSP | `soundfile`, `numpy`, `scipy` | Read/write, metering, alignment checks, and deterministic operations. |
| Loudness analysis | `pyloudnorm` + FFmpeg `loudnorm` | Measure/adjust loudness and report peak/true-peak limitations clearly. Loudness normalization alone is not mastering. |
| Free plugin suite | [Venn Audio Free Suite](https://www.vennaudio.com/free-suite/) | Free Windows VST3 suite including EQ, compressor, delay, reverb, clipper and meters. Freeware, not necessarily open source; check terms before redistributing. |
| Dynamic EQ | [TDR Nova](https://www.tokyodawn.ru/tdr-nova/) | Free EQ/dynamic EQ for resonances and controlled tonal shaping; optional plugin integration. |
| Creative saturation / color | [Airwindows](https://www.airwindows.com/) | Large collection of free audio effects; choose a small tested subset rather than installing everything. Check the current build format and each license. |
| Additional open-source effects | [LSP Plugins](https://lsp-plug.in/) | Open-source plugin collection; confirm Windows binary format and plugin-host compatibility for each chosen effect. |
| Reference-based mastering | [Matchering](https://github.com/sergree/matchering) optional | Useful when the user provides an approved reference track; GPLv3 and reference-dependent. Not a substitute for an intentional mix. |
| Test harness | `pytest` + generated synthetic audio | Test routing, timing, silence, clipping, sample rate, export integrity, parameter bounds and repeatability without committing personal recordings. |
| Desktop shell | Python desktop app (framework choice remains a separate implementation decision) | The UI must support audio audition, prompt editing, processing plans, plugin-chain review, A/B playback, undo/versions, and exports. |

## Plugin-hosting decision

Do not claim VST3 plugins are integrated merely because plugin names are in a list. First implement and test a reliable offline rendering path. A plugin host can be a dedicated engine or a supported external-host adapter, depending on Windows compatibility, plugin formats, automation, crash isolation, and license review. Native FFmpeg/DSP operations remain available as a dependable fallback. Keep plugin presets and parameter changes explicit, versioned, and reproducible.

## Prompt-driven effects — not random presets

Translate the user's prompt into a structured mix brief: target emotion/style, vocal placement, ambience, delay rhythm, stereo width, saturation, dynamics, references, and things to avoid. For every proposed effect, the plan must state its purpose, target track/bus, key parameters, wet/dry range, automation intent if any, and why it supports the prompt. Use conservative starting values, preview changes, and reject parameter combinations outside validated ranges. Do not insert every effect by default.

## Hardware and privacy

The target PC is Windows 11, 16 GB RAM, and a very weak 1 GB GPU. Plan for CPU-first processing. Most classic DSP/plugin effects should be feasible; large neural models may not be. The base workflow must not need a cloud service. Do not upload audio without explicit approval, and never require paid APIs or subscriptions.

## License gate

Keep a third-party notices inventory for application dependencies, FFmpeg build flags, plugins, plugin SDKs, presets, and models. Free-to-use does not always mean open-source or redistributable. Do not bundle freeware plugins without checking the developer's distribution terms.
