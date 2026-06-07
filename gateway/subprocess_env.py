"""Subprocess environment scrubbing for the gateway.

Removes credential env vars from subprocess environments to prevent
cross-platform credential leakage (GHSA-m4m8-xjp4-5rmm).
"""

import os
from typing import Dict, Optional, Set

CREDENTIAL_ENV_VARS: frozenset = frozenset({
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_TOKEN",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "FAL_KEY",
    "VOICE_TOOLS_OPENAI_KEY",
    "BROWSERBASE_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "DISCORD_BOT_TOKEN",
    "SLACK_BOT_TOKEN",
    "MATTERMOST_TOKEN",
    "MATRIX_ACCESS_TOKEN",
    "MATRIX_PASSWORD",
    "WEIXIN_TOKEN",
    "HASS_TOKEN",
    "EMAIL_PASSWORD",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "API_SERVER_KEY",
    "WEBHOOK_SECRET",
    "DINGTALK_CLIENT_ID",
    "DINGTALK_CLIENT_SECRET",
    "FEISHU_APP_ID",
    "FEISHU_APP_SECRET",
    "FEISHU_ENCRYPT_KEY",
    "FEISHU_VERIFICATION_TOKEN",
    "WECOM_SECRET",
    "WECOM_CALLBACK_CORP_SECRET",
    "WECOM_CALLBACK_TOKEN",
    "WECOM_CALLBACK_ENCODING_AES_KEY",
    "BLUEBUBBLES_PASSWORD",
    "QQ_CLIENT_SECRET",
    "YUANBAO_APP_ID",
    "YUANBAO_APP_KEY",
    "YUANBAO_APP_SECRET",
})


def scrubbed_env(*, keep: Optional[Set[str]] = None) -> Dict[str, str]:
    """Return a copy of os.environ with credential keys removed."""
    keep = keep or set()
    return {
        k: v for k, v in os.environ.items()
        if k not in CREDENTIAL_ENV_VARS or k in keep
    }
