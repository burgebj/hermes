from typing import Any

from agent.transports import register_transport
from agent.transports.chat_completions import ChatCompletionsTransport


class ClaudeCodeCliTransport(ChatCompletionsTransport):
    @property
    def api_mode(self) -> str:
        return "claude_code_cli"

    def build_kwargs(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **params,
    ) -> dict[str, Any]:
        kwargs = super().build_kwargs(model, messages, tools=None, **params)
        kwargs["binding_key"] = params.get("session_id")
        return kwargs


register_transport("claude_code_cli", ClaudeCodeCliTransport)
