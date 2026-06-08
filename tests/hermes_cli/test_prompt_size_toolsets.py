"""Tests for prompt-size toolset filtering (#41445)."""

from unittest.mock import patch, MagicMock
import pytest


class TestBuildInspectionAgentToolsets:
    """Verify _build_inspection_agent passes enabled/disabled toolsets."""

    def test_passes_platform_toolsets_to_agent(self):
        """Enabled toolsets from _get_platform_tools should be forwarded to AIAgent."""
        import hermes_cli.prompt_size as ps

        fake_cfg = {"model": {"default": "test-model"}}

        with (
            patch("hermes_cli.config.load_config", return_value=fake_cfg),
            patch("hermes_cli.tools_config._get_platform_tools", return_value={"core", "web", "file"}) as mock_gpt,
            patch("run_agent.AIAgent") as mock_agent,
        ):
            ps._build_inspection_agent("feishu")

        mock_gpt.assert_called_once_with(fake_cfg, "feishu")
        _, kwargs = mock_agent.call_args
        assert sorted(kwargs["enabled_toolsets"]) == ["core", "file", "web"]

    def test_passes_disabled_toolsets_from_config(self):
        """agent.disabled_toolsets from config should be forwarded to AIAgent."""
        import hermes_cli.prompt_size as ps

        fake_cfg = {
            "model": {"default": "test-model"},
            "agent": {"disabled_toolsets": ["tts", "delegation"]},
        }

        with (
            patch("hermes_cli.config.load_config", return_value=fake_cfg),
            patch("hermes_cli.tools_config._get_platform_tools", return_value={"core"}),
            patch("run_agent.AIAgent") as mock_agent,
        ):
            ps._build_inspection_agent("feishu")

        _, kwargs = mock_agent.call_args
        assert kwargs["disabled_toolsets"] == ["tts", "delegation"]

    def test_no_disabled_toolsets_when_absent(self):
        """When agent config has no disabled_toolsets, pass None."""
        import hermes_cli.prompt_size as ps

        fake_cfg = {"model": {"default": "test-model"}}

        with (
            patch("hermes_cli.config.load_config", return_value=fake_cfg),
            patch("hermes_cli.tools_config._get_platform_tools", return_value={"core"}),
            patch("run_agent.AIAgent") as mock_agent,
        ):
            ps._build_inspection_agent("cli")

        _, kwargs = mock_agent.call_args
        assert kwargs["disabled_toolsets"] is None

    def test_disabled_toolsets_empty_list_becomes_none(self):
        """Empty disabled_toolsets list should be passed as None."""
        import hermes_cli.prompt_size as ps

        fake_cfg = {
            "model": {"default": "test-model"},
            "agent": {"disabled_toolsets": []},
        }

        with (
            patch("hermes_cli.config.load_config", return_value=fake_cfg),
            patch("hermes_cli.tools_config._get_platform_tools", return_value={"core"}),
            patch("run_agent.AIAgent") as mock_agent,
        ):
            ps._build_inspection_agent("cli")

        _, kwargs = mock_agent.call_args
        assert kwargs["disabled_toolsets"] is None
