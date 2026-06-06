---
name: prismtek-youtube-buddy-lipsync
description: Use when producing Prismtek/Buddy YouTube videos that need a clean pixel-art Buddy host overlay with audio-reactive mouth movement.
version: 1.0.0
author: Prismtek / Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [youtube, video, ffmpeg, imagemagick, pixel-art, vtuber, prismtek]
    related_skills: [youtube-content]
---
# Prismtek YouTube Buddy Lip-Sync

## Overview

Use this skill to turn a static clean Buddy host PNG into a lightweight audio-reactive VTuber-style overlay for narrated Prismtek YouTube videos.

The workflow is intentionally simple and robust on low-memory machines:
- no ML lip-sync dependency;
- no Pillow/PIL dependency;
- ImageMagick for tiny pixel-art viseme generation;
- FFmpeg/ffprobe for audio RMS analysis and video compositing;
- small v12-style mouth assets that match Buddy's reference sheet.

## When to Use

- A Prismtek YouTube video has narration and Buddy should look like he is speaking.
- The static Buddy overlay feels too lifeless.
- You need a reproducible way to generate mouth states from a clean Buddy base PNG.
- You need to avoid previous bad mouth regressions: giant oval mouth, darker mint mouth patch, or two-mouth artifact.

## Required Tools

```bash
command -v magick
command -v ffmpeg
command -v ffprobe
python3 --version
```

Do **not** use PIL/Pillow; some target environments intentionally do not have it installed.

## Canonical Local Asset Pattern

A known-good Prismtek production base on Cody's Mac is:

```text
~/.hermes/assets/prismtek-youtube/avatar/buddy-host-main-v5-full-arm-clean.png
```

This base is already cropped/cleaned so it preserves Buddy's full viewer-right arm and avoids source-sheet borders/sparkles.

Generate v12 visemes from that clean base:

```bash
python3 optional-skills/media/prismtek-youtube-buddy-lipsync/scripts/generate_buddy_v12_visemes.py \
  ~/.hermes/assets/prismtek-youtube/avatar/buddy-host-main-v5-full-arm-clean.png \
  --out-dir ~/.hermes/assets/prismtek-youtube/avatar
```

Then render a proof clip:

```bash
python3 optional-skills/media/prismtek-youtube-buddy-lipsync/scripts/prismtek_youtube_avatar_lipsync.py \
  /path/to/base-video.mp4 \
  --closed ~/.hermes/assets/prismtek-youtube/avatar/buddy-host-main-v12-mouth-closed.png \
  --open ~/.hermes/assets/prismtek-youtube/avatar/buddy-host-main-v12-mouth-small-open.png \
  --output /tmp/buddy-lipsync-proof.mp4 \
  --limit-seconds 20
```

For full render, omit `--limit-seconds`.

## v12 Mouth Style Rules

v12 is the current accepted style:
- slightly bigger than the first good tiny-mouth attempt;
- still a small/cute pixel-art mouth, not a large oval;
- no darker mint rectangle around the mouth;
- no original-smile leftovers that create a second mouth;
- full Buddy crop/arm remains intact.

Rejected styles:
- oversized v5 open-mouth/Pac-Man mouth;
- v8 darker mint erase patch;
- v10 two-mouth artifact from leftover original-smile pixels.

## Verification Checklist

Before upload, render at least a 20s proof and extract frames around speech/silence:

```bash
ffmpeg -y -v error -ss 00:00:05 -i /tmp/buddy-lipsync-proof.mp4 -frames:v 1 /tmp/buddy-open.png
ffmpeg -y -v error -ss 00:00:10 -i /tmp/buddy-lipsync-proof.mp4 -frames:v 1 /tmp/buddy-closed.png
ffprobe -v error -show_entries format=duration -show_entries stream=codec_type,codec_name,width,height -of compact=p=0:nk=1 /tmp/buddy-lipsync-proof.mp4
```

Visual QA:
- one mouth only;
- no lower/side second mouth dashes;
- no darker mint patch around mouth;
- mouth opens/closes with narration energy;
- Buddy's full viewer-right arm remains visible;
- no source-sheet cyan border/sparkles;
- output duration/audio streams are preserved.

## Scripts

- `scripts/generate_buddy_v12_visemes.py` — creates no-mouth base and v12 mouth states from a clean Buddy PNG using ImageMagick.
- `scripts/prismtek_youtube_avatar_lipsync.py` — overlays closed/open mouth states based on audio RMS.

## Notes

This package does not include private production videos, credentials, OAuth tokens, or YouTube receipts. It stores the reusable process only.
