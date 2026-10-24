# VeryRare AI Studio NEXT GEN

An AI-assisted audio production studio focused on high-quality vocal processing, voice conversion workflows, and transparent, testable audio engineering.

## Project status

Early foundation stage. Features are added incrementally and should not be considered complete until implemented and tested.

## Principles

- Preserve original audio files; process copies and make changes reversible.
- Make cloud processing opt-in and clearly disclose when audio leaves the device.
- Never commit API keys, passwords, private recordings, or other secrets.
- Keep provider integrations configurable and respect usage limits.
- Use measurable checks and human A/B listening for audio quality; do not claim subjective quality has been validated without listening tests.

## Planned architecture

- `docs/`: architecture, development plan, and security notes.
- `apps/desktop/`: desktop user interface (planned).
- `services/orchestrator/`: AI task planning and tool orchestration (planned).
- `services/audio-engine/`: audio processing adapters and validation (planned).
- `tests/`: automated tests and fixtures (planned; never commit personal audio without explicit consent).

The directory layout above is a plan, not a claim that these components already exist.

## Development

The initial commit establishes project documentation and repository hygiene. Runtime/framework choices will be finalized after dependency and platform checks, before introducing application code.
