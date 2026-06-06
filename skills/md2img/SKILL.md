---
name: md2img
description: Convert markdown to styled PNG images via a compiled Go binary. Renders tables, headers, code blocks, lists, blockquotes to dark/light themed images for sharing on Matrix/chat.
category: creative
tags: [markdown, png, image, rendering, matrix]
---

# md2img — Markdown to PNG

Renders markdown to styled PNG images using a pure Go binary (`~/bin/md2img`). No external runtime dependencies.

## Pipeline

```
markdown → goldmark (parser) → canvas (golang.org/x/image + image/draw) → PNG
```

**No Ghostscript, no PDF intermediate.** The renderer draws directly to an `image.NRGBA` canvas using `golang.org/x/image/font` for TTF text and `image/draw` for shapes.

**Fonts**: Loads system TTF fonts via `findFirst()` — checks macOS paths (`/Library/Fonts/`, `~/Library/Fonts/`) then Ubuntu paths (`/usr/share/fonts/truetype/`). Falls back to `golang.org/x/image/font/basicfont` (bitmap, fixed-size — smaller output on systems without TTF fonts).

## Install

```bash
# Homebrew
brew install jmaciasluque/tap/md2img

# From source
cd ~/src/md2img && make build && make install
```

## Usage

```bash
# From file (RELIABLE — always works)
md2img -o output.png input.md

# From stdin
echo "## Hello" | md2img -o output.png

# With customization flags
md2img -o dark.png -heading-color "#006600" -table-header-bg "#2d3748" -dpi 300 input.md

# Auto-crop whitespace (tight around content)
echo "| A | B |" | md2img -o tight.png -trim

# Trim with custom padding (mm)
md2img -o padded.png -trim -trim-padding 10 input.md
```

**⚠️ Pitfall: heredoc paste in zsh.** Pasting a multi-line `cat << 'EOF' | md2img` block into zsh often fails silently. **Always write to a file first, then render from the file.**

**⚠️ Pitfall: `cat` aliased to `bat -n`.** On some machines, `cat` is aliased to `bat -n` which adds line numbers. This breaks markdown table parsing. Use `command cat` to bypass the alias when creating files.

## CLI Flags

See [references/cli-flags.md](references/cli-flags.md) for the full flag reference. Key groups:

- **Output**: `-o`, `-trim`, `-trim-padding`, `-dpi`, `-version`
- **Font**: `-font`, `-font-size`, `-heading-font`
- **Page**: `-page-w`, `-page-h`, `-margin`
- **Colors** (all accept hex like `#333366`): `-text-color`, `-heading-color`, `-table-header-bg`, `-table-header-fg`, `-table-row-even`, `-table-row-odd`, `-code-bg`, `-blockquote-line-color`, `-blockquote-text-color`, `-hr-color`
- **Table**: `-table-header-font`, `-table-header-size`, `-table-full-width` (opt-in to stretch tables across full width; default is auto-width fitting content)
- **Code**: `-code-font`, `-code-font-size`

**Note**: Input is a positional arg (not `-input`). Output is `-o` (not `-output`). Stdin is used when no positional arg is given.

## Library API

```go
import md2img "github.com/jmaciasluque/md2img"

// Simple
err := md2img.Render("# Hello\n\nWorld.", "output.png")

// With config
cfg := md2img.DefaultConfig()
cfg.DPI = 300
cfg.TableHeaderBg = md2img.Color{R: 45, G: 55, B: 72}
err := md2img.RenderWithConfig(input, output, cfg)
```

- `Config` struct holds all options, `DefaultConfig()` returns sensible defaults
- `HexToColor("#333366")` parses hex strings to `Color`
- `Color{R, G, B int}` — uses `int` (not `uint8`)
- **No `AsPDF` field** — PDF mode was removed with the Ghostscript pipeline

## Supported Markdown

- **Headers** (H1–H6) — bold, sized proportionally
- **Tables** — auto-width by default (columns fit content), configurable header/row colors, cell borders, zebra striping. Use `-table-full-width` to stretch across page width.
- **Bullet & numbered lists**
- **Code blocks** — monospace font, configurable background
- **Blockquotes** — configurable left border, italic
- **Horizontal rules** — configurable color and thickness
- **Bold** and **italic** text — rendered via `renderInline()` which walks AST children, switches font faces for `Emphasis` (level 2 = bold, level 1 = italic), and handles `CodeSpan` with monospace font
- **Inline code** — monospace font via `CodeSpan` nodes, rendered at body FontSize (not CodeFontSize) to avoid superscript floating. Uses `drawStringAt` with baseline offset for consistent alignment with surrounding text.

## Limitations

- **No inline images** — only text-based rendering.
- **No nested lists** — flat lists only.
- **Font availability varies by platform** — macOS has good TTF coverage; Ubuntu needs `fonts-liberation` package for proper rendering (CI installs it).

## Source & Repo

**GitHub:** https://github.com/jmaciasluque/md2img
**PR #2 (merged):** https://github.com/jmaciasluque/md2img/pull/2 — full changelog in [references/pr-history.md](references/pr-history.md)
**Tap:** https://github.com/jmaciasluque/homebrew-tap
**Local:** `~/src/md2img/` | **Binary:** `~/bin/md2img`

### Project Structure

```
md2img/
├── cmd/md2img/       # CLI entry point (thin wrapper)
│   ├── main.go       # Flag parsing, calls RenderWithConfig
│   └── main_test.go  # CLI integration tests
├── render.go         # Pure Go canvas renderer: Config, Render(), RenderWithConfig()
├── fonts.go          # TTF font loader: findFirst(), system font paths, basicfont fallback
├── trim.go           # Auto-crop: scans NRGBA Pix buffer for content bounding box
├── render_test.go    # ~42 tests (render + config + HexToColor + trim)
├── bench_test.go     # Benchmarks (simple, table, complex, trimmed)
├── sanitize.go       # Unicode → ASCII replacement table
├── sanitize_test.go  # Sanitize tests
├── Makefile          # build / test / install
├── .github/workflows/
│   ├── ci.yml        # Build + test on macOS & Ubuntu (installs fonts-liberation)
│   ├── bench.yml     # Benchmarks + benchstat on macOS & Ubuntu
│   └── release.yml   # 6-platform binary builds on tag push
├── spikes/           # Experimental spikes (pure Go rendering prototype)
├── README.md
└── LICENSE (MIT)
```

Architecture: library package at root with exported `Render()` and `RenderWithConfig(cfg)`, CLI at `cmd/md2img/`.

### Tests & Benchmarks

```bash
cd ~/src/md2img
make test       # ~70 tests

# Benchmarks (tracks time, memory, allocations)
go test -bench=. -benchmem -count=3 ./...

# Coverage
go test -cover ./...    # 80.4% on core library
```

**Benchmark baseline (M4, DPI 200):**
| Document | Time | Memory |
|----------|------|--------|
| Simple (heading) | ~7.3ms | 64MB |
| Table | ~9.6ms | 65MB |
| Complex (all elements) | ~21ms | 73MB |
| Trimmed | ~24ms | 73MB |
| DPI 100 | ~8.5ms | 26MB |
| DPI 300 | ~36ms | 150MB |

The old pipeline (~370ms) was 99.7% Ghostscript. The pure Go renderer eliminated that bottleneck entirely.

### Benchmarks in CI

`.github/workflows/bench.yml` runs on push to main and PRs, on both macOS and Ubuntu. Uses `benchstat` to summarize.

## Visual Quality Guidelines

When iterating on the renderer's visual output, keep these principles (learned from user feedback):

- **Cell padding matters** — table cells need generous internal padding so text doesn't touch borders. Cramped cells look unpleasant.
- **Element spacing** — headings, paragraphs, tables, lists, and code blocks need clear vertical separation. Too little spacing makes the output feel dense and hard to scan.
- **Text-to-cell proportions** — font size relative to cell height/width needs to feel balanced. Tiny text in oversized cells or large text in tight cells both look wrong.
- **Code blocks need breathing room** — internal padding around code text, distinct background, proper line spacing.
- **Blockquotes** — left border + italic is good, but ensure the border is visible and spacing separates it from adjacent elements.
- **HR spacing** — horizontal rules need margin above and below to function as visual separators.

When in doubt, render and visually inspect. The vision_analyze tool can assess rendered output quality.

### Proven Default Values (v1.3+)

These defaults were tuned through multiple rounds of user feedback. Changing one value often requires adjusting others to maintain visual balance:

```
FontSize:         14pt     (body text — 11 was too small)
CodeFontSize:     11pt     (monospace — proportional to body)
TableCellHeight:  5mm      (was 10→7→5mm — cells were dwarfing text)
TableHeaderSize:  12pt     (slightly smaller than body, bold)
TableAutoWidth:   true     (columns fit content, not stretch to page)
CodeLineHeight:   6.5mm
CodeBlockPadding: 1.5mm    (tight but readable — 3mm was still too much ocean)
```

**Flag convention: default to the good behavior, negate with flag.**
When auto-width tables proved better than full-width, the default was flipped and the old behavior became `-table-full-width` (opt-in). This pattern — "good behavior is default, flag opts out" — is preferred over "bad behavior is default, flag opts in".

**Line spacing values (in pixels, added after faceHeight):**
```
Paragraph:      lh + 12   (was +6 — too cramped)
List items:     lh + 6    (was +3)
List trailing:  10px      (was 8px)
Heading after:  lh/2 + 16 (was +10)
Blockquote:     faceHeight + 12 (was +4 — no separation from next element)
Code block:     padding + 12   (was +6)
HR:             +12 above, +16 below
Table trailing: 14px
```

**Key relationships:**
- `TableCellHeight` must be proportional to `FontSize` — if you bump font, reduce cell height or it looks like empty boxes with tiny text
- `CodeFontSize` should be ~75-80% of `FontSize` for visual hierarchy
- `TableHeaderSize` should be between body and heading sizes
- Line spacing of +10-12px after body text gives comfortable reading rhythm

### Pitfall: MarginTop Must Be Applied to Initial Canvas Position

The `Config` struct has `MarginTop` but the original `newCanvas()` only set `c.margin = mmToPx(cfg.MarginLeft, dpi)` and left `c.y = 0`. This means top margin was silently ignored — text started at the very top edge. Always ensure `c.y` is initialized to `mmToPx(cfg.MarginTop, dpi)` in `newCanvas()`.

### Pitfall: Auto-Crop Must Preserve Symmetric Margins

The trim logic scans for the leftmost and rightmost non-white pixels. If you crop to `Rect(0, 0, right+1, h)`, the left margin survives by accident (crop starts at x=0) but the right margin is cut off. Fix: set the right crop edge to `right + 1 + left` so right padding equals left padding. This ensures symmetric margins in trimmed output.

## Pitfalls (Debugging Notes)

### 0. EAT YOUR OWN DOG FOOD — always render tables as images in chat

When presenting tabular data in Matrix/Slack, **always** render it with md2img and send via `MEDIA:`. Do NOT paste markdown tables as text — they won't render as tables in chat. The user built this tool specifically for this purpose.

### 1. Matrix doesn't render HTML tables

`<table>` is NOT in the Matrix spec — no client renders it. Alternatives: code fences (monospace, readable), or md2img images (graphical). Same applies to Slack.

### 2. TableHeader → TableCell directly (no TableRow wrapper)

Goldmark's GFM table AST: `TableHeader → TableCell` directly, NOT `TableHeader → TableRow → TableCell`.

### 3. Code blocks have no child Text nodes

`FencedCodeBlock`/`CodeBlock` store text in `Lines()` segments, not child nodes. Use type assertion + `Lines().At(i).Value(src)`.

### 4. Font fallback on CI/Ubuntu

Ubuntu doesn't have macOS system fonts. CI workflow installs `fonts-liberation` package. If tests fail with tiny PNGs on Linux, check if TTF fonts are available or if it fell back to `basicfont` (bitmap, much smaller output).

### 5. Cross-machine build produces different output

Check for uncommitted local changes (debug code, AST dumps). Always `git diff` before claiming "same code."

### 6. drawString MUST advance c.x (inline formatting bug)

`drawString` uses a local `font.Drawer`. After `d.DrawString(s)`, the cursor advances in `d.Dot.X` but NOT in `c.x`. If you forget to extract it (`c.x = int(d.Dot.X >> 6)`), every subsequent inline element (bold, italic, code) draws on top of the previous one at the same position. This was the root cause of "bold/italic not rendering" — they were all drawn at the same x coordinate.

**Code block lines must also reset c.x.** When `drawString` advances `c.x`, the code block rendering loop (which draws multiple lines) must reset `c.x = c.margin + padding` before each line, otherwise each line starts where the previous one ended.

### 7. Inline baseline alignment — use drawStringAt, not drawString

Different font families (Arial, Courier, etc.) have different internal metrics even at the same point size. If you use each font's own `faceHeight` for y-positioning, inline code will float above/below the surrounding text baseline.

**Fix:** Use `drawStringAt(s, face, col, yOff)` where `yOff = baseH - faceHeight(face)`. The base face height is computed once from the paragraph's regular face, and every inline element (bold, italic, code) gets offset so they all sit on the same baseline. The `renderInline` and `renderInlineWithOffset` functions implement this.

**Inline code uses body FontSize, not CodeFontSize.** Code blocks use `CodeFontSize` (11pt) for compact display, but inline code spans use `FontSize` (14pt) in Courier — same size as surrounding text, just monospace. This prevents the "superscript" look.

### 8. TableAutoWidth defaults to true

Columns auto-fit to content by default. Use `-table-full-width` to opt into the old stretch-across-page behavior. When implementing auto-width: measure max text width per column with `measure(face, text)`, add cell padding (12px per side), and if total exceeds page width, scale proportionally.

## When to Use

- Sharing formatted tables/code on Matrix (which doesn't render HTML tables)
- Quick visual docs for chat
- Conference schedule summaries
- Comparison tables
- **AI agent output** — chat platforms (Matrix, Slack) don't render `<table>` HTML. When an agent needs to present structured data in conversation, md2img renders it as an image that sends natively via `MEDIA:`
