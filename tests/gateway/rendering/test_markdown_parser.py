from gateway.rendering.document import (
    CodeBlock,
    DividerBlock,
    HeadingBlock,
    ParagraphBlock,
    TableBlock,
)
from gateway.rendering.markdown_parser import parse_markdown_document


def test_plain_paragraphs_parse_as_paragraph_blocks():
    doc = parse_markdown_document("First paragraph.\n\nSecond paragraph.")

    assert doc.blocks == [
        ParagraphBlock("First paragraph."),
        ParagraphBlock("Second paragraph."),
    ]


def test_headings_and_dividers_parse_as_structural_blocks():
    doc = parse_markdown_document("## Result\n\n---\n\nBody")

    assert doc.blocks == [
        HeadingBlock(level=2, text="Result"),
        DividerBlock(),
        ParagraphBlock("Body"),
    ]


def test_fenced_code_block_is_preserved_and_not_parsed_for_tables():
    text = "Before\n\n```md\n| A | B |\n|---|---|\n| 1 | 2 |\n```\n\nAfter"
    doc = parse_markdown_document(text)

    assert doc.blocks == [
        ParagraphBlock("Before"),
        CodeBlock(language="md", code="| A | B |\n|---|---|\n| 1 | 2 |"),
        ParagraphBlock("After"),
    ]


def test_markdown_table_parses_headers_rows_and_raw_markdown():
    table = "| 名称 | 状态 |\n| :--- | ---: |\n| A | **完成** |\n| B | [详情](https://example.com) |"
    doc = parse_markdown_document(f"Intro\n\n{table}\n\nOutro")

    assert doc.blocks == [
        ParagraphBlock("Intro"),
        TableBlock(
            headers=["名称", "状态"],
            rows=[["A", "**完成**"], ["B", "[详情](https://example.com)"]],
            raw_markdown=table,
        ),
        ParagraphBlock("Outro"),
    ]


def test_pipe_text_without_separator_is_paragraph():
    text = "This is A | B but not a table."
    doc = parse_markdown_document(text)

    assert doc.blocks == [ParagraphBlock(text)]
