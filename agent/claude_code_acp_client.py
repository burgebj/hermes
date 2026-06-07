"""ACP subprocess client for Claude Code.

Lets Hermes treat Claude Code as a chat-style backend by spawning the
`claude-code-acp` bridge (https://github.com/zed-industries/claude-code-acp,
published as `@zed-industries/claude-code-acp` — the same bridge the Zed editor
uses to drive Claude Code over the Agent Client Protocol). Each request starts
a short-lived ACP session over stdio, sends the formatted conversation as a
single prompt, collects the streamed text chunks, and converts the result back
into the minimal shape Hermes expects from an OpenAI client.

Authentication is delegated entirely to the Claude Code binary the bridge
spawns (i.e. whatever `claude` login the user already has). Hermes does not
manage an Anthropic API key for this provider.
"""

from __future__ import annotations

from agent.copilot_acp_client import ACPSubprocessClient

ACP_MARKER_BASE_URL = "acp://claude-code"


class ClaudeCodeACPClient(ACPSubprocessClient):
    """ACP subprocess client for the Claude Code ACP bridge."""

    PROVIDER_LABEL = "Claude Code ACP"
    MARKER_BASE_URL = ACP_MARKER_BASE_URL
    DEFAULT_API_KEY = "claude-code-acp"
    DEFAULT_MODEL = "claude-code-acp"
    # The bridge ships a `claude-code-acp` binary and speaks ACP over stdio
    # with no extra flags. Override the command/args via env if it lives
    # elsewhere or needs wrapping (e.g. `npx @zed-industries/claude-code-acp`).
    COMMAND_ENV_VARS = ("HERMES_CLAUDE_CODE_ACP_COMMAND",)
    DEFAULT_COMMAND = "claude-code-acp"
    ARGS_ENV_VAR = "HERMES_CLAUDE_CODE_ACP_ARGS"
    DEFAULT_ARGS = ()

    def _startup_error_message(self, command: str) -> str:
        return (
            f"Could not start Claude Code ACP command '{command}'. "
            "Install the bridge with `npm install -g @zed-industries/claude-code-acp` "
            "(and Claude Code itself), or point Hermes at it explicitly via "
            "HERMES_CLAUDE_CODE_ACP_COMMAND."
        )
