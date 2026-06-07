"""Tests for web_server auxiliary endpoints including plugin-registered slots.

Covers:
  - GET /api/model/auxiliary includes plugin-registered task slots
  - POST /api/model/set accepts plugin-registered task names (scope=auxiliary)
  - POST /api/model/set __reset__ resets plugin slots alongside built-in ones
  - POST /api/model/set empty-task broadcast includes plugin slots
  - _get_all_aux_slots merges _AUX_TASK_SLOTS with plugin keys
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(plugins_aux=None, builtin_aux=None):
    """Build a minimal config dict for the web_server endpoints."""
    cfg = {
        "model": {"provider": "test", "default": "test-model"},
        "auxiliary": dict(builtin_aux or {}),
    }
    if plugins_aux:
        cfg["auxiliary"].update(plugins_aux)
    return cfg


def _patch_config_load(config):
    """Return a patcher for web_server.load_config returning *config*."""
    from hermes_cli import web_server
    return patch.object(web_server, "load_config", return_value=config)


def _patch_config_save():
    """Return a patcher for web_server.save_config that captures writes."""
    from hermes_cli import web_server
    saved = []
    def _save(cfg):
        saved.append(cfg)
    return patch.object(web_server, "save_config", side_effect=_save), saved


def _patch_plugin_aux_tasks(task_keys):
    """Monkeypatch get_plugin_auxiliary_tasks to return entries for *task_keys*."""
    entries = []
    for key in task_keys:
        entries.append({
            "key": key,
            "display_name": key.replace("_", " ").title(),
            "description": f"Plugin task {key}",
            "defaults": {"provider": "auto", "model": ""},
            "plugin": "test_plugin",
        })
    mod = __import__("hermes_cli.plugins", fromlist=["get_plugin_auxiliary_tasks"])
    return patch.object(mod, "get_plugin_auxiliary_tasks", return_value=entries)


@pytest.fixture(autouse=True)
def _bypass_auth():
    """Disable dashboard auth for all tests in this module.

    Patch _has_valid_session_token to always return True so the TestClient
    requests pass through the auth middleware without a real session token.
    """
    from hermes_cli import web_server
    with patch.object(web_server, "_has_valid_session_token", return_value=True):
        yield


# ---------------------------------------------------------------------------
# _get_all_aux_slots unit tests
# ---------------------------------------------------------------------------

class TestGetAllAuxSlots:
    """Verify the helper that merges built-in + plugin auxiliary slot keys."""

    def test_builtin_only_when_no_plugins(self):
        from hermes_cli.web_server import _AUX_TASK_SLOTS
        try:
            from hermes_cli.web_server import _get_all_aux_slots
        except ImportError:
            pytest.skip("_get_all_aux_slots not yet implemented (RED phase)")
        with _patch_plugin_aux_tasks([]):
            slots = _get_all_aux_slots()
        for builtin in _AUX_TASK_SLOTS:
            assert builtin in slots

    def test_includes_plugin_keys(self):
        try:
            from hermes_cli.web_server import _get_all_aux_slots
        except ImportError:
            pytest.skip("_get_all_aux_slots not yet implemented (RED phase)")
        with _patch_plugin_aux_tasks(["custom_rag", "ops_routine"]):
            slots = _get_all_aux_slots()
        assert "custom_rag" in slots
        assert "ops_routine" in slots

    def test_deduplicates(self):
        """If a plugin registers a key that collides with a built-in, no dup."""
        try:
            from hermes_cli.web_server import _get_all_aux_slots
        except ImportError:
            pytest.skip("_get_all_aux_slots not yet implemented (RED phase)")
        from hermes_cli.web_server import _AUX_TASK_SLOTS
        with _patch_plugin_aux_tasks([_AUX_TASK_SLOTS[0]]):
            slots = _get_all_aux_slots()
        assert slots.count(_AUX_TASK_SLOTS[0]) == 1


# ---------------------------------------------------------------------------
# GET /api/model/auxiliary
# ---------------------------------------------------------------------------

class TestGetAuxiliaryModels:
    """GET /api/model/auxiliary must include plugin-registered task slots."""

    def test_plugin_slots_in_response(self):
        from hermes_cli.web_server import app

        cfg = _make_config()
        with _patch_config_load(cfg), _patch_plugin_aux_tasks(["custom_rag"]):
            client = TestClient(app)
            resp = client.get("/api/model/auxiliary")
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        task_names = [t["task"] for t in data["tasks"]]
        assert "custom_rag" in task_names, (
            f"Plugin slot 'custom_rag' missing from GET response. "
            f"Got: {task_names}"
        )

    def test_plugin_slot_config_returned(self):
        """If user has configured a plugin slot, its values appear in GET."""
        from hermes_cli.web_server import app

        cfg = _make_config(
            plugins_aux={"custom_rag": {"provider": "openai", "model": "gpt-5"}}
        )
        with _patch_config_load(cfg), _patch_plugin_aux_tasks(["custom_rag"]):
            client = TestClient(app)
            resp = client.get("/api/model/auxiliary")
        assert resp.status_code == 200
        data = resp.json()
        rag_task = next(t for t in data["tasks"] if t["task"] == "custom_rag")
        assert rag_task["provider"] == "openai"
        assert rag_task["model"] == "gpt-5"


# ---------------------------------------------------------------------------
# POST /api/model/set — plugin task accepted
# ---------------------------------------------------------------------------

class TestSetModelAssignmentPluginSlot:
    """POST /api/model/set must accept plugin-registered task names."""

    def test_assign_to_plugin_slot(self):
        from hermes_cli.web_server import app

        cfg = _make_config()
        save_patcher, saved = _patch_config_save()
        with _patch_config_load(cfg), save_patcher, _patch_plugin_aux_tasks(["custom_rag"]):
            client = TestClient(app)
            resp = client.post("/api/model/set", json={
                "scope": "auxiliary",
                "task": "custom_rag",
                "provider": "openai",
                "model": "gpt-5",
            })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["ok"] is True
        assert "custom_rag" in data["tasks"]

    def test_reject_unknown_still_works(self):
        """Unknown task names (not built-in, not plugin) must still be rejected."""
        from hermes_cli.web_server import app

        cfg = _make_config()
        with _patch_config_load(cfg), _patch_plugin_aux_tasks([]):
            client = TestClient(app)
            resp = client.post("/api/model/set", json={
                "scope": "auxiliary",
                "task": "nonexistent_task",
                "provider": "openai",
                "model": "gpt-5",
            })
        assert resp.status_code == 400
        assert "unknown auxiliary task" in resp.text.lower()

    def test_assign_all_includes_plugin_slot(self):
        """Empty task broadcasts model assignment to built-ins and plugins."""
        from hermes_cli.web_server import app

        cfg = _make_config()
        save_patcher, saved = _patch_config_save()
        with _patch_config_load(cfg), save_patcher, _patch_plugin_aux_tasks(["custom_rag"]):
            client = TestClient(app)
            resp = client.post("/api/model/set", json={
                "scope": "auxiliary",
                "task": "",
                "provider": "openai",
                "model": "gpt-5",
            })

        assert resp.status_code == 200
        saved_cfg = saved[0]
        rag_cfg = saved_cfg["auxiliary"]["custom_rag"]
        assert rag_cfg["provider"] == "openai"
        assert rag_cfg["model"] == "gpt-5"


# ---------------------------------------------------------------------------
# POST /api/model/set — __reset__ includes plugin slots
# ---------------------------------------------------------------------------

class TestResetIncludesPluginSlots:
    """The __reset__ action must reset plugin slots, not just built-in ones."""

    def test_reset_clears_plugin_slot(self):
        from hermes_cli.web_server import app

        cfg = _make_config(
            plugins_aux={"custom_rag": {"provider": "openai", "model": "gpt-5"}}
        )
        save_patcher, saved = _patch_config_save()
        with _patch_config_load(cfg), save_patcher, _patch_plugin_aux_tasks(["custom_rag"]):
            client = TestClient(app)
            resp = client.post("/api/model/set", json={
                "scope": "auxiliary",
                "task": "__reset__",
                "provider": "",
                "model": "",
            })
        assert resp.status_code == 200
        assert resp.json()["reset"] is True
        # Verify the plugin slot was reset in the saved config
        saved_cfg = saved[0]
        rag_cfg = saved_cfg["auxiliary"]["custom_rag"]
        assert rag_cfg["provider"] == "auto"
        assert rag_cfg["model"] == ""
