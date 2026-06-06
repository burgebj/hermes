# md2img CLI Flags Reference

Input is a **positional arg** (not a flag). Output uses `-o`. Stdin is used when no positional arg is given.

## Output
| Flag | Description | Default |
|------|-------------|---------|
| `-o`, `--output` | Output file path | `/tmp/md2img_output.png` |
| `-trim`, `--trim` | Auto-crop whitespace from PNG output | `false` |
| `-trim-padding`, `--trim-padding` | Padding around content after trim (mm) | `5` |
| `-dpi`, `--dpi` | PNG resolution (DPI) | `200` |
| `-version`, `--version` | Print version | — |

## Font
| Flag | Description | Default |
|------|-------------|---------|
| `-font`, `--font` | Body font (loads system TTF: Arial, Helvetica, Times, Courier) | `Helvetica` |
| `-font-size`, `--font-size` | Body font size (points) | `14` |
| `-heading-font`, `--heading-font` | Heading font (empty = same as body) | (same as body) |

## Page Layout
| Flag | Description | Default |
|------|-------------|---------|
| `-page-w`, `--page-w` | Page width in mm | `210` (A4) |
| `-page-h`, `--page-h` | Page height in mm | `297` (A4) |
| `-margin`, `--margin` | All margins in mm | `15` |

## Colors (accept hex: `#333366`, `333366`, `#fff`)
| Flag | Description | Default |
|------|-------------|---------|
| `-text-color` | Body text color | `#282828` |
| `-heading-color` | Heading text color | `#282850` |
| `-table-header-bg` | Table header background | `#323250` |
| `-table-header-fg` | Table header text color | `#C8C8FF` |
| `-table-header-font` | Table header font | (same as body) |
| `-table-header-size` | Table header font size | `12` |
| `-table-full-width` | Stretch tables across full page width (default: auto-width, columns fit content) | `false` |
| `-table-row-even` | Even row background | `#F5F5FA` |
| `-table-row-odd` | Odd row background | `#FFFFFF` |
| `-code-bg` | Code block background | `#F0F0F0` |
| `-code-font` | Code font | `Courier` |
| `-code-font-size` | Code font size | `11` |
| `-blockquote-line-color` | Blockquote left border | `#6464C8` |
| `-blockquote-text-color` | Blockquote text color | `#646464` |
| `-hr-color` | Horizontal rule color | `#B4B4B4` |

## Examples

```bash
# Render from file
md2img -o output.png input.md

# Dark theme table
echo "| Name | Score |" | md2img -o dark.png \
  -text-color "#E2E8F0" \
  -table-header-bg "#2D3748" \
  -table-header-fg "#E2E8F0"

# US Letter, high resolution
md2img -o report.png -page-w 215.9 -page-h 279.4 -dpi 300 report.md

# Trim whitespace (tight crop)
echo "| A | B |" | md2img -o tight.png -trim -trim-padding 2

# Force full-width table (overrides default auto-width)
md2img -o wide.png -table-full-width input.md
```
