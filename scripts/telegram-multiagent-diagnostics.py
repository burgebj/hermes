#!/usr/bin/env python3
"""Telegram multi-agent workspace diagnostics.

Checks inline mode readiness, bot capabilities, agent registry config,
and workspace topic consistency for the Eternal group.

Usage:
    python scripts/telegram-multiagent-diagnostics.py [--token TOKEN]

The bot token is read from ~/.hermes/.env (TELEGRAM_BOT_TOKEN) unless
--token is passed explicitly.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _load_token(token_arg: str | None) -> str | None:
    if token_arg:
        return token_arg
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val and not val.startswith("$"):
                    return val
    return os.environ.get("TELEGRAM_BOT_TOKEN")


def _api_get(token: str, method: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.read().decode()[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _check(label: str, passed: bool, detail: str = "") -> str:
    icon = "✅" if passed else "❌"
    suffix = f"  → {detail}" if detail else ""
    return f"{icon} {label}{suffix}"


def run_diagnostics(token: str) -> None:
    print("=" * 60)
    print("Telegram Multi-Agent Workspace Diagnostics")
    print("=" * 60)
    print()

    # --- Bot info ---
    print("## Bot Capabilities")
    resp = _api_get(token, "getMe")
    if not resp.get("ok"):
        print(f"❌ Could not reach Telegram API: {resp.get('error', 'unknown')}")
        print("   Check TELEGRAM_BOT_TOKEN in ~/.hermes/.env")
        return

    bot = resp["result"]
    print(_check("Bot connected", True, f"@{bot.get('username')} (id={bot.get('id')})"))
    print(_check("Inline queries supported",
                 bot.get("supports_inline_queries", False),
                 "Disabled — enable in BotFather → Bot Settings → Inline Mode" if not bot.get("supports_inline_queries") else ""))
    print(_check("Can connect to business",
                 bot.get("can_connect_to_business", False),
                 "Requires Telegram Premium (BotFather → Bot Settings → Business Mode)" if not bot.get("can_connect_to_business") else ""))
    print(_check("Can join groups",
                 bot.get("can_join_groups", False),
                 "Enable in BotFather → Bot Settings → Allow Groups" if not bot.get("can_join_groups") else ""))
    print(_check("Can read all group messages",
                 bot.get("can_read_all_group_messages", False),
                 "Disabled (Privacy Mode ON — normal for most bots)"))
    print()

    # --- Agent registry ---
    print("## Agent Registry")
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from gateway.agent_registry import load_agent_registry
        registry = load_agent_registry()
        enabled = [e for e in registry.values() if e.enabled]
        disabled = [e for e in registry.values() if not e.enabled]
        print(_check(f"Agent registry loaded ({len(enabled)} enabled, {len(disabled)} disabled)", True))
        for entry in sorted(enabled, key=lambda e: e.alias):
            risk = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(entry.cost_risk, "⚪")
            lane = f" #{entry.topic_lane}" if entry.topic_lane else ""
            print(f"   @{entry.alias} {risk} {entry.display_name}{lane}")
    except Exception as e:
        print(f"❌ Could not load agent registry: {e}")
    print()

    # --- Workspace topics ---
    print("## Workspace Topic Registry")
    topics = {}
    drift = []
    try:
        from gateway.topic_registry import load_topic_registry, check_topic_drift
        topics = load_topic_registry()
        if topics:
            print(_check(f"Topic registry loaded ({len(topics)} topics)", True))
            for entry in sorted(topics.values(), key=lambda e: e.display_name):
                purpose = f" — {entry.purpose}" if entry.purpose else ""
                print(f"   #{entry.alias}: {entry.display_name} ({entry.ref.full}){purpose}")
        else:
            print("❌ No topics registered. Run: hermes workspace eternal-example --apply")
        drift = check_topic_drift()
        if drift:
            print(f"\n⚠️  Drift detected ({len(drift)} issues):")
            for issue in drift:
                print(f"   • {issue}")
        else:
            print(_check("No workspace drift detected", True))
    except Exception as e:
        print(f"❌ Could not check workspace topics: {e}")
    print()

    # --- Workspace feature modules ---
    print("## Workspace Feature Modules")
    try:
        from hermes_cli.commands import GATEWAY_KNOWN_COMMANDS
        required_commands = {"guide", "agent_status", "summon", "swarm", "route", "checklist", "say", "tts", "voice_status"}
        missing_commands = sorted(required_commands - set(GATEWAY_KNOWN_COMMANDS))
        for module_name in ("gateway.workspace_router", "gateway.workspace_keyboards", "gateway.checklist_store"):
            __import__(module_name)
            print(_check(f"{module_name} importable", True))
        print(_check("Workspace Telegram commands registered", not missing_commands,
                     f"missing: {', '.join(missing_commands)}" if missing_commands else ""))
    except Exception as e:
        print(f"❌ Workspace feature module check failed: {e}")
    print()

    # --- BotFather inline mode checklist ---
    print("## Inline Mode (Manual BotFather Steps Required)")
    inline_on = bot.get("supports_inline_queries", False)
    if inline_on:
        print("✅ Inline mode is already enabled.")
    else:
        print("ℹ️  Inline mode is OFF. To enable (cannot be done via API):")
        print("   1. Open @BotFather in Telegram")
        print("   2. /mybots → select @huntingtonjeff_bot")
        print("   3. Bot Settings → Inline Mode → Enable")
        print("   4. (Optional) Set inline placeholder text")
        print("   5. Re-run this script to verify")
    print()

    # --- Voice / TTS ---
    print("## Voice & TTS")
    print("ℹ️  Voice messages from Telegram are auto-transcribed if:")
    print("   • stt.enabled: true in config.yaml")
    print("   • A provider is available (faster-whisper, Groq, OpenAI, Mistral)")
    print("   Run: hermes config | grep -A5 stt")
    print()

    # --- Summary ---
    print("## Recommended Actions")
    actions = []
    if not bot.get("supports_inline_queries"):
        actions.append("Enable inline mode in BotFather (see above)")
    if not topics:
        actions.append("Run: hermes workspace eternal-example --apply")
    if drift:
        actions.append("Fix workspace drift: hermes workspace drift")
    if not actions:
        print("✅ All checks passed. Workspace is ready for multi-agent operation.")
    else:
        for i, action in enumerate(actions, 1):
            print(f"{i}. {action}")
    print()
    print("For full compatibility contract: hermes workspace guide")
    print("For agent roster:               /agent_status (in Telegram)")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Telegram multi-agent workspace diagnostics")
    parser.add_argument("--token", help="Bot token (default: from ~/.hermes/.env)")
    args = parser.parse_args()

    token = _load_token(args.token)
    if not token:
        print("Error: No bot token found.")
        print("Set TELEGRAM_BOT_TOKEN in ~/.hermes/.env or pass --token")
        sys.exit(1)

    run_diagnostics(token)


if __name__ == "__main__":
    main()
