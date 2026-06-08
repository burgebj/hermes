"""Document text extraction for the read_file tool.

Ported/adapted from Kilo-Org/kilocode PRs #10733 (notebooks), #10737 (DOCX),
and #10740 (XLSX), which added structured-document reading to their CLI `read`
tool. Kilo bundled the `mammoth` JS library for DOCX; hermes-agent instead uses
a pure-stdlib approach (``json`` + ``zipfile`` + ``xml.etree``) so no new Python
dependency is added — ``.docx`` and ``.xlsx`` are both Zip+OOXML containers that
stdlib can unpack and parse.

The router (:func:`extract_document_text`) returns a plain-text rendering of the
document. The caller (``read_file_tool``) then routes that text through the
existing line-numbering, pagination, truncation, char-limit and redaction
pipeline — exactly as it does for a normal text file. That keeps a single set of
output semantics for every readable format.

Design constraints (from the hermes-agent-dev skill):
  * No new hard dependency. Everything here is stdlib.
  * Extraction reads local bytes directly (works regardless of terminal
    backend, since the file is resolved to a host path before we get here).
  * Malformed inputs degrade gracefully: callers fall back to raw-text reading
    so the file stays inspectable rather than throwing an opaque error.
"""

from __future__ import annotations

import json
import zipfile
from typing import Optional
from xml.etree import ElementTree as ET

__all__ = [
    "EXTRACTABLE_EXTENSIONS",
    "is_extractable_document",
    "extract_document_text",
    "ExtractionError",
]

# Extensions we can render to text in-process. Lowercase, leading dot.
EXTRACTABLE_EXTENSIONS = frozenset({".ipynb", ".docx", ".xlsx"})

# Workbook hard cap mirrors Kilo #10740 (reject >50 MB before parsing). Applied
# by the caller via file size; re-stated here as the documented contract.
MAX_XLSX_BYTES = 50 * 1024 * 1024

# Bound worksheet extraction so a pathological workbook can't blow up context
# before the read tool's own char-limit guard runs. Generous — the read tool
# truncates afterward anyway.
_MAX_XLSX_ROWS_PER_SHEET = 5000
_MAX_XLSX_COLS = 256

# OOXML namespaces.
_NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_NS_S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


class ExtractionError(Exception):
    """Raised when a document can't be extracted to text.

    The caller treats this as a signal to fall back to raw-text reading so the
    file remains inspectable (matching Kilo's malformed-notebook behavior).
    """


def is_extractable_document(path: str) -> bool:
    """True if ``path`` has an extension we can render to text."""
    lower = path.lower()
    return any(lower.endswith(ext) for ext in EXTRACTABLE_EXTENSIONS)


def _ext_of(path: str) -> str:
    lower = path.lower()
    for ext in EXTRACTABLE_EXTENSIONS:
        if lower.endswith(ext):
            return ext
    return ""


def extract_document_text(path: str) -> str:
    """Render a supported document to plain text.

    Args:
        path: Local filesystem path to a ``.ipynb`` / ``.docx`` / ``.xlsx`` file.

    Returns:
        Plain-text rendering suitable for line-numbered display.

    Raises:
        ExtractionError: if the file is malformed or can't be parsed. The caller
            should fall back to raw-text reading.
    """
    ext = _ext_of(path)
    if ext == ".ipynb":
        return _extract_notebook(path)
    if ext == ".docx":
        return _extract_docx(path)
    if ext == ".xlsx":
        return _extract_xlsx(path)
    raise ExtractionError(f"Unsupported document type: {ext or path!r}")


# ──────────────────────────────────────────────────────────────────────────
# Jupyter notebooks (.ipynb) — Kilo #10733
# ──────────────────────────────────────────────────────────────────────────

def _extract_notebook(path: str) -> str:
    """Extract markdown + code cell sources in document order.

    Raw ``.ipynb`` JSON drowns the model in metadata and output payloads
    (base64 images, execution counts, stream noise). We keep only the cell
    sources, labelled by type, so the agent sees the actual document.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            nb = json.load(fh)
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        raise ExtractionError(f"Not a valid notebook: {exc}") from exc

    if not isinstance(nb, dict):
        raise ExtractionError("Notebook root is not a JSON object")

    cells = nb.get("cells")
    if not isinstance(cells, list):
        # nbformat < 4 stored cells under worksheets[].cells.
        worksheets = nb.get("worksheets")
        if isinstance(worksheets, list) and worksheets:
            cells = []
            for ws in worksheets:
                if isinstance(ws, dict) and isinstance(ws.get("cells"), list):
                    cells.extend(ws["cells"])
        else:
            raise ExtractionError("Notebook has no cells array")

    parts: list[str] = []
    code_n = 0
    md_n = 0
    for idx, cell in enumerate(cells):
        if not isinstance(cell, dict):
            continue
        cell_type = cell.get("cell_type", "")
        source = _join_source(cell.get("source", ""))
        if cell_type == "markdown":
            md_n += 1
            parts.append(f"# ── Markdown cell {md_n} ──")
            parts.append(source.rstrip("\n"))
            parts.append("")
        elif cell_type == "code":
            code_n += 1
            parts.append(f"# ── Code cell {code_n} ──")
            parts.append(source.rstrip("\n"))
            parts.append("")
        elif cell_type == "raw":
            parts.append("# ── Raw cell ──")
            parts.append(source.rstrip("\n"))
            parts.append("")
        # Unknown cell types are skipped silently.

    if not parts:
        raise ExtractionError("Notebook contains no readable cells")

    text = "\n".join(parts).rstrip("\n") + "\n"
    return text


def _join_source(source) -> str:
    """Notebook ``source`` is either a string or a list of line strings."""
    if isinstance(source, list):
        return "".join(s for s in source if isinstance(s, str))
    if isinstance(source, str):
        return source
    return ""


# ──────────────────────────────────────────────────────────────────────────
# Word documents (.docx) — Kilo #10737 (stdlib instead of mammoth)
# ──────────────────────────────────────────────────────────────────────────

def _extract_docx(path: str) -> str:
    """Extract paragraph text from a DOCX in document order.

    A ``.docx`` is a Zip container; the body text lives in
    ``word/document.xml`` as ``<w:p>`` paragraphs containing ``<w:t>`` text
    runs. We walk paragraphs in order, join their runs, and emit one line per
    paragraph. ``<w:tab>`` becomes a tab and ``<w:br>``/``<w:cr>`` become
    newlines so basic layout survives.
    """
    try:
        with zipfile.ZipFile(path) as zf:
            try:
                xml_bytes = zf.read("word/document.xml")
            except KeyError as exc:
                raise ExtractionError("DOCX missing word/document.xml") from exc
    except (zipfile.BadZipFile, OSError) as exc:
        raise ExtractionError(f"Not a valid DOCX (zip) file: {exc}") from exc

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ExtractionError(f"DOCX document.xml is malformed: {exc}") from exc

    w = "{%s}" % _NS_W
    lines: list[str] = []

    # Iterate paragraphs in document order. Nested paragraphs (e.g. inside
    # tables) are flattened, which is acceptable for text extraction.
    for para in root.iter(f"{w}p"):
        buf: list[str] = []
        for node in para.iter():
            tag = node.tag
            if tag == f"{w}t":
                buf.append(node.text or "")
            elif tag == f"{w}tab":
                buf.append("\t")
            elif tag in (f"{w}br", f"{w}cr"):
                buf.append("\n")
        para_text = "".join(buf)
        # A paragraph may itself contain explicit line breaks.
        lines.extend(para_text.split("\n"))

    if not any(line.strip() for line in lines):
        raise ExtractionError("DOCX contains no extractable text")

    return "\n".join(lines).rstrip("\n") + "\n"


# ──────────────────────────────────────────────────────────────────────────
# Excel workbooks (.xlsx) — Kilo #10740 (stdlib instead of a parser lib)
# ──────────────────────────────────────────────────────────────────────────

def _extract_xlsx(path: str) -> str:
    """Extract visible worksheets as labelled tab-separated text.

    An ``.xlsx`` is a Zip of OOXML parts:
      * ``xl/workbook.xml``         — sheet names + visibility + rId mapping
      * ``xl/_rels/workbook.xml.rels`` — rId → worksheet part path
      * ``xl/sharedStrings.xml``    — interned string table
      * ``xl/worksheets/sheetN.xml``— cell data (values reference shared strings)

    Hidden sheets are omitted. Cells are rendered as their formatted value;
    string cells dereference the shared-string table. Rows/cols are bounded.
    """
    try:
        zf = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as exc:
        raise ExtractionError(f"Not a valid XLSX (zip) file: {exc}") from exc

    with zf:
        names = set(zf.namelist())
        if "xl/workbook.xml" not in names:
            raise ExtractionError("XLSX missing xl/workbook.xml")

        shared = _read_shared_strings(zf, names)
        sheets = _read_workbook_sheets(zf)
        rels = _read_workbook_rels(zf, names)

        out: list[str] = []
        for sheet in sheets:
            if sheet["state"] in ("hidden", "veryHidden"):
                continue
            target = rels.get(sheet["rid"])
            if not target:
                # Fallback: positional guess (xl/worksheets/sheetN.xml).
                continue
            part = _normalize_sheet_target(target)
            if part not in names:
                continue
            try:
                rows = _read_sheet_rows(zf.read(part), shared)
            except ET.ParseError:
                continue
            out.append(f"# ── Sheet: {sheet['name']} ──")
            if rows:
                out.extend("\t".join(r) for r in rows)
            else:
                out.append("(empty)")
            out.append("")

        if not out:
            raise ExtractionError("XLSX has no visible sheets with content")

        return "\n".join(out).rstrip("\n") + "\n"


def _read_shared_strings(zf: zipfile.ZipFile, names: set) -> list:
    if "xl/sharedStrings.xml" not in names:
        return []
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except ET.ParseError:
        return []
    s = "{%s}" % _NS_S
    result: list[str] = []
    for si in root.iter(f"{s}si"):
        # A shared string item is either a single <t> or rich-text runs <r><t>.
        texts = [t.text or "" for t in si.iter(f"{s}t")]
        result.append("".join(texts))
    return result


def _read_workbook_sheets(zf: zipfile.ZipFile) -> list:
    root = ET.fromstring(zf.read("xl/workbook.xml"))
    s = "{%s}" % _NS_S
    r = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    sheets = []
    for sheet in root.iter(f"{s}sheet"):
        sheets.append({
            "name": sheet.get("name", "Sheet"),
            "state": sheet.get("state", "visible"),
            "rid": sheet.get(f"{r}id", ""),
        })
    return sheets


def _read_workbook_rels(zf: zipfile.ZipFile, names: set) -> dict:
    rels_path = "xl/_rels/workbook.xml.rels"
    if rels_path not in names:
        return {}
    try:
        root = ET.fromstring(zf.read(rels_path))
    except ET.ParseError:
        return {}
    pr = "{http://schemas.openxmlformats.org/package/2006/relationships}"
    mapping = {}
    for rel in root.iter(f"{pr}Relationship"):
        rid = rel.get("Id", "")
        target = rel.get("Target", "")
        if rid and target:
            mapping[rid] = target
    return mapping


def _normalize_sheet_target(target: str) -> str:
    """Workbook rels target is relative to ``xl/`` (e.g. ``worksheets/sheet1.xml``)."""
    target = target.lstrip("/")
    if target.startswith("xl/"):
        return target
    return "xl/" + target


def _col_index(cell_ref: str) -> int:
    """Convert an A1-style cell ref's column letters to a 0-based index."""
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch.upper()) - ord("A") + 1)
    return idx - 1 if idx > 0 else 0


def _read_sheet_rows(xml_bytes: bytes, shared: list) -> list:
    root = ET.fromstring(xml_bytes)
    s = "{%s}" % _NS_S
    rows_out: list[list[str]] = []
    row_count = 0
    for row in root.iter(f"{s}row"):
        if row_count >= _MAX_XLSX_ROWS_PER_SHEET:
            break
        row_count += 1
        cells: dict[int, str] = {}
        max_col = -1
        for c in row.iter(f"{s}c"):
            ref = c.get("r", "")
            col = _col_index(ref) if ref else (max_col + 1)
            if col >= _MAX_XLSX_COLS:
                continue
            value = _cell_value(c, shared, s)
            cells[col] = value
            if col > max_col:
                max_col = col
        if max_col < 0:
            rows_out.append([])
            continue
        rows_out.append([cells.get(i, "") for i in range(max_col + 1)])
    # Trim trailing fully-empty rows.
    while rows_out and not any(cell.strip() for cell in rows_out[-1]):
        rows_out.pop()
    return rows_out


def _cell_value(c, shared: list, s: str) -> str:
    cell_type = c.get("t", "")
    v = c.find(f"{s}v")
    if cell_type == "s":
        # Shared-string index.
        if v is not None and v.text is not None:
            try:
                idx = int(v.text)
                if 0 <= idx < len(shared):
                    return shared[idx]
            except ValueError:
                pass
        return ""
    if cell_type == "inlineStr":
        is_node = c.find(f"{s}is")
        if is_node is not None:
            return "".join(t.text or "" for t in is_node.iter(f"{s}t"))
        return ""
    if cell_type == "str":
        # Formula result string.
        return v.text if (v is not None and v.text is not None) else ""
    if cell_type == "b":
        if v is not None and v.text is not None:
            return "TRUE" if v.text.strip() in ("1", "true", "TRUE") else "FALSE"
        return ""
    if cell_type == "e":
        # Error value (e.g. #DIV/0!).
        return v.text if (v is not None and v.text is not None) else "#ERROR"
    # Numeric / general.
    if v is not None and v.text is not None:
        return v.text
    return ""
