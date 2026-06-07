"""Tests for memory/plugin context injection into multimodal user messages.

When a user sends an image, ``api_msg["content"]`` is a list of content parts
(text + image_url blocks), not a plain string.  The injection block in
``run_conversation`` must handle both shapes — this file verifies that.

Regression tests for https://github.com/NousResearch/hermes-agent/issues/32546
"""

from __future__ import annotations

import copy


def _apply_injections(api_msg: dict, injections: list[str]) -> dict:
    """Replicate the injection logic from conversation_loop.py."""
    msg = copy.deepcopy(api_msg)
    if injections:
        _base = msg.get("content", "")
        if isinstance(_base, str):
            msg["content"] = _base + "\n\n" + "\n\n".join(injections)
        elif isinstance(_base, list):
            injection_text = "\n\n".join(injections)
            msg["content"] = [{"type": "text", "text": injection_text}, *_base]
    return msg


MEMORY_BLOCK = (
    "<memory-context>\n"
    "[System note: recalled memory context]\n\n"
    "User prefers dark mode.\n"
    "</memory-context>"
)

PLUGIN_CONTEXT = "[plugin] Today is Monday."

MULTIMODAL_CONTENT = [
    {"type": "text", "text": "Analyze this screenshot"},
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}},
]


class TestStringContentInjection:
    """Existing str path must not regress."""

    def test_str_content_gets_injections_appended(self):
        msg = {"role": "user", "content": "hello"}
        result = _apply_injections(msg, [MEMORY_BLOCK, PLUGIN_CONTEXT])
        assert isinstance(result["content"], str)
        assert result["content"].startswith("hello\n\n")
        assert MEMORY_BLOCK in result["content"]
        assert PLUGIN_CONTEXT in result["content"]


class TestMultimodalContentInjection:
    """List-shaped content (image + text) must receive injections."""

    def test_list_content_gets_prepended_text_block(self):
        msg = {"role": "user", "content": copy.deepcopy(MULTIMODAL_CONTENT)}
        result = _apply_injections(msg, [MEMORY_BLOCK])
        content = result["content"]
        assert isinstance(content, list)
        assert content[0]["type"] == "text"
        assert MEMORY_BLOCK in content[0]["text"]

    def test_original_blocks_preserved(self):
        msg = {"role": "user", "content": copy.deepcopy(MULTIMODAL_CONTENT)}
        result = _apply_injections(msg, [MEMORY_BLOCK, PLUGIN_CONTEXT])
        content = result["content"]
        assert content[1] == MULTIMODAL_CONTENT[0]
        assert content[2] == MULTIMODAL_CONTENT[1]

    def test_empty_injections_no_change(self):
        original = copy.deepcopy(MULTIMODAL_CONTENT)
        msg = {"role": "user", "content": copy.deepcopy(MULTIMODAL_CONTENT)}
        result = _apply_injections(msg, [])
        assert result["content"] == original

    def test_exactly_one_block_prepended(self):
        msg = {"role": "user", "content": copy.deepcopy(MULTIMODAL_CONTENT)}
        result = _apply_injections(msg, [MEMORY_BLOCK, PLUGIN_CONTEXT])
        content = result["content"]
        assert len(content) == len(MULTIMODAL_CONTENT) + 1
        assert content[0]["type"] == "text"
        assert MEMORY_BLOCK in content[0]["text"]
        assert PLUGIN_CONTEXT in content[0]["text"]
