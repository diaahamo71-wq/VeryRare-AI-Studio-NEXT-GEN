# Audio engineering agent team

## Core principle

These are **specialist roles in a controlled workflow**, not a claim that six independently trained audio engineers are already implemented. Initially, roles may share one local LLM; the audio is processed by real deterministic tools, and agents must cite measurements/tool results rather than invent listening observations. A future implementation may use different models per role if they are available at no cost.

## Proposed team

### 1. Studio Director / Producer
- Converts the user's natural-language brief into an explicit goal, constraints, and acceptance criteria.
- Asks a question only when a missing detail materially changes the result.
- Produces a proposed processing plan and explains trade-offs before rendering.
- Never overwrites source media or authorizes cloud upload without consent.

### 2. Audio Forensics Engineer
- Inspects duration, sample rate, channel count, peak, true peak where available, integrated loudness, silence, clipping, and file integrity.
- Runs approved analysis for spectral balance, dynamics, stereo correlation, and vocal/instrument separation when relevant.
- Reports measured facts separately from hypotheses; cannot claim to have heard an artifact unless a supported listening/evaluation step actually occurred.

### 3. Vocal & Voice-Conversion Engineer
- Determines whether the task needs separation, cleanup, conversion, de-essing, level control, or restoration.
- Calls only configured backends such as UVR or the user's Applio/RVC installation.
- Compares source and result for duration/alignment, clipping, spectral discontinuities, pitch-tracking failures, and obvious file errors.
- Preserves the original vocal and avoids aggressive processing by default.

### 4. Mix Engineer
- Proposes a restrained sequence for EQ/filtering, dynamics, ambience, stereo placement, and level balance.
- Uses reversible processing and bounded parameter ranges.
- Uses reference audio only when the user provides or approves a reference.
- Does not invent a universal preset; adapts to measurements and the user's stated style.

### 5. Mastering Engineer
- Checks tonal balance, dynamics, integrated LUFS, loudness range, true peak, clipping, and export format.
- Uses Matchering only when reference matching is requested and the reference is suitable.
- Presents at least one conservative version and, where useful, an alternate version rather than silently maximizing loudness.

### 6. Independent QA Engineer / Skeptic
- Reviews the plan before execution and output reports after rendering.
- Rejects missing files, unexpected duration changes, clipping, invalid sample rates, silent output, broken alignment, and out-of-range settings.
- Compares before/after metrics and flags regressions.
- Requires human A/B listening for subjective claims such as warmth, emotion, naturalness, or whether a vocal sounds better.

## Workflow and gates

1. Import the song; preserve a read-only source reference and create a working copy.
2. Inspect metadata and run a quick analysis pass.
3. Producer creates a structured brief and asks for clarification only if necessary.
4. Specialist roles propose operations; the orchestrator checks the plan against a strict allowlist and typed schemas.
5. Show a preview plan, estimated processing steps, and any cloud/privacy implications. User approves the plan.
6. Execute one operation at a time, log parameters, and render new intermediate files.
7. Run objective QA after each risky step; stop or roll back if validation fails.
8. Produce before/after A/B playback, a report of what changed, and export options.
9. User decides whether to accept the master. Do not auto-publish or delete intermediates.

## Required output report

- Input and output filenames, duration, sample rate, channels, and format.
- Each operation and exact parameters used.
- Before/after loudness and peak measurements where supported.
- Validation failures, warnings, and steps skipped.
- Clear distinction between measured results, model recommendations, and subjective listening notes supplied by the user.
- Cloud status: local-only by default; if cloud was used, name the provider and files sent.

## Guardrails

- No arbitrary shell, Python, PowerShell, or filesystem tools exposed to the LLM.
- All tools use typed inputs, allowlisted operations, path confinement, file-size/time limits, and cancellation.
- Ask before replacing files, uploading audio, installing software, or making any billable request.
- Retry loops are bounded. QA cannot claim success simply because a file was created.
- Keep logs free of API keys and sensitive audio payloads.
