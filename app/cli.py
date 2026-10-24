"""Command-line interface for VeryRare AI Studio's local mix engine."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.audio_engine import MixSettings, analyze_file, mix_tracks


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="veryrare-studio",
        description="Mix an already-converted vocal WAV with an instrumental WAV locally.",
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
    args = parser.parse_args()

    if args.command == "analyze":
        print(json.dumps(analyze_file(args.audio), indent=2))
        return 0
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


if __name__ == "__main__":
    raise SystemExit(main())
