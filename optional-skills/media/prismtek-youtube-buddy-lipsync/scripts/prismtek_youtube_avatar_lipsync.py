#!/usr/bin/env python3
"""Audio-reactive Buddy avatar overlay for Prismtek/Buddy YouTube videos.

Creates a lightweight two-state VTuber mouth animation driven by input audio RMS.
Designed for low-memory machines: no ML lip-sync, no PIL/Pillow, only FFmpeg.
"""
from __future__ import annotations

import argparse
import array
import json
import math
import os
import shutil
import statistics
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def check_output(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def duration_seconds(path: Path) -> float:
    return float(check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ]))


def stream_summary(path: Path) -> str:
    try:
        return check_output([
            "ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height",
            "-of", "compact=p=0:nk=1", str(path),
        ])
    except Exception as exc:  # pragma: no cover - receipt helper
        return f"ffprobe_failed:{exc}"


def audio_rms_by_frame(video: Path, fps: int, duration: float) -> list[float]:
    sample_rate = 16000
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", str(sample_rate), "-f", "s16le", "-",
    ])
    samples = array.array("h")
    samples.frombytes(raw)
    frame_count = max(1, math.ceil(duration * fps))
    samples_per_frame = max(1, round(sample_rate / fps))
    rms: list[float] = []
    for i in range(frame_count):
        start = i * samples_per_frame
        chunk = samples[start:start + samples_per_frame]
        if not chunk:
            rms.append(0.0)
            continue
        mean_sq = sum(int(x) * int(x) for x in chunk) / len(chunk)
        rms.append(math.sqrt(mean_sq) / 32768.0)
    return rms


def mouth_states(rms: list[float], sensitivity: float) -> tuple[list[bool], dict[str, float]]:
    if not rms:
        return [], {"threshold": 0.0}
    nonzero = [x for x in rms if x > 0.0005] or rms
    med = statistics.median(nonzero)
    p85 = sorted(nonzero)[int(0.85 * (len(nonzero) - 1))]
    p95 = sorted(nonzero)[int(0.95 * (len(nonzero) - 1))]
    threshold = max(0.006, med + (p85 - med) * (0.42 / max(0.1, sensitivity)))
    open_threshold = threshold
    close_threshold = threshold * 0.62

    states: list[bool] = []
    open_now = False
    hold = 0
    for val in rms:
        if open_now:
            if val < close_threshold and hold <= 0:
                open_now = False
            else:
                hold -= 1
        elif val > open_threshold:
            open_now = True
            hold = 1
        states.append(open_now)

    # Tiny deterministic syllable closures during long open runs prevent a stuck-open mouth.
    run_start = None
    for i, state in enumerate(states + [False]):
        if state and run_start is None:
            run_start = i
        if (not state) and run_start is not None:
            run_len = i - run_start
            if run_len >= 10:
                for j in range(run_start + 5, i, 7):
                    if j < len(states):
                        states[j] = False
            run_start = None

    return states, {
        "median_rms": med,
        "p85_rms": p85,
        "p95_rms": p95,
        "threshold": threshold,
        "open_ratio": sum(states) / max(1, len(states)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Overlay audio-reactive Buddy mouth animation onto a video")
    parser.add_argument("input_video", type=Path)
    parser.add_argument("--closed", type=Path, required=True, help="Closed-mouth Buddy PNG")
    parser.add_argument("--open", type=Path, required=True, help="Open-mouth Buddy PNG")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--width", type=int, default=360)
    parser.add_argument("--margin-x", type=int, default=34)
    parser.add_argument("--margin-y", type=int, default=42)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--sensitivity", type=float, default=1.0)
    parser.add_argument("--limit-seconds", type=float, help="Optional render limit for proof clips")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    for dep in ["ffmpeg", "ffprobe"]:
        if shutil.which(dep) is None:
            raise SystemExit(f"Missing dependency: {dep}")
    for p in [args.input_video, args.closed, args.open]:
        if not p.exists():
            raise SystemExit(f"Missing file: {p}")

    source_duration = duration_seconds(args.input_video)
    render_duration = min(source_duration, args.limit_seconds) if args.limit_seconds else source_duration
    output = args.output or args.input_video.with_name(f"{args.input_video.stem}-buddy-lipsync.mp4")
    output.parent.mkdir(parents=True, exist_ok=True)

    rms = audio_rms_by_frame(args.input_video, args.fps, render_duration)
    states, stats = mouth_states(rms, args.sensitivity)
    frame_count = max(1, math.ceil(render_duration * args.fps))
    states = states[:frame_count]

    with tempfile.TemporaryDirectory(prefix="buddy_lipsync_frames_") as td:
        frames = Path(td)
        for i in range(frame_count):
            src = args.open if states[i] else args.closed
            os.symlink(src, frames / f"frame_{i:06d}.png")
        vf = f"[1:v]scale={args.width}:-1[avatar];[0:v][avatar]overlay=W-w-{args.margin_x}:H-h-{args.margin_y}:format=auto[v]"
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(args.input_video),
            "-framerate", str(args.fps), "-i", str(frames / "frame_%06d.png"),
            "-filter_complex", vf,
            "-map", "[v]", "-map", "0:a?",
            "-t", f"{render_duration:.3f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "veryfast",
            "-c:a", "copy", str(output),
        ]
        run(cmd)

    receipt = {
        "receipt_type": "buddy_lipsync_receipt",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_video": str(args.input_video),
        "output_video": str(output),
        "closed_avatar": str(args.closed),
        "open_avatar": str(args.open),
        "source_duration_seconds": source_duration,
        "render_duration_seconds": render_duration,
        "fps": args.fps,
        "overlay": {"width": args.width, "margin_x": args.margin_x, "margin_y": args.margin_y},
        "mouth_stats": stats,
        "output_size_bytes": output.stat().st_size if output.exists() else None,
        "streams": stream_summary(output) if output.exists() else None,
    }
    receipt_path = args.receipt or output.with_suffix(".lipsync-receipt.json")
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
