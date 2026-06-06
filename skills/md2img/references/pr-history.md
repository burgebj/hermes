# md2img PR History

## PR #2 — feat: pure Go rendering engine (MERGED)
**Branch:** `feat/pure-go-rendering` → `main`
**Date:** 2026-05-07

### Changes
- Replaced Ghostscript pipeline with pure Go canvas renderer
- Removed `-pdf` flag (no longer needed)
- Added `-table-full-width` flag (auto-width is now default)
- Added inline formatting: bold, italic, code spans via `renderInline()`
- Added `drawStringAt()` with baseline offset for cross-font alignment
- Fixed auto-crop symmetric margins
- Updated defaults: FontSize 11→14, TableCellHeight 10→5mm, CodeBlockPadding 4→1.5mm
- 70 tests, 80.4% coverage, all CI green (macOS + Ubuntu)

### Key Commits
```
f455835 docs: update README and benchmarks for new features
b601dbe feat: inline formatting, auto-width tables, visual polish
4f316e6 fix: improve visual design and CI font support
9e7827c test: add complex all-elements render tests
6b7919a feat: replace Ghostscript pipeline with pure Go rendering
```
