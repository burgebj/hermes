# Allowed JSON-RPC methods (read bundle)

Bundled whitelist only:

| Method | Typical `params` |
|--------|------------------|
| `eth_chainId` | `[]` |
| `eth_blockNumber` | `[]` |
| `eth_gasPrice` | `[]` |
| `eth_getBalance` | `[address, block_tag]` e.g. `["0x…", "latest"]` |
| `eth_getTransactionCount` | `[address, block_tag]` |
| `eth_getCode` | `[address, block_tag]` |
| `eth_call` | `[{from?, to?, gas?, gasPrice?, value?, data?}, block_tag]` |

**`eth_call` notes**

- `data` MUST be ABI-encoded calldata (hex string starting with `0x`).
- Very large payloads are rejected to avoid oversized HTTP bodies against public RPC tiers.
- `from` may be omitted; some nodes infer a dummy sender — behavior is node-specific.

**Not covered here**

Sending transactions (`eth_send*`), traces (`debug_*`), filters, subscriptions — use audited wallet / indexer tooling outside this playbook.
