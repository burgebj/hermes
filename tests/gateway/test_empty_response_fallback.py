from gateway.run import (
    _ensure_deliverable_gateway_response,
    _normalize_empty_agent_response,
)


def test_normalize_empty_agent_response_leaves_zero_api_call_gap_empty():
    agent_result = {
        "final_response": "",
        "messages": [],
        "api_calls": 0,
        "failed": False,
        "partial": False,
        "interrupted": False,
    }

    assert _normalize_empty_agent_response(agent_result, "") == ""


def test_ensure_deliverable_gateway_response_replaces_empty_silence():
    agent_result = {
        "api_calls": 0,
        "failed": False,
        "partial": False,
        "interrupted": False,
    }

    response = _ensure_deliverable_gateway_response(agent_result, "")

    assert "produced no deliverable response" in response
    assert "Please send it again." in response


def test_ensure_deliverable_gateway_response_keeps_interrupted_empty_response():
    agent_result = {"interrupted": True}

    assert _ensure_deliverable_gateway_response(agent_result, "") == ""
