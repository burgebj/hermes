"""Tests for hermes dump helpers."""


def test_count_mcp_servers_uses_top_level_config_shape():
    from hermes_cli.dump import _count_mcp_servers

    assert _count_mcp_servers({"mcp_servers": {"search-corpus": {}, "mem0": {}}}) == 2


def test_count_mcp_servers_keeps_legacy_fallback():
    from hermes_cli.dump import _count_mcp_servers

    assert _count_mcp_servers({"mcp": {"servers": {"legacy": {}}}}) == 1
    assert _count_mcp_servers({}) == 0
