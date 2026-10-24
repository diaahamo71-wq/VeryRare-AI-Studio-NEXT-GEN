# Advanced vocal processing and plugin hosting plan

## The core decision

The studio should support a broad, extensible processing chain rather than pretending a few built-in effects are a professional mix. It accepts an already-converted vocal WAV and instrumental WAV. Voice conversion and source separation are out of scope.

## Capability groups

1. **Pitch and musical layers:** pitch correction, key/scale selection, formant-preserving pitch shift, harmonizer, octave layers and doubling.
2. **Restoration:** dereverb, denoise, hum removal and declipping, only when analysis indicates a problem.
3. **Vocal dynamics:** clip gain, compression, de-essing, transient control and breath control.
4. **Tone:** corrective EQ, dynamic EQ, saturation, tape color and controlled distortion.
5. **Space and motion:** room/plate/hall reverb, tempo-synced delay, ping-pong delay, modulation, stereo width and section-specific throws.
6. **Mixing:** vocal/beat balance, vocal-aware ducking, mono compatibility and bus processing.
7. **Mastering and QA:** LUFS and true-peak measurement, limiter, reference comparison, export checks and A/B renders.

## Plugin execution architecture

- Built-in DSP is available without third-party plugins.
- External VST3/CLAP plugins require a real plugin host/bridge, an installed compatible binary, valid parameter mapping, offline rendering support and tests.
- A registry entry is not proof that a plugin is installed or functioning.
- The scanner must record plugin format, path, vendor/name/version, architecture, license/source, scan result and known crash state.
- The render engine should fail closed when a requested plugin is unavailable: explain the missing capability, offer a supported alternative, and never silently claim the effect was applied.
- Use isolated plugin worker processes where practical so a broken third-party plugin cannot corrupt the main project.
- All generated plans must state track/bus, effect order, parameter values/ranges, automation region, wet/dry, rationale, expected risk and fallback.
- Render a dry reference and gain-matched A/B candidate. Preserve originals and write new output files only.

## Candidate open-source / free tools to evaluate (not bundled or assumed installed)

- OpenVoxTuner: pitch correction and harmony; AGPL-3.0; Windows VST3/standalone. Verify releases and license obligations before any distribution.
- x42 Auto Tune: free pitch correction, primarily small corrections; check its formant limitations and the exact Windows package.
- TDR Nova: dynamic EQ; proprietary freeware, so do not redistribute binaries without permission.
- Venn Audio Free Suite: useful free Windows VST3 processors; freeware, not necessarily open source.
- FFmpeg: audio filters and file conversion; build license depends on configuration.
- LSP Plugins and Airwindows: broad free/open-source plugin options; verify exact Windows formats and licenses per component.

## Milestones

### P0 — current local DSP foundation
Track gain, high-pass, gentle presence EQ, simple compression, basic room taps, delay and peak safety. This is not a complete mastering chain.

### P1 — plugin inventory and request planning
Expose capability catalog and distinguish built-in, external-required and planned features. Parse prompts into a reviewable plan, but don't execute arbitrary LLM code.

### P2 — real plugin discovery and hosting
Implement VST3/CLAP discovery, licensing metadata, parameter introspection, plugin isolation, offline render and integration tests. Select a host technology only after proving it can load and render actual plugins on Windows.

### P3 — advanced vocal processing
Integrate and test pitch correction/harmonies, de-essing, dereverb/denoise and saturation. Ask for key/scale when the tuner cannot infer it reliably; preserve bypass paths.

### P4 — mix intelligence and mastering
Section markers, automation, sidechain ducking, loudness/true-peak analysis, limiter, reference A/B and quality reports.

## Acceptance criteria

- Every effect in a render report has a real processor ID and verified execution status.
- Missing plugins never appear as applied effects.
- Dry/bypass render is available.
- Render is finite, duration and sample rate are reported, peak and loudness measurements are included when implemented, and export format is verified.
- Pitch/harmony features are tested with known notes and key/scale cases.
- Restoration tools are evaluated for artifacts against source audio, not only by model scores.
- User audio never leaves the device unless the user explicitly enables a cloud service.
