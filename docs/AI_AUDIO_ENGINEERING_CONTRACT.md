# AI Audio Engineering — implementation contract

This document is the acceptance contract for the next VeryRare AI Studio releases. It distinguishes working behavior from planned behavior so the UI and MCP tools never pretend to perform work they did not do.

## User workflow

1. Import the original reference song, the user's converted vocal, and the target instrumental. Keep all processing local by default.
2. Analyze reference and target: duration, sample rate, channels, loudness/peak, sections and phrase boundaries, pitch/key estimates where confidence permits, and reference-effect changes. Preserve confidence and provenance for each estimate.
3. Ask for a style in natural language. The planner turns it into a typed, editable automation timeline, not a prose-only suggestion.
4. Resolve every effect against the installed plugin catalog and built-in processors. Inspect the actual parameter schema; never invent parameter names or claim a capability based on a plugin's name alone.
5. Render to a new output file, preserve source files, report the actual executed steps and failures, and provide A/B preview.
6. Let the user edit events and rerender without restarting the project.

## Required timeline model

Each event must carry:
- stable event id, track id, effect id, start/end seconds;
- wet/dry, parameter values validated against the effect schema;
- optional fade-in/fade-out, tail policy, and enabled/bypassed state;
- source of the decision (user, AI suggestion, or imported reference analysis);
- confidence and warnings when values are inferred;
- execution status (planned, rendered, failed, or skipped) and an error message when applicable.

Events must be clamped to track duration, reject NaN/infinite numbers and invalid ranges, and never silently overwrite a source or previous render. Effects with latency, tails, sidechains, MIDI, or changing buffer sizes must explicitly declare support; unsupported processing must fail clearly rather than silently corrupt timing.

## Plugin management

- Start with Windows VST3 discovery and exact parameter inspection.
- Show plugin name, path, format, scan status, last validation result, and capabilities actually verified.
- Discovery is not compatibility validation. Only load trusted plugins; plugin hosts are not a security sandbox.
- Never install or execute a plugin from a YouTube link. A link can be a research reference; the user must obtain a legitimate installer from a trusted source, install it, then scan and inspect it.
- Do not bundle or redistribute third-party plugins without permission.
- Prefer a separate worker process for plugin inspection/rendering so a broken plugin cannot take down the main UI/MCP process.

## Reference matching

The system should estimate audible characteristics and recreate a similar treatment on the user's vocal, not claim to recover hidden original plugin identities or exact settings from a finished stereo master. When available, use separated reference stems for better analysis. Pitch correction needs a known or confidently estimated key/scale and a user override; harmonies need pitch-aware generation; timing alignment and vocal/instrumental sample-rate compatibility must be checked before mixing.

## AI + MCP control

The MCP server should expose truthful tools for status, import/analysis, plugin scan/inspection, plan validation, timeline editing, preview render, final render, and report retrieval. Tool results must clearly distinguish planned actions from executed actions. The assistant may adjust project settings only through these tools and should ask before destructive operations, plugin installation, or cloud upload.

## UI contract

- Modern, restrained, responsive interface with meaningful controls only.
- Every visible button must be connected to a real action; unavailable features are visibly disabled or absent.
- No fake waveform, fake progress, decorative-only controls, or invented analysis.
- One project workspace for reference, vocal, instrumental, plugin catalog, timeline, A/B preview, and export.
- Show actionable errors, keyboard focus, labels, progress from actual jobs, and clear local/cloud status.
- Preserve the original files; use unique renders and a clear undo/history strategy.

## Acceptance gates

- Unit tests for timeline validation, event boundaries, parameter ranges, file-path safety, and no-overwrite behavior.
- Integration tests using a generated WAV and a known test plugin or built-in processor.
- Confirm sample rate/channel handling, finite output, duration/tail policy, peak safety, and honest execution reports.
- Manual listening QA for telephone sections, harmonizer, pitch correction, reverb tails, and vocal/beat balance.
- Windows 11 checks in current Chrome/Edge and MCP client connection tests.
- Never mark a feature complete merely because its UI or MCP schema exists.
