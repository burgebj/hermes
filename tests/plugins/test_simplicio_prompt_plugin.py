from __future__ import annotations

import shutil
from pathlib import Path

import yaml


def _clear_flags(monkeypatch):
    monkeypatch.delenv("SIMPLICIO_PROMPT", raising=False)
    monkeypatch.delenv("HERMES_SIMPLICIO_PROMPT", raising=False)


def test_simplicio_prompt_disabled_by_default(monkeypatch):
    _clear_flags(monkeypatch)

    from plugins import simplicio_prompt as sp

    assert sp.build_context(config={}) is None


def test_simplicio_prompt_enabled_by_env(monkeypatch):
    _clear_flags(monkeypatch)
    monkeypatch.setenv("SIMPLICIO_PROMPT", "true")

    from plugins import simplicio_prompt as sp

    payload = sp.build_context(config={})

    assert payload is not None
    assert payload["context"].startswith("[SIMPLICIO_PROMPT]")
    assert "Treat every\nprompt/message as eligible" in payload["context"]
    assert "Bundled local snapshot" in payload["context"]
    assert "Do not fetch or consult an external GitHub repository" in payload["context"]
    assert "[Proximo Yool a executar]" in payload["context"]
    assert (
        "https://github.com/wesleysimplicio/simplicio-prompt" not in payload["context"]
    )


def test_simplicio_prompt_enabled_by_alias_env(monkeypatch):
    _clear_flags(monkeypatch)
    monkeypatch.setenv("HERMES_SIMPLICIO_PROMPT", "true")

    from plugins import simplicio_prompt as sp

    assert sp.build_context(config={}) is not None


def test_simplicio_prompt_pre_llm_hook_ignores_trigger_words(monkeypatch):
    _clear_flags(monkeypatch)
    monkeypatch.setenv("SIMPLICIO_PROMPT", "true")

    from plugins import simplicio_prompt as sp

    payload = sp._pre_llm_call(
        messages=[
            {
                "role": "user",
                "content": "Can you explain the dashboard layout and summarize the tradeoffs?",
            }
        ]
    )

    assert payload is not None
    assert "Trigger rule: this runtime is ALWAYS-ON" in payload["context"]
    assert "Treat ANY user input as the task X" in payload["context"]
    assert "You do NOT need a keyword such as" in payload["context"]
    assert "`Implement`, `Fix`" in payload["context"]
    assert "`Build`, `Refactor`" in payload["context"]


def test_simplicio_prompt_pre_llm_hook_accepts_varied_prompt_shapes(monkeypatch):
    _clear_flags(monkeypatch)
    monkeypatch.setenv("SIMPLICIO_PROMPT", "true")

    from plugins import simplicio_prompt as sp

    messages = [
        "layout",
        "/sendsprint",
        "Fix the checkout view",
        "```diff\n- old\n+ new\n```",
        "   ",
    ]

    for content in messages:
        payload = sp._pre_llm_call(messages=[{"role": "user", "content": content}])
        assert payload is not None
        assert "no keyword required" in payload["context"]


def test_simplicio_prompt_enabled_by_config(monkeypatch):
    _clear_flags(monkeypatch)

    from plugins import simplicio_prompt as sp

    payload = sp.build_context(config={"simplicio_prompt": {"enabled": True}})

    assert payload is not None
    assert "tuple-space" in payload["context"]
    assert "For every user input X" in payload["context"]


def test_simplicio_prompt_disabled_config_wins_over_env(monkeypatch):
    _clear_flags(monkeypatch)
    monkeypatch.setenv("SIMPLICIO_PROMPT", "true")

    from plugins import simplicio_prompt as sp

    payload = sp.build_context(config={"plugins": {"disabled": ["SIMPLICIO_PROMPT"]}})

    assert payload is None


def test_simplicio_prompt_vendored_runtime_files_exist():
    from plugins import simplicio_prompt as sp

    expected = [
        "README.md",
        "YOOL_TUPLE_HAMT.md",
        "kernel/yool_tuple_kernel.py",
        "guardrails/cpu_throttle.py",
        "guardrails/disk_gc.py",
        "examples/python/receipts.py",
        "scripts/build_hamt.py",
        "prompts/agent-runtime-execution-prompt.md",
    ]

    for relative_path in expected:
        assert (sp.VENDORED_ROOT / relative_path).is_file()


def test_simplicio_prompt_enabled_by_plugin_allow_list(monkeypatch):
    _clear_flags(monkeypatch)

    from plugins import simplicio_prompt as sp

    payload = sp.build_context(config={"plugins": {"enabled": ["SIMPLICIO_PROMPT"]}})

    assert payload is not None
    assert "provider-ban risk" in payload["context"]


def test_simplicio_prompt_registers_pre_llm_hook():
    from plugins import simplicio_prompt as sp

    class FakeContext:
        def __init__(self):
            self.hooks = []

        def register_hook(self, name, callback):
            self.hooks.append((name, callback))

    ctx = FakeContext()
    sp.register(ctx)

    assert len(ctx.hooks) == 1
    assert ctx.hooks[0][0] == "pre_llm_call"
    assert ctx.hooks[0][1] is sp._pre_llm_call


def _write_hook_plugin(root: Path, *, manifest: dict) -> None:
    plugin_dir = root / manifest["name"]
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    (plugin_dir / "__init__.py").write_text(
        "def register(ctx):\n"
        "    ctx.register_hook('pre_llm_call', lambda **kw: {'context': 'auto'})\n",
        encoding="utf-8",
    )


def _copy_real_simplicio_plugin(root: Path) -> None:
    from plugins import simplicio_prompt as sp

    shutil.copytree(
        sp.PLUGIN_DIR,
        root / "SIMPLICIO_PROMPT",
        ignore=shutil.ignore_patterns("__pycache__"),
    )


def test_real_simplicio_prompt_manifest_auto_enables_from_alias_env(
    tmp_path, monkeypatch
):
    from hermes_cli.plugins import PluginManager

    bundled = tmp_path / "bundled"
    bundled.mkdir()
    _copy_real_simplicio_plugin(bundled)
    hermes_home = tmp_path / "home"
    hermes_home.mkdir()
    monkeypatch.setenv("HERMES_BUNDLED_PLUGINS", str(bundled))
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    monkeypatch.setenv("HERMES_SIMPLICIO_PROMPT", "true")

    manager = PluginManager()
    manager.discover_and_load()

    loaded = manager._plugins["SIMPLICIO_PROMPT"]
    assert loaded.enabled is True
    assert "pre_llm_call" in loaded.hooks_registered


def test_real_simplicio_prompt_manifest_disabled_wins(tmp_path, monkeypatch):
    from hermes_cli.plugins import PluginManager

    bundled = tmp_path / "bundled"
    bundled.mkdir()
    _copy_real_simplicio_plugin(bundled)
    hermes_home = tmp_path / "home"
    hermes_home.mkdir()
    (hermes_home / "config.yaml").write_text(
        yaml.safe_dump({"plugins": {"disabled": ["SIMPLICIO_PROMPT"]}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_BUNDLED_PLUGINS", str(bundled))
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    monkeypatch.setenv("SIMPLICIO_PROMPT", "true")

    manager = PluginManager()
    manager.discover_and_load()

    loaded = manager._plugins["SIMPLICIO_PROMPT"]
    assert loaded.enabled is False
    assert loaded.error == "disabled via config"


def test_bundled_plugin_auto_enables_from_manifest_env_gate(tmp_path, monkeypatch):
    from hermes_cli.plugins import PluginManager

    bundled = tmp_path / "bundled"
    _write_hook_plugin(
        bundled,
        manifest={
            "name": "auto_prompt_env",
            "hooks": ["pre_llm_call"],
            "auto_enable_env": ["AUTO_PROMPT_TEST"],
        },
    )
    hermes_home = tmp_path / "home"
    hermes_home.mkdir()
    monkeypatch.setenv("HERMES_BUNDLED_PLUGINS", str(bundled))
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    monkeypatch.setenv("AUTO_PROMPT_TEST", "true")

    manager = PluginManager()
    manager.discover_and_load()

    loaded = manager._plugins["auto_prompt_env"]
    assert loaded.enabled is True
    assert "pre_llm_call" in loaded.hooks_registered


def test_bundled_plugin_auto_enables_from_manifest_config_gate(tmp_path, monkeypatch):
    from hermes_cli.plugins import PluginManager

    bundled = tmp_path / "bundled"
    _write_hook_plugin(
        bundled,
        manifest={
            "name": "auto_prompt_config",
            "hooks": ["pre_llm_call"],
            "auto_enable_config": ["auto_prompt.enabled"],
        },
    )
    hermes_home = tmp_path / "home"
    hermes_home.mkdir()
    (hermes_home / "config.yaml").write_text(
        yaml.safe_dump({"auto_prompt": {"enabled": True}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_BUNDLED_PLUGINS", str(bundled))
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    manager = PluginManager()
    manager.discover_and_load()

    loaded = manager._plugins["auto_prompt_config"]
    assert loaded.enabled is True
    assert "pre_llm_call" in loaded.hooks_registered
