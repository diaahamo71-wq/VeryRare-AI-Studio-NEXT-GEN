# Plugin selection — mixing, effects, and mastering

## Product scope

The input is the user's already-converted vocal WAV plus its instrumental/beat (or stems). Do not build voice conversion or vocal separation into the default path. Focus on intentional vocal engineering, effects, balancing, mixing, mastering, and reliable export.

## Priority list

| Priority | Integration | Intended role | Status / caveat |
|---|---|---|---|
| P0 | FFmpeg + ffprobe | File inspection, decoding, alignment checks, supported DSP filters, export | Core candidate; pin a build and verify licensing/configuration. |
| P0 | soundfile + NumPy/SciPy | File I/O, gain, meters, signal analysis and deterministic DSP | Core candidate; add automated tests and non-destructive output paths. |
| P0 | pyloudnorm + FFmpeg loudness tools | LUFS and peak/loudness reporting | Measure first; loudness normalization is not a full mastering chain. |
| P0 | LangGraph + local Ollama model | Prompt interpretation, specialist workflow, checkpoints, approvals | No API fees by default; model performance on CPU must be benchmarked. |
| P1 | Venn Audio Free Suite | EQ, compressor, gate, delay, reverb, clipper, gain and meters | Free Windows VST3 suite; verify redistribution terms. Official site: https://www.vennaudio.com/free-suite/ |
| P1 | TDR Nova | Corrective/dynamic EQ, resonance control, de-essing-style dynamic control | Free plugin; use the official download: https://www.tokyodawn.ru/tdr-nova/ |
| P1 | Airwindows | Creative saturation, color and other effects | Free collection; pick and test a minimal set from https://www.airwindows.com/ |
| P1 | LSP Plugins | Additional open-source EQ, dynamics, metering and utility effects | Check available Windows builds and the host format at https://lsp-plug.in/ |
| P2 | Matchering | Reference-based tonal/dynamic matching when a user supplies a suitable reference | Optional; GPLv3, reference-dependent, and not a substitute for a deliberately engineered mix. https://github.com/sergree/matchering |
| P2 | External VST3/CLAP plugin host | Run third-party plugins with parameter automation and offline render | Architecture proof required before claiming support; check plugin format, crash isolation, licensing and reproducibility. |

## Important distinctions

- **Free vs open source:** Venn Audio Free Suite and TDR Nova are free to use but should not automatically be described as open-source. Do not redistribute binaries unless their terms allow it.
- **Open-source does not mean every model/preset is open:** check the exact license and usage rights for all bundled components.
- **Plugin names do not equal integration:** mark an effect as supported only after automated offline render and parameter-setting tests pass.
- **No random FX:** every effect is selected because it serves the user's prompt, assigned to a track or bus, and controlled by validated parameter ranges. Automate effects by song section only when musically justified.
- **Quality assurance:** compare levels fairly in A/B listening and report loudness/peak metrics. A louder version is not automatically a better mix.

## Official sources

- Venn Audio Free Suite: https://www.vennaudio.com/free-suite/
- TDR Nova: https://www.tokyodawn.ru/tdr-nova/
- Airwindows: https://www.airwindows.com/
- LSP Plugins: https://lsp-plug.in/
- Matchering: https://github.com/sergree/matchering
- FFmpeg filters and loudness: https://ffmpeg.org/ffmpeg-filters.html

This is a researched selection, not a claim that these plugins are installed or already connected to the application. The next implementation step is a tested offline-render proof of concept and a prompt-to-effects plan schema.
