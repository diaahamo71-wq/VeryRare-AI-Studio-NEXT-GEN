"""Command-line interface for VeryRare AI Studio."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.audio_engine import MixSettings, analyze_file, mix_tracks


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="veryrare-studio",
        description="Local audio engineering for already-converted vocal + instrumental WAVs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="Measure a WAV file")
    analyze.add_argument("audio", type=Path)

    mix = sub.add_parser("mix", help="Render a conservative vocal + beat mix")
    mix.add_argument("--vocal", required=True, type=Path)
    mix.add_argument("--instrumental", required=True, type=Path)
    mix.add_argument("--output", required=True, type=Path)
    mix.add_argument("--vocal-gain-db", type=float, default=0.0)
    mix.add_argument("--beat-gain-db", type=float, default=-3.0)
    mix.add_argument("--reverb", type=float, default=0.08)
    mix.add_argument("--delay", type=float, default=0.0)

    sub.add_parser("vst3-scan", help="Discover and smoke-test VST3 plugins in standard folders")
    inspect = sub.add_parser("vst3-inspect", help="Load one VST3 and list its exposed parameter names")
    inspect.add_argument("--plugin", required=True, type=Path)

    render = sub.add_parser("vst3-render", help="Render a WAV through one VST3 effect")
    render.add_argument("--input", required=True, type=Path)
    render.add_argument("--output", required=True, type=Path)
    render.add_argument("--plugin", required=True, type=Path)
    render.add_argument("--wet", type=float, default=1.0)
    render.add_argument("--param", action="append", default=[], metavar="NAME=VALUE",
                        help="Plugin parameter; repeat as needed. Inspect plugin first.")

    chain = sub.add_parser("vst3-chain", help="Render an explicit sequential VST3 effect-chain manifest")
    chain.add_argument("--input", required=True, type=Path)
    chain.add_argument("--output", required=True, type=Path)
    chain.add_argument("--manifest", required=True, type=Path)

    plan = sub.add_parser("agent-plan", help="Generate an advisory effect plan; does not execute plugins")
    plan.add_argument("--prompt", required=True)
    plan.add_argument("--mode", choices=("auto", "local", "cloud"), default="auto")
    plan.add_argument("--allow-cloud", action="store_true",
                      help="Explicitly allow text-only cloud fallback (requires GEMINI_API_KEY)")
    plan.add_argument("--local-model", default="gemma3:4b")
    plan.add_argument("--cloud-model", default="gemini-2.5-flash")
    plan.add_argument("--output", type=Path)

    args = parser.parse_args()
    if args.command == "analyze":
        print(json.dumps(analyze_file(args.audio), indent=2))
        return 0
    if args.command == "mix":
        settings = MixSettings(
            vocal_gain_db=args.vocal_gain_db,
            instrumental_gain_db=args.beat_gain_db,
            reverb_mix=args.reverb,
            delay_mix=args.delay,
        )
        report = mix_tracks(args.vocal, args.instrumental, args.output, settings)
        print(json.dumps(report, indent=2))
        print(f"\nRendered: {args.output}")
        print(f"Report: {args.output.with_suffix('.report.json')}")
        return 0
    if args.command == "vst3-scan":
        from app.plugin_scanner import scan_and_test
        result = scan_and_test()
        print(json.dumps(result, indent=2))
        print(f"\nDiscovered {len(result)} VST3 bundle(s). A discovered plugin is not necessarily compatible.")
        return 0
    if args.command == "vst3-inspect":
        from app.vst3_host import inspect_plugin
        print(json.dumps(inspect_plugin(args.plugin), indent=2))
        return 0
    if args.command == "vst3-render":
        from app.vst3_host import render_vst3
        params = {}
        for item in args.param:
            if "=" not in item:
                parser.error(f"Invalid --param {item!r}; expected NAME=VALUE")
            name, value = item.split("=", 1)
            try:
                params[name] = float(value)
            except ValueError:
                parser.error(f"Parameter value must be numeric: {item!r}")
        print(json.dumps(render_vst3(args.input, args.output, args.plugin, params, args.wet), indent=2))
        return 0
    if args.command == "vst3-chain":
        from app.plugin_chain import render_chain
        print(json.dumps(render_chain(args.input, args.output, args.manifest), indent=2, ensure_ascii=False))
        return 0
    if args.command == "agent-plan":
        from app.agent_router import AgentConfig, plan_with_agent, save_plan
        config = AgentConfig(
            mode=args.mode,
            local_model=args.local_model,
            cloud_model=args.cloud_model,
            allow_cloud=args.allow_cloud,
        )
        result = plan_with_agent(args.prompt, config)
        if args.output:
            save_plan(result, str(args.output))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("agent") not in ("local-unavailable",) else 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
