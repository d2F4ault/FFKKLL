#!/usr/bin/env python3
"""
Deterministic Headless MIDI-to-MP4 Renderer (CLI & Python Library Interface)
============================================================================

Turns any Standard MIDI File (.mid / .midi) into a silent, frame-exact,
lossless MP4 video alongside a machine-readable JSON synchronization manifest.

Usage from CLI / CI:
    python3 render_midi.py --input fixtures/torture_test.mid --output output/torture_test.mp4 \\
        --width 1920 --height 1080 --fps 60 --lead-in 2.0 --quality rgb-lossless

Usage from Python:
    from render_midi import render_midi_to_mp4
    result = render_midi_to_mp4("fixtures/bach_846.mid", "output/bach.mp4", fps=60, lead_in=2.0)
    print(result["synchronization"]["midiToVideoOffsetSeconds"])
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parent
CLI_MJS = PROJECT_ROOT / "scripts" / "render-cli.mjs"


def render_midi_to_mp4(
    input_midi: str,
    output_mp4: str,
    *,
    sync_out: Optional[str] = None,
    width: int = 1920,
    height: int = 1080,
    fps: float = 60,
    lead_in: float = 2.0,
    tail_out: float = 1.0,
    quality: str = "rgb-lossless",
    preset: str = "medium",
    color_mode: str = "hand",
    note_label: str = "fingering",
    key_label: str = "onlyC",
    fall_seconds: float = 2.4,
    fit_range: bool = False,
    no_hud: bool = False,
) -> Dict[str, Any]:
    """
    Renders `input_midi` to `output_mp4` deterministically and returns the parsed JSON result
    including the synchronization manifest metadata. Raises RuntimeError on failure.
    """
    cmd = [
        "node",
        str(CLI_MJS),
        "--input",
        str(input_midi),
        "--output",
        str(output_mp4),
        "--width",
        str(width),
        "--height",
        str(height),
        "--fps",
        str(fps),
        "--lead-in",
        str(lead_in),
        "--tail-out",
        str(tail_out),
        "--quality",
        quality,
        "--preset",
        preset,
        "--color-mode",
        color_mode,
        "--note-label",
        note_label,
        "--key-label",
        key_label,
        "--fall-seconds",
        str(fall_seconds),
        "--json",
    ]
    if sync_out:
        cmd.extend(["--sync-out", str(sync_out)])
    if fit_range:
        cmd.append("--fit-range")
    if no_hud:
        cmd.append("--no-hud")

    proc = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"MIDI render failed (exit code {proc.returncode}):\n{proc.stderr.strip()}"
        )

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Could not parse JSON output from renderer: {exc}\nRaw stdout: {proc.stdout}"
        ) from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render any MIDI file into a silent, frame-exact, lossless MP4 video."
    )
    parser.add_argument("-i", "--input", default=None, help="Input .mid / .midi file path")
    parser.add_argument("-o", "--output", default=None, help="Output .mp4 video file path")
    parser.add_argument(
        "-c",
        "--config",
        default=None,
        help="Path to JSON configuration job file (overrides/supplements CLI options)",
    )
    parser.add_argument(
        "--sync-out",
        default=None,
        help="Output .sync.json manifest path (default: <output>.sync.json)",
    )
    parser.add_argument("-w", "--width", type=int, default=1920, help="Video width (default: 1920)")
    parser.add_argument("--height", type=int, default=1080, help="Video height (default: 1080)")
    parser.add_argument("-r", "--fps", type=float, default=60, help="Constant frame rate (default: 60)")
    parser.add_argument(
        "--lead-in",
        type=float,
        default=2.0,
        help="Constant lead-in before MIDI t=0.0s in seconds (default: 2.0, use 0.0 for zero offset)",
    )
    parser.add_argument(
        "--tail-out",
        type=float,
        default=1.0,
        help="Tail-out after last noteOff in seconds (default: 1.0)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        choices=["rgb-lossless", "yuv444-lossless", "compatible-lossless"],
        default="rgb-lossless",
        help="Lossless encoding profile (default: rgb-lossless)",
    )
    parser.add_argument(
        "--preset",
        default="medium",
        help="x264 encoding speed preset (ultrafast..veryslow, default: medium)",
    )
    parser.add_argument(
        "--color-mode",
        choices=["hand", "finger", "pitch", "colorblind", "monochrome"],
        default="hand",
        help="Note & key pigment mode (default: hand)",
    )
    parser.add_argument(
        "--note-label",
        choices=["fingering", "noteName", "solfege", "scaleDegree", "none"],
        default="fingering",
        help="Pedagogical label inside falling notes (default: fingering)",
    )
    parser.add_argument(
        "--key-label",
        choices=["onlyC", "allWhite", "all88", "solfege", "none"],
        default="onlyC",
        help="Piano key label mode (default: onlyC)",
    )
    parser.add_argument(
        "--fall-seconds",
        type=float,
        default=2.4,
        help="Falling note lookahead duration in seconds (default: 2.4)",
    )
    parser.add_argument(
        "--fit-range",
        action="store_true",
        help="Fit keyboard zoom to piece's active note range instead of full 88 keys",
    )
    parser.add_argument(
        "--no-hud",
        action="store_true",
        help="Disable top-left tempo/chord HUD text",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON summary to stdout",
    )

    args = parser.parse_args()
    if not args.config and (not args.input or not args.output):
        parser.error("Either --config <file.json> or both --input and --output must be provided.")

    # Forward directly to scripts/render-cli.mjs
    forward_cmd = ["node", str(CLI_MJS)] + sys.argv[1:]
    proc = subprocess.run(forward_cmd, cwd=str(PROJECT_ROOT))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
