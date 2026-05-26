"""Credential exposure policy for Hermes-managed subprocesses.

This module owns the env-var rules that prevent Hermes provider, tool, and
gateway credentials from leaking into child processes.  Callers choose the
execution shape they need:

* terminal subprocesses preserve normal env vars and strip known credentials;
* execute_code children use a small allowlist plus the same credential block.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Mapping

logger = logging.getLogger(__name__)

HERMES_CREDENTIAL_FORCE_PREFIX = "_HERMES_FORCE_"

SAFE_SANDBOX_ENV_PREFIXES = (
    "PATH",
    "HOME",
    "USER",
    "LANG",
    "LC_",
    "TERM",
    "TMPDIR",
    "TMP",
    "TEMP",
    "SHELL",
    "LOGNAME",
    "XDG_",
    "PYTHONPATH",
    "VIRTUAL_ENV",
    "CONDA",
    "HERMES_",
)

SECRET_ENV_SUBSTRINGS = (
    "KEY",
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "CREDENTIAL",
    "PASSWD",
    "AUTH",
)

# Windows-only: a handful of variables are required by the OS/CRT itself.
WINDOWS_ESSENTIAL_ENV_VARS = frozenset({
    "SYSTEMROOT",
    "SYSTEMDRIVE",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
    "OS",
    "PROCESSOR_ARCHITECTURE",
    "NUMBER_OF_PROCESSORS",
    "PUBLIC",
    "ALLUSERSPROFILE",
    "PROGRAMDATA",
    "PROGRAMFILES",
    "PROGRAMFILES(X86)",
    "PROGRAMW6432",
    "APPDATA",
    "LOCALAPPDATA",
    "USERPROFILE",
    "USERDOMAIN",
    "USERNAME",
    "HOMEDRIVE",
    "HOMEPATH",
    "COMPUTERNAME",
})

AWS_SDK_CREDENTIAL_ENV_VARS = frozenset({
    # Bedrock bearer-token auth.
    "AWS_BEARER_TOKEN_BEDROCK",
    # Static and temporary IAM credentials.
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    # Named profile / shared config sources.
    "AWS_PROFILE",
    "AWS_DEFAULT_PROFILE",
    "AWS_SHARED_CREDENTIALS_FILE",
    "AWS_CONFIG_FILE",
    # Web identity / assume-role sources.
    "AWS_ROLE_ARN",
    "AWS_ROLE_SESSION_NAME",
    "AWS_WEB_IDENTITY_TOKEN_FILE",
    # Container credentials.
    "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
    "AWS_CONTAINER_CREDENTIALS_FULL_URI",
    "AWS_CONTAINER_AUTHORIZATION_TOKEN",
    "AWS_CONTAINER_AUTHORIZATION_TOKEN_FILE",
})

_STATIC_HERMES_CREDENTIAL_ENV_VARS = frozenset({
    "OPENAI_BASE_URL",
    "OPENAI_API_KEY",
    "OPENAI_API_BASE",
    "OPENAI_ORG_ID",
    "OPENAI_ORGANIZATION",
    "OPENROUTER_API_KEY",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_TOKEN",
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
    "HASS_TOKEN",
    "HASS_URL",
    "EMAIL_ADDRESS",
    "EMAIL_PASSWORD",
    "EMAIL_IMAP_HOST",
    "EMAIL_SMTP_HOST",
    "EMAIL_HOME_ADDRESS",
    "EMAIL_HOME_ADDRESS_NAME",
    "GATEWAY_ALLOWED_USERS",
    "GH_TOKEN",
    "GITHUB_APP_ID",
    "GITHUB_APP_PRIVATE_KEY_PATH",
    "GITHUB_APP_INSTALLATION_ID",
    "MODAL_TOKEN_ID",
    "MODAL_TOKEN_SECRET",
    "DAYTONA_API_KEY",
    "VERCEL_OIDC_TOKEN",
    "VERCEL_TOKEN",
    "VERCEL_PROJECT_ID",
    "VERCEL_TEAM_ID",
})


def build_credential_env_blocklist() -> frozenset[str]:
    """Derive the credential blocklist from provider, tool, and gateway config."""
    blocked: set[str] = set(_STATIC_HERMES_CREDENTIAL_ENV_VARS)
    blocked.update(AWS_SDK_CREDENTIAL_ENV_VARS)

    try:
        from hermes_cli.auth import PROVIDER_REGISTRY

        for pconfig in PROVIDER_REGISTRY.values():
            blocked.update(pconfig.api_key_env_vars)
            if pconfig.base_url_env_var:
                blocked.add(pconfig.base_url_env_var)
            if pconfig.auth_type == "aws_sdk":
                blocked.update(AWS_SDK_CREDENTIAL_ENV_VARS)
    except ImportError:
        pass

    try:
        from hermes_cli.config import OPTIONAL_ENV_VARS

        for name, metadata in OPTIONAL_ENV_VARS.items():
            category = metadata.get("category")
            if category in {"tool", "messaging"}:
                blocked.add(name)
            elif category == "setting" and metadata.get("password"):
                blocked.add(name)
    except ImportError:
        pass

    return frozenset(blocked)


HERMES_CREDENTIAL_ENV_BLOCKLIST = build_credential_env_blocklist()


def is_hermes_credential_env_var(name: str) -> bool:
    """Return True when *name* is a Hermes-managed credential source."""
    return name in HERMES_CREDENTIAL_ENV_BLOCKLIST


def _default_passthrough(_name: str) -> bool:
    return False


@dataclass(frozen=True)
class CredentialExposurePolicy:
    """Sanitize child-process environments without exposing Hermes secrets."""

    blocked_env_vars: frozenset[str] = field(
        default_factory=lambda: HERMES_CREDENTIAL_ENV_BLOCKLIST
    )
    force_prefix: str = HERMES_CREDENTIAL_FORCE_PREFIX
    safe_sandbox_prefixes: tuple[str, ...] = SAFE_SANDBOX_ENV_PREFIXES
    secret_substrings: tuple[str, ...] = SECRET_ENV_SUBSTRINGS
    windows_essential_env_vars: frozenset[str] = field(
        default_factory=lambda: WINDOWS_ESSENTIAL_ENV_VARS
    )

    def is_blocked(self, name: str) -> bool:
        return name in self.blocked_env_vars

    def sanitize_terminal_env(
        self,
        base_env: Mapping[str, str] | None,
        extra_env: Mapping[str, str] | None = None,
        *,
        is_passthrough: Callable[[str], bool] | None = None,
    ) -> dict[str, str]:
        """Strip Hermes credentials while preserving ordinary terminal env."""
        passthrough = is_passthrough or _default_passthrough
        sanitized: dict[str, str] = {}

        for key, value in (base_env or {}).items():
            if key.startswith(self.force_prefix):
                continue
            if self._terminal_var_allowed(key, passthrough):
                sanitized[key] = value

        for key, value in (extra_env or {}).items():
            if key.startswith(self.force_prefix):
                real_key = key[len(self.force_prefix):]
                sanitized[real_key] = value
                logger.info(
                    "credential exposure policy: force-exposed env var %s "
                    "to terminal subprocess",
                    real_key,
                )
                continue
            if self._terminal_var_allowed(key, passthrough):
                sanitized[key] = value

        return sanitized

    def sanitize_sandbox_env(
        self,
        source_env: Mapping[str, str],
        *,
        is_passthrough: Callable[[str], bool] | None = None,
        is_windows: bool = False,
    ) -> dict[str, str]:
        """Build the minimal environment used by execute_code children."""
        passthrough = is_passthrough or _default_passthrough
        scrubbed: dict[str, str] = {}

        for key, value in source_env.items():
            if key.startswith(self.force_prefix):
                continue
            if self.is_blocked(key):
                if passthrough(key):
                    logger.warning(
                        "credential exposure policy: refusing passthrough "
                        "for Hermes credential env var %s",
                        key,
                    )
                continue
            if passthrough(key):
                scrubbed[key] = value
                continue
            if any(s in key.upper() for s in self.secret_substrings):
                continue
            if any(key.startswith(p) for p in self.safe_sandbox_prefixes):
                scrubbed[key] = value
                continue
            if is_windows and key.upper() in self.windows_essential_env_vars:
                scrubbed[key] = value

        return scrubbed

    def _terminal_var_allowed(
        self,
        key: str,
        passthrough: Callable[[str], bool],
    ) -> bool:
        if self.is_blocked(key):
            if passthrough(key):
                logger.warning(
                    "credential exposure policy: refusing passthrough for "
                    "Hermes credential env var %s",
                    key,
                )
            return False
        return True


DEFAULT_CREDENTIAL_EXPOSURE_POLICY = CredentialExposurePolicy()
