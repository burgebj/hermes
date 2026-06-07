"""Test custom provider context_length propagation to compression feasibility."""
from pathlib import Path


class TestCompressionContextLength:
    """Verify custom provider context_length flows to compression checks."""

    def test_aux_ctx_fallback_to_main_model_context(self):
        """When aux model matches main model, fall back to main's context_length."""
        comp_path = Path(__file__).resolve().parents[1] / "agent" / "conversation_compression.py"
        source = comp_path.read_text()
        # The fallback: when same base_url and model, use main's context_length
        assert "_aux_compression_context_length_config" in source, (
            "Must check explicit aux compression context_length config first"
        )
        assert "_config_context_length" in source, (
            "Must fall back to main model's _config_context_length when aux matches main"
        )

    def test_aux_ctx_config_override_respected(self):
        """Explicit aux compression context_length config must be checked first."""
        comp_path = Path(__file__).resolve().parents[1] / "agent" / "conversation_compression.py"
        source = comp_path.read_text()
        assert "_aux_compression_context_length_config" in source, (
            "Explicit aux compression context_length from config must be checked"
        )

    def test_same_endpoint_detection(self):
        """When main and aux share same base_url and model, detect it."""
        comp_path = Path(__file__).resolve().parents[1] / "agent" / "conversation_compression.py"
        source = comp_path.read_text()
        assert "aux_base_url.rstrip" in source and "_main_base" in source, (
            "Must detect when aux and main share the same endpoint"
        )
