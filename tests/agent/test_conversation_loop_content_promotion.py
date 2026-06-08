from agent.conversation_loop import _promote_content_tool_calls
from agent.transports.types import NormalizedResponse


def _msg(content, tool_calls=None, finish="stop"):
    return NormalizedResponse(
        content=content, tool_calls=tool_calls, finish_reason=finish
    )


def test_promotes_when_no_structured_calls():
    msg = _msg('<tool_call>{"name":"web_search","arguments":{"query":"x"}}</tool_call>')
    _promote_content_tool_calls(msg, {"web_search"})
    assert msg.tool_calls
    assert msg.tool_calls[0].name == "web_search"
    assert msg.finish_reason == "tool_calls"
    assert "<tool_call>" not in (msg.content or "")


def test_noop_when_structured_calls_present():
    existing = [object()]
    msg = _msg("anything", tool_calls=existing, finish="tool_calls")
    _promote_content_tool_calls(msg, {"web_search"})
    assert msg.tool_calls is existing  # untouched → non-breaking


def test_noop_when_nothing_recognised():
    msg = _msg("a normal answer")
    _promote_content_tool_calls(msg, {"web_search"})
    assert not msg.tool_calls
    assert msg.finish_reason == "stop"
    assert msg.content == "a normal answer"


def test_noop_when_content_not_a_string():
    msg = _msg(None)
    _promote_content_tool_calls(msg, {"web_search"})
    assert not msg.tool_calls
    assert msg.finish_reason == "stop"


def test_double_call_is_idempotent():
    # The helper runs at TWO seams on the GLM/Ollama path (early truncation gate
    # + main normalize seam). If the same message reaches it twice, the second
    # call must be a no-op — no duplicated calls, no content stripped twice.
    msg = _msg('<tool_call>{"name":"web_search","arguments":{"q":"x"}}</tool_call>')
    _promote_content_tool_calls(msg, {"web_search"})
    first_calls = msg.tool_calls
    first_content = msg.content
    _promote_content_tool_calls(msg, {"web_search"})
    assert msg.tool_calls is first_calls  # same list object, not re-promoted
    assert len(msg.tool_calls) == 1  # not doubled
    assert msg.content == first_content  # residual not re-stripped


def test_two_seam_promotion_yields_identical_call_id():
    # Real two-seam flow: the early gate promotes object A, then the main seam
    # re-normalizes a FRESH object B from the same wire response and promotes
    # again. Deterministic ids must match so the two are the SAME logical call
    # (any downstream dedup collapses them) — never a double execution.
    wire = '<tool_call>{"name":"web_search","arguments":{"q":"x"}}</tool_call>'
    a, b = _msg(wire), _msg(wire)
    _promote_content_tool_calls(a, {"web_search"})
    _promote_content_tool_calls(b, {"web_search"})
    assert a.tool_calls[0].id == b.tool_calls[0].id


def test_promotion_disarms_glm_truncation_quirk():
    # run_agent._should_treat_stop_as_truncated fires only on
    # finish_reason=="stop" AND falsy tool_calls. Promotion flips both gates,
    # so a promoted Ollama-GLM content call can never be rewritten to "length".
    msg = _msg('<tool_call>{"name":"web_search","arguments":{}}</tool_call>')
    _promote_content_tool_calls(msg, {"web_search"})
    assert msg.finish_reason != "stop"
    assert msg.tool_calls
