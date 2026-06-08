"""Tests for request/response tracing feature."""

import pytest


_TRACE_DEFAULT = False
try:
    from hermes_logging import _TRACE_ENABLED as _initial
    _TRACE_DEFAULT = _initial
except ImportError:
    pass


class TestRequestTracing:
    def test_tracing_disabled_by_default(self):
        assert _TRACE_DEFAULT is False

    def test_enable_tracing_sets_flag(self):
        from hermes_logging import enable_tracing
        enable_tracing()
        from hermes_logging import _TRACE_ENABLED as enabled
        assert enabled is True

    def test_log_api_request(self):
        from hermes_logging import enable_tracing, log_api_request
        enable_tracing()
        log_api_request("anthropic", "claude-sonnet-4", 500, 1000)

    def test_log_api_response_success(self):
        from hermes_logging import enable_tracing, log_api_response
        enable_tracing()
        log_api_response("openai", "gpt-4o", "success", 200, 1500.0)

    def test_log_api_response_error(self):
        from hermes_logging import enable_tracing, log_api_response
        enable_tracing()
        log_api_response("anthropic", "claude-haiku", "error", 0, 5000.0, error="rate_limit")

    def test_enable_tracing_creates_handler(self):
        from hermes_logging import enable_tracing, _trace_logger
        enable_tracing()
        assert len(_trace_logger.handlers) > 0