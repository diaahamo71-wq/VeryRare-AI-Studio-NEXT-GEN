---
name: veryrare-ui-review
description: Review and improve the VeryRare AI Studio UI using XIAS-inspired design-system, accessibility, responsive-layout, and interaction-truthfulness gates.
---

# VeryRare UI review skill

Use the upstream open-source reference [UX/UI Agent Skills (XIAS)](https://github.com/plugin87/ux-ui-agent-skills) as a design-review reference. XIAS is an agent-oriented design knowledge kit, not a runtime UI dependency. Do not claim that upstream automated gates were run unless they were actually executed.

## Product contract

- The product is a local-first audio engineering studio for already-converted vocal WAVs and instrumentals.
- Never add voice conversion or source separation to this studio.
- Audio must remain local by default. Cloud use must be opt-in and explicitly state whether audio or text leaves the device.
- Do not make a UI control look functional unless it is connected to a real operation.
- Separate implemented, external-plugin-required, and planned features.
- Never present decorative waveform graphics as measured waveform data.
- Never present an AI plan as executed processing; only a successful render response confirms a render.
- Preserve source files and use unique output names.

## Design tokens and visual direction

- Background: near-black plum; cards: dark plum/purple; borders: muted violet; primary accent: lavender; healthy/local/success state: restrained teal.
- Use the tokens already defined in `frontend/assets/studio.css`; do not add a competing palette per page.
- Maintain clear hierarchy, compact metadata, consistent spacing, readable labels, and distinct primary/secondary actions.
- Keep keyboard focus visible. Use semantic buttons, labels, headings, landmarks, and live status announcements.
- Do not add remote font, icon, analytics, or asset requests to the local UI without explicit review and a documented need.
- Respect `prefers-reduced-motion` and preserve the system-font fallback.

## Required review gates

Before calling a UI change complete, check:

1. **Truthfulness:** every button/control performs its stated action; unsupported features are labeled.
2. **Accessibility:** keyboard-only navigation, visible focus, labels and accessible names, live error/success announcements, contrast in normal/hover/disabled/error/success states.
3. **Responsive layout:** no horizontal overflow at 320, 375, 768, 1024, and 1440 CSS pixels.
4. **Audio workflow:** import validation, sample-rate mismatch feedback, render failure recovery, A/B reference and processed playback, and download.
5. **File safety:** path traversal rejection, no silent overwrite, original inputs preserved, workspace ignored by Git.
6. **Performance:** avoid decoding full long-form audio in the browser; do not claim streamed progress when the server returns only after rendering.
7. **Quality evidence:** run automated checks and report exact results. A successful test suite does not establish subjective audio quality; listen to rendered output.
8. **Scope discipline:** no voice conversion, no separation, no arbitrary shell execution, and no automatic cloud audio upload.

## Current UI known limitations

- The interface is served by a local FastAPI process; it is not yet packaged as a native desktop executable.
- The production brief can request an advisory text plan, but that plan is not executed and does not automatically alter mixer controls.
- Waveform drawings are decorative; live waveform rendering is not implemented.
- Render progress is not streamed; output metrics are not a mastering or listening-quality certification.
- VST3 plugins are not sandboxed and each plugin needs explicit compatibility and audio-quality testing.
