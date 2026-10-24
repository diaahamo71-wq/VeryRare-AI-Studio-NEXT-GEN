# VeryRare AI Studio — runnable audio-engine MVP

This is the first executable foundation, not a claim of finished professional mastering.

## Scope

- Input: **already-converted vocal WAV** + instrumental/beat WAV.
- Local deterministic processing: vocal high-pass, gentle presence EQ, conservative compression, small room reverb, optional delay, track gains and peak ceiling.
- Output: 24-bit PCM WAV plus a JSON measurement/settings report.
- No voice conversion, no vocal separation, no cloud upload, no paid API.
- The first version does not automatically align timing, time-stretch, detect song sections, host arbitrary VST plugins, or perform LUFS-target mastering. Listen to the render and compare it with the original before release.

## Windows 11 setup

Install Python 3.11 or 3.12, then in the repository folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run

Analyze a WAV:

```powershell
python -m app.cli analyze "D:\Audio\vocal.wav"
```

Render a mix:

```powershell
python -m app.cli mix --vocal "D:\Audio\vocal.wav" --instrumental "D:\Audio\beat.wav" --output "D:\Audio\VeryRare-Mix.wav" --reverb 0.08 --delay 0.05
```

Use WAV files with matching sample rates. Inputs are read only; output and report are written to the output path.

## Tests

```powershell
pip install pytest
pytest -q
```

The DSP is intentionally conservative. A future prompt planner must translate the user's sound description into a reviewable settings plan, not execute arbitrary generated code. Additional agent roles and VST hosting should be added only with tests and verified plugin licensing.
