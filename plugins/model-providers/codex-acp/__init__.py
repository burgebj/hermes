"""OpenAI Codex ACP provider profile.

codex-acp uses a local ACP subprocess, typically Zed's
@zed-industries/codex-acp adapter. It is routed through Hermes'
OpenAI-compatible ACP facade rather than the OpenAI Responses API.
"""

from providers import register_provider
from providers.base import ProviderProfile


class CodexACPProfile(ProviderProfile):
    """OpenAI Codex ACP — external process, no REST models endpoint."""

    def fetch_models(
        self,
        *,
        api_key: str | None = None,
        timeout: float = 8.0,
    ) -> list[str] | None:
        """Model listing is handled by the ACP subprocess."""
        return None


codex_acp = CodexACPProfile(
    name="codex-acp",
    aliases=("openai-codex-acp", "acp-codex"),
    api_mode="chat_completions",
    env_vars=(),
    base_url="acp://codex",
    auth_type="external_process",
)

register_provider(codex_acp)
