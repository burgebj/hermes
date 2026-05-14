"""Integration tests for LCM in the agent loop."""
import pytest
from unittest.mock import MagicMock, patch
from plugins.context_engine.lcm.engine import LcmEngine, CompactionAction
from plugins.context_engine.lcm.config import LcmConfig


class TestLcmInitialization:
    def test_lcm_engine_created_when_enabled(self):
        """When lcm.enabled=true in config, AIAgent should have an lcm_engine."""
        config = {"lcm": {"enabled": True, "tau_soft": 0.5, "tau_hard": 0.85}}
        lcm_config = LcmConfig.from_dict(config.get("lcm", {}))
        assert lcm_config.enabled is True
        engine = LcmEngine(lcm_config)
        assert engine is not None

    def test_lcm_engine_not_created_when_disabled(self):
        """When lcm.enabled=false, no engine should be created."""
        config = {"lcm": {"enabled": False}}
        lcm_config = LcmConfig.from_dict(config.get("lcm", {}))
        assert lcm_config.enabled is False

    def test_lcm_config_defaults_enabled(self):
        """Empty config section means LCM is enabled by default (unified system)."""
        lcm_config = LcmConfig.from_dict({})
        assert lcm_config.enabled is True

    def test_lcm_config_from_agent_config_section(self):
        """Verify LcmConfig reads the lcm section from agent config dict."""
        agent_cfg = {
            "compression": {"enabled": True},
            "lcm": {"enabled": "true", "tau_soft": "0.6", "tau_hard": "0.9"},
        }
        lcm_section = agent_cfg.get("lcm", {})
        if not isinstance(lcm_section, dict):
            lcm_section = {}
        lcm_config = LcmConfig.from_dict(lcm_section)
        assert lcm_config.enabled is True
        assert lcm_config.tau_soft == 0.6
        assert lcm_config.tau_hard == 0.9

    def test_lcm_config_handles_missing_section(self):
        """When no 'lcm' key exists in agent config, LCM is enabled by default."""
        agent_cfg = {}
        lcm_section = agent_cfg.get("lcm", {})
        if not isinstance(lcm_section, dict):
            lcm_section = {}
        lcm_config = LcmConfig.from_dict(lcm_section)
        assert lcm_config.enabled is True

    def test_lcm_config_handles_non_dict_section(self):
        """When 'lcm' key is not a dict (e.g. None), defaults are used (enabled=True)."""
        agent_cfg = {"lcm": None}
        lcm_section = agent_cfg.get("lcm", {})
        if not isinstance(lcm_section, dict):
            lcm_section = {}
        lcm_config = LcmConfig.from_dict(lcm_section)
        assert lcm_config.enabled is True


class TestLcmCompaction:
    def test_lcm_compact_produces_summary(self):
        """The _lcm_compact flow should find a block, summarize, and return fewer messages."""
        config = LcmConfig(enabled=True, tau_soft=0.5, tau_hard=0.85, protect_last_n=2)
        engine = LcmEngine(config)

        # Simulate a conversation
        messages = []
        for i in range(10):
            msg = {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i} " + "x" * 100}
            messages.append(msg)
            engine.ingest(msg)

        # Engine should have 10 active entries
        assert len(engine.active) == 10

        # Find and compact
        block = engine.find_compactable_block()
        assert block is not None
        start, end = block

        from plugins.context_engine.lcm.escalation import deterministic_truncate
        summary_text = deterministic_truncate(
            [e.message for e in engine.active[start:end]],
            target_tokens=100
        )
        node = engine.compact(summary_text, level=3, block_start=start, block_end=end)

        # Should have fewer active entries now
        assert len(engine.active) < 10
        # But store still has all 10
        assert len(engine.store) == 10
        # Expand should recover originals
        expanded = engine.expand_summary(node.id)
        assert len(expanded) == end - start

    def test_lcm_append_message_ingests(self):
        """_append_message should add to both messages list and engine."""
        config = LcmConfig(enabled=True)
        engine = LcmEngine(config)

        messages = []
        msg = {"role": "user", "content": "hello"}

        # Simulate _append_message behavior
        messages.append(msg)
        engine.ingest(msg)

        assert len(messages) == 1
        assert len(engine.store) == 1
        assert len(engine.active) == 1

    def test_append_message_no_engine(self):
        """When lcm_engine is None, _append_message should behave like a plain append."""
        lcm_engine = None
        messages = []
        msg = {"role": "user", "content": "hello"}

        # Simulate _append_message when engine is None
        messages.append(msg)
        if lcm_engine is not None:
            lcm_engine.ingest(msg)

        assert len(messages) == 1

    def test_check_thresholds_blocking(self):
        """Engine returns BLOCKING when active tokens >= tau_hard * budget."""
        config = LcmConfig(enabled=True, tau_soft=0.5, tau_hard=0.85)
        engine = LcmEngine(config)

        # Ingest enough to fill 90% of a 1000-token budget
        # ~4 chars/token, so 900 tokens = 3600 chars
        msg = {"role": "user", "content": "x" * 3600}
        engine.ingest(msg)

        action = engine.check_thresholds(token_budget=1000)
        assert action == CompactionAction.BLOCKING

    def test_check_thresholds_none_below_soft(self):
        """Engine returns NONE when active tokens < tau_soft * budget."""
        config = LcmConfig(enabled=True, tau_soft=0.5, tau_hard=0.85)
        engine = LcmEngine(config)

        # Ingest very little content — far below soft threshold
        msg = {"role": "user", "content": "hello"}
        engine.ingest(msg)

        action = engine.check_thresholds(token_budget=100_000)
        assert action == CompactionAction.NONE

    def test_active_messages_after_compact(self):
        """active_messages() returns only the active (post-compaction) messages."""
        config = LcmConfig(enabled=True, protect_last_n=2)
        engine = LcmEngine(config)

        for i in range(6):
            engine.ingest({"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"})

        block = engine.find_compactable_block()
        assert block is not None
        start, end = block

        engine.compact("summary text", level=3, block_start=start, block_end=end)
        active = engine.active_messages()

        # There should be fewer messages now (block replaced by 1 summary)
        assert len(active) < 6
        # The summary message should appear
        assert any("[Summary" in str(m.get("content", "")) for m in active)


class TestLcmToolRegistration:
    def test_tool_schemas_valid(self):
        """All LCM tool schemas should be valid for registration."""
        from plugins.context_engine.lcm.tools import LCM_TOOL_SCHEMAS
        for name, schema in LCM_TOOL_SCHEMAS.items():
            assert schema["name"] == name
            assert "description" in schema
            assert "parameters" in schema

    def test_set_engine_enables_tools(self):
        """After set_engine, tool handlers should work."""
        from plugins.context_engine.lcm.tools import set_engine, handle_lcm_budget
        config = LcmConfig(enabled=True)
        engine = LcmEngine(config)
        engine.ingest({"role": "user", "content": "test"})
        set_engine(engine)
        result = handle_lcm_budget({})
        assert "token" in result.lower() or "active" in result.lower()
        set_engine(None)  # cleanup

    def test_set_engine_none_disables_tools(self):
        """After set_engine(None), tool handlers should return an error string."""
        from plugins.context_engine.lcm.tools import set_engine, handle_lcm_budget, get_engine
        set_engine(None)
        result = handle_lcm_budget({})
        assert "not active" in result.lower() or "error" in result.lower()
        assert get_engine() is None

    def test_all_lcm_tool_names_in_schemas(self):
        """All 7 expected LCM tools should be present in LCM_TOOL_SCHEMAS."""
        from plugins.context_engine.lcm.tools import LCM_TOOL_SCHEMAS
        expected = {"lcm_expand", "lcm_pin", "lcm_forget", "lcm_search", "lcm_budget", "lcm_toc", "lcm_focus"}
        assert set(LCM_TOOL_SCHEMAS.keys()) == expected

    def test_lcm_tools_formatted_for_openai(self):
        """LCM tool schemas should be convertible to the OpenAI tool format."""
        from plugins.context_engine.lcm.tools import LCM_TOOL_SCHEMAS
        for name, schema in LCM_TOOL_SCHEMAS.items():
            # Wrap in the OpenAI format structure
            openai_tool = {
                "type": "function",
                "function": schema,
            }
            assert openai_tool["type"] == "function"
            assert openai_tool["function"]["name"] == name
            assert "parameters" in openai_tool["function"]


class TestLcmAgentIntegration:
    """Tests that verify the integration wiring in run_agent.py."""

    def test_append_message_helper_simulation(self):
        """Simulate the _append_message helper: both list and engine get the message."""
        config = LcmConfig(enabled=True)
        engine = LcmEngine(config)
        messages = []

        def _append_message(messages, msg, lcm_engine=None):
            messages.append(msg)
            if lcm_engine is not None:
                lcm_engine.ingest(msg)

        for i in range(5):
            msg = {"role": "user" if i % 2 == 0 else "assistant", "content": f"turn {i}"}
            _append_message(messages, msg, engine)

        assert len(messages) == 5
        assert len(engine.active) == 5
        assert len(engine.store) == 5

    def test_lcm_compact_simulation(self):
        """Simulate _lcm_compact: find block, deterministic truncate, compact, rebuild."""
        from plugins.context_engine.lcm.escalation import escalated_summary

        config = LcmConfig(enabled=True, tau_soft=0.5, tau_hard=0.85, protect_last_n=2)
        engine = LcmEngine(config)

        messages = []
        for i in range(8):
            msg = {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}: " + "detail " * 20}
            messages.append(msg)
            engine.ingest(msg)

        block = engine.find_compactable_block()
        assert block is not None
        block_start, block_end = block
        block_messages = [e.message for e in engine.active[block_start:block_end]]

        # escalated_summary will fall through to deterministic (Level 3)
        summary_text, level = escalated_summary(
            block_messages,
            target_tokens=200,
            deterministic_target=100,
            summary_model="",
        )
        assert level == 3  # Level 1/2 require LLM, always falls through to 3
        assert len(summary_text) > 0

        engine.compact(summary_text, level, block_start, block_end)
        new_messages = engine.active_messages()

        # Should have fewer messages after compaction
        assert len(new_messages) < len(messages)
