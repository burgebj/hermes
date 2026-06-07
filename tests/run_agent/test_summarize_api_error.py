"""Tests for AIAgent._summarize_api_error — especially empty SDK bodies (#36109)."""

from __future__ import annotations

from types import SimpleNamespace

from run_agent import AIAgent


class _EmptyBodyHttpError(Exception):
    status_code = 400
    body = None

    def __init__(self, response_text: str) -> None:
        super().__init__(f"Error code: 400")
        self.response = SimpleNamespace(text=response_text)


def test_summarize_api_error_reads_response_text_when_body_empty():
    error = _EmptyBodyHttpError('{"error":{"message":"No models provided"}}')
    summary = AIAgent._summarize_api_error(error)
    assert summary == "HTTP 400: No models provided"


def test_summarize_api_error_plain_response_text_when_not_json():
    error = _EmptyBodyHttpError("upstream rejected the request")
    summary = AIAgent._summarize_api_error(error)
    assert summary == "HTTP 400: upstream rejected the request"
