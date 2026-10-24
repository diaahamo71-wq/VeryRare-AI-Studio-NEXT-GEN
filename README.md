# VeryRare AI Studio NEXT GEN

A local-first audio engineering studio for already-converted vocal WAVs and instrumental/beat WAVs. It does **not** perform voice conversion or vocal separation.

## Current implementation

- Local browser UI served by FastAPI on loopback: import WAVs, inspect basic measurements, adjust built-in DSP controls, render a new 24-bit PCM WAV, play/download it, and inspect the measurement report.
- Built-in deterministic DSP for track mixing: high-pass, presence EQ, simple compression, short-tap room reverb, delay, track gain and a sample-peak ceiling.
- Experimental Pedalboard VST3 adapter and sequential effect-chain tools. Plugin compatibility is specific to each installed plugin.
- Local stdio MCP server for audio analysis, VST3 discovery/inspection, actual VST3 rendering, timeline validation, and **time-local automation rendering for one WAV track at a time**.
- Time-local automation supports built-in telephone-style filtering/saturation, reverb, delay, EQ, compressor, and discovered VST3 effects, with event start/end, wet mix, fade-in and fade-out. It writes a report and does not overwrite source or existing output files.
- XIAS-inspired UI quality guide: `docs/XIAS_UI_GUIDELINES.md`.

## Windows 11 quick start

**Simplest route:** run `setup_windows.bat` once, then double-click `start_studio.bat`. The setup script creates a local virtual environment and installs the declared dependencies. The launcher starts the app only on loopback. Keep its terminal window open while using it.

Manual route (Python 3.11 or 3.12) from the repository folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.web_app:app --host 127.0.0.1 --port 8765
```

Open **http://127.0.0.1:8765** in Chrome or Edge. The server command binds to loopback, so it is intended for this computer only. Keep that host setting; do not expose the development server to your network or the public internet.

Default audio workspace: `workspace/` inside the repository. To use another folder, set `VERYRARE_AUDIO_ROOT` before starting the server. The UI accepts WAV files up to 500 MiB each. Source files are copied into the workspace; renders use unique names and do not overwrite imported files.

## Automation renderer: current boundaries

- MCP tool `render_automation_timeline` renders a validated JSON timeline against one input WAV/track. Run it separately for vocal and instrumental tracks; it rejects enabled events targeting a different track.
- Supported built-in events: `builtin_telephone`, `builtin_reverb`, `builtin_delay`, `builtin_eq`, and `builtin_compressor`. A VST3 event requires an exact discovered plugin path and inspected parameters.
- Events run sequentially in ascending start-time order; overlapping events therefore process the result of earlier events. Effects are confined to the selected segment. Reverb/delay tails are not extended beyond event end in this version.
- Harmonizer and pitch correction are **not implemented**. Those events fail explicitly rather than producing a fake success. No reference-song effect matching is implemented yet.
- The renderer does not silently normalize loudness. It reports if the render may clip. Listen and A/B against the source before release.
- The browser UI does not yet expose a timeline editor or call the new MCP renderer directly. The optional text planner remains advisory and does not automatically transfer suggestions into render controls.
- Third-party VST3 plugins are not sandboxed; a faulty or untrusted plugin can crash the process.

## Privacy and file safety

Audio processing is local; the web UI does not upload audio to an AI/cloud service. The optional text planner may use a cloud provider only through its separate explicitly enabled configuration. The local server should stay bound to 127.0.0.1. Do not store secrets in this repository.

## Tests and release status

Run the current tests with:

```powershell
pip install pytest
pytest -q
```

Tests were added for timeline validation and segment rendering, but they have **not yet been run in the user's Windows environment**. GitHub commits confirm files were stored, not that the app works on the target machine. Before treating this as a release, run tests and verify WAV import, automation rendering, playback and download locally.

## AI audio engineering roadmap

See [AI audio engineering contract](docs/AI_AUDIO_ENGINEERING_CONTRACT.md) for the reference-song workflow, plugin safety rules, timeline schema and acceptance gates. Reference-to-vocal matching, a timeline editor UI, automatic harmonizer/pitch correction, VST3 latency compensation and Windows integration testing remain unfinished.


### WAV / MP3 import and VST3 effects

The local UI accepts WAV and MP3 uploads. MP3 files are decoded locally to a working 24-bit PCM WAV copy; the original upload is not modified and audio is not sent to cloud services. MP3 decoding uses the `miniaudio` Python package listed in `requirements.txt`.

Use **Scan installed VST3 plugins** in the time-local effects panel to discover plugins in the standard Windows VST3 folder. A compatible installed VST3 effect such as a Valhalla reverb may then be selected for a timed segment. Plugin compatibility depends on Pedalboard and the plugin; third-party plugins are not sandboxed, so use only trusted plugins and test with a copy of your audio. Plugins installed in non-standard folders are not automatically found by this UI version.
