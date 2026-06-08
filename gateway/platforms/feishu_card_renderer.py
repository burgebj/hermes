"""Feishu Card JSON 2.0 renderer for final assistant replies.

Converts a platform-neutral ``MessageDocument`` into a Feishu Card JSON 2.0 dict
suitable for ``msg_type=interactive``. This module is purely functional — it
produces card dictionaries and has no transport dependency on ``FeishuAdapter``
or the lark SDK.
"""

from __future__ import annotations

import re
from typing import Any

from gateway.rendering.document import (
    CodeBlock,
    DividerBlock,
    HeadingBlock,
    MessageDocument,
    ParagraphBlock,
    TableBlock,
)

_PLAINTEXT_SUMMARY_MAX_LENGTH = 80
_FIXED_CARD_TITLE = "Hermes"
_UNDESIRED_SUMMARY_CHARS_RE = re.compile(r"[`*_~\[\]!#>"">]")


def render_document_to_feishu_card_v2(
    doc: MessageDocument,
    *,
    title: str = _FIXED_CARD_TITLE,
    table_policy: str = "table",
    table_cell_type: str = "markdown",
    max_tables: int = 5,
    max_columns: int = 8,
    max_rows: int = 20,
) -> dict[str, Any]:
    """Convert a ``MessageDocument`` into a Feishu Card JSON 2.0 dict."""
    elements: list[Any] = []
    table_count = 0

    for block in doc.blocks:
        if isinstance(block, ParagraphBlock):
            elements.append(
                {"tag": "markdown", "content": block.text, "text_size": "normal"}
            )
        elif isinstance(block, HeadingBlock):
            elements.append(
                {"tag": "markdown", "content": block.text, "text_size": "heading"}
            )
        elif isinstance(block, CodeBlock):
            content = _render_code_block_content(block)
            elements.append(
                {"tag": "markdown", "content": content, "text_size": "normal"}
            )
        elif isinstance(block, DividerBlock):
            elements.append({"tag": "hr"})
        elif isinstance(block, TableBlock):
            use_table = (
                table_policy == "table"
                and table_count < max_tables
                and len(block.headers) <= max_columns
                and len(block.rows) <= max_rows
                and bool(block.headers)
                and bool(block.rows)
            )
            if use_table:
                elements.append(_build_table_element(block, table_cell_type, len(block.rows)))
                table_count += 1
            else:
                content = _render_code_block_content_from_raw(
                    language="markdown", code=block.raw_markdown or _table_to_markdown(block)
                )
                elements.append(
                    {"tag": "markdown", "content": content, "text_size": "normal"}
                )
        # Unknown block types are silently ignored.

    summary = _build_summary(doc.blocks)

    return {
        "schema": "2.0",
        "config": {
            "update_multi": True,
            "width_mode": "fill",
            "summary": {"content": summary},
        },
        "header": {
            "title": {"tag": "plain_text", "content": title},
            "template": "blue",
        },
        "body": {
            "direction": "vertical",
            "padding": "12px 8px 12px 8px",
            "elements": elements,
        },
    }


def build_feishu_card_v2_payload(text: str, *, table_policy: str = "table") -> str:
    import json

    from gateway.rendering.markdown_parser import parse_markdown_document

    return json.dumps(
        render_document_to_feishu_card_v2(
            parse_markdown_document(text), table_policy=table_policy
        ),
        ensure_ascii=False,
    )


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


def _build_summary(blocks: list[Any]) -> str:
    for block in blocks:
        if isinstance(block, ParagraphBlock):
            return _strip_inline_markdown(block.text)[:_PLAINTEXT_SUMMARY_MAX_LENGTH]
    for block in blocks:
        if isinstance(block, HeadingBlock):
            return _strip_inline_markdown(block.text)[:_PLAINTEXT_SUMMARY_MAX_LENGTH]
    return ""


def _strip_inline_markdown(text: str) -> str:
    """Best-effort inline Markdown removal for notification summaries."""
    return _UNDESIRED_SUMMARY_CHARS_RE.sub("", text).strip()


def _render_code_block_content(block: CodeBlock) -> str:
    code = block.code.replace("\r\n", "\n").rstrip("\n")
    return f"```{block.language}\n{code}\n```"


def _render_code_block_content_from_raw(*, language: str, code: str) -> str:
    normalized = code.replace("\r\n", "\n").rstrip("\n")
    return f"```{language}\n{normalized}\n```"


def _build_table_element(data: TableBlock, cell_type: str, row_count: int) -> dict[str, Any]:
    return {
        "tag": "table",
        "page_size": min(row_count, 10),
        "row_height": "auto",
        "row_max_height": "124px",
        "freeze_first_column": len(data.headers) > 2,
        "header_style": {
            "text_align": "left",
            "text_size": "normal",
            "background_style": "none",
            "text_color": "grey",
            "bold": True,
            "lines": 1,
        },
        "columns": [
            {"name": f"col_{i}", "display_name": header, "data_type": cell_type}
            for i, header in enumerate(data.headers)
        ],
        "rows": [
            {f"col_{i}": cell for i, cell in enumerate(padded_row)}
            for padded_row in (
                _fit_row(row, len(data.headers)) for row in data.rows
            )
        ],
    }


def _table_to_markdown(data: TableBlock) -> str:
    lines = ["| " + " | ".join(data.headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in data.headers) + " |")
    for row in data.rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _fit_row(row: list[str], width: int) -> list[str]:
    fitted = list(row)[:width]
    if len(fitted) < width:
        fitted.extend("" for _ in range(width - len(fitted)))
    return fitted