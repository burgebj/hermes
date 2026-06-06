# Goldmark AST Reference

## Table Node Structure

Goldmark's GFM table AST (with `extension.GFM`):

```
Table
├── TableHeader
│   ├── TableCell (no TableRow wrapper!)
│   ├── TableCell
│   └── TableCell
├── TableRow
│   ├── TableCell
│   ├── TableCell
│   └── TableCell
└── TableRow
    └── ...
```

**Key insight:** `TableHeader` has `TableCell` children directly. There is NO `TableRow` wrapper inside `TableHeader`. Code that iterates `TableHeader` children looking for `TableRow` will find nothing.

## Code Block Lines

`FencedCodeBlock` and `CodeBlock` do NOT have child `Text` nodes. Text is stored in `Lines()` segments:

```go
case *ast.FencedCodeBlock:
    for i := 0; i < block.Lines().Len(); i++ {
        seg := block.Lines().At(i)
        text := string(seg.Value(src))
    }
```

`extractText()` (which walks child nodes) will return empty for code blocks. Must handle them separately.

## Segment.Value(src) Requires Live Source

```go
seg.Value(src)  // panics if src is nil or garbage-collected
```

Store the original `[]byte` on a struct and pass it through the render lifecycle.

## Common Node Kinds

| Kind | AST Type | Notes |
|------|----------|-------|
| `Heading` | `*ast.Heading` | `.Level` = 1-6 |
| `Paragraph` | `*ast.Paragraph` | Children include inline formatting |
| `FencedCodeBlock` | `*ast.FencedCodeBlock` | `.Lines()` for text, `.Language(src)` for lang |
| `CodeBlock` | `*ast.CodeBlock` | Indented code blocks |
| `Table` | via extension | |
| `TableHeader` | via extension | Direct TableCell children |
| `TableRow` | via extension | Direct TableCell children |
| `TableCell` | via extension | |
| `List` | `*ast.List` | `.IsOrdered()` |
| `ListItem` | `*ast.ListItem` | |
| `Blockquote` | `*ast.Blockquote` | |
| `ThematicBreak` | `*ast.ThematicBreak` | `---` in markdown |
| `Text` | `*ast.Text` | Inline text, has `.Segment` |
| `String` | `*ast.String` | Has `.Value` directly |
| `Emphasis` | `*ast.Emphasis` | `.Level` = 1 (italic), 2 (bold), 3 (bold+italic) |
| `CodeSpan` | via extension | Inline code, use `extractText()` to get content |

## Parser Setup

```go
import (
    "github.com/yuin/goldmark"
    "github.com/yuin/goldmark/extension"
    "github.com/yuin/goldmark/text"
)

parser := goldmark.New(
    goldmark.WithExtensions(extension.GFM),
).Parser()

doc := parser.Parse(text.NewReader(srcBytes))
```

Note: `goldmark.Markdown` does NOT have a `DefaultParser()` method. Use `goldmark.New(...).Parser()` instead.

## Inline Formatting (Emphasis, CodeSpan)

Paragraphs contain inline formatting as child nodes. Walk children with a recursive `renderInline()` function:

```go
func (c *canvas) renderInline(n ast.Node, src []byte, baseFace font.Face, baseCol color.RGBA) {
    for child := n.FirstChild(); child != nil; child = child.NextSibling() {
        switch child.Kind().String() {
        case "Text":
            t := child.(*ast.Text)
            c.drawString(string(t.Segment.Value(src)), baseFace, baseCol)
        case "Emphasis":
            em := child.(*ast.Emphasis)
            face := baseFace
            if em.Level == 2 {
                // Bold — load bold TTF face
                face = loadFace(family.bold, cfg.FontSize)
            } else if em.Level == 1 {
                // Italic — use italic face
                face = c.fonts.italic
            }
            c.renderInline(child, src, face, baseCol) // recurse into children
        case "CodeSpan":
            code := extractText(child, src)
            c.drawString(code, c.fonts.code, cfg.TextColor.toRGBA())
        default:
            c.renderInline(child, src, baseFace, baseCol)
        }
    }
}
```

**Key:** `drawString` MUST advance `c.x` after drawing, or all inline segments overlap at the same position. Extract the cursor from `font.Drawer.Dot.X` after `DrawString()`.

**Baseline consistency:** When switching faces mid-line (regular → bold → italic), the vertical position (`c.y`) stays the same. Only the font face changes. This keeps text on a single baseline.
