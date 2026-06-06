"""Tests for verbose logging feature."""

import pytest


class TestVerboseLogging:
    def test_format_verbose_config(self):
        from hermes_cli.debug import format_verbose
        output = format_verbose(sections=["config"])
        assert "Config" in output or "config" in output

    def test_format_verbose_providers(self):
        from hermes_cli.debug import format_verbose
        output = format_verbose(sections=["providers"])
        assert "Providers" in output or "providers" in output

    def test_format_verbose_all_sections(self):
        from hermes_cli.debug import format_verbose
        output = format_verbose()
        assert "──" in output
        assert len(output) > 50

    def test_format_verbose_with_specific_sections(self):
        from hermes_cli.debug import format_verbose
        output = format_verbose(sections=["session"])
        assert "Session" in output or "session" in output

    def test_format_verbose_returns_string(self):
        from hermes_cli.debug import format_verbose
        output = format_verbose()
        assert isinstance(output, str)

    def test_verbose_sections_constant(self):
        from hermes_cli.debug import VERBOSE_SECTIONS
        assert "config" in VERBOSE_SECTIONS
        assert "providers" in VERBOSE_SECTIONS
        assert "tools" in VERBOSE_SECTIONS
        assert "memory" in VERBOSE_SECTIONS
        assert "session" in VERBOSE_SECTIONS