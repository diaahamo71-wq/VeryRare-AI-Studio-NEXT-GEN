# VeryRare AI Studio NEXT GEN

A local-first audio engineering studio for already-converted vocal WAVs and instrumental/beat WAVs. It does **not** perform voice conversion or vocal separation.

## Current implementation

- Local browser UI served by FastAPI on loopback: import WAVs, inspect basic measurements, adjust the built-in DSP controls, render a new 24-bit PCM WAV, play/download it, and inspect the measurement report.
- Built-in deterministic DSP: high-pass, presence EQ, simple compression, short-tap room reverb, delay, track gain and a sample-peak ceiling.
- Experimental Pedalboard VST3 adapter and sequential effect-chain tools. Compatibility is plugin-specific and has not yet been verified against the user's Windows plugins.
- Local stdio MCP server for compatible MCP clients; optional text-only planner. The **AI Engineer · Plan and mix** action can use a local Ollama model or, only when the cloud checkbox is enabled, OpenRouter via `OPENROUTER_API_KEY`. Both modes receive the creative brief and objective measurements, validate all proposed DSP values against strict ranges, then pass settings to the actual local renderer. The cloud mode sends the brief and numeric measurements to OpenRouter; it does not upload WAV audio. The model is not claimed to have listened to the tracks. Missing model/key, network errors, and quota failures are shown explicitly; there is no silent heuristic/random fallback.
- XIAS-inspired UI quality guide: `docs/XIAS_UI_GUIDELINES.md`.

## Windows 11 quick start

**Simplest route:** run `setup_windows.bat` once, then double-click `start_studio.bat`. The setup script creates a local virtual environment and installs the declared dependencies. The launcher starts the app only on loopback. Keep its terminal window open while using the UI.

Manual route (Python 3.11 or 3.12) from the repository folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.web_app:app --host 127.0.0.1 --port 8765
```

Open **http://127.0.0.1:8765** in Chrome or Edge. For local AI, install Ollama, then run `ollama pull qwen3:4b-instruct` once; set `VERYRARE_LOCAL_MODEL` to change it. For cloud AI, create an OpenRouter API key and set it only in your local terminal environment as `OPENROUTER_API_KEY` before starting the app. The default cloud model is `openrouter/free`, which routes to a free model that supports the request features; free model availability, speed and limits can vary. Optionally set `VERYRARE_CLOUD_MIX_MODEL` to a specific supported OpenRouter model. Never commit API keys. Tick **Use cloud AI for mix plan** to opt in. That sends the production brief and numeric measurements, not the audio files. The server command binds to loopback; do not expose the development server to your network or the public internet.

Default audio workspace: `workspace/` inside the repository. To use another folder, set `VERYRARE_AUDIO_ROOT` before starting the server. The UI accepts WAV files up to 500 MiB each. Source files are copied into the workspace; renders use unique names and do not overwrite imported files.

## Important feature boundaries

- The AI Engineer can propose bounded settings and transfer them into the existing mix controls before the local DSP render. It does not yet execute arbitrary plugin chains or judge audio by listening.
- Built-in reverb is a simple early-reflection-style tap model, not convolution reverb or a professional room simulator.
- Peak limiting is not LUFS/true-peak mastering. The UI reports basic peak/RMS measurements, not subjective quality.
- Auto-Tune, harmonizer, dereverb, denoising and other advanced processing require a separately verified implementation/plugin. They are not silently simulated by the built-in engine.
- The first UI pass has no live waveform analysis, cancellation, streamed render progress, undo stack, packaged desktop executable, or persistent cross-session render history.
- The VST3 host is experimental and does not sandbox third-party plugins. Only load plugins you trust; a faulty plugin may crash the process.

## Privacy and file safety

The audio DSP render stays local. Cloud AI mode sends the production brief and numeric measurements to OpenRouter but does not upload the source WAVs. Use cloud mode only if you agree to send that text/metadata to the provider. Keep API keys in environment variables, never in source control. The local server should stay bound to 127.0.0.1.

## XIAS / UI quality

XIAS is used as an open-source design and accessibility reference, not as an application runtime dependency. Review the UI against `docs/XIAS_UI_GUIDELINES.md`; accessibility, responsive-browser, and Windows integration checks are still required before release.

## Tests and release status

Run the current tests with:

```powershell
pip install pytest
pytest -q
```

GitHub commits confirm that files were stored in the repository; they do **not** prove that the app runs correctly on Windows. The new UI and API have not yet been executed in the user's environment. Validate the setup, WAV import, render, playback, and download locally before treating this as a working release.
