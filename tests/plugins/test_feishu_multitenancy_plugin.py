"""Tests for the bundled Feishu multitenancy plugin."""

from __future__ import annotations

import json
import asyncio
import contextvars
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType, SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_KEY = "platforms/feishu-multitenancy"
PLUGIN_DIR = REPO_ROOT / "plugins" / "platforms" / "feishu-multitenancy"


def _forget_multitenancy_modules() -> None:
    for name in list(sys.modules):
        if (
            name == "hermes_multitenancy"
            or name.startswith("hermes_multitenancy.")
            or name.startswith("hermes_plugins.platforms__feishu_multitenancy")
        ):
            sys.modules.pop(name, None)


def _install_fake_feishu_oapi(monkeypatch) -> None:
    current_sender_open_id = contextvars.ContextVar("current_sender_open_id", default=None)

    @contextmanager
    def sender_open_id_scope(value):
        token = current_sender_open_id.set(value)
        try:
            yield
        finally:
            current_sender_open_id.reset(token)

    fake_feishu_oapi = SimpleNamespace(
        current_sender_open_id=current_sender_open_id,
        sender_open_id_scope=sender_open_id_scope,
        FEISHU_UAT_PATH=None,
        FEISHU_UAT_DIR=None,
    )
    try:
        import tools as tools_mod
    except Exception:
        tools_mod = ModuleType("tools")
    tools_mod.feishu_oapi_client = fake_feishu_oapi
    monkeypatch.setitem(sys.modules, "tools", tools_mod)
    monkeypatch.setitem(sys.modules, "tools.feishu_oapi_client", fake_feishu_oapi)


def _install_fake_approval(monkeypatch):
    registered: dict[str, object] = {}
    resolved: list[tuple[str, str]] = []
    current_session = contextvars.ContextVar("approval_session", default="")

    def set_current_session_key(session_key: str):
        return current_session.set(session_key)

    def reset_current_session_key(token):
        current_session.reset(token)

    def register_gateway_notify(session_key: str, cb):
        registered[session_key] = cb

    def unregister_gateway_notify(session_key: str):
        registered.pop(session_key, None)

    def resolve_gateway_approval(session_key: str, choice: str, resolve_all=False):
        resolved.append((session_key, choice))
        return 1

    fake_approval = SimpleNamespace(
        set_current_session_key=set_current_session_key,
        reset_current_session_key=reset_current_session_key,
        register_gateway_notify=register_gateway_notify,
        unregister_gateway_notify=unregister_gateway_notify,
        resolve_gateway_approval=resolve_gateway_approval,
    )
    try:
        import tools as tools_mod
    except Exception:
        tools_mod = ModuleType("tools")
    tools_mod.approval = fake_approval
    monkeypatch.setitem(sys.modules, "tools", tools_mod)
    monkeypatch.setitem(sys.modules, "tools.approval", fake_approval)
    return registered, resolved


@contextmanager
def _bundled_plugin_path():
    _forget_multitenancy_modules()
    sys.path.insert(0, str(PLUGIN_DIR))
    try:
        yield
    finally:
        try:
            sys.path.remove(str(PLUGIN_DIR))
        except ValueError:
            pass
        _forget_multitenancy_modules()


def test_bundled_plugin_loads_when_enabled(tmp_path, monkeypatch):
    hermes_home = tmp_path / "hermes-home"
    hermes_home.mkdir()
    (hermes_home / "config.yaml").write_text(
        "plugins:\n"
        "  enabled:\n"
        f"    - {PLUGIN_KEY}\n"
    )
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    from hermes_cli.plugins import PluginManager

    _forget_multitenancy_modules()
    manager = PluginManager()
    manager.discover_and_load(force=True)

    loaded = manager._plugins[PLUGIN_KEY]
    assert loaded.enabled
    assert loaded.error is None
    assert "pre_gateway_dispatch" in loaded.hooks_registered
    assert any(
        getattr(callback, "__name__", "") == "on_pre_gateway_dispatch"
        for callback in manager._hooks["pre_gateway_dispatch"]
    )


def test_route_sync_wrapper_applies_users(tmp_path):
    users_json = tmp_path / "users.json"
    db_path = tmp_path / "multitenancy.db"
    users_json.write_text(
        json.dumps(
            [
                {
                    "user_id": "tenant-a",
                    "profile_name": "alice",
                    "open_id": "ou_test_alice",
                    "union_id": "on_test_alice",
                },
                {
                    "user_id": "tenant-b",
                    "profile_name": "bob",
                    "open_id": "ou_test_bob",
                },
            ]
        )
    )

    result = subprocess.run(
        [
            sys.executable,
            str(PLUGIN_DIR / "sync.py"),
            "apply",
            str(users_json),
            "--db",
            str(db_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert json.loads(result.stdout) == {
        "upserted": 2,
        "soft_deleted": 0,
        "kept": 0,
    }

    with _bundled_plugin_path():
        from hermes_multitenancy.routing import RoutingTable

        table = RoutingTable(db_path)
        try:
            row = table.lookup_by_open_id("ou_test_alice")
            assert row is not None
            assert row.profile_name == "alice"
            assert row.union_id == "on_test_alice"
        finally:
            table.close()


def test_router_prefers_feishu_open_id_from_raw_event():
    with _bundled_plugin_path():
        from hermes_multitenancy.router import _resolve_sender_for_routing

        event = SimpleNamespace(
            source=SimpleNamespace(user_id="tenant-local-id", user_id_alt="on_union"),
            raw={
                "event": {
                    "sender": {
                        "sender_id": {
                            "open_id": "ou_real_sender",
                            "union_id": "on_union",
                        }
                    }
                }
            },
        )

        assert _resolve_sender_for_routing(event) == "ou_real_sender"


def test_bundled_history_key_uses_sender_not_shared_alt(tmp_path):
    with _bundled_plugin_path():
        from hermes_multitenancy.router import _history_key

        assert _history_key("coder", "ou_a", "shared_alt") == ("coder", "ou_a")
        assert _history_key("coder", "ou_a", "shared_alt") != _history_key(
            "coder",
            "ou_b",
            "shared_alt",
        )


def test_bundled_media_directives_stay_inside_profile(tmp_path):
    with _bundled_plugin_path():
        from hermes_multitenancy.router import _profile_scoped_media_response

        profile_home = tmp_path / "profiles" / "coder"
        profile_home.mkdir(parents=True)
        inside = profile_home / "cache" / "out.md"
        outside = tmp_path / "profiles" / "other" / "secret.md"
        inside.parent.mkdir()
        outside.parent.mkdir(parents=True)

        scoped = _profile_scoped_media_response(
            f"ok\nMEDIA:{inside}\nMEDIA:{outside}",
            profile_home,
        )

        assert f"MEDIA:{inside}" in scoped
        assert str(outside) not in scoped


def test_bundled_router_uses_legacy_alt_route_when_open_id_missing(tmp_path, monkeypatch):
    with _bundled_plugin_path():
        from hermes_multitenancy import router as router_mod

        db_path = tmp_path / "routing.db"
        router_mod.override_routing_table(db_path)
        table = router_mod._get_routing_table()
        table.upsert(
            user_id="legacy",
            profile_name="legacy_profile",
            open_id="on_legacy",
            union_id="on_legacy",
        )
        monkeypatch.setattr(
            router_mod,
            "_profile_name_to_home",
            lambda profile_name: tmp_path / "profiles" / profile_name,
        )

        captured: dict[str, object] = {}

        class Pool:
            async def dispatch(self, profile_name, profile_home, event):
                captured["profile_name"] = profile_name
                captured["profile_home"] = profile_home
                return "ok"

        monkeypatch.setattr(router_mod, "_get_pool", lambda: Pool())
        event = SimpleNamespace(
            text="hi",
            source=SimpleNamespace(
                platform=SimpleNamespace(value="feishu"),
                chat_id="oc_test",
                user_id="tenant-local-id",
                user_id_alt="on_legacy",
                user_name="legacy-user",
                chat_type="dm",
            ),
        )

        asyncio.run(
            router_mod.handle_async(
                event=event,
                gateway=SimpleNamespace(adapters={}),
            )
        )

        assert captured == {
            "profile_name": "legacy_profile",
            "profile_home": tmp_path / "profiles" / "legacy_profile",
        }
        assert table.lookup_by_open_id("tenant-local-id") is None
        router_mod.override_routing_table(None)


def test_bundled_router_sets_resolved_raw_event_open_id_on_agent_event(tmp_path, monkeypatch):
    with _bundled_plugin_path():
        from hermes_multitenancy import router as router_mod
        from hermes_multitenancy.runtime import add_in_memory_route, clear_in_memory_routes

        clear_in_memory_routes()
        profile_home = tmp_path / "raw-sender"
        profile_home.mkdir()
        add_in_memory_route("ou_raw_sender", profile_home)

        captured: dict[str, object] = {}

        class Pool:
            async def dispatch(self, profile_name, profile_home, event):
                captured["profile_name"] = profile_name
                captured["sender_open_id"] = getattr(event, "sender_open_id", None)
                return "ok"

        monkeypatch.setattr(router_mod, "_get_pool", lambda: Pool())
        event = SimpleNamespace(
            text="hi",
            raw_event={
                "event": {
                    "message": {
                        "sender": {
                            "sender_id": {
                                "open_id": "ou_raw_sender",
                                "union_id": "on_raw_sender",
                            }
                        }
                    }
                }
            },
            source=SimpleNamespace(
                platform=SimpleNamespace(value="feishu"),
                chat_id="oc_test",
                user_id="tenant-local-id",
                user_name="raw-user",
                chat_type="dm",
            ),
        )

        asyncio.run(
            router_mod.handle_async(
                event=event,
                gateway=SimpleNamespace(adapters={}),
            )
        )

        assert captured == {
            "profile_name": "raw-sender",
            "sender_open_id": "ou_raw_sender",
        }
        clear_in_memory_routes()


def test_auto_profile_config_does_not_invent_a_default_model():
    with _bundled_plugin_path():
        from hermes_multitenancy.router import _normalize_profile_config

        assert _normalize_profile_config({}) == {}
        assert _normalize_profile_config({"tools": ["web"]}) == {"tools": ["web"]}


def test_aiagent_toolsets_merge_explicit_feishu_entries_with_defaults():
    with _bundled_plugin_path():
        from hermes_multitenancy.agent_real import _resolve_enabled_toolsets

        seen: dict[str, object] = {}

        def fake_get_platform_tools(config, platform, *, include_default_mcp_servers=True):
            seen["platform_toolsets"] = config.get("platform_toolsets")
            seen["platform"] = platform
            seen["include_default_mcp_servers"] = include_default_mcp_servers
            return {"web", "browser", "feishu_doc"}

        config = {"platform_toolsets": {"feishu": ["feishu_drive"]}}

        assert _resolve_enabled_toolsets(
            config,
            "feishu",
            platform_tools_resolver=fake_get_platform_tools,
        ) == ["browser", "feishu_doc", "feishu_drive", "web"]
        assert seen == {
            "platform_toolsets": {},
            "platform": "feishu",
            "include_default_mcp_servers": True,
        }


def test_aiagent_toolsets_allow_explicit_mode(monkeypatch):
    with _bundled_plugin_path():
        from hermes_multitenancy.agent_real import _resolve_enabled_toolsets

        def fake_get_platform_tools(*_args, **_kwargs):
            raise AssertionError("explicit mode must not resolve platform defaults")

        monkeypatch.setenv("HERMES_MULTITENANCY_TOOLSETS_MODE", "explicit")

        assert _resolve_enabled_toolsets(
            {"platform_toolsets": {"feishu": ["feishu_drive", "web"]}},
            "feishu",
            platform_tools_resolver=fake_get_platform_tools,
        ) == ["feishu_drive", "web"]


def test_bundled_cron_jobs_bind_to_shared_gateway_home(tmp_path, monkeypatch):
    with _bundled_plugin_path():
        from hermes_multitenancy import agent_real

        profile_home = tmp_path / ".hermes" / "profiles" / "coder"
        shared_home = tmp_path / ".hermes"
        profile_home.mkdir(parents=True)
        shared_home.mkdir(exist_ok=True)

        cron_pkg = ModuleType("cron")
        cron_jobs = ModuleType("cron.jobs")
        tools_pkg = ModuleType("tools")
        cronjob_tools = ModuleType("tools.cronjob_tools")
        path_security = ModuleType("tools.path_security")
        path_security.validate_within_dir = lambda path, root: None
        cron_pkg.jobs = cron_jobs
        tools_pkg.cronjob_tools = cronjob_tools
        tools_pkg.path_security = path_security

        monkeypatch.setitem(sys.modules, "cron", cron_pkg)
        monkeypatch.setitem(sys.modules, "cron.jobs", cron_jobs)
        monkeypatch.setitem(sys.modules, "tools", tools_pkg)
        monkeypatch.setitem(sys.modules, "tools.cronjob_tools", cronjob_tools)
        monkeypatch.setitem(sys.modules, "tools.path_security", path_security)
        monkeypatch.setenv("HERMES_HOME", str(profile_home))

        agent_real._configure_cron_home(shared_home)

        assert cron_jobs.JOBS_FILE == shared_home.resolve() / "cron" / "jobs.json"
        assert cron_jobs.OUTPUT_DIR == shared_home.resolve() / "cron" / "output"
        assert os.environ["HERMES_HOME"] == str(profile_home)
        assert cronjob_tools._validate_cron_script_path("reminder.py") is None
        assert "relative to shared" in cronjob_tools._validate_cron_script_path("/tmp/reminder.py")


def test_aiagent_subprocess_payload_carries_router_messages(tmp_path):
    with _bundled_plugin_path():
        from hermes_multitenancy.agent_real import _event_to_subprocess_payload

        event = SimpleNamespace(
            text="send me the link",
            message_id="om_current",
            source=SimpleNamespace(
                platform=SimpleNamespace(value="feishu"),
                chat_id="oc_test",
                user_id="ou_test",
            ),
        )
        messages = [
            {"role": "user", "content": "create a doc"},
            {"role": "assistant", "content": "created doc doxcn123"},
            {"role": "user", "content": "send me the link"},
        ]

        payload = _event_to_subprocess_payload(event, tmp_path, messages=messages)

        assert payload["messages"] == messages


def test_bundled_stream_aiagent_subprocess_forwards_child_approval_events(monkeypatch, tmp_path):
    with _bundled_plugin_path():
        from hermes_multitenancy import agent_real

        class FakeStdin:
            def write(self, _payload):
                pass

            async def drain(self):
                pass

            def close(self):
                pass

            async def wait_closed(self):
                pass

        class FakeStdout:
            def __init__(self):
                self.lines = [
                    json.dumps({
                        "event": "approval_required",
                        "session_key": "multitenancy:feishu:coder:oc_test:ou_test",
                        "approval_id": "approval_1",
                        "command": "python -c \"print(1)\"",
                        "description": "script execution via -e/-c flag",
                        "decision_path": "/tmp/approval_1.json",
                    }).encode() + b"\n",
                    json.dumps({
                        "event": "approval_resolved",
                        "session_key": "multitenancy:feishu:coder:oc_test:ou_test",
                        "approval_id": "approval_1",
                        "choice": "once",
                    }).encode() + b"\n",
                    b'{"event": "done", "result": "ok", "error": null}\n',
                ]

            async def readline(self):
                if self.lines:
                    return self.lines.pop(0)
                return b""

        class FakeStderr:
            async def read(self):
                return b""

        class FakeProc:
            def __init__(self):
                self.stdin = FakeStdin()
                self.stdout = FakeStdout()
                self.stderr = FakeStderr()
                self.pid = 123
                self.returncode = None
                self.killed = False

            async def wait(self):
                self.returncode = 0
                return 0

            def kill(self):
                self.killed = True
                self.returncode = -9

        async def fake_create_subprocess_exec(*_args, **_kwargs):
            return FakeProc()

        monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

        async def collect_events():
            event = SimpleNamespace(
                text="hello",
                message_id="om_test",
                source=SimpleNamespace(
                    platform=SimpleNamespace(value="feishu"),
                    chat_id="oc_test",
                    user_id="ou_test",
                ),
            )
            return [
                item
                async for item in agent_real._stream_aiagent_subprocess(event, tmp_path)
            ]

        assert asyncio.run(collect_events()) == [
            ("approval_required", {
                "session_key": "multitenancy:feishu:coder:oc_test:ou_test",
                "approval_id": "approval_1",
                "command": "python -c \"print(1)\"",
                "description": "script execution via -e/-c flag",
                "decision_path": "/tmp/approval_1.json",
            }),
            ("approval_resolved", {
                "session_key": "multitenancy:feishu:coder:oc_test:ou_test",
                "approval_id": "approval_1",
                "choice": "once",
            }),
            ("done", "ok"),
        ]


def test_aiagent_session_id_is_stable_and_user_isolated(tmp_path):
    with _bundled_plugin_path():
        from hermes_multitenancy.agent_real import _resolve_aiagent_session_id

        profile_home = tmp_path / "profiles" / "coder"
        event = SimpleNamespace(
            text="hello",
            message_id="om_first",
            source=SimpleNamespace(
                platform=SimpleNamespace(value="feishu"),
                chat_id="oc_test",
                chat_type="dm",
                user_id="ou_fallback",
                message_id="om_source_first",
            ),
        )
        next_event = SimpleNamespace(
            text="next",
            message_id="om_second",
            source=SimpleNamespace(
                platform=SimpleNamespace(value="feishu"),
                chat_id="oc_test",
                chat_type="dm",
                user_id="ou_fallback",
                message_id="om_source_second",
            ),
        )

        first_session = _resolve_aiagent_session_id(event, profile_home, "ou_sender")
        next_session = _resolve_aiagent_session_id(next_event, profile_home, "ou_sender")

        assert first_session == next_session
        assert "profile:coder" in first_session
        assert "chat:oc_test" in first_session
        assert "user:ou_sender" in first_session
        assert first_session != _resolve_aiagent_session_id(
            event,
            profile_home,
            "ou_other",
        )


def test_bundled_multitenant_gateway_session_key_matches_router_shape(tmp_path):
    with _bundled_plugin_path():
        from hermes_multitenancy.agent_real import _resolve_multitenant_gateway_session_key

        profile_home = tmp_path / "profiles" / "coder"
        event = SimpleNamespace(
            text="hello",
            source=SimpleNamespace(
                platform=SimpleNamespace(value="feishu"),
                chat_id="oc_test",
                chat_type="dm",
                user_id="ou_test",
            ),
        )

        assert _resolve_multitenant_gateway_session_key(
            event,
            profile_home,
            "ou_test",
        ) == "multitenancy:feishu:coder:oc_test:ou_test"


def test_bundled_aiagent_bridges_gateway_approval(monkeypatch, tmp_path):
    with _bundled_plugin_path():
        from hermes_multitenancy import agent_real

        profile_home = tmp_path / "profiles" / "coder"
        profile_home.mkdir(parents=True)
        (profile_home / "config.yaml").write_text(
            "model:\n  default: openai/test-model\n",
            encoding="utf-8",
        )
        (profile_home / ".env").write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")
        approval_dir = tmp_path / "approval"
        monkeypatch.setenv("HERMES_MULTITENANCY_APPROVAL_DIR", str(approval_dir))
        monkeypatch.setenv("HERMES_MULTITENANCY_APPROVAL_TIMEOUT", "1")
        registered, resolved = _install_fake_approval(monkeypatch)
        _install_fake_feishu_oapi(monkeypatch)

        class FakeAgent:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def run_conversation(self, user_message, task_id):
                session_key = self.kwargs["gateway_session_key"]
                assert session_key == "multitenancy:feishu:coder:oc_test:ou_test"
                registered[session_key]({
                    "command": "python -c 'print(1)'",
                    "description": "script execution via -c flag",
                    "pattern_keys": ["script execution via -c flag"],
                })
                return {"final_response": "approved"}

            def close(self):
                pass

        events: list[dict] = []

        def sink(event, **payload):
            events.append({"event": event, **payload})
            if event == "approval_required":
                Path(payload["decision_path"]).write_text(
                    json.dumps({"choice": "once"}),
                    encoding="utf-8",
                )

        monkeypatch.setitem(sys.modules, "run_agent", SimpleNamespace(AIAgent=FakeAgent))

        source = SimpleNamespace(
            platform=SimpleNamespace(value="feishu"),
            chat_id="oc_test",
            chat_type="dm",
            user_id="ou_test",
            user_name="tester",
        )
        event = SimpleNamespace(text="hello", message_id="om_test", source=source)

        assert agent_real._run_with_aiagent(event, profile_home, event_sink=sink) == "approved"
        assert events[0]["event"] == "approval_required"
        assert events[0]["session_key"] == "multitenancy:feishu:coder:oc_test:ou_test"
        assert events[1]["event"] == "approval_resolved"
        assert events[1]["choice"] == "once"
        assert resolved == [("multitenancy:feishu:coder:oc_test:ou_test", "once")]


def test_bundled_approval_bridge_exposes_session_key_to_tool_worker_threads(monkeypatch, tmp_path):
    with _bundled_plugin_path():
        from hermes_multitenancy import agent_real

        approval_dir = tmp_path / "approval"
        monkeypatch.setenv("HERMES_MULTITENANCY_APPROVAL_DIR", str(approval_dir))
        monkeypatch.setenv("HERMES_MULTITENANCY_APPROVAL_TIMEOUT", "1")
        monkeypatch.delenv("HERMES_SESSION_KEY", raising=False)
        monkeypatch.delenv("HERMES_GATEWAY_SESSION", raising=False)
        monkeypatch.delenv("HERMES_EXEC_ASK", raising=False)
        registered, resolved = _install_fake_approval(monkeypatch)
        events: list[dict] = []

        def sink(event, **payload):
            events.append({"event": event, **payload})
            if event == "approval_required":
                Path(payload["decision_path"]).write_text(
                    json.dumps({"choice": "once"}),
                    encoding="utf-8",
                )

        cleanup = agent_real._configure_gateway_approval_bridge(
            sink,
            "multitenancy:feishu:coder:oc_test:ou_test",
        )
        try:
            worker_result: dict[str, str] = {}

            def worker_thread_tool_guard():
                session_key = os.getenv("HERMES_SESSION_KEY", "default")
                notify = registered.get(session_key)
                if notify is None:
                    worker_result["status"] = "missing"
                    return
                notify({
                    "command": "python -c 'print(1)'",
                    "description": "script execution via -c flag",
                    "pattern_keys": ["script execution via -c flag"],
                })
                worker_result["status"] = "notified"

            worker_thread_tool_guard()

            assert worker_result == {"status": "notified"}
            assert events[0]["event"] == "approval_required"
            assert resolved == [("multitenancy:feishu:coder:oc_test:ou_test", "once")]
        finally:
            cleanup()

        assert os.getenv("HERMES_SESSION_KEY") is None
        assert os.getenv("HERMES_GATEWAY_SESSION") is None
        assert os.getenv("HERMES_EXEC_ASK") is None


def test_bundled_aiagent_closes_real_agent_resources(monkeypatch, tmp_path):
    with _bundled_plugin_path():
        from hermes_multitenancy import agent_real

        profile_home = tmp_path / "profiles" / "coder"
        profile_home.mkdir(parents=True)
        (profile_home / "config.yaml").write_text(
            "model:\n  default: openai/test-model\n",
            encoding="utf-8",
        )
        (profile_home / ".env").write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")
        _install_fake_feishu_oapi(monkeypatch)
        seen = {"closed": False}

        class FakeAgent:
            def __init__(self, **kwargs):
                pass

            def run_conversation(self, user_message, task_id):
                return {"final_response": "ok"}

            def close(self):
                seen["closed"] = True

        monkeypatch.setitem(sys.modules, "run_agent", SimpleNamespace(AIAgent=FakeAgent))

        source = SimpleNamespace(
            platform=SimpleNamespace(value="feishu"),
            chat_id="oc_test",
            chat_type="dm",
            user_id="ou_test",
            user_name="tester",
        )
        event = SimpleNamespace(text="hello", message_id="om_test", source=source)

        assert agent_real._run_with_aiagent(event, profile_home) == "ok"
        assert seen["closed"] is True


def test_bundled_command_parser_uses_hermes_registry():
    with _bundled_plugin_path():
        from hermes_multitenancy.commands import parse_command

        assert parse_command("/model gpt-5") == ("model", "gpt-5")
        assert parse_command("/provider gpt-5") == ("model", "gpt-5")
        assert parse_command("/reload_mcp") == ("reload-mcp", "")
        assert parse_command("/definitely_unknown") == ("definitely_unknown", "")
        assert parse_command("/some/path") is None


def test_bundled_router_delegates_known_gateway_command(tmp_path, caplog):
    caplog.set_level("INFO")
    with _bundled_plugin_path():
        from hermes_multitenancy import router as router_mod
        from hermes_multitenancy.runtime import add_in_memory_route, clear_in_memory_routes

        clear_in_memory_routes()
        profile_home = tmp_path / "coder"
        profile_home.mkdir()
        add_in_memory_route("ou_model", profile_home)
        sends: list[str] = []

        class Adapter:
            async def send(self, _chat_id, message, *, reply_to=None, metadata=None):
                sends.append(message)

        class Gateway:
            adapters = {"feishu": Adapter()}

            def _session_key_for_source(self, _source):
                return "native-session"

            async def _handle_model_command(self, event):
                return self._session_key_for_source(event.source)

        event = SimpleNamespace(
            text="/model gpt-5",
            source=SimpleNamespace(
                platform=SimpleNamespace(value="feishu"),
                chat_id="oc_test",
                user_id="ou_model",
                user_id_alt="shared_alt",
                user_name="model-user",
                chat_type="dm",
            ),
        )

        asyncio.run(router_mod.handle_async(event=event, gateway=Gateway()))

        assert sends == ["multitenancy:feishu:coder:oc_test:ou_model"]
        assert "Hermes gateway command handled: model" in caplog.text
        clear_in_memory_routes()


def test_bundled_router_approval_prompt_and_approve_resolves(tmp_path):
    with _bundled_plugin_path():
        from hermes_multitenancy import router as router_mod

        sent: list[tuple[str, str]] = []
        decision_path = tmp_path / "approval-decision.json"

        class Adapter:
            async def send(self, chat_id, message, *, reply_to=None, metadata=None):
                sent.append((chat_id, message))

        adapter = Adapter()
        payload = {
            "approval_id": "approval-1",
            "session_key": "multitenancy:feishu:coder:oc_test:ou_test",
            "command": "python -c 'print(1)'",
            "description": "script execution via -c flag",
            "decision_path": str(decision_path),
        }

        asyncio.run(router_mod._handle_child_approval_required(adapter, "oc_test", payload))

        assert sent
        assert "requires approval" in sent[0][1]
        assert "/approve" in sent[0][1]

        event = SimpleNamespace(
            text="/approve",
            source=SimpleNamespace(
                platform=SimpleNamespace(value="feishu"),
                chat_id="oc_test",
                user_id="ou_test",
                user_name="tester",
                chat_type="dm",
            ),
            get_command_args=lambda: "",
        )
        gateway = SimpleNamespace(adapters={"feishu": adapter}, config={})

        asyncio.run(
            router_mod._handle_command(
                ("approve", ""),
                "ou_test",
                None,
                "coder",
                tmp_path,
                "oc_test",
                gateway,
                event,
            )
        )

        assert json.loads(decision_path.read_text(encoding="utf-8")) == {"choice": "once"}
        assert "approved" in sent[-1][1].lower()


def test_bundled_concurrent_gateway_commands_keep_profile_context(tmp_path):
    with _bundled_plugin_path():
        from hermes_multitenancy import router as router_mod
        from hermes_multitenancy.runtime import add_in_memory_route, clear_in_memory_routes

        clear_in_memory_routes()
        profile_a = tmp_path / "alice"
        profile_b = tmp_path / "bob"
        profile_a.mkdir()
        profile_b.mkdir()
        add_in_memory_route("ou_cmd_a", profile_a)
        add_in_memory_route("ou_cmd_b", profile_b)

        sends: list[tuple[str, str]] = []
        observations: list[tuple[str, str | None, str]] = []

        class Adapter:
            async def send(self, chat_id, message, *, reply_to=None, metadata=None):
                sends.append((chat_id, message))

        class Gateway:
            adapters = {"feishu": Adapter()}

            def _session_key_for_source(self, _source):
                return "native-session"

            async def _handle_model_command(self, event):
                source = event.source
                observations.append(
                    (
                        source.user_id,
                        os.environ.get("HERMES_HOME"),
                        self._session_key_for_source(source),
                    )
                )
                await asyncio.sleep(0.01)
                observations.append(
                    (
                        source.user_id,
                        os.environ.get("HERMES_HOME"),
                        self._session_key_for_source(source),
                    )
                )
                return os.environ.get("HERMES_HOME")

        async def run_both():
            gateway = Gateway()
            await asyncio.gather(
                router_mod.handle_async(
                    event=SimpleNamespace(
                        text="/model gpt-5",
                        source=SimpleNamespace(
                            platform=SimpleNamespace(value="feishu"),
                            chat_id="oc_a",
                            user_id="ou_cmd_a",
                            user_name="a",
                            chat_type="dm",
                        ),
                    ),
                    gateway=gateway,
                ),
                router_mod.handle_async(
                    event=SimpleNamespace(
                        text="/model gpt-5",
                        source=SimpleNamespace(
                            platform=SimpleNamespace(value="feishu"),
                            chat_id="oc_b",
                            user_id="ou_cmd_b",
                            user_name="b",
                            chat_type="dm",
                        ),
                    ),
                    gateway=gateway,
                ),
            )

        asyncio.run(run_both())

        expected_home = {"ou_cmd_a": str(profile_a), "ou_cmd_b": str(profile_b)}
        expected_key = {
            "ou_cmd_a": "multitenancy:feishu:alice:oc_a:ou_cmd_a",
            "ou_cmd_b": "multitenancy:feishu:bob:oc_b:ou_cmd_b",
        }
        assert sorted(message for _chat, message in sends) == sorted(expected_home.values())
        for user_id, home, session_key in observations:
            assert home == expected_home[user_id]
            assert session_key == expected_key[user_id]
        clear_in_memory_routes()


def test_bundled_router_rejects_unknown_slash_without_agent(tmp_path, caplog):
    caplog.set_level("INFO")
    with _bundled_plugin_path():
        from hermes_multitenancy import router as router_mod
        from hermes_multitenancy.runtime import clear_in_memory_routes

        clear_in_memory_routes()
        sends: list[str] = []

        class Adapter:
            async def send(self, _chat_id, message, *, reply_to=None, metadata=None):
                sends.append(message)

        event = SimpleNamespace(
            text="/unknown_control",
            source=SimpleNamespace(
                platform=SimpleNamespace(value="feishu"),
                chat_id="oc_test",
                user_id="ou_unknown",
                user_name="unknown-user",
                chat_type="dm",
            ),
        )

        asyncio.run(
            router_mod.handle_async(
                event=event,
                gateway=SimpleNamespace(adapters={"feishu": Adapter()}),
            )
        )

        assert sends == [
            "Unknown command `/unknown_control`. Type /commands to see what's available, "
            "or resend without the leading slash to send as a regular message."
        ]
        assert "Unknown command `/unknown_control`" in caplog.text


def test_bundled_router_rewrites_skill_slash_into_agent_prompt(tmp_path, monkeypatch, caplog):
    caplog.set_level("INFO")
    with _bundled_plugin_path():
        from hermes_multitenancy import router as router_mod
        from hermes_multitenancy.runtime import add_in_memory_route, clear_in_memory_routes

        clear_in_memory_routes()
        profile_home = tmp_path / "coder"
        profile_home.mkdir()
        add_in_memory_route("ou_skill", profile_home)

        fake_skill_commands = SimpleNamespace(
            get_skill_commands=lambda: {"/demo-skill": {"name": "demo-skill"}},
            resolve_skill_command_key=lambda command: "/demo-skill"
            if command.replace("_", "-") == "demo-skill"
            else None,
            build_skill_invocation_message=lambda cmd_key, user_instruction, task_id=None: (
                f"[skill:{cmd_key} task:{task_id}] {user_instruction}"
            ),
        )
        fake_skill_utils = SimpleNamespace(get_disabled_skill_names=lambda platform=None: set())
        monkeypatch.setitem(sys.modules, "agent", ModuleType("agent"))
        monkeypatch.setitem(sys.modules, "agent.skill_commands", fake_skill_commands)
        monkeypatch.setitem(sys.modules, "agent.skill_utils", fake_skill_utils)

        seen: dict[str, object] = {}

        class Pool:
            async def dispatch(self, profile_name, home, event):
                seen["profile_name"] = profile_name
                seen["home"] = home
                seen["text"] = event.text
                return "agent ok"

        monkeypatch.setattr(router_mod, "_get_pool", lambda: Pool())

        sends: list[str] = []

        class Adapter:
            async def send_typing(self, _chat_id):
                pass

            async def send(self, _chat_id, message, *, reply_to=None, metadata=None):
                sends.append(message)

        event = SimpleNamespace(
            text="/demo-skill write docs",
            source=SimpleNamespace(
                platform=SimpleNamespace(value="feishu"),
                chat_id="oc_test",
                user_id="ou_skill",
                user_name="skill-user",
                chat_type="dm",
            ),
        )

        asyncio.run(
            router_mod.handle_async(
                event=event,
                gateway=SimpleNamespace(adapters={"feishu": Adapter()}),
            )
        )

        assert seen == {
            "profile_name": "coder",
            "home": profile_home,
            "text": "[skill:/demo-skill task:multitenancy:feishu:coder:oc_test:ou_skill] write docs",
        }
        assert sends == ["agent ok"]
        assert "Hermes skill slash invocation" in caplog.text
        clear_in_memory_routes()


def test_bundled_router_delegates_plugin_slash_command(tmp_path, monkeypatch, caplog):
    caplog.set_level("INFO")
    with _bundled_plugin_path():
        from hermes_multitenancy import router as router_mod
        from hermes_multitenancy.runtime import add_in_memory_route, clear_in_memory_routes

        clear_in_memory_routes()
        add_in_memory_route("ou_plugin", tmp_path)

        called: dict[str, str] = {}

        async def plugin_handler(args):
            called["args"] = args
            called["hermes_home"] = os.environ.get("HERMES_HOME")
            return f"plugin handled {args}"

        fake_plugins = SimpleNamespace(
            get_plugin_command_handler=lambda name: plugin_handler
            if name == "demo-plugin"
            else None
        )
        monkeypatch.setitem(sys.modules, "hermes_cli.plugins", fake_plugins)

        class PoolShouldNotRun:
            async def dispatch(self, *args, **kwargs):
                raise AssertionError("plugin slash command leaked into AIAgent dispatch")

        monkeypatch.setattr(router_mod, "_get_pool", lambda: PoolShouldNotRun())

        sends: list[str] = []

        class Adapter:
            async def send(self, _chat_id, message, *, reply_to=None, metadata=None):
                sends.append(message)

        event = SimpleNamespace(
            text="/demo_plugin hi there",
            source=SimpleNamespace(
                platform=SimpleNamespace(value="feishu"),
                chat_id="oc_test",
                user_id="ou_plugin",
                user_name="plugin-user",
                chat_type="dm",
            ),
        )

        asyncio.run(
            router_mod.handle_async(
                event=event,
                gateway=SimpleNamespace(adapters={"feishu": Adapter()}),
            )
        )

        assert called["args"] == "hi there"
        assert called["hermes_home"] == str(tmp_path)
        assert sends == ["plugin handled hi there"]
        assert "Hermes plugin slash handler: demo-plugin" in caplog.text
        clear_in_memory_routes()


def test_bundled_router_handles_quick_command_alias(tmp_path, monkeypatch, caplog):
    caplog.set_level("INFO")
    with _bundled_plugin_path():
        from hermes_multitenancy import router as router_mod
        from hermes_multitenancy.runtime import add_in_memory_route, clear_in_memory_routes

        clear_in_memory_routes()
        add_in_memory_route("ou_quick_alias", tmp_path)

        class PoolShouldNotRun:
            async def dispatch(self, *args, **kwargs):
                raise AssertionError("quick-command alias leaked into AIAgent dispatch")

        monkeypatch.setattr(router_mod, "_get_pool", lambda: PoolShouldNotRun())

        sends: list[str] = []

        class Adapter:
            async def send(self, _chat_id, message, *, reply_to=None, metadata=None):
                sends.append(message)

        class Gateway:
            adapters = {"feishu": Adapter()}
            config = {"quick_commands": {"mini": {"type": "alias", "target": "/model glm-5.1"}}}

            async def _handle_model_command(self, event):
                return f"model handler saw: {event.text}"

        event = SimpleNamespace(
            text="/mini high",
            source=SimpleNamespace(
                platform=SimpleNamespace(value="feishu"),
                chat_id="oc_test",
                user_id="ou_quick_alias",
                user_name="quick-user",
                chat_type="dm",
            ),
        )

        asyncio.run(router_mod.handle_async(event=event, gateway=Gateway()))

        assert sends == ["model handler saw: /model glm-5.1 high"]
        assert "Hermes quick command alias" in caplog.text
        clear_in_memory_routes()


def test_bundled_router_disables_quick_command_exec_by_default(tmp_path, monkeypatch):
    with _bundled_plugin_path():
        from hermes_multitenancy import router as router_mod
        from hermes_multitenancy.runtime import add_in_memory_route, clear_in_memory_routes

        clear_in_memory_routes()
        add_in_memory_route("ou_quick_exec_denied", tmp_path)

        class PoolShouldNotRun:
            async def dispatch(self, *args, **kwargs):
                raise AssertionError("quick-command exec leaked into AIAgent dispatch")

        monkeypatch.setattr(router_mod, "_get_pool", lambda: PoolShouldNotRun())

        sends: list[str] = []

        class Adapter:
            async def send(self, _chat_id, message, *, reply_to=None, metadata=None):
                sends.append(message)

        event = SimpleNamespace(
            text="/ping",
            source=SimpleNamespace(
                platform=SimpleNamespace(value="feishu"),
                chat_id="oc_test",
                user_id="ou_quick_exec_denied",
                user_name="quick-user",
                chat_type="dm",
            ),
        )
        gateway = SimpleNamespace(
            adapters={"feishu": Adapter()},
            config={"quick_commands": {"ping": {"type": "exec", "command": "printf quick-ok"}}},
        )

        asyncio.run(router_mod.handle_async(event=event, gateway=gateway))

        assert sends == [
            "Quick command '/ping' exec is disabled for Feishu multitenancy. "
            "Enable only after profile sandboxing is in place."
        ]
        clear_in_memory_routes()


def test_bundled_router_handles_enabled_quick_command_exec_in_profile_env(tmp_path, monkeypatch, caplog):
    caplog.set_level("INFO")
    with _bundled_plugin_path():
        from hermes_multitenancy import router as router_mod
        from hermes_multitenancy.runtime import add_in_memory_route, clear_in_memory_routes

        clear_in_memory_routes()
        profile_home = tmp_path / "quick-profile"
        profile_home.mkdir()
        add_in_memory_route("ou_quick_exec", profile_home)

        class PoolShouldNotRun:
            async def dispatch(self, *args, **kwargs):
                raise AssertionError("quick-command exec leaked into AIAgent dispatch")

        monkeypatch.setattr(router_mod, "_get_pool", lambda: PoolShouldNotRun())

        sends: list[str] = []

        class Adapter:
            async def send(self, _chat_id, message, *, reply_to=None, metadata=None):
                sends.append(message)

        event = SimpleNamespace(
            text="/ping",
            source=SimpleNamespace(
                platform=SimpleNamespace(value="feishu"),
                chat_id="oc_test",
                user_id="ou_quick_exec",
                user_name="quick-user",
                chat_type="dm",
            ),
        )
        gateway = SimpleNamespace(
            adapters={"feishu": Adapter()},
            config={
                "multitenancy": {"allow_quick_exec": True},
                "quick_commands": {"ping": {"type": "exec", "command": "printf \"$HERMES_HOME\""}},
            },
        )

        asyncio.run(router_mod.handle_async(event=event, gateway=gateway))

        assert sends == [str(profile_home)]
        assert "Hermes quick command exec" in caplog.text
        clear_in_memory_routes()


def test_processing_outcome_fallback_without_gateway_package(monkeypatch):
    with _bundled_plugin_path():
        from hermes_multitenancy.router import _processing_outcome

        monkeypatch.delitem(sys.modules, "gateway.platforms.base", raising=False)

        assert str(_processing_outcome(failed=False)) == "ProcessingOutcome.SUCCESS"
        assert str(_processing_outcome(failed=True)) == "ProcessingOutcome.FAILURE"
