# Secret broker integration (`HERMES_S6_EXEC_WRAPPER`)

When running the official `hermes-agent` container, the dashboard and
profile-gateway processes run as **s6-supervised services**, not as
children of whatever the container CMD evaluates to. s6 launches each
supervised service from `/run/service/<svc>/run` independently of the
entrypoint, so any environment variables added by wrapping the CMD
— for example `agent-vault run -- hermes gateway run`,
`vault agent exec -- …`, `sops exec-env …`, or `doppler run --` —
**are not inherited** by the supervised worker, and therefore not by
any subprocess the worker forks (slash workers, MCP clients, …).

The consequence: brokers that work by setting `HTTPS_PROXY` /
`REQUESTS_CA_BUNDLE` / `SSL_CERT_FILE` on the child process don't
get to intercept outbound HTTPS from the dashboard or gateway. Any
provider key still stored as a placeholder (e.g. the literal string
`__OPENROUTER_API_KEY__`) leaks verbatim to the LLM provider →
HTTP 401.

## The hook

Set `HERMES_S6_EXEC_WRAPPER` in the container environment. Every
s6-supervised hermes service (`dashboard`, `gateway-<profile>`)
prepends this string to its final `exec` line, putting the broker
**inside** the supervised slot:

```yaml
# docker-compose.yml
services:
  hermes:
    image: nousresearch/hermes-agent:main
    environment:
      HERMES_S6_EXEC_WRAPPER: "agent-vault run --"
    # CMD stays as the default — no wrapping needed at the container
    # entrypoint, because the wrapper now applies per-service.
```

Properties:

- **Word-split intentionally.** Multi-token prefixes
  (`agent-vault run --`, `vault agent exec --`) work as written.
- **Unset / empty is a no-op.** Existing deployments see no change.
- **Applies to all supervised hermes services**: `dashboard` and every
  `gateway-<profile>` registered via the dynamic service manager.
- **`main-hermes` is unaffected.** It is a no-op `sleep infinity`
  slot (see `docker/s6-rc.d/main-hermes/run`); the container CMD
  remains the place to wrap the foreground process.

## Examples

Infisical agent-vault:

```yaml
environment:
  HERMES_S6_EXEC_WRAPPER: "/opt/agent-vault/agent-vault run --"
```

HashiCorp Vault Agent:

```yaml
environment:
  HERMES_S6_EXEC_WRAPPER: "vault agent exec -config=/etc/vault/agent.hcl --"
```

Doppler:

```yaml
environment:
  HERMES_S6_EXEC_WRAPPER: "doppler run --"
```

## Compatibility

The hook is purely additive: scripts expand `${HERMES_S6_EXEC_WRAPPER:-}`,
so the variable being unset reproduces the previous (unwrapped) exec
line byte-for-byte. No existing deployment needs to set it.
