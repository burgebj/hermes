#!/usr/bin/env python3
"""Generate v12 Buddy pixel-art mouth/viseme assets from a clean base PNG.

Dependencies: ImageMagick `magick` only. No PIL/Pillow.

This implements the accepted Prismtek/Buddy v12 mouth recipe:
- start from a clean full-arm Buddy base PNG;
- create a no-mouth base by cloning nearby face texture over the original smile;
- surgically erase the remaining lower smile dashes that caused a two-mouth artifact;
- draw small, slightly larger-than-v8 pixel-art mouth states.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def magick(*args: str | Path) -> None:
    run(["magick", *map(str, args)])


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate v12 Buddy mouth/viseme PNGs from a clean base avatar")
    parser.add_argument("base", type=Path, help="Clean Buddy PNG, e.g. buddy-host-main-v5-full-arm-clean.png")
    parser.add_argument("--out-dir", type=Path, help="Output directory. Defaults to base image directory")
    parser.add_argument("--prefix", default="buddy-host-main-v12", help="Output filename prefix")
    args = parser.parse_args()

    if shutil.which("magick") is None:
        raise SystemExit("Missing dependency: ImageMagick `magick`")
    if not args.base.exists():
        raise SystemExit(f"Base image not found: {args.base}")

    out_dir = args.out_dir or args.base.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix

    no_mouth = out_dir / f"{prefix}-no-mouth-base.png"

    # Clone clean face texture from above the mouth into the original smile zone.
    # Coordinates are for the canonical 442x440 v5 clean crop.
    magick(
        args.base,
        "(", args.base, "-crop", "50x30+216+224", "+repage", ")",
        "-geometry", "+216+246", "-compose", "over", "-composite",
        no_mouth,
    )

    # Surgical erase of the leftover lower smile dashes identified in v10/v11 QA.
    magick(
        no_mouth,
        "-fill", "#d2f5eb", "-draw", "rectangle 222,273 232,278",
        "-fill", "#d1f4ea", "-draw", "rectangle 252,273 263,278",
        no_mouth,
    )

    states: dict[str, list[str]] = {
        "mouth-closed": [
            "-fill", "#18205e", "-draw",
            "rectangle 229,253 234,258 rectangle 234,258 244,262 rectangle 244,253 250,258",
        ],
        "mouth-small-open": [
            "-fill", "#18205e", "-draw", "rectangle 231,249 249,266 rectangle 234,266 246,270",
            "-fill", "#ff6f8f", "-draw", "rectangle 235,254 245,268",
            "-fill", "#ffe2d2", "-draw", "rectangle 236,252 244,255",
        ],
        "mouth-wide-open": [
            "-fill", "#18205e", "-draw", "rectangle 226,248 254,264 rectangle 230,264 250,270",
            "-fill", "#ff6f8f", "-draw", "rectangle 231,254 249,268",
            "-fill", "#ffe2d2", "-draw", "rectangle 233,252 247,255",
        ],
        "mouth-round-o": [
            "-fill", "#18205e", "-draw", "rectangle 232,249 248,266 rectangle 235,266 245,270",
            "-fill", "#ff6f8f", "-draw", "rectangle 236,253 244,265",
        ],
        "mouth-soft": [
            "-fill", "#18205e", "-draw", "rectangle 229,255 250,261",
        ],
    }

    for name, draw_args in states.items():
        out = out_dir / f"{prefix}-{name}.png"
        magick(no_mouth, *draw_args, out)
        print(out)

    print(no_mouth)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
