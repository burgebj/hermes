# mcp_lazy

Config-gated Phase 1 lazy MCP schema loading for Hermes Agent.

When `mcp.lazy_loading: true` is enabled, MCP tool schemas are replaced
with lightweight stubs in API requests. The model can call
`load_mcp_tools` to promote selected MCP tools to their full schemas for
the rest of the current session.

This Phase 1 slice intentionally covers only:
- request-time MCP tool stubs
- on-demand tool promotion
- per-session promoted-tool state

It does not include server-level discovery, eager server promotion, or
baseline telemetry/reporting.
