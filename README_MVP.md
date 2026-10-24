# VeryRare AI Studio — runnable local audio-engine MVP

This is an executable foundation, not a claim of finished professional mastering.

## Scope

- Input: **already-converted vocal WAV** + instrumental/beat WAV.
- Local deterministic DSP: vocal high-pass, presence EQ, compression, simple room reverb, delay, track gains and peak ceiling.
- **VST3 hosting via Spotify Pedalboard:** inspect a plugin, discover common Windows VST3 folders, render a WAV through one plugin, or run a sequential chain from a reviewed JSON manifest.
- **AI planning:** local-first Ollama text planner; optional Gemini cloud text planner only with explicit `--allow-cloud` and a user-supplied `GEMINI_API_KEY`. Audio is not uploaded by the agent router.
- Output: 24-bit PCM WAV plus JSON measurement/render report.
- No voice conversion, no vocal separation, no automatic plugin downloads, no arbitrary LLM-generated code or shell commands.
- The VST3 adapter is an early offline MVP: no plugin GUI, MIDI/instrument rendering in the chain, sidechain routing, latency compensation, real-time monitoring, or section automation yet. Third-party plugins are not sandboxed in this version; only load trusted plugins.
- Discovered/loaded plugins are not automatically guaranteed to sound good or be compatible. Listen to every render and compare with bypass before release.

## Windows 11 setup

Install Python 3.11 or 3.12, then in the repository folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Existing mixer

```powershell
python -m app.cli analyze "D:\Audio\vocal.wav"
python -m app.cli mix --vocal "D:\Audio\vocal.wav" --instrumental "D:\Audio\beat.wav" --output "D:\Audio\VeryRare-Mix.wav"
```

## VST3 hosting

Discover plugins in standard Windows VST3 locations:

```powershell
python -m app.cli vst3-scan
```

Inspect one plugin and see its actual exposed parameter names:

```powershell
python -m app.cli vst3-inspect --plugin "C:\Program Files\Common Files\VST3\Example.vst3"
```

Render one plugin:

```powershell
python -m app.cli vst3-render --input "D:\Audio\vocal.wav" --output "D:\Audio\vocal-fx.wav" --plugin "C:\Program Files\Common Files\VST3\Example.vst3" --wet 0.8 --param mix=0.25
```

Parameter names and values depend on the actual plugin; inspect first. For a sequential chain, create a JSON manifest with a `plugins` array, each containing an explicit `path`, optional `parameters` object, and `wet` value, then run:

```powershell
python -m app.cli vst3-chain --input "D:\Audio\vocal.wav" --output "D:\Audio\vocal-chain.wav" --manifest "D:\Audio\chain.json"
```

Use only plugins you trust and have permission to use. Pedalboard is GPL-3.0; review licensing before distributing the app as closed-source or bundling it into another product. Third-party plugin licenses remain separate.

## MCP server for Claude and compatible clients

Install dependencies, then set the audio workspace to a folder containing your WAV files:

```powershell
$env:VERYRARE_AUDIO_ROOT = "D:\\VeryRareAudio"
python -m app.mcp_server
```

The server uses MCP stdio transport, suitable for local MCP clients such as Claude Desktop. Configure the client to launch the command from the repository directory using the same Python environment. Tools include studio status, plugin scan/inspect, WAV analysis, single-plugin render, and sequential VST3 chain render. Paths are restricted to the configured audio workspace; plugin paths must match discovered VST3 bundles. Outputs are not overwritten silently.

To use the server with ChatGPT, product/account support and connection method matter. ChatGPT custom MCP availability is restricted by plan/workspace and may require a remotely reachable HTTPS endpoint or Secure MCP Tunnel. A local stdio server is not automatically connected to this chat. See the official docs: https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt

## AI agent planner

Local-only planning (requires Ollama running and the selected model installed):

```powershell
python -m app.cli agent-plan --mode local --local-model gemma3:4b --prompt "Make the vocal clearer but keep it soft and natural."
```

Cloud fallback is off by default. To explicitly enable text-only Gemini planning, first set your own key in the environment, then:

```powershell
$env:GEMINI_API_KEY = "YOUR_KEY"
python -m app.cli agent-plan --mode auto --allow-cloud --prompt "Suggest an effect chain for a dark, dreamy vocal."
```

Cloud free-tier availability and quotas can change. This app does not enable paid billing or automatically attempt a paid fallback. Do not send confidential text to a cloud service. The AI output is advisory: it does not yet automatically execute the plan. Plugin execution must go through reviewed manifests and the installed-plugin checks.

## Tests

```powershell
pip install pytest
pytest -q
```

The code has been committed to GitHub but has not yet been run on your Windows machine; actual VST3 compatibility must be verified with your installed plugins.
