"""Tests for the prometheus_avatar plugin.

Covers registration contract (3 tools with correct names, toolset, schemas)
and each stub handler's deterministic output.

These tests do not touch the global ``tools.registry`` singleton. They use a
lightweight ``_MockContext`` that records ``register_tool`` calls so the tests
stay hermetic and never conflict with other plugin or tool tests.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# The plugin lives outside the standard test path. Add the repo root to
# sys.path so ``from plugins.prometheus_avatar import register`` resolves.
_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from plugins.prometheus_avatar import (  # noqa: E402
    TOOLSET,
    __version__,
    _DEMO_CATALOG,
    _describe_handler,
    _list_assets_handler,
    _status_handler,
    register,
)


# ===========================================================================
# Fixtures
# ===========================================================================


class _MockContext:
    """Minimal stand-in for ``hermes_cli.plugins.PluginContext``.

    Records every ``register_tool`` call so tests can assert on the
    registration contract without mutating global state.
    """

    def __init__(self) -> None:
        self.tools: list[dict] = []

    def register_tool(
        self,
        *,
        name: str,
        toolset: str,
        schema: dict,
        handler,
        check_fn=None,
        requires_env=None,
        is_async: bool = False,
        description: str = "",
        emoji: str = "",
    ) -> None:
        self.tools.append({
            "name": name,
            "toolset": toolset,
            "schema": schema,
            "handler": handler,
            "check_fn": check_fn,
            "requires_env": requires_env,
            "is_async": is_async,
            "description": description,
            "emoji": emoji,
        })


@pytest.fixture
def ctx() -> _MockContext:
    return _MockContext()


# ===========================================================================
# Registration contract
# ===========================================================================


class TestRegistration:
    def test_register_returns_none(self, ctx: _MockContext) -> None:
        assert register(ctx) is None

    def test_register_adds_three_tools(self, ctx: _MockContext) -> None:
        register(ctx)
        assert len(ctx.tools) == 3

    def test_tool_names(self, ctx: _MockContext) -> None:
        register(ctx)
        names = {t["name"] for t in ctx.tools}
        assert names == {"avatar_list_assets", "avatar_describe", "avatar_status"}

    def test_all_tools_share_toolset(self, ctx: _MockContext) -> None:
        register(ctx)
        toolsets = {t["toolset"] for t in ctx.tools}
        assert toolsets == {TOOLSET}
        assert TOOLSET == "avatar"

    def test_all_tools_are_sync(self, ctx: _MockContext) -> None:
        register(ctx)
        assert all(t["is_async"] is False for t in ctx.tools)

    def test_schemas_are_openai_format(self, ctx: _MockContext) -> None:
        register(ctx)
        for t in ctx.tools:
            schema = t["schema"]
            assert "description" in schema
            assert "parameters" in schema
            assert schema["parameters"]["type"] == "object"

    def test_list_assets_requires_category(self, ctx: _MockContext) -> None:
        register(ctx)
        tool = next(t for t in ctx.tools if t["name"] == "avatar_list_assets")
        params = tool["schema"]["parameters"]
        assert params["required"] == ["category"]
        assert set(params["properties"]["category"]["enum"]) == {
            "skins", "voices", "personas", "effects"
        }

    def test_describe_requires_asset_id(self, ctx: _MockContext) -> None:
        register(ctx)
        tool = next(t for t in ctx.tools if t["name"] == "avatar_describe")
        assert tool["schema"]["parameters"]["required"] == ["asset_id"]

    def test_status_has_no_required_args(self, ctx: _MockContext) -> None:
        register(ctx)
        tool = next(t for t in ctx.tools if t["name"] == "avatar_status")
        params = tool["schema"]["parameters"]
        assert params.get("required", []) == []


# ===========================================================================
# Handler behavior
# ===========================================================================


class TestStatusHandler:
    def test_returns_ok(self) -> None:
        payload = json.loads(_status_handler({}))
        assert payload["service"] == "ok"
        assert payload["plugin"] == "prometheus_avatar"
        assert payload["version"] == __version__
        assert payload["mode"] == "stub"

    def test_ignores_extra_kwargs(self) -> None:
        # Handlers accept **kwargs from the dispatcher. Extra kwargs must not
        # break the stub contract.
        payload = json.loads(_status_handler({}, session_id="x", caller="y"))
        assert payload["service"] == "ok"


class TestListAssetsHandler:
    @pytest.mark.parametrize("category", ["skins", "voices", "personas", "effects"])
    def test_valid_categories(self, category: str) -> None:
        payload = json.loads(_list_assets_handler({"category": category}))
        assert payload["category"] == category
        assert payload["mode"] == "stub"
        assert payload["assets"] == _DEMO_CATALOG[category]

    def test_rejects_unknown_category(self) -> None:
        payload = json.loads(_list_assets_handler({"category": "weapons"}))
        assert "error" in payload
        assert "Unknown category" in payload["error"]

    def test_rejects_missing_category(self) -> None:
        payload = json.loads(_list_assets_handler({}))
        assert "error" in payload

    def test_handles_none_args(self) -> None:
        payload = json.loads(_list_assets_handler(None))  # type: ignore[arg-type]
        assert "error" in payload


class TestDescribeHandler:
    def test_valid_asset_id(self) -> None:
        payload = json.loads(_describe_handler(
            {"asset_id": "prometheus_avatar:skin/demo-neon"}
        ))
        assert payload["id"] == "prometheus_avatar:skin/demo-neon"
        assert payload["name"] == "Neon Demo"
        assert payload["category"] == "skins"
        assert payload["mode"] == "stub"

    def test_unknown_asset_id(self) -> None:
        payload = json.loads(_describe_handler({"asset_id": "prometheus_avatar:skin/nope"}))
        assert "error" in payload
        assert "Unknown asset_id" in payload["error"]

    def test_missing_asset_id(self) -> None:
        payload = json.loads(_describe_handler({}))
        assert "error" in payload
        assert "asset_id" in payload["error"]

    def test_non_string_asset_id(self) -> None:
        payload = json.loads(_describe_handler({"asset_id": 42}))
        assert "error" in payload

    def test_describe_finds_each_category(self) -> None:
        # Walk the catalog and confirm every asset ID resolves. Guards against
        # silent catalog drift.
        for category, assets in _DEMO_CATALOG.items():
            for asset in assets:
                payload = json.loads(_describe_handler({"asset_id": asset["id"]}))
                assert payload["id"] == asset["id"], category
                assert payload["category"] == category
