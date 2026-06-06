"""Tests for copilot-acp api_mode detection (#14437).

Without the fix, copilot-acp falls through to the default chat_completions
api_mode. The streaming path then attempts to iterate a SimpleNamespace
object returned by CopilotACPClient, causing a TypeError crash.
"""
import re
import pytest


def _extract_api_mode_chain(source: str) -> list[tuple[str, str]]:
    """Parse the api_mode if/elif/else chain from the init function.

    Accepts both ``self.`` (legacy AIAgent.__init__) and ``agent.``
    (current ``agent.agent_init.init_agent``) attribute styles so this
    test survives the refactor that moved init logic into a helper.
    """
    results = []
    for match in re.finditer(
        r'(?:self|agent)\.provider\s*==\s*"([^"]+)".*?(?:self|agent)\.api_mode\s*=\s*"([^"]+)"',
        source,
        re.DOTALL,
    ):
        results.append((match.group(1), match.group(2)))
    return results


def _init_source() -> str:
    """Return the source of whichever function owns api_mode detection.

    Tries the refactored helper first, then falls back to ``AIAgent.__init__``.
    """
    import inspect
    try:
        from agent.agent_init import init_agent
        return inspect.getsource(init_agent)
    except Exception:
        from run_agent import AIAgent
        return inspect.getsource(AIAgent.__init__)


class TestCopilotACPApiMode:
    """copilot-acp provider must use codex_responses api_mode (#14437)."""

    def test_copilot_acp_in_api_mode_chain(self):
        """Verify that copilot-acp is explicitly handled before the else clause."""
        source = _init_source()
        chain = _extract_api_mode_chain(source)
        providers = {provider for provider, _ in chain}
        assert "copilot-acp" in providers, (
            "copilot-acp is not in the api_mode detection chain — "
            "will fall through to chat_completions and crash"
        )

    def test_copilot_acp_gets_codex_responses(self):
        """Verify copilot-acp is mapped to codex_responses, not chat_completions."""
        source = _init_source()
        chain = _extract_api_mode_chain(source)
        mode_map = dict(chain)
        assert mode_map.get("copilot-acp") == "codex_responses", (
            f"copilot-acp mapped to '{mode_map.get('copilot-acp', 'MISSING')}' "
            f"instead of 'codex_responses'"
        )
