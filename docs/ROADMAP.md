# Roadmap

## Phase 0 — repository foundation

- [x] Create project README.
- [x] Document proposed architecture and safety boundaries.
- [x] Define phased implementation plan.
- [ ] Add ignore rules and contribution/development instructions.
- [ ] Verify repository baseline and available CI.

## Phase 1 — technology proof

- [ ] Compare desktop frameworks and choose one based on Windows support, packaging, accessibility, and performance.
- [ ] Prototype audio import, metadata inspection, playback, and export.
- [ ] Establish automated tests for file handling and non-destructive processing.
- [ ] Verify licenses and installation requirements of external audio tools.

## Phase 2 — reliable audio workspace

- [ ] Project/session model with undoable, non-destructive operations.
- [ ] Waveform/transport and A/B playback.
- [ ] Job queue, progress, cancellation, and readable logs.
- [ ] Audio validation for duration, channels, sample rate, clipping, and empty output.

## Phase 3 — real AI orchestration

- [ ] Provider-independent model interface and user-managed credentials.
- [ ] Structured plans validated against an allowlisted tool registry.
- [ ] Explicit approval for destructive actions, cloud upload, and potentially billable calls.
- [ ] Agent roles kept narrow: coordinator, audio specialist, and independent reviewer.
- [ ] Retry/review loop with bounded attempts and a user-visible explanation of changes.

## Phase 4 — voice conversion and production tools

- [ ] Test compatible conversion backends against representative, consented audio.
- [ ] Compare source and converted audio using objective checks plus human listening.
- [ ] Add optional restoration, EQ, dynamics, reverb, and mastering as reversible steps.
- [ ] Record settings and provide exportable presets.

## Acceptance rule

A checkbox is marked complete only after implementation and verification. Planned functionality must not be advertised as available.
