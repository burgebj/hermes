"""Environment variable passthrough registry.

Skills that declare ``required_environment_variables`` in their frontmatter
need those vars available in sandboxed execution environments (execute_code,
terminal).  By default both sandboxes strip secrets from the child process
environment for security.  This module provides a session-scoped allowlist
so skill-declared vars (and user-configured overrides) pass through.

Two sources feed the allowlist:

1. **Skill declarations** — when a skill is loaded via ``skill_view``, its
   ``required_environment_variables`` are registered here automatically.
2. **User config** — ``terminal.env_passthrough`` in config.yaml lets users
   explicitly allowlist vars for non-skill use cases.

Both ``code_execution_tool.py`` and ``tools/environments/local.py`` consult
:func:`is_env_passthrough` before stripping a variable.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Iterable
from hermes_cli.config import cfg_get

logger = logging.getLogger(__name__)

# Session-scoped set of env var names that should pass through to sandboxes.
# Backed by ContextVar to prevent cross-session data bleed in the gateway pipeline.
_allowed_env_vars_var: ContextVar[set[str]] = ContextVar("_allowed_env_vars")


def _get_allowed() -> set[str]:
    """Get or create the allowed env vars set for the current context/session."""
    try:
        return _allowed_env_vars_var.get()
    except LookupError:
        val: set[str] = set()
        _allowed_env_vars_var.set(val)
        return val


# Cache for the config-based allowlist (loaded once per process).
_config_passthrough: frozenset[str] | None = None

# Hard-coded minimum set of well-known Hermes provider credential env var names.
# Used as a fail-closed fallback when ``tools.environments.local`` cannot be
# imported (e.g. partial install, import cycle during early bootstrap).
#
# This list mirrors the *hardcoded* subset of the full blocklist built by
# ``_build_provider_env_blocklist()`` in tools/environments/local.py and is
# intentionally conservative — it covers the highest-value credentials that
# must NEVER leak into a sandbox child process regardless of whether the full
# dynamic blocklist is available.  When local.py IS importable, the full
# blocklist is authoritative and this set is ignored.
#
# The list here should stay in sync with the hardcoded block in
# ``_build_provider_env_blocklist()`` for the most sensitive keys.  Adding a
# new key here does NOT replace keeping it there as well.
#
# Fixes: https://github.com/NousResearch/hermes-agent/issues/37950
_FALLBACK_PROVIDER_ENV_BLOCKLIST: frozenset[str] = frozenset({
    # LLM provider API keys / base URLs (mirrors hardcoded block in local.py)
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_API_BASE",
    "OPENAI_ORG_ID",
    "OPENAI_ORGANIZATION",
    "OPENROUTER_API_KEY",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_TOKEN",
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "LLM_MODEL",
    "GOOGLE_API_KEY",
    "DEEPSEEK_API_KEY",
    "MISTRAL_API_KEY",
    "GROQ_API_KEY",
    "TOGETHER_API_KEY",
    "PERPLEXITY_API_KEY",
    "COHERE_API_KEY",
    "FIREWORKS_API_KEY",
    "XAI_API_KEY",
    "HELICONE_API_KEY",
    "PARALLEL_API_KEY",
    "FIRECRAWL_API_KEY",
    "FIRECRAWL_API_URL",
    "DAYTONA_API_KEY",
    # Messaging bot tokens
    "TELEGRAM_BOT_TOKEN",
    "DISCORD_BOT_TOKEN",
    "SLACK_BOT_TOKEN",
    # Messaging config vars (in local.py hardcoded block as "messaging" category)
    "TELEGRAM_HOME_CHANNEL",
    "TELEGRAM_HOME_CHANNEL_NAME",
    "DISCORD_HOME_CHANNEL",
    "DISCORD_HOME_CHANNEL_NAME",
    "DISCORD_REQUIRE_MENTION",
    "DISCORD_FREE_RESPONSE_CHANNELS",
    "DISCORD_AUTO_THREAD",
    "SLACK_HOME_CHANNEL",
    "SLACK_HOME_CHANNEL_NAME",
    "SLACK_ALLOWED_USERS",
    "WHATSAPP_ENABLED",
    "WHATSAPP_MODE",
    "WHATSAPP_ALLOWED_USERS",
    "SIGNAL_HTTP_URL",
    "SIGNAL_ACCOUNT",
    "SIGNAL_ALLOWED_USERS",
    "SIGNAL_GROUP_ALLOWED_USERS",
    "SIGNAL_HOME_CHANNEL",
    "SIGNAL_HOME_CHANNEL_NAME",
    "SIGNAL_IGNORE_STORIES",
    # Home automation
    "HASS_TOKEN",
    "HASS_URL",
    # Email credentials
    "EMAIL_ADDRESS",
    "EMAIL_PASSWORD",
    "EMAIL_IMAP_HOST",
    "EMAIL_SMTP_HOST",
    "EMAIL_HOME_ADDRESS",
    "EMAIL_HOME_ADDRESS_NAME",
    # GitHub credentials
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GITHUB_APP_ID",
    "GITHUB_APP_PRIVATE_KEY_PATH",
    "GITHUB_APP_INSTALLATION_ID",
    # Modal / Daytona tokens
    "MODAL_TOKEN_ID",
    "MODAL_TOKEN_SECRET",
    # Gateway / dashboard
    "HERMES_DASHBOARD_SESSION_TOKEN",
    "GATEWAY_ALLOWED_USERS",
    # System-level credentials
    "SUDO_PASSWORD",
})


def _is_hermes_provider_credential(name: str) -> bool:
    """True if ``name`` is a Hermes-managed provider credential (API key,
    token, or similar) per ``_HERMES_PROVIDER_ENV_BLOCKLIST``.

    Skill-declared ``required_environment_variables`` frontmatter must
    not be able to override this list — that was the bypass in
    GHSA-rhgp-j443-p4rf where a malicious skill registered
    ``ANTHROPIC_TOKEN`` / ``OPENAI_API_KEY`` as passthrough and received
    the credential in the ``execute_code`` child process, defeating the
    sandbox's scrubbing guarantee.

    Non-Hermes API keys (TENOR_API_KEY, NOTION_TOKEN, etc.) are NOT
    in the blocklist and remain legitimately registerable — skills that
    wrap third-party APIs still work.

    Fail-closed: if ``tools.environments.local`` cannot be imported
    (partial install, import cycle, etc.), falls back to
    ``_FALLBACK_PROVIDER_ENV_BLOCKLIST`` — a hardcoded minimum set of
    well-known provider credentials — rather than returning ``False`` for
    every name.  The fallback keeps the most sensitive keys protected even
    when the full dynamic blocklist is unavailable.

    Why: an ``except Exception: return False`` guard was the original
    implementation, which meant any import failure turned the function
    fail-open — a skill could register ``ANTHROPIC_TOKEN`` as passthrough
    and receive it in the execute_code child process.
    Test: simulate a broken import of tools.environments.local and verify
    that _is_hermes_provider_credential("ANTHROPIC_TOKEN") still returns True.
    """
    try:
        from tools.environments.local import _HERMES_PROVIDER_ENV_BLOCKLIST
    except Exception:
        logger.warning(
            "env passthrough: could not import _HERMES_PROVIDER_ENV_BLOCKLIST "
            "from tools.environments.local — falling back to minimum hardcoded "
            "blocklist to fail closed. Provider credentials may still be "
            "protected, but the full dynamic blocklist is unavailable.",
        )
        return name in _FALLBACK_PROVIDER_ENV_BLOCKLIST
    return name in _HERMES_PROVIDER_ENV_BLOCKLIST


def register_env_passthrough(var_names: Iterable[str]) -> None:
    """Register environment variable names as allowed in sandboxed environments.

    Typically called when a skill declares ``required_environment_variables``.

    Variables that are Hermes-managed provider credentials (from
    ``_HERMES_PROVIDER_ENV_BLOCKLIST``) are rejected here to preserve
    the ``execute_code`` sandbox's credential-scrubbing guarantee per
    GHSA-rhgp-j443-p4rf. A skill that needs to talk to a Hermes-managed
    provider should do so via the agent's main-process tools (web_search,
    web_extract, etc.) where the credential remains safely in the main
    process.

    Non-Hermes third-party API keys (TENOR_API_KEY, NOTION_TOKEN, etc.)
    pass through normally — they were never in the sandbox scrub list.
    """
    for name in var_names:
        name = name.strip()
        if not name:
            continue
        if _is_hermes_provider_credential(name):
            logger.warning(
                "env passthrough: refusing to register Hermes provider "
                "credential %r (blocked by _HERMES_PROVIDER_ENV_BLOCKLIST). "
                "Skills must not override the execute_code sandbox's "
                "credential scrubbing; see GHSA-rhgp-j443-p4rf.",
                name,
            )
            continue
        _get_allowed().add(name)
        logger.debug("env passthrough: registered %s", name)


def _load_config_passthrough() -> frozenset[str]:
    """Load ``tools.env_passthrough`` from config.yaml (cached)."""
    global _config_passthrough
    if _config_passthrough is not None:
        return _config_passthrough

    result: set[str] = set()
    try:
        from hermes_cli.config import read_raw_config
        cfg = read_raw_config()
        passthrough = cfg_get(cfg, "terminal", "env_passthrough")
        if isinstance(passthrough, list):
            for item in passthrough:
                if not isinstance(item, str) or not item.strip():
                    continue
                name = item.strip()
                # Mirror the skill-path filter in register_env_passthrough:
                # Hermes-managed provider credentials must not be passed
                # through to execute_code / terminal children, regardless of
                # whether the request came from a skill or from config.yaml.
                # See GHSA-rhgp-j443-p4rf.
                if _is_hermes_provider_credential(name):
                    logger.warning(
                        "env passthrough: refusing to register Hermes "
                        "provider credential %r from config.yaml (blocked "
                        "by _HERMES_PROVIDER_ENV_BLOCKLIST). Operator "
                        "configuration must not override the execute_code "
                        "sandbox's credential scrubbing; see "
                        "GHSA-rhgp-j443-p4rf.",
                        name,
                    )
                    continue
                result.add(name)
    except Exception as e:
        logger.debug("Could not read tools.env_passthrough from config: %s", e)

    _config_passthrough = frozenset(result)
    return _config_passthrough


def is_env_passthrough(var_name: str) -> bool:
    """Check whether *var_name* is allowed to pass through to sandboxes.

    Returns ``True`` if the variable was registered by a skill or listed in
    the user's ``tools.env_passthrough`` config.
    """
    if var_name in _get_allowed():
        return True
    return var_name in _load_config_passthrough()


def get_all_passthrough() -> frozenset[str]:
    """Return the union of skill-registered and config-based passthrough vars."""
    return frozenset(_get_allowed()) | _load_config_passthrough()


def clear_env_passthrough() -> None:
    """Reset the skill-scoped allowlist (e.g. on session reset)."""
    _get_allowed().clear()


