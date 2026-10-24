# VST3 hosting and AI-agent control

## Implemented adapter

VeryRare AI Studio uses Spotify Pedalboard as the first offline VST3 hosting backend. The Python adapter in `app/vst3_host.py` can discover common Windows VST3 folders, smoke-test an explicitly selected plugin, inspect exposed parameter keys, and render one WAV through one plugin. It writes a JSON report. The scanner in `app/plugin_scanner.py` reports load failures rather than pretending a discovered plugin works.

Install the current dependency with:

```powershell
python -m pip install -r requirements.txt
```

Usage:

```powershell
python -m app.cli vst3-scan
python -m app.cli vst3-inspect --plugin "C:\Program Files\Common Files\VST3\Example.vst3"
python -m app.cli vst3-render --input "D:\Audio\vocal.wav" --output "D:\Audio\vocal-fx.wav" --plugin "C:\Program Files\Common Files\VST3\Example.vst3" --wet 0.8
```

Parameter names and values differ by plugin. Inspect first, then pass exact exposed names with `--param NAME=VALUE`. The adapter currently requires equal-length effect output; instruments, MIDI, sidechains, latency compensation, realtime audio, plugin GUIs, and time automation are not yet implemented.

## Important limitations

- Discovery does not mean compatible; a successful load is only a smoke test.
- This first adapter is **not sandboxed**. Only load trusted plugins. Some plugins may hang or crash; robust production use should isolate plugin loading/rendering in a separate worker process with timeout and crash recovery.
- Pedalboard is GPL-3.0. Review the license before distributing VeryRare AI Studio as a closed-source or bundled product. Do not bundle third-party plugins without checking their individual licenses.
- Plugins remain user-installed. The studio does not silently download plugins or bypass licenses.
- The existing DSP mix engine remains available. VST3 support is additive and does not yet replace every DSP stage with plugin hosting.

## Agent access and permissions

`app/agent_router.py` supports a local Ollama planner and an optional cloud Gemini planner. Local is preferred by default. Cloud planning is disabled unless explicitly opted in, and requires a key supplied through `GEMINI_API_KEY`. Only the text prompt/plan is sent to the cloud; this module does not upload audio.

Agents can recommend a chain and settings, but do not get unrestricted file-system or shell access. A later execution controller must validate each requested plugin against the user's scanned plugin manifest, check parameter names/ranges, ask before destructive or high-risk operations, and record every executed step. No plugin is claimed as active until a render succeeds.

## Local/cloud design

- Local: Ollama API on `127.0.0.1:11434`. On a 16 GB RAM machine with a very weak GPU, use a small quantized model and expect slower CPU inference.
- Cloud: Gemini API free-tier availability depends on account, model and current quotas. Free-tier data handling may differ from paid tier; do not send confidential text. No paid billing is enabled by this app, and no paid fallback is attempted.
- Fail closed: if local is unavailable and cloud consent is off, return a clear unavailable status rather than sending anything externally.
