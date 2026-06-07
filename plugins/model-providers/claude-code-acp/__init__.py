"""Claude Code ACP provider profile.

claude-code-acp uses an external ACP subprocess (the `claude-code-acp` bridge,
npm `@zed-industries/claude-code-acp`) — NOT the standard transport. Routing is
handled separately in agent_runtime_helpers.py via the ``acp://claude-code``
base-url marker. The profile captures auth + endpoint metadata for registry
migration. Authentication is delegated to the user's existing Claude Code login.
"""

from providers import register_provider
from providers.base import ProviderProfile


class ClaudeCodeACPProfile(ProviderProfile):
    """Claude Code ACP — external process, no REST models endpoint."""

    def fetch_models(
        self,
        *,
        api_key: str | None = None,
        timeout: float = 8.0,
    ) -> list[str] | None:
        """Model listing is handled by the ACP subprocess."""
        return None


claude_code_acp = ClaudeCodeACPProfile(
    name="claude-code-acp",
    aliases=("claude-acp", "claude-code-acp-agent", "zed-claude-acp"),
    api_mode="chat_completions",  # ACP subprocess uses chat_completions routing
    env_vars=(),  # Managed by ACP subprocess / Claude Code login
    base_url="acp://claude-code",  # ACP internal scheme
    auth_type="external_process",
)

register_provider(claude_code_acp)
