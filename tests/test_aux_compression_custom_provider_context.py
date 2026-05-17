"""Regression test for auxiliary compression context lookup on custom endpoints.

The startup feasibility check used to call ``get_model_context_length()`` for the
auxiliary compression model without threading through ``custom_providers``.
That caused named custom endpoints to miss per-model overrides and fall back to
``DEFAULT_FALLBACK_CONTEXT`` (256K), even when startup had already resolved a
larger explicit context window for the same endpoint/model.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from run_agent import AIAgent


class _DummyCompressor:
    def __init__(self, threshold_tokens: int = 500_000, context_length: int = 1_000_000):
        self.threshold_tokens = threshold_tokens
        self.threshold_percent = threshold_tokens / context_length
        self.context_length = context_length


def test_aux_compression_feasibility_threads_custom_provider_overrides():
    agent = object.__new__(AIAgent)
    agent.compression_enabled = True
    agent.context_compressor = _DummyCompressor()
    agent.provider = "gpt"
    agent.model = "gpt-5.4"
    agent._aux_compression_context_length_config = None
    agent._custom_providers = [
        {
            "name": "gpt",
            "base_url": "https://lovethea.org",
            "models": {
                "gpt-5.4": {"context_length": 1_000_000},
            },
        }
    ]
    agent._compression_warning = None
    agent.status_callback = None
    agent._emit_status = lambda msg: None
    agent._current_main_runtime = lambda: {}

    captured = {}

    def _fake_get_model_context_length(*args, **kwargs):
        captured["kwargs"] = kwargs
        return 1_000_000

    fake_client = SimpleNamespace(base_url="https://lovethea.org", api_key="redacted")

    with patch("agent.auxiliary_client.get_text_auxiliary_client", return_value=(fake_client, "gpt-5.4")), \
         patch("agent.auxiliary_client._resolve_task_provider_model", return_value=("gpt", "gpt-5.4", "", "", {})), \
         patch("agent.model_metadata.get_model_context_length", side_effect=_fake_get_model_context_length):
        agent._check_compression_model_feasibility()

    assert captured["kwargs"]["custom_providers"] == agent._custom_providers
    assert agent.context_compressor.threshold_tokens == 500_000
    assert agent._compression_warning is None
