#!/usr/bin/env python3
"""Read raw grayscale pixel data from stdin and render as ASCII art.

Usage: python3 /path/to/ascii_viewer.py [width]
  Default width: 60 columns. Height is auto-detected from pixel data.
  Use with ffmpeg's scale=W:-1 to preserve aspect ratio.

Examples:
  ffmpeg -i img.jpg -vf "scale=60:-1,format=gray" -frames:v 1 -f rawvideo pipe: | python3 ascii_viewer.py
  ffmpeg -i img.jpg -vf "scale=80:-1,format=gray" -frames:v 1 -f rawvideo pipe: | python3 ascii_viewer.py 80
"""
import sys

# Width from CLI arg (default 60), height auto-detected from data
w = int(sys.argv[1]) if len(sys.argv) > 1 else 60
chars = " .:-=+*#%@"
data = sys.stdin.buffer.read()
h = len(data) // w  # auto-detect height from byte count

for y in range(h):
    line = ""
    for x in range(w):
        idx = y * w + x
        if idx < len(data):
            v = data[idx]
            # Map 0-255 brightness to character index via v * 10 // 256
            c = chars[min(v * len(chars) // 256, len(chars) - 1)]
            line += c
    print(line)
