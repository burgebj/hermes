"""Verify the `response.completed` SSE payload is bounded under CPython's
`http.client._MAXLINE` SSE-line ceiling (128 KB; not configurable).

Regression test for #18021 — long agent sessions with many tool calls and
large outputs were producing terminal `response.completed` events that
exceeded 128 KB on the wire, breaking Open WebUI and any other client
that reads the SSE stream via Python's stdlib HTTP client.
"""

from __future__ import annotations

import json

from gateway.platforms.api_server import (
    _RESPONSE_COMPLETED_SAFE_BYTES,
    _trim_response_completed_items,
    _trim_response_completed_payload,
)


def _huge_function_call(name: str, arg_size: int = 50_000) -> dict:
    """Build a single function_call item whose serialised arguments alone
    exceed `arg_size` bytes — far past the 128 KB SSE line limit when
    repeated."""
    return {
        "id": f"call_{name}",
        "type": "function_call",
        "name": name,
        "arguments": json.dumps({
            "content": "x" * arg_size,
            "query": "y" * arg_size,
            "extra": "z" * arg_size,  # not in the old hardcoded trim list
        }),
    }


def _huge_function_output(call_id: str, text_size: int = 50_000) -> dict:
    return {
        "id": f"out_{call_id}",
        "type": "function_call_output",
        "call_id": call_id,
        "output": [
            {"type": "input_text", "text": "a" * text_size},
            {"type": "input_text", "text": "b" * text_size},
            {"type": "input_text", "text": "c" * text_size},
        ],
    }


def test_safe_threshold_is_below_maxline():
    """Sanity: the soft cap leaves room for SSE envelope below 128 KB."""
    import http.client

    maxline_ceiling = getattr(http.client, "_MAXLINE", 65536) * 2
    # Keep at least 20 KB headroom for envelope fields (response id, usage,
    # event prefix, etc.).
    assert _RESPONSE_COMPLETED_SAFE_BYTES + 20_000 <= maxline_ceiling


def test_huge_payload_trimmed_below_safe_limit():
    """A payload built to be ~600 KB before trimming must come back under
    `_RESPONSE_COMPLETED_SAFE_BYTES` after trimming."""
    items = [
        _huge_function_call("read_file"),
        _huge_function_output("read_file"),
        _huge_function_call("web_extract"),
        _huge_function_output("web_extract"),
        {"type": "message", "role": "assistant",
         "content": [{"type": "output_text", "text": "summary"}]},
    ]
    raw_size = len(json.dumps(items))
    assert raw_size > 200_000, f"test setup too small ({raw_size} bytes)"

    _trim_response_completed_payload(items)
    trimmed_size = len(json.dumps(items))
    assert trimmed_size <= _RESPONSE_COMPLETED_SAFE_BYTES, (
        f"after trimming, payload is still {trimmed_size} bytes "
        f"(limit {_RESPONSE_COMPLETED_SAFE_BYTES})"
    )


def test_soft_trim_replaces_strings_above_500_chars():
    items = [{
        "type": "function_call",
        "arguments": json.dumps({
            "small": "ok",
            "big": "x" * 600,
            "extra": "y" * 1000,  # not in the old hardcoded list
        }),
    }]
    _trim_response_completed_items(items, soft=True)
    args = json.loads(items[0]["arguments"])
    assert args["small"] == "ok", "small strings must pass through"
    assert "truncated for response.completed" in args["big"]
    assert "truncated for response.completed" in args["extra"]


def test_soft_trim_does_not_drop_non_first_output_entries():
    items = [{
        "type": "function_call_output",
        "output": [
            {"type": "input_text", "text": "first"},
            {"type": "input_text", "text": "second"},
            {"type": "input_text", "text": "third"},
        ],
    }]
    _trim_response_completed_items(items, soft=True)
    assert len(items[0]["output"]) == 3, (
        "soft trim must preserve all output entries; the old code only "
        "trimmed the first entry, leaving big tails on subsequent ones"
    )


def test_hard_trim_collapses_to_single_output_entry():
    """The hard pass is the last-resort fallback when the payload is still
    over budget. It reduces multi-entry tool outputs to the first entry."""
    items = [{
        "type": "function_call_output",
        "output": [
            {"type": "input_text", "text": "first" * 200},
            {"type": "input_text", "text": "second" * 200},
            {"type": "input_text", "text": "third" * 200},
        ],
    }]
    _trim_response_completed_items(items, soft=False)
    assert len(items[0]["output"]) == 1


def test_message_items_pass_through_untouched():
    """Final assistant message items must NOT be trimmed — that's the user-
    facing text and clients depend on it being intact."""
    items = [{
        "type": "message",
        "role": "assistant",
        "content": [{"type": "output_text", "text": "hello world " * 100}],
    }]
    expected = json.dumps(items)
    _trim_response_completed_payload(items)
    assert json.dumps(items) == expected


def test_malformed_function_call_arguments_do_not_crash():
    """If `arguments` isn't valid JSON, the trim must not raise — just
    leave that item alone."""
    items = [{
        "type": "function_call",
        "arguments": "not valid json {{{",
    }]
    _trim_response_completed_items(items, soft=True)  # should not raise
    assert items[0]["arguments"] == "not valid json {{{"
