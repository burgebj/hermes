"""Tests for Webhook Dispatcher."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from agent.webhook_dispatcher import WebhookDispatcher, WebhookConfig


@pytest.fixture
def dispatcher(tmp_path):
    return WebhookDispatcher(tmp_path)


def test_register_webhook(dispatcher):
    wid = dispatcher.register("https://example.com/hook", ["task.completed"])
    assert wid.startswith("wh_")
    assert len(dispatcher.list_webhooks()) == 1


def test_unregister_webhook(dispatcher):
    wid = dispatcher.register("https://example.com/hook", ["task.completed"])
    assert dispatcher.unregister(wid) is True
    assert len(dispatcher.list_webhooks()) == 0


def test_unregister_nonexistent(dispatcher):
    assert dispatcher.unregister("wh_nonexistent") is False


def test_list_webhooks_empty(dispatcher):
    assert dispatcher.list_webhooks() == []


def test_list_webhooks_multiple(dispatcher):
    dispatcher.register("https://a.com/hook", ["task.completed"])
    dispatcher.register("https://b.com/hook", ["cron.completed"])
    assert len(dispatcher.list_webhooks()) == 2


def test_sign_payload():
    sig = WebhookDispatcher._sign_payload(b"test payload", "secret123")
    assert sig.startswith("sha256=")
    assert len(sig) > 10


def test_persistence(tmp_path):
    d1 = WebhookDispatcher(tmp_path)
    wid = d1.register("https://example.com/hook", ["task.completed"])

    # Reload from disk
    d2 = WebhookDispatcher(tmp_path)
    assert len(d2.list_webhooks()) == 1
    assert d2.list_webhooks()[0]["id"] == wid


def test_dispatch_no_matching(dispatcher):
    results = dispatcher.dispatch("task.completed", {"test": True})
    assert results == []


@patch("urllib.request.urlopen")
def test_dispatch_success(mock_urlopen, dispatcher):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_urlopen.return_value.__enter__ = MagicMock(return_value=mock_response)
    mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)

    dispatcher.register("https://example.com/hook", ["task.completed"])
    results = dispatcher.dispatch("task.completed", {"test": True})
    assert len(results) == 1
    assert results[0]["success"] is True


def test_webhook_config_serialization():
    config = WebhookConfig(
        id="wh_test",
        url="https://example.com",
        events=["task.completed"],
        secret="s3cret",
    )
    d = config.to_dict()
    assert d["id"] == "wh_test"
    assert d["url"] == "https://example.com"

    config2 = WebhookConfig.from_dict(d)
    assert config2.id == config.id
    assert config2.secret == config.secret
