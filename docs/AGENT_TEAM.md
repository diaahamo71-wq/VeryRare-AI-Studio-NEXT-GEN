# Prompt-driven audio engineering team

## Scope

The user provides an **already-converted vocal WAV** and the beat/instrumental (or a full song and stems). This team does not perform voice conversion, train voice models, or separate vocals by default. Its job is to engineer the supplied audio into a complete, polished song using deliberate, prompt-guided processing.

These are specialist workflow roles, not a claim that six independently trained human engineers are running. At first they may share one local LLM. Real audio operations are performed by tested DSP tools and plugins; agents must not invent measurements or claim to have heard qualities that were not evaluated.

## The six roles

### 1. Producer / Prompt Interpreter
- Converts the user's prompt into a concise creative brief: emotion, genre, vocal intimacy, space, tone, dynamics, stereo image, and explicit avoid-list.
- Clarifies only when an ambiguity materially affects the result.
- Creates an effects map before processing and explains why each effect is chosen.

### 2. Audio Analyst
- Inspects files, loudness, peaks, clipping, silence, channel count, sample rate, phase/correlation where available, timing and alignment.
- Measures the vocal and instrumental separately and checks headroom before mixing.
- Distinguishes measured facts from hypotheses; no unsupported listening claims.

### 3. Vocal Mix Engineer
- Engineers the supplied vocal: corrective EQ, de-essing if needed, gentle compression, automation, saturation, reverb, delay, modulation, filtering, or creative treatments when the prompt calls for them.
- Preserves vocal identity, phrasing, transients and intelligibility. Avoids high-frequency harshness and excessive processing unless specifically requested.
- Chooses effect sends and automation intentionally; never adds effects randomly.

### 4. Instrumental / Balance Engineer
- Balances vocal and beat, manages masking, gain staging, low-end conflicts, stereo placement, and bus routing.
- Uses side-chain or dynamic EQ only when justified by the material and available tools.
- Preserves the arrangement and timing unless the user asks for changes.

### 5. Mix Director / Creative FX Designer
- Turns evocative prompts such as “dreamcore, from another world, intimate, distant and warm” into explicit, time-aware effect choices: pre-delay, decay, delay subdivisions, filtering, stereo movement, send levels, automation and transitions.
- Builds a coherent motif across sections (intro, verse, chorus, bridge, outro), not a random effect on every track.
- Creates a conservative main version and an optional more creative alternate when useful.

### 6. Mastering & Independent QA Engineer
- Checks tonal balance, dynamics, integrated loudness, peak/true peak where supported, clipping, export format and translation risks.
- Compares before/after measurements and rejects silent, clipped, misaligned, corrupted, or unexpectedly shortened renders.
- Makes subjective quality claims only after supported listening evaluation; asks the user for A/B preference when taste is the deciding factor.

## Workflow

1. Import the supplied vocal WAV and instrumental/beat, preserve read-only originals, inspect metadata and align tracks.
2. Analyze each file separately and establish safe gain/headroom.
3. Interpret the prompt and prepare a structured plan with track routing, plugin/FX choices, parameter ranges, automation points, and rationale.
4. Show the plan and ask approval before risky changes or any cloud upload. Local processing is default.
5. Render reversible stages: cleanup only if needed, vocal chain, instrumental/bus balance, creative FX, mix bus, master, export.
6. Validate each stage and roll back failed steps. Bound retries to avoid endless processing.
7. Present A/B playback and at least one report with operations, plugin versions, parameter values, loudness and peak measurements, warnings, and output paths.
8. Keep intermediate versions; never overwrite the source or auto-publish.

## Required effect-plan schema

Every effect entry should specify: track/bus, purpose, effect/plugin ID, parameters and allowed bounds, wet/dry, automation or section scope, dependencies/order, and the reason it serves the user's prompt. The orchestrator validates this plan against registered plugins and operations before execution. Missing plugins must be reported; never silently substitute an unrelated effect.

## Safety and quality boundaries

- No arbitrary shell or code execution from LLM output.
- Tool arguments are typed, bounded, allowlisted and logged.
- No voice conversion or source separation in the default workflow.
- No cloud upload without explicit opt-in and a clear disclosure.
- No claim of professional quality based only on a model's self-review. Use objective checks plus human A/B listening.
