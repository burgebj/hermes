"""Tests for local provider stream read timeout auto-detection.

When a local LLM provider is detected (Ollama, llama.cpp, vLLM, etc.),
the httpx stream read timeout should be automatically increased from the
default 60s to HERMES_API_TIMEOUT (1800s) to avoid premature connection
kills during long prefill phases.
"""

import os
import pytest
from types import SimpleNamespace
from unittest.mock import patch

from agent.chat_completion_helpers import (
    _compute_stream_stale_timeout,
    _is_known_local_inference_endpoint,
)
from agent.model_metadata import is_local_endpoint


class TestLocalStreamReadTimeout:
    """Verify stream read timeout auto-detection logic."""

    @pytest.mark.parametrize("base_url", [
        "http://localhost:11434",
        "http://127.0.0.1:8080",
        "http://0.0.0.0:5000",
        "http://192.168.1.100:8000",
        "http://10.0.0.5:1234",
        "http://host.docker.internal:11434",
        "http://host.containers.internal:11434",
        "http://host.lima.internal:11434",
    ])
    def test_local_endpoint_bumps_read_timeout(self, base_url):
        """Local endpoint + default timeout -> bumps to base_timeout."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("HERMES_STREAM_READ_TIMEOUT", None)
            _base_timeout = float(os.getenv("HERMES_API_TIMEOUT", 1800.0))
            _stream_read_timeout = float(os.getenv("HERMES_STREAM_READ_TIMEOUT", 120.0))
            if _stream_read_timeout == 120.0 and base_url and is_local_endpoint(base_url):
                _stream_read_timeout = _base_timeout
            assert _stream_read_timeout == 1800.0

    def test_user_override_respected_for_local(self):
        """User sets HERMES_STREAM_READ_TIMEOUT -> keep their value even for local."""
        with patch.dict(os.environ, {"HERMES_STREAM_READ_TIMEOUT": "300"}, clear=False):
            _base_timeout = float(os.getenv("HERMES_API_TIMEOUT", 1800.0))
            _stream_read_timeout = float(os.getenv("HERMES_STREAM_READ_TIMEOUT", 120.0))
            base_url = "http://localhost:11434"
            if _stream_read_timeout == 120.0 and base_url and is_local_endpoint(base_url):
                _stream_read_timeout = _base_timeout
            assert _stream_read_timeout == 300.0

    @pytest.mark.parametrize("base_url", [
        "https://api.openai.com",
        "https://openrouter.ai/api",
        "https://api.anthropic.com",
    ])
    def test_remote_endpoint_keeps_default(self, base_url):
        """Remote endpoint -> keep 120s default."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("HERMES_STREAM_READ_TIMEOUT", None)
            _base_timeout = float(os.getenv("HERMES_API_TIMEOUT", 1800.0))
            _stream_read_timeout = float(os.getenv("HERMES_STREAM_READ_TIMEOUT", 120.0))
            if _stream_read_timeout == 120.0 and base_url and is_local_endpoint(base_url):
                _stream_read_timeout = _base_timeout
            assert _stream_read_timeout == 120.0

    def test_empty_base_url_keeps_default(self):
        """No base_url set -> keep 120s default."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("HERMES_STREAM_READ_TIMEOUT", None)
            _base_timeout = float(os.getenv("HERMES_API_TIMEOUT", 1800.0))
            _stream_read_timeout = float(os.getenv("HERMES_STREAM_READ_TIMEOUT", 120.0))
            base_url = ""
            if _stream_read_timeout == 120.0 and base_url and is_local_endpoint(base_url):
                _stream_read_timeout = _base_timeout
            assert _stream_read_timeout == 120.0


class TestLocalStreamStaleTimeout:
    """Verify stale-stream timeout is disabled only for known local inference."""

    @pytest.mark.parametrize("base_url", [
        "http://localhost:11434/v1",
        "http://127.0.0.1:8080/v1",
        "http://10.0.0.5:1234/v1",
        "http://localhost:5555/omlx/v1",
    ])
    def test_known_local_inference_endpoints_disable_default_stale_timeout(
        self, base_url, monkeypatch
    ):
        monkeypatch.delenv("HERMES_STREAM_STALE_TIMEOUT", raising=False)
        monkeypatch.setattr(
            "agent.chat_completion_helpers.get_provider_stale_timeout",
            lambda provider, model: None,
        )
        agent = SimpleNamespace(provider="custom", model="local-model", base_url=base_url)

        assert _is_known_local_inference_endpoint(base_url) is True
        assert _compute_stream_stale_timeout(agent, {"messages": []}) == float("inf")

    def test_generic_local_relay_keeps_default_stale_timeout(self, monkeypatch):
        monkeypatch.delenv("HERMES_STREAM_STALE_TIMEOUT", raising=False)
        monkeypatch.setattr(
            "agent.chat_completion_helpers.get_provider_stale_timeout",
            lambda provider, model: None,
        )
        base_url = "http://127.0.0.1:9999/v1"
        agent = SimpleNamespace(provider="custom", model="cloud-proxy", base_url=base_url)

        assert _is_known_local_inference_endpoint(base_url) is False
        assert _compute_stream_stale_timeout(agent, {"messages": []}) == 180.0

    def test_env_override_keeps_stale_timeout_even_for_known_local(self, monkeypatch):
        monkeypatch.setenv("HERMES_STREAM_STALE_TIMEOUT", "180")
        monkeypatch.setattr(
            "agent.chat_completion_helpers.get_provider_stale_timeout",
            lambda provider, model: None,
        )
        agent = SimpleNamespace(
            provider="custom",
            model="local-model",
            base_url="http://localhost:11434/v1",
        )

        assert _compute_stream_stale_timeout(agent, {"messages": []}) == 180.0

    def test_provider_stale_timeout_keeps_precedence_for_known_local(self, monkeypatch):
        monkeypatch.delenv("HERMES_STREAM_STALE_TIMEOUT", raising=False)
        monkeypatch.setattr(
            "agent.chat_completion_helpers.get_provider_stale_timeout",
            lambda provider, model: 240.0,
        )
        agent = SimpleNamespace(
            provider="custom",
            model="local-model",
            base_url="http://localhost:11434/v1",
        )

        assert _compute_stream_stale_timeout(agent, {"messages": []}) == 240.0


class TestIsLocalEndpoint:
    """Direct unit tests for is_local_endpoint."""

    @pytest.mark.parametrize("url", [
        "http://localhost:11434",
        "http://127.0.0.1:8080",
        "http://0.0.0.0:5000",
        "http://[::1]:11434",
        "http://192.168.1.100:8000",
        "http://10.0.0.5:1234",
        "http://172.17.0.1:11434",
    ])
    def test_classic_local_addresses(self, url):
        assert is_local_endpoint(url) is True

    @pytest.mark.parametrize("url", [
        "http://host.docker.internal:11434",
        "http://host.docker.internal:8080/v1",
        "http://gateway.docker.internal:11434",
        "http://host.containers.internal:11434",
        "http://host.lima.internal:11434",
    ])
    def test_container_dns_names(self, url):
        assert is_local_endpoint(url) is True

    @pytest.mark.parametrize("url", [
        "http://ollama:11434",
        "http://litellm:4000/v1",
        "http://hermes-litellm:8080",
        "http://vllm:8000",
    ])
    def test_unqualified_docker_hostnames(self, url):
        """Unqualified hostnames (no dots) are local — Docker Compose, /etc/hosts, etc."""
        assert is_local_endpoint(url) is True

    @pytest.mark.parametrize("url", [
        "https://api.openai.com",
        "https://openrouter.ai/api",
        "https://api.anthropic.com",
        "https://evil.docker.internal.example.com",
    ])
    def test_remote_endpoints(self, url):
        assert is_local_endpoint(url) is False

    @pytest.mark.parametrize("url", [
        "http://100.64.0.0:11434",            # lower bound of CGNAT block
        "http://100.64.0.1:11434/v1",         # lower bound +1
        "http://100.77.243.5:11434",          # representative Tailscale host
        "https://100.100.100.100:443",        # Tailscale MagicDNS anchor
        "https://100.127.255.254:443",        # upper bound -1
        "http://100.127.255.255:11434",       # upper bound of CGNAT block
    ])
    def test_tailscale_cgnat_is_local(self, url):
        """Tailscale 100.64.0.0/10 should be treated as local for timeout bumps."""
        assert is_local_endpoint(url) is True

    @pytest.mark.parametrize("url", [
        "http://100.63.255.255:11434",        # just below CGNAT block
        "http://100.128.0.1:11434",           # just above CGNAT block
        "http://100.200.0.1:11434",           # well outside CGNAT
        "http://99.64.0.1:11434",             # first octet wrong
    ])
    def test_near_but_not_cgnat_is_remote(self, url):
        """Hosts adjacent to but outside 100.64.0.0/10 must not match."""
        assert is_local_endpoint(url) is False
