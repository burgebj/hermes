"""Tests for IRC platform adapter."""
import pytest
from gateway.config import Platform

class TestIRCPlatformEnum:
    def test_irc_enum_exists(self):
        assert Platform.IRC.value == "irc"
    def test_irc_in_platform_list(self):
        assert "irc" in [p.value for p in Platform]

class TestIRCToolset:
    def test_hermes_irc_toolset_exists(self):
        from toolsets import get_toolset
        assert get_toolset("hermes-irc") is not None

class TestIRCPlatformHint:
    def test_irc_platform_hint_exists(self):
        from agent.prompt_builder import PLATFORM_HINTS
        assert "irc" in PLATFORM_HINTS
