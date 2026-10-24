# UI quality guide — XIAS-inspired

Reference: [plugin87/ux-ui-agent-skills (XIAS)](https://github.com/plugin87/ux-ui-agent-skills). XIAS is an agent-oriented design and accessibility knowledge kit, not a runtime component library. This project adopts its review-first approach; no XIAS scripts are executed as part of the application runtime.

## Visual direction

- Product: VeryRare AI Studio, a local-first audio engineering desktop-style web UI.
- Palette: near-black plum surfaces, lavender as the primary action/accent, muted purple borders, teal reserved for local/healthy/success states.
- Typography: high-legibility sans-serif with compact metadata. A system font fallback is mandatory.
- Layout: persistent workspace navigation on wide screens, single-column responsive layout on narrow screens, clear section hierarchy, cards for track and processing groups.
- Avoid fake waveform data being presented as audio analysis. The current track-card waveforms are decorative placeholders; actual waveform rendering is not yet implemented.
- Avoid fake processing progress. The current render action reports its actual request/result state but does not stream progress updates.

## Interaction truthfulness

- Only enable rendering after both files are successfully imported and validated.
- Clearly identify the current engine as deterministic DSP MVP.
- The production brief is informational only in this build and does not change effect parameters. AI planning/execution must remain marked unavailable until connected to validated tools.
- Distinguish built-in processors, external-plugin-required capabilities, and planned features.
- Never claim subjective audio quality is verified from metrics alone.
- Preserve input files, create unique output names, and disclose local/cloud behavior.

## Quality gates before release

1. Keyboard: all actions reachable by Tab, visible focus, labels associated with controls, no keyboard trap.
2. Responsive: no horizontal overflow at 320 px, 375 px, tablet, and desktop widths.
3. Contrast: check normal, hover, disabled, error, and success states; target WCAG 2.2 AA.
4. Semantics: one primary heading per view, landmarks, accessible names, status announcements.
5. Input validation: reject non-WAV/invalid WAV, empty uploads, oversize files, mismatched sample rates, invalid parameter ranges, and unsafe paths.
6. File safety: preserve originals; output names are unique; no path traversal.
7. Error recovery: clear actionable errors and allow retry after a failed import/render.
8. Audio QA: finite output, output peak ceiling, correct file format, matching sample rates; listening review remains mandatory.
9. Browser checks: test current stable Chrome and Edge on Windows 11, including file import, rendering, playback, and download.
10. Licensing: keep notices for application dependencies and any bundled fonts/assets. Do not depend on remotely hosted fonts for core layout; a system fallback must remain usable offline.

## Known gaps in the first UI pass

- This is a browser-based local UI served on loopback, not yet a packaged desktop executable.
- No waveform analysis/visualization, undo stack, cancellation, streamed job progress, plugin GUI, automatic AI effect planning, Auto-Tune, harmonizer, or dereverb is implemented by the UI itself.
- The backend uses a conservative built-in DSP engine. Plugin hosting remains a separate experimental path and must be validated with each installed plugin.
- Automated UI, accessibility, and Windows integration tests are still required; do not claim the release gates have passed until run.
