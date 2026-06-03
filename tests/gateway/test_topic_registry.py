import json
from types import SimpleNamespace
from unittest.mock import patch

from gateway.config import Platform
from gateway.decision_records import format_decision_record
from gateway.topic_registry import (
    check_topic_drift,
    describe_current_topic,
    generate_ops_index,
    generate_workspace_guide,
    load_topic_registry,
)
from hermes_cli.workspace import build_eternal_example_config


def _config():
    return {
        "workspace": {
            "topic_registry": {
                "topics": {
                    "dev-logs": {
                        "target": "telegram:-1001:15",
                        "name": "Eternal / #dev-logs",
                        "purpose": "builds/CI/errors",
                    },
                    "briefings-alerts": {
                        "target": "telegram:-1001:707",
                        "name": "Eternal / Briefings & Alerts",
                        "purpose": "briefings",
                    },
                }
            },
            "service_urls": {"dashboard": "https://hermes.example"},
        },
        "telegram": {
            "channel_prompts": {
                "-1001:15": "dev prompt",
                "-1001:707": "briefing prompt",
            }
        },
    }


def test_load_topic_registry_keys_by_full_ref():
    registry = load_topic_registry(_config())
    assert registry["telegram:-1001:15"].alias == "dev-logs"
    assert registry["telegram:-1001:707"].purpose == "briefings"


def test_describe_current_topic_reports_alias_and_prompt():
    source = SimpleNamespace(
        platform=Platform.TELEGRAM,
        chat_id="-1001",
        thread_id="15",
        chat_name="Eternal",
    )
    text = describe_current_topic(source, _config())
    assert "Alias: #dev-logs" in text
    assert "Channel prompt: configured" in text
    assert "Target ref: telegram:-1001:15" in text


def test_generate_workspace_guide_includes_topics_707_and_708_from_example():
    cfg = build_eternal_example_config({})
    guide = generate_workspace_guide(cfg)
    assert "telegram:-1003932124823:707" in guide
    assert "Eternal / Agent Workbench" in guide
    assert check_topic_drift(cfg) == []


def test_eternal_example_preserves_legacy_string_channel_prompts():
    cfg = build_eternal_example_config({
        "telegram": {
            "channel_prompts": json.dumps({"-1003932124823:14": "custom alert prompt"})
        }
    })
    prompts = cfg["telegram"]["channel_prompts"]
    assert prompts["-1003932124823:14"] == "custom alert prompt"
    assert "-1003932124823:707" in prompts
    assert check_topic_drift(cfg) == []


def test_eternal_example_migrates_stale_internal_topic_keys():
    cfg = build_eternal_example_config({
        "workspace": {
            "topic_registry": {
                "topics": {
                    "daily-briefing": {
                        "alias": "daily-briefing",
                        "target": "telegram:-1003932124823:707",
                        "name": "Eternal / #daily-briefing",
                    },
                    "group-meta": {
                        "alias": "group-meta",
                        "target": "telegram:-1003932124823:708",
                        "name": "Eternal / #group-meta",
                    },
                }
            }
        }
    })
    topics = cfg["workspace"]["topic_registry"]["topics"]
    assert "daily-briefing" not in topics
    assert "group-meta" not in topics
    assert topics["briefings-alerts"]["alias"] == "briefings-alerts"
    assert topics["briefings-alerts"]["name"] == "Eternal / Briefings & Alerts"
    assert topics["agent-workbench"]["alias"] == "agent-workbench"
    assert topics["agent-workbench"]["name"] == "Eternal / Agent Workbench"


def test_drift_reports_prompt_missing_from_registry():
    cfg = _config()
    cfg["telegram"]["channel_prompts"]["-1001:708"] = "meta prompt"
    issues = check_topic_drift(cfg)
    assert "channel_prompts defines telegram:-1001:708" in "\n".join(issues)


def test_drift_reports_notify_env_target_missing_from_registry(monkeypatch):
    monkeypatch.setenv("BLAZEMIND_NOTIFY_TARGET", "telegram:-1001:708")
    issues = check_topic_drift(_config())
    assert "BLAZEMIND_NOTIFY_TARGET points at telegram:-1001:708" in "\n".join(issues)


def test_ops_index_redacts_env_and_lists_cron(tmp_path, monkeypatch):
    (tmp_path / "cron").mkdir()
    (tmp_path / "cron" / "jobs.json").write_text(
        json.dumps({"jobs": [{"id": "daily", "name": "Daily Briefing", "deliver": "telegram:-1001:707"}]}),
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_HOME_CHANNEL", "-1001")
    monkeypatch.setenv("TELEGRAM_CRON_THREAD_ID", "707")
    text = generate_ops_index(_config())
    assert "Daily Briefing" in text
    assert "TELEGRAM_CRON_THREAD_ID" in text
    assert "https://hermes.example" in text


def test_decision_record_redacts_secret_text():
    text = format_decision_record(
        title="Token changed",
        change_type="secret",
        target="TELEGRAM_BOT_TOKEN",
        after="TELEGRAM_BOT_TOKEN=123:ABC",
    )
    assert "123:ABC" not in text
