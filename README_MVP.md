# VeryRare AI Studio — local audio-engine MVP

The repository now includes a first functional UI/API pass. This is an executable foundation, not a claim of finished professional mastering.

## Start the UI (Windows 11)

Install Python 3.11 or 3.12 and run from the repository folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.web_app:app --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765. The first UI supports WAV import (500 MiB/file), metadata analysis, built-in DSP controls, render to a new 24-bit WAV, audio preview/download, and basic output measurements. Default workspace is the repository's `workspace/` directory; set `VERYRARE_AUDIO_ROOT` to change it.

## Scope

- Input: **already-converted vocal WAV** + instrumental/beat WAV.
- Local deterministic DSP: vocal high-pass, presence EQ, simple compression, simple room reverb, delay, track gains and peak ceiling.
- **VST3 hosting via Spotify Pedalboard:** inspect a plugin, discover common Windows VST3 folders, render a WAV through one plugin, or run a sequential chain from a reviewed JSON manifest.
- **AI planning:** local-first Ollama text planner; optional Gemini cloud text planner only with explicit `--allow-cloud` and a user-supplied `GEMINI_API_KEY`. Audio is not uploaded by the agent router.
- Output: 24-bit PCM WAV plus JSON measurement/render report.
- No voice conversion, no vocal separation, no automatic plugin downloads, no arbitrary LLM-generated code or shell commands.
- The VST3 adapter is an early offline MVP: no plugin GUI, MIDI/instrument rendering in the chain, sidechain routing, latency compensation, real-time monitoring, or section automation. Third-party plugins are not sandboxed; only load trusted plugins.
- The Production Brief in the UI is informational only in this version and is not yet connected to an AI planner.
- The UI is not packaged as a native desktop executable. Render history is in-memory for the current browser session only.

## CLI mixer

```powershell
python -m app.cli analyze "D:\Audio\vocal.wav"
python -m app.cli mix --vocal "D:\Audio\vocal.wav" --instrumental "D:\Audio\beat.wav" --output "D:\Audio\VeryRare-Mix.wav"
```

## VST3 hosting

Discover plugins in standard Windows VST3 locations:

```powershell
python -m app.cli vst3-scan
```

Inspect one plugin:

```powershell
python -m app.cli vst3-inspect --plugin "C:\Program Files\Common Files\VST3\Example.vst3"
```

Render one plugin:

```powershell
python -m app.cli vst3-render --input "D:\Audio\vocal.wav" --output "D:\Audio\vocal-fx.wav" --plugin "C:\Program Files\Common Files\VST3\Example.vst3" --wet 0.8 --param mix=0.25
```

Plugin parameter names/values depend on the installed plugin; inspect first. For a sequential chain, create a JSON manifest with a `plugins` array and run `python -m app.cli vst3-chain --input "D:\Audio\vocal.wav" --output "D:\Audio\vocal-chain.wav" --manifest "D:\Audio\chain.json"`.

Use only plugins you trust and have permission to use. Pedalboard is GPL-3.0; review licensing before distributing the app as closed-source or bundling it into another product. Third-party plugin licenses remain separate.

## MCP server for compatible local clients

The server uses MCP stdio transport. Configure a compatible local MCP client to launch `python -m app.mcp_server` from the repository folder using the same Python environment. Audio paths are restricted to the configured workspace and outputs are not silently overwritten. Keep the UI server and MCP server separate.

ChatGPT custom MCP availability depends on product plan/workspace and supported connection method. A local stdio server is not automatically connected to this conversation. See https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt

## AI planner

Local-only planning requires Ollama and a downloaded model:

```powershell
python -m app.cli agent-plan --mode local --local-model gemma3:4b --prompt "Make the vocal clearer but keep it soft and natural."
```

Cloud fallback is off by default. To explicitly enable text-only Gemini planning, set your own key in the environment and pass `--allow-cloud`. Cloud quotas can change; this project does not enable paid billing or automatically attempt a paid fallback. The plan remains advisory and does not yet automatically execute effects.

## Tests and caveats

```powershell
pip install pytest
pytest -q
```

The new web UI/API has not yet been run on the user's Windows machine. Confirm WAV import, matching sample rates, rendering, playback, downloads, responsive layout, and security boundaries before relying on it for releases. A discovered VST3 is not guaranteed to load or sound good; listen and A/B every result.
