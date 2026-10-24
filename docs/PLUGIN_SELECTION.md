# Plugin and integration selection

The term *plugin* here includes software libraries, command-line tools, and optional external applications. Nothing in this list should be described in the UI as installed or operational until the adapter is implemented and tested.

## Recommended integrations

| Priority | Integration | Role | Decision |
|---|---|---|---|
| P0 | FFmpeg + ffprobe | File inspection, format conversion, filter graphs, loudness tools | Core engine dependency; pin/test a known build and inspect enabled codecs and license flags |
| P0 | soundfile + NumPy/SciPy | Safe file I/O and deterministic DSP | Core libraries; all operations must be tested on copies |
| P0 | pyloudnorm | Integrated LUFS measurement | Core validation tool; report its method and version |
| P0 | Ollama + configurable Qwen3 4B Q4_K_M candidate | Local LLM, no API charge | Optional install; baseline must still allow non-AI/manual processing if Ollama is absent |
| P0 | LangGraph | Agent graph, state, checkpoints, human approval | Core orchestration choice; agent output is constrained by registered tool schemas |
| P1 | UVR / Ultimate Vocal Remover | Vocal/instrumental separation | Optional adapter; benchmark multiple model families on a short excerpt and respect model-weight terms |
| P1 | Applio / RVC | Voice conversion | Optional adapter to an existing installation/model; do not bundle weights without checking their terms |
| P1 | Matchering | Reference-based mastering | Optional adapter; GPLv3 licensing must be reflected in distribution choices |
| P2 | Pedalboard | Additional studio effects / VST3 hosting from Python | Not in the default core. The project is GPLv3; assess license compatibility and plugin licenses before enabling or redistributing it |
| P2 | External VST3/AU effects | User-installed effects | Do not bundle third-party plugins by default. AU is macOS-specific; Windows focus means VST3 is the relevant format |

## Why not add every plugin?

More dependencies increase installation failures, licensing work, security surface, and the chance that the app cannot run on the target PC. Add a plugin only when it solves a verified use case, has a maintained installation path, has compatible licensing, and has an automated or repeatable test.

## Model quality and hardware

A small local LLM can plan operations and explain reports; it cannot substitute for signal processing, and it does not become an expert audio listener merely because it has an audio-engineer role prompt. Voice conversion and high-quality separation use separate neural models and can be far more demanding than the text agent. Keep the model/runtime choices swappable and benchmark on the actual target PC.

## License references

- [LangGraph](https://github.com/langchain-ai/langgraph) — MIT license; verify the current repository license before release.
- [Ollama for Windows](https://ollama.com/download/windows) and [Ollama Windows docs](https://github.com/ollama/ollama/blob/main/docs/windows.mdx).
- [Qwen3 model family](https://ollama.com/library/qwen3); the [Qwen3 4B Q4_K_M registry entry](https://registry.ollama.com/library/qwen3%3A4b-q4_K_M) lists Apache-2.0 and about 2.6 GB.
- [FFmpeg licensing](https://github.com/FFmpeg/FFmpeg/blob/master/LICENSE.md) — LGPL by default for most code, with optional GPL components depending on build configuration.
- [pyloudnorm](https://pypi.org/project/pyloudnorm/) — MIT license on the current PyPI page.
- [Matchering](https://github.com/sergree/matchering) — GPLv3.
- [Ultimate Vocal Remover GUI](https://github.com/Anjok07/ultimatevocalremovergui) — MIT code license; model terms must be checked separately.
- [Applio](https://applio.org/) — project states MIT licensing; check model weights and downloaded assets separately.
- [RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/main/LICENSE) — MIT code license; check weights and datasets separately.
- [Spotify Pedalboard](https://github.com/spotify/pedalboard) — GPLv3; do not assume it can be embedded into a differently licensed proprietary app without reviewing the implications.

This document is a selection proposal. The license inventory and installation tests remain release gates.
