# signet — cryptographic audit trail

Tamper-evident audit log for every tool call. Addresses the request in
[#487](https://github.com/NousResearch/hermes-agent/issues/487) (SHA-256
hash-chained audit trail, inspired by OpenFang) and optionally upgrades
to Ed25519-signed receipts via the `signet-auth` library.

## What it does

- Registers the existing `post_tool_call` hook. Every tool call becomes
  an audit entry.
- Entries are chained by SHA-256: any deletion, reordering, or in-place
  edit is detected by `verify()`.
- Optional: Ed25519 signature per entry when `signet-auth` is installed
  and `audit.provider: signet` is configured. This closes the
  "attacker with write access rewrites the chain" gap discussed in
  #487 — forging entries now requires forging signatures under the
  agent's private key.

Zero core code was modified — the plugin piggybacks on the existing
`post_tool_call` hook already invoked by `model_tools.py`.

## Enable

```bash
hermes plugins enable signet
```

Or in `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - signet
```

## Default provider: hash chain (no extra dependencies)

This ships stdlib-only. SHA-256 hash chain, one JSONL entry per tool
call, written to `$HERMES_HOME/signet/audit.jsonl`.

```
$HERMES_HOME/signet/
└── audit.jsonl   # append-only chain
```

## Optional provider: Ed25519 signatures via signet-auth

```bash
pip install signet-auth
```

And in `~/.hermes/config.yaml`:

```yaml
plugins:
  signet:
    provider: signet   # default is "hashchain"
```

Or the env override (useful in CI / tests):

```bash
export HERMES_SIGNET_PROVIDER=signet
```

Keys are created on first use under `$HERMES_HOME/signet/keys/` and are
managed by `signet-auth`; Hermes never sees raw key bytes.

## Inspect the chain

```
/signet status         # provider, path, event count, chain OK/broken
/signet verify         # walk and re-hash the full chain
/signet tail 10        # last 10 entries
/signet path           # print the audit directory
```

`verify` reports the first broken entry on failure so operators know
where tampering started.

## Schema

Each entry:

```jsonc
{
  "sequence": 0,                      // monotonic, gap-free
  "timestamp": "2026-04-20T10:00:00Z",
  "session_id": "...",
  "task_id": "...",
  "tool_name": "write_file",
  "tool_call_id": "...",
  "args_digest": "sha256 of canonical args",
  "result_digest": "sha256 of result string",
  "prev_hash": "sha256 of prior entry (or 64 zeros for genesis)",
  "hash": "sha256 of the above"
}
```

Canonicalization for the default provider: sorted keys, tightest JSON
separators, non-ASCII preserved. The Signet provider upgrades to
RFC 8785 JCS via its Rust core.

## Threat model (short version)

Hash chaining alone proves sequence integrity (no silent edits), not
authorship. An attacker with write access can fork the chain from any
point and rewrite everything after it — recomputed hashes will still
validate. This is a known limitation acknowledged in #487's discussion.

Mitigations (opt in via the Signet provider):

1. **Ed25519 per entry** — each hash is also signed. Rewriting the
   chain requires signing with the agent's private key.
2. **Key separation** — `signet-auth` stores keys under a configurable
   directory and is compatible with external key stores (HSM / KMS) for
   stronger custody.
3. **Bilateral receipts** — when the downstream tool server also signs
   (supported by `signet-auth`), forging requires compromising both
   keys, which live in different trust domains.

Bilateral signing is out of scope for the first cut of this plugin and
can be added in a follow-up without changing the hook wiring.

## Relation to `disk-cleanup`

Same plugin mechanics: a `post_tool_call` observer that writes under
`$HERMES_HOME/<plugin>/`, plus a `/signet` command for inspection. No
agent compliance is required.
