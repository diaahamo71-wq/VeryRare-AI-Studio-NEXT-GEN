# Technology selection — free-first, Windows-first

Research snapshot: 24 October 2026. Recheck versions, model licenses, and third-party terms before packaging a release.

## Decision

Use a **local-first Python desktop application** with a deterministic audio engine and a controlled agent workflow. Do not require a paid API, cloud GPU, subscription, or online account for the baseline product.

## Selected baseline

| Area | Selection | Why | Constraints |
|---|---|---|---|
| Agent orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) | Open-source, stateful workflows, checkpoints, and human approval gates | The model is not the audio engine; every tool must be explicitly registered and schema-validated |
| Local LLM runtime | [Ollama for Windows](https://ollama.com/download/windows) | Local HTTP API; no per-request API bill | CPU inference may be slow; model quality is limited by available RAM and model size |
| Default local model candidate | [Qwen3 4B Q4_K_M](https://ollama.com/library/qwen3:4b-q4_K_M) | Listed at about 2.6 GB, Apache-2.0 model variant; plausible starting point for a 16 GB PC | This is a candidate to benchmark, not a guarantee of high-end reasoning or fast inference. Keep model choice configurable |
| Audio metadata / conversion / filters | [FFmpeg](https://ffmpeg.org/) + `ffprobe` | Mature command-line tools, codecs, filter graphs, and measurable loudness processing | Bundle only a correctly licensed build; FFmpeg's license depends on build options and enabled components |
| Audio file I/O | `soundfile` | Read/write WAV and other supported formats without a large DAW runtime | Validate codec support and malformed files |
| Signal processing | `numpy` + `scipy` | Local, reproducible DSP building blocks | DSP parameters need tests; don't claim that arbitrary settings are professionally tuned |
| Audio feature analysis | `librosa` | Tempo, onset, spectral and related analysis features | Use selectively; avoid expensive analysis when a lightweight measurement is enough |
| Loudness validation | [pyloudnorm](https://pypi.org/project/pyloudnorm/) plus FFmpeg `loudnorm` | LUFS measurement and loudness normalization workflows | True-peak, clipping, and loudness targets must be reported separately; loudness normalization is not mastering by itself |
| Reference matching / mastering | [Matchering](https://github.com/sergree/matchering) as an optional adapter | Open-source reference-based matching of spectrum, RMS, peak and stereo width | GPLv3; keep optional and document the license. A poor reference can produce a poor result |
| Vocal separation | [Ultimate Vocal Remover GUI](https://github.com/Anjok07/ultimatevocalremovergui) / UVR models as an optional adapter | Strong practical ecosystem with multiple separation model families | Code is MIT, but each model/weight can have separate terms. Separation artifacts are possible; compare candidate stems before conversion |
| Voice conversion | Existing user-selected [Applio](https://applio.org/) or [RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) model through an isolated adapter | Reuses the user's existing workflow and keeps conversion engine swappable | Code license does not automatically settle the terms of downloaded weights, datasets, or voice consent. Keep it optional and out of the core dependency set |
| Desktop UI | Python + PySide6 candidate | Native-feeling Windows UI and direct integration with Python audio tools | Verify Qt/PySide license obligations for the exact distribution model before packaging |
| Automated checks | `pytest` + generated synthetic audio fixtures | Repeatable regression tests without exposing private recordings | Never commit the user's song or voice dataset as a test fixture |

## Why not use a cloud model as the default?

Cloud free tiers and credits can change, require accounts, impose limits, or later become paid. The baseline must therefore work without them. A provider adapter may be added later only if the user explicitly opts in and the UI displays the provider, data sent, and any cost/limit uncertainty before upload.

## Why not let agents generate arbitrary shell commands?

The LLM should choose among approved audio operations, not write and execute arbitrary commands. Each operation has a typed schema, bounded parameter ranges, a timeout, a cancellation path, a declared input/output path, and a validation step. Preserve the original file and render to a new version.

## Hardware reality

The target PC has 16 GB RAM and a very weak 1 GB GPU. Plan for CPU-first audio processing and small local language models. Large speech separation and voice-conversion neural models may be slow or infeasible locally; those tasks must be optional and can run in an explicitly approved free cloud notebook when one is available, with no guarantee of availability or speed. The app must never silently upload audio.

## License gate before release

Create a third-party notices inventory covering application dependencies, FFmpeg build flags, UI framework, model code, model weights, VSTs, and any bundled assets. Do not assume an open-source repository means every model weight or pretrained checkpoint is cleared for commercial use.
