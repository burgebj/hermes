"""Tests for Feishu markdown table rendering.

Issue #26658: Feishu natively supports tables in post format, so the
_MARKDOWN_TABLE_RE workaround that forced table content to plain text
has been removed. Table content should now flow through the normal
markdown post pipeline and render as native Feishu tables.

Coverage:
- _MARKDOWN_HINT_RE detects table syntax (lines starting with |)
- _build_markdown_post_payload produces valid post payloads for tables
- _build_outbound_payload routes tables to "post" type (not "text")
- Edge cases: alignment rows, empty cells, inline code in tables,
  mixed table+prose, table+code block combinations
"""

import json
import unittest

from gateway.platforms.feishu import (
    _build_markdown_post_payload,
    _MARKDOWN_HINT_RE,
)


# --- Route detection tests (_MARKDOWN_HINT_RE) ------------------------------

class TestMarkdownHintReDetectsTables(unittest.TestCase):
    """_MARKDOWN_HINT_RE must detect table syntax so tables route to post type."""

    def test_simple_markdown_table_detected(self):
        content = "| Name  | Age |\n|------|-----|\n| Alice | 30 |"
        match = _MARKDOWN_HINT_RE.search(content)
        self.assertIsNotNone(match)

    def test_table_with_alignment_row_detected(self):
        content = "| Left | Center | Right |\n|:-----|:------:|------:|\n| L1   | C1    | R1    |"
        match = _MARKDOWN_HINT_RE.search(content)
        self.assertIsNotNone(match)

    def test_inline_code_in_table_detected(self):
        content = "| Command | Description |\n|---------|-------------|\n| `ls`   | list files  |"
        match = _MARKDOWN_HINT_RE.search(content)
        self.assertIsNotNone(match)

    def test_table_with_empty_cells_detected(self):
        content = "| A | B |\n|---|---|\n| 1 |   |"
        match = _MARKDOWN_HINT_RE.search(content)
        self.assertIsNotNone(match)

    def test_table_with_special_chars_detected(self):
        content = "| Name | Note |\n|-----|------|\n| Bob | **bold** |"
        match = _MARKDOWN_HINT_RE.search(content)
        self.assertIsNotNone(match)

    def test_multiline_table_detected(self):
        rows = ["| Col1 | Col2 |", "|------|------|"] + \
               [f"| R{i}A | R{i}B |" for i in range(1, 21)]
        content = "\n".join(rows)
        match = _MARKDOWN_HINT_RE.search(content)
        self.assertIsNotNone(match)

    def test_table_with_leading_whitespace_detected(self):
        content = "\n| Name  | Value |\n|-------|-------|\n| Alpha | 1     |"
        match = _MARKDOWN_HINT_RE.search(content)
        self.assertIsNotNone(match)

    def test_table_followed_by_prose_detected(self):
        content = "Here is the report:\n\n| Item  | Qty |\n|-------|-----|\n| Apple | 10  |"
        match = _MARKDOWN_HINT_RE.search(content)
        self.assertIsNotNone(match)

    def test_heading_before_table_detected(self):
        content = "## Report\n\n| Item | Count |\n|------|-------|\n| Apples | 3 |"
        match = _MARKDOWN_HINT_RE.search(content)
        self.assertIsNotNone(match)

    def test_plain_text_not_detected_as_markdown(self):
        content = "Hello, this is plain text without any markdown formatting."
        match = _MARKDOWN_HINT_RE.search(content)
        self.assertIsNone(match)

    def test_no_false_positive_on_word_with_pipe(self):
        """A single word with a pipe (e.g., '|foo|') should not trigger table detection."""
        content = "Use the |foo| operator to filter results."
        match = _MARKDOWN_HINT_RE.search(content)
        self.assertIsNone(match)


# --- Payload structure tests -------------------------------------------------

class TestTablePayloadStructure(unittest.TestCase):
    """_build_markdown_post_payload must produce valid post payloads for tables."""

    def test_table_only_produces_post_payload(self):
        content = "| Col1 | Col2 |\n|------|------|\n| A    | B    |"
        payload_str = _build_markdown_post_payload(content)
        payload = json.loads(payload_str)
        self.assertIn("zh_cn", payload)
        self.assertIn("content", payload["zh_cn"])
        rows = payload["zh_cn"]["content"]
        self.assertIsInstance(rows, list)
        self.assertGreater(len(rows), 0)

    def test_table_payload_text_contains_table_content(self):
        content = "| A | B |\n|---|---|\n| 1 | 2 |"
        payload_str = _build_markdown_post_payload(content)
        payload = json.loads(payload_str)
        # Collect all text from md tag cells
        all_text = ""
        for row in payload["zh_cn"]["content"]:
            for cell in row:
                if isinstance(cell, dict) and cell.get("tag") == "md":
                    all_text += cell.get("text", "")
        self.assertIn("| A | B |", all_text)
        self.assertIn("| 1 | 2 |", all_text)

    def test_table_with_heading_includes_both(self):
        content = "## Report\n\n| Item | Count |\n|------|-------|\n| Apples | 3 |"
        payload_str = _build_markdown_post_payload(content)
        payload = json.loads(payload_str)
        all_text = ""
        for row in payload["zh_cn"]["content"]:
            for cell in row:
                if isinstance(cell, dict) and cell.get("tag") == "md":
                    all_text += cell.get("text", "")
        self.assertIn("## Report", all_text)
        self.assertIn("Apples", all_text)

    def test_empty_table_still_produces_valid_payload(self):
        content = "| A | B |\n|---|---|\n|   |   |"
        payload_str = _build_markdown_post_payload(content)
        payload = json.loads(payload_str)
        self.assertIn("zh_cn", payload)

    def test_table_with_special_chars_in_cells(self):
        content = "| Name | Note |\n|-----|------|\n| Alice | [test] |"
        payload_str = _build_markdown_post_payload(content)
        payload = json.loads(payload_str)
        all_text = ""
        for row in payload["zh_cn"]["content"]:
            for cell in row:
                if isinstance(cell, dict) and cell.get("tag") == "md":
                    all_text += cell.get("text", "")
        self.assertIn("Alice", all_text)


# --- End-to-end routing tests -----------------------------------------------

class TestTableRoutingEndToEnd(unittest.TestCase):
    """_build_outbound_payload must route tables to 'post', not 'text'."""

    def _outbound(self, content: str) -> tuple[str, str]:
        """Return (msg_type, payload_str) by calling the instance method."""
        from unittest.mock import MagicMock, patch
        import gateway.platforms.feishu

        # Patch FeishuAdapter.__init__ to avoid triggering lark_oapi SDK initialization
        original_init = gateway.platforms.feishu.FeishuAdapter.__init__
        patch_init = patch.object(
            gateway.platforms.feishu.FeishuAdapter,
            "__init__",
            lambda self, *args, **kwargs: None,
        )
        with patch_init:
            from gateway.platforms.feishu import FeishuAdapter

            adapter = FeishuAdapter()
            adapter._lark_client = MagicMock()
            adapter._bot_info = {}
            adapter._tenant_access_token = "mock_token"
            msg_type, payload_str = adapter._build_outbound_payload(content)
            return msg_type, payload_str

    def test_simple_table_routes_to_post(self):
        content = "| Name  | Age |\n|------|-----|\n| Alice | 30 |\n| Bob   | 25 |"
        msg_type, _ = self._outbound(content)
        self.assertEqual(msg_type, "post")

    def test_table_with_prose_routes_to_post(self):
        content = "Here is the report:\n\n| Item  | Qty |\n|-------|-----|\n| Apple | 10  |"
        msg_type, _ = self._outbound(content)
        self.assertEqual(msg_type, "post")

    def test_table_only_post_payload_structure(self):
        content = "| Col1 | Col2 |\n|------|------|\n| A    | B    |"
        msg_type, payload_str = self._outbound(content)
        self.assertEqual(msg_type, "post")
        payload = json.loads(payload_str)
        self.assertIn("zh_cn", payload)

    def test_table_with_alignment_row_routes_to_post(self):
        content = "| Left | Center | Right |\n|:-----|:------:|------:|\n| L1   | C1    | R1    |"
        msg_type, _ = self._outbound(content)
        self.assertEqual(msg_type, "post")

    def test_inline_code_in_table_routes_to_post(self):
        content = "| Command | Description |\n|---------|-------------|\n| `ls`   | list files  |"
        msg_type, _ = self._outbound(content)
        self.assertEqual(msg_type, "post")

    def test_table_with_empty_cells_routes_to_post(self):
        content = "| A | B | C |\n|---|---|---|\n| 1 |   | 3 |"
        msg_type, _ = self._outbound(content)
        self.assertEqual(msg_type, "post")

    def test_table_with_special_chars_routes_to_post(self):
        content = "| Name | Note |\n|-----|------|\n| Alice | [test] |"
        msg_type, _ = self._outbound(content)
        self.assertEqual(msg_type, "post")

    def test_table_with_leading_whitespace_routes_to_post(self):
        content = "\n| Name  | Value |\n|-------|-------|\n| Alpha | 1     |"
        msg_type, _ = self._outbound(content)
        self.assertEqual(msg_type, "post")

    def test_table_followed_by_code_block_routes_to_post(self):
        content = "| A | B |\n|---|---|\n| 1 | 2 |\n\n```\necho hello\n```"
        msg_type, _ = self._outbound(content)
        self.assertEqual(msg_type, "post")

    def test_code_block_before_table_routes_to_post(self):
        content = "```\ndef foo():\n    pass\n```\n| X | Y |\n|---|---|\n| 1 | 2 |"
        msg_type, _ = self._outbound(content)
        self.assertEqual(msg_type, "post")

    def test_plain_text_without_table_routes_to_text(self):
        content = "Hello, this is plain text without any markdown formatting."
        msg_type, _ = self._outbound(content)
        self.assertEqual(msg_type, "text")

    def test_other_markdown_without_table_routes_to_post(self):
        content = "# Heading\n\n- bullet 1\n- bullet 2\n\n**bold text**"
        msg_type, _ = self._outbound(content)
        self.assertEqual(msg_type, "post")

    def test_no_false_positive_pipe_in_sentence(self):
        """A sentence with a pipe character should NOT route to post."""
        content = "Use the |foo| operator to filter results."
        msg_type, _ = self._outbound(content)
        self.assertEqual(msg_type, "text")


if __name__ == "__main__":
    unittest.main()
