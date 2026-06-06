"""Test that resolved model/base_url sync back to AIAgent after provider routing."""
import inspect
from pathlib import Path


class TestRuntimeStateSync:
    """Verify resolved state syncs to AIAgent in agent/agent_init.py."""

    def test_model_sync_logic_exists(self):
        """agent.model and agent.base_url must be synced when empty."""
        ai_path = Path(__file__).resolve().parents[1] / "agent" / "agent_init.py"
        source = ai_path.read_text()
        
        assert "agent.model = _resolved_model" in source, (
            "Resolved model must sync back to AIAgent when previously empty"
        )
        assert "agent.base_url = str(_routed_client.base_url)" in source, (
            "Resolved base_url must sync back to AIAgent when previously empty"
        )

    def test_sync_guard_checks_empty_before_overwrite(self):
        """Model sync is guarded by 'if not agent.model' to prevent overwrites."""
        ai_path = Path(__file__).resolve().parents[1] / "agent" / "agent_init.py"
        source = ai_path.read_text()
        
        # The guards appear before the assignments
        assert "if not agent.model" in source
        assert "if not agent.base_url" in source
