import json
from unittest.mock import Mock, patch

import pytest

from agent.gbrain_minions_transport import post_completion_envelope, post_enqueue_envelope


def test_post_enqueue_envelope_uses_bearer_auth_and_returns_json():
    envelope = {"version": "1.0", "kind": "background", "task_id": "bg_1"}
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {"task_id": "bg_1", "backend": "gbrain", "queue": "background"}

    with patch("agent.gbrain_minions_transport.requests.post", return_value=response) as post_mock:
        result = post_enqueue_envelope(
            envelope,
            url="https://gbrain.example/jobs",
            api_key="secret",
            timeout=12,
        )

    assert result["backend"] == "gbrain"
    kwargs = post_mock.call_args.kwargs
    assert kwargs["headers"]["Authorization"] == "Bearer secret"
    assert kwargs["timeout"] == 12
    assert kwargs["json"] == envelope


def test_post_enqueue_envelope_requires_url():
    with pytest.raises(ValueError):
        post_enqueue_envelope({"task_id": "bg_1"}, url="")


def test_post_completion_envelope_sends_json_and_accepts_text_response():
    completion = {"version": "1.0", "kind": "background", "task_id": "bg_1", "status": "succeeded"}
    response = Mock()
    response.raise_for_status = Mock()
    response.json.side_effect = ValueError("not json")
    response.text = "accepted"

    with patch("agent.gbrain_minions_transport.requests.post", return_value=response) as post_mock:
        result = post_completion_envelope(
            completion,
            url="https://hermes.example/api/minions/completions",
            api_key="secret",
            timeout=7,
        )

    assert result == {"ok": True, "raw": "accepted"}
    kwargs = post_mock.call_args.kwargs
    assert kwargs["headers"]["Authorization"] == "Bearer secret"
    assert kwargs["json"] == completion
