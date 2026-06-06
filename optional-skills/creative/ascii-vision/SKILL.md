---
name: ascii-vision
description: "Use when vision_analyze fails. Converts images to ASCII art via ffmpeg + Python as a diagnostic fallback to identify visual content — brightness distribution, texture, and structure — without vision APIs."
version: 1.1.0
author: chdlc
license: MIT
metadata:
  hermes:
    tags: [vision, ascii, fallback, image, diagnostic]
    related_skills: [ascii-art, hyperframes]
    category: creative
---

# ASCII Vision

Fallback image viewer when vision models are unavailable (rate limited, model down, etc.). Converts images to ASCII art using ffmpeg + Python so you (or the agent) can identify visual content — shapes, brightness distribution, textures, and structure — without relying on any vision API.

## When to Use

- `vision_analyze` returns rate limit, model unavailable, or timeout errors
- You need to quickly distinguish between similar-looking images (e.g., "is this a dark variant of the same composition?")
- The agent needs visual inspection but no vision provider is configured
- Debugging image generation output — check if an image was actually produced before sending it to the user

## How It Works

1. ffmpeg scales the image to a low resolution (e.g. 60 columns) in grayscale, preserving aspect ratio
2. A Python script maps each pixel (0-255) to an ASCII character
3. The output reveals shapes, textures, relative brightness, and spatial distribution

### Character Map

The formula `v * len(chars) // 256` evenly divides 256 brightness levels across 10 characters:

| Range | Char | Meaning |
|-------|------|---------|
| 0-25  | ` `  | Pure black |
| 26-51 | `.`  | Very dark |
| 52-76 | `:`  | Dark |
| 77-102 | `-` | Mid-dark |
| 103-127 | `=` | Medium |
| 128-153 | `+` | Mid-light |
| 154-179 | `*` | Light |
| 180-204 | `#` | Very light |
| 205-230 | `%` | Near white |
| 231-255 | `@` | Pure white |

## Setup

The bundled script is at `scripts/ascii_viewer.py`. Reference it directly:

```bash
SCRIPT=~/.hermes/hermes-agent/optional-skills/creative/ascii-vision/scripts/ascii_viewer.py
```

It accepts an optional **width** argument (default: 60). Height is auto-detected from the pixel data, so you can use ffmpeg's `scale=W:-1` to preserve the original aspect ratio without distortion.

## Usage

### Basic ASCII Conversion

```bash
SCRIPT=~/.hermes/hermes-agent/optional-skills/creative/ascii-vision/scripts/ascii_viewer.py

# Default 60 columns (auto height, aspect ratio preserved)
ffmpeg -y -i <image_path> -vf "scale=60:-1,format=gray" -frames:v 1 -f rawvideo pipe: 2>/dev/null | python3 "$SCRIPT"

# Custom width
ffmpeg -y -i <image_path> -vf "scale=80:-1,format=gray" -frames:v 1 -f rawvideo pipe: 2>/dev/null | python3 "$SCRIPT" 80
```

### Batch Scan Multiple Images

```bash
SCRIPT=~/.hermes/hermes-agent/optional-skills/creative/ascii-vision/scripts/ascii_viewer.py

for f in *.jpg; do
    echo "=== $f ==="
    ffmpeg -y -i "$f" -vf "scale=60:-1,format=gray" -frames:v 1 -f rawvideo pipe: 2>/dev/null | python3 "$SCRIPT"
done
```

### Recommended Widths

| Width | Use case |
|-------|----------|
| `40`  | Quick scan, simple images |
| `60`  | Balanced readability vs detail (default) |
| `80`  | More detail, complex images |
| `120` | Maximum detail, readable text (may be too wide for chat) |

## Interpreting the Output

### Overall Brightness
- **Many `@%#`** → bright scene, well-lit
- **Many `.-:`** → dark scene, night-time
- **Top-to-bottom gradient** → directional lighting (lamp above, shadow below)

### Content Patterns
- **Clusters of `#%@`** → bright objects, light sources, highlights
- **Vertical/horizontal lines of `-=`** → edges, furniture, structures
- **Organized patterns with mixed brightness** → text, diagrams, labeled elements
- **Heavy texture (`*#%@` intermixed)** → detailed surfaces (fabric, foliage, textured objects)
- **Flat bands with little variation** → night scenes, skies, plain backgrounds

### Distinguishing Image Types
- Bright top + textured center + dark bottom → product shot or figure with directional lighting
- Uniformly dark with sparse clusters → night scene, silhouettes
- Structured patterns with `+=-:#%@` formations → technical diagram, text overlay
- Same scene as another but with more detail/texture in a zone → variant with more content/elements

## Limitations

ASCII art is a **mechanical fallback** — it does NOT replace a vision model. Here's what it can and cannot do:

| Detects | Does NOT detect |
|---------|-----------------|
| Overall brightness (light vs dark scene) | Semantic meaning (what the subject is) |
| Contrast between regions | Color (everything is grayscale) |
| Texture (smooth vs detailed surface) | Legible text (only knows "something is there") |
| Lighting gradients (top-down, side, etc.) | Faces, emotions, or expressions |
| Edges and sharp transitions | Specific objects (person, cat, mask) |
| Spatial distribution of content | Depth, perspective, or real dimensions |

**Good for:**
- Checking if a generated image actually has content vs being blank
- Distinguishing between two variants of the same composition
- Detecting if there's text/detail in a specific region
- Confirming an image exists before sending it to the user

**Not good for:**
- Reading text (signs, screenshots, memes)
- Color-critical analysis
- Identifying objects, people, or animals
- Images with very fine detail (< 2-3 pixels wide)

ASCII gives you **structural data** (brightness, texture, edges), not semantics. It's like looking at a photo with your eyes closed — you can feel light and shadow, but you can't name what you see.

## Common Pitfalls

1. **Brightness-only.** You cannot distinguish red from blue if they have the same luminance — color information is lost.
2. **Too-low width** (e.g. 30) loses fine detail like small text. Stick to 60 minimum.
3. **Too-high width** (e.g. 120+) produces ASCII that is illegible in a chat context — the output is too wide to display cleanly.
4. **Smooth gradients** render as solid bands of a single character. This is expected, not a bug.
5. **Not a vision replacement.** ASCII art is a fallback for when `vision_analyze` is unavailable, not a substitute. Always prefer the real tool when it works.
6. **ffmpeg not installed.** Verify with `which ffmpeg` before attempting. On most systems ffmpeg is available, but minimal Docker images may lack it.

## Verification Checklist

- [ ] ffmpeg is installed (`which ffmpeg`)
- [ ] Script at `scripts/ascii_viewer.py` exists and is executable
- [ ] Image path exists and is a valid image file
- [ ] Width is appropriate for the level of detail needed (60 default)
- [ ] ffmpeg scale uses `-1` for height to preserve aspect ratio (e.g. `scale=60:-1`)
- [ ] Output shows recognizable patterns, not just noise
