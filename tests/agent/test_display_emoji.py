"""Tests for get_tool_emoji in agent/display.py — skin + registry integration."""

from unittest.mock import patch as mock_patch, MagicMock

from agent.display import format_skill_progress, get_tool_emoji


class TestGetToolEmoji:
    """Verify the skin → registry → fallback resolution chain."""

    def test_returns_registry_emoji_when_no_skin(self):
        """Registry-registered emoji is used when no skin is active."""
        mock_registry = MagicMock()
        mock_registry.get_emoji.return_value = "🎨"
        with mock_patch("agent.display._get_skin", return_value=None), \
             mock_patch("agent.display.registry", mock_registry, create=True):
            # Need to patch the import inside get_tool_emoji
            pass
        # Direct test: patch the lazy import path
        with mock_patch("agent.display._get_skin", return_value=None):
            # get_tool_emoji will try to import registry — mock that
            mock_reg = MagicMock()
            mock_reg.get_emoji.return_value = "📖"
            with mock_patch.dict("sys.modules", {}):
                import sys
                # Patch tools.registry module
                mock_module = MagicMock()
                mock_module.registry = mock_reg
                with mock_patch.dict(sys.modules, {"tools.registry": mock_module}):
                    result = get_tool_emoji("read_file")
                    assert result == "📖"

    def test_skin_override_takes_precedence(self):
        """Skin tool_emojis override registry defaults."""
        skin = MagicMock()
        skin.tool_emojis = {"terminal": "⚔"}
        with mock_patch("agent.display._get_skin", return_value=skin):
            result = get_tool_emoji("terminal")
            assert result == "⚔"

    def test_skin_empty_dict_falls_through(self):
        """Empty skin tool_emojis falls through to registry."""
        skin = MagicMock()
        skin.tool_emojis = {}
        mock_reg = MagicMock()
        mock_reg.get_emoji.return_value = "💻"
        import sys
        mock_module = MagicMock()
        mock_module.registry = mock_reg
        with mock_patch("agent.display._get_skin", return_value=skin), \
             mock_patch.dict(sys.modules, {"tools.registry": mock_module}):
            result = get_tool_emoji("terminal")
            assert result == "💻"

    def test_fallback_default(self):
        """When neither skin nor registry has an emoji, use the default."""
        skin = MagicMock()
        skin.tool_emojis = {}
        mock_reg = MagicMock()
        mock_reg.get_emoji.return_value = ""
        import sys
        mock_module = MagicMock()
        mock_module.registry = mock_reg
        with mock_patch("agent.display._get_skin", return_value=skin), \
             mock_patch.dict(sys.modules, {"tools.registry": mock_module}):
            result = get_tool_emoji("unknown_tool")
            assert result == "⚡"

    def test_custom_default(self):
        """Custom default is returned when nothing matches."""
        with mock_patch("agent.display._get_skin", return_value=None):
            mock_reg = MagicMock()
            mock_reg.get_emoji.return_value = ""
            import sys
            mock_module = MagicMock()
            mock_module.registry = mock_reg
            with mock_patch.dict(sys.modules, {"tools.registry": mock_module}):
                result = get_tool_emoji("x", default="⚙️")
                assert result == "⚙️"

    def test_skin_override_only_for_matching_tool(self):
        """Skin override for one tool doesn't affect others."""
        skin = MagicMock()
        skin.tool_emojis = {"terminal": "⚔"}
        mock_reg = MagicMock()
        mock_reg.get_emoji.return_value = "🔍"
        import sys
        mock_module = MagicMock()
        mock_module.registry = mock_reg
        with mock_patch("agent.display._get_skin", return_value=skin), \
             mock_patch.dict(sys.modules, {"tools.registry": mock_module}):
            assert get_tool_emoji("terminal") == "⚔"  # skin override
            assert get_tool_emoji("web_search") == "🔍"  # registry fallback


class TestSkinConfigToolEmojis:
    """Verify SkinConfig handles tool_emojis field correctly."""

    def test_skin_config_has_tool_emojis_field(self):
        from hermes_cli.skin_engine import SkinConfig
        skin = SkinConfig(name="test")
        assert skin.tool_emojis == {}

    def test_skin_config_accepts_tool_emojis(self):
        from hermes_cli.skin_engine import SkinConfig
        emojis = {"terminal": "⚔", "web_search": "🔮"}
        skin = SkinConfig(name="test", tool_emojis=emojis)
        assert skin.tool_emojis == emojis

    def test_build_skin_config_includes_tool_emojis(self):
        from hermes_cli.skin_engine import _build_skin_config
        data = {
            "name": "custom",
            "tool_emojis": {"terminal": "🗡️", "patch": "⚒️"},
        }
        skin = _build_skin_config(data)
        assert skin.tool_emojis == {"terminal": "🗡️", "patch": "⚒️"}

    def test_build_skin_config_empty_tool_emojis_default(self):
        from hermes_cli.skin_engine import _build_skin_config
        data = {"name": "minimal"}
        skin = _build_skin_config(data)
        assert skin.tool_emojis == {}


class TestFormatSkillProgress:
    """Verify the 🔌 plugin-skill override for tool-progress messages."""

    def test_plugin_skill_qualified_name(self):
        """Qualified ``namespace:bare`` renders as ``🔌 namespace · bare``."""
        result = format_skill_progress({"name": "bp-shopify:seo-reports"})
        assert result == "🔌 bp-shopify · seo-reports"

    def test_native_skill_no_namespace(self):
        """Bare names (native skills) fall through to default render."""
        assert format_skill_progress({"name": "axolotl"}) is None

    def test_native_skill_categorized_path(self):
        """Native skills with category-path slashes still fall through."""
        assert format_skill_progress({"name": "fine-tuning/axolotl"}) is None

    def test_empty_args(self):
        assert format_skill_progress({}) is None

    def test_none_args(self):
        assert format_skill_progress(None) is None

    def test_missing_name(self):
        assert format_skill_progress({"file_path": "foo.md"}) is None

    def test_non_string_name(self):
        assert format_skill_progress({"name": 42}) is None
        assert format_skill_progress({"name": None}) is None
        assert format_skill_progress({"name": ["a", "b"]}) is None

    def test_empty_namespace(self):
        """Defensive: leading colon means no namespace — fall through."""
        assert format_skill_progress({"name": ":seo-reports"}) is None

    def test_empty_bare(self):
        """Defensive: trailing colon means no bare name — fall through."""
        assert format_skill_progress({"name": "bp-shopify:"}) is None

    def test_multi_colon_partitions_on_first(self):
        """If a skill name contains multiple colons, split on the first."""
        result = format_skill_progress({"name": "foo:bar:baz"})
        assert result == "🔌 foo · bar:baz"
