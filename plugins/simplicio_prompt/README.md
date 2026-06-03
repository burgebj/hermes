# SIMPLICIO_PROMPT

SIMPLICIO_PROMPT is an opt-in Hermes plugin that injects the SIMPLICIO_PROMPT V2 execution overlay into every main-agent turn through the `pre_llm_call` hook.

The runtime is bundled in this plugin. Hermes does not need to fetch or consult
an external GitHub repository to apply the prompt.

Bundled snapshot: `plugins/simplicio_prompt/vendor/simplicio_prompt/`

![YOOL V2 Safe-Speed Runtime reference infographic](../../website/static/img/simplicio-prompt/yool-v2-safe-speed-infographic-en.png)

## Enable

Environment flag:

```bash
SIMPLICIO_PROMPT=true hermes chat
```

Config flag:

```yaml
simplicio_prompt:
  enabled: true
```

The plugin also activates when explicitly enabled through the normal plugin allow-list:

```bash
hermes plugins enable SIMPLICIO_PROMPT
```

`plugins.disabled: [SIMPLICIO_PROMPT]` still wins and prevents loading.

## What It Adds

| Item | Behaviour |
|---|---|
| Automatic prompt pass-through | Every enabled main-agent turn receives the overlay before the model call; any prompt/message is eligible, including questions, commands, code snippets, layout edits, refactors, and normal chat. The user does not need to type "Implement", "Fix", "Build", or any other trigger word. |
| Tuple-space planning | Requests are framed as root tuple plus explicit work graph, lane, authority, receipts, and source pointers. |
| Massive-agent abstraction | `batch_spawn(depth, branching, compression_threshold)` is used as a summarized hierarchy for 1,000,000+ subagents without enumerating them. |
| Safe speed policy | Cache by receipt/input hash, batch small tasks, compress context, route deterministic work to local tools, and use speculative work only when idempotent. |
| Provider safety | Backoff with jitter and circuit breakers are required; provider limits and terms must be respected. |
| Stable reporting | The default output contract keeps tuple-space state, active agents, totals, next yool, and partial result visible. |

The plugin is intentionally local-only. It does not call external services and
does not bypass provider throttles. Its runtime work is a local boolean check
plus a cached read of the bundled prompt context returned from `pre_llm_call`
when enabled.

## Bundled Runtime Files

The plugin vendors the SIMPLICIO_PROMPT runtime files from source commit
`c1df48534a6e23cacee94c8894cc4ca382aa3459`, including:

| Local file | Purpose |
|---|---|
| `vendor/simplicio_prompt/prompts/agent-runtime-execution-prompt.md` | Prompt loaded into the Hermes `pre_llm_call` context. |
| `vendor/simplicio_prompt/YOOL_TUPLE_HAMT.md` | Tuple-space, yool, HAMT, hookwall, receipt, and lane specification. |
| `vendor/simplicio_prompt/kernel/yool_tuple_kernel.py` | Reference kernel with `batch_spawn`, tuple routing, hookwall, and compression. |
| `vendor/simplicio_prompt/guardrails/cpu_throttle.py` | CPU quota guardrail reference. |
| `vendor/simplicio_prompt/guardrails/disk_gc.py` | Disk GC and disk-pressure reference. |
| `vendor/simplicio_prompt/examples/python/receipts.py` | Content-addressable receipt example. |
| `vendor/simplicio_prompt/scripts/build_hamt.py` | HAMT/catalog builder script. |
| `vendor/simplicio_prompt/benchmarks/` | V1/normal vs SIMPLICIO_PROMPT V2 benchmark reports and PDFs. |

At runtime, the plugin reads the Hermes-adapted vendored prompt from the local
bundle before injecting it into the model context.

## Activation Semantics

`SIMPLICIO_PROMPT` is gated only by Hermes configuration, not by message text.
After `SIMPLICIO_PROMPT=true`, `HERMES_SIMPLICIO_PROMPT=true`,
`simplicio_prompt.enabled: true`, or `hermes plugins enable SIMPLICIO_PROMPT`,
the plugin injects the overlay into every main-agent `pre_llm_call` hook.

This means every prompt or message receives the same SIMPLICIO_PROMPT V2
execution policy automatically: normal chat, questions, commands, pasted code,
single-word requests, layout edits, refactors, bug fixes, documentation work,
benchmark requests, and implementation tasks. The hook intentionally ignores the
message body, so the user never has to write "Implement" to activate it.

## Bundled SIMPLICIO_PROMPT V2 Reference Data

The bundled `vendor/simplicio_prompt/README.md` reports these local
SIMPLICIO_PROMPT V2 benchmark highlights for the safe-speed runtime. In this
plugin documentation, V2 means the bundled SIMPLICIO_PROMPT runtime snapshot;
the comparisons are against normal and V1 instruction baselines.

| Area | Reported SIMPLICIO_PROMPT V2 result vs normal/V1 |
|---|---:|
| Scale representation | `2,833.75x` faster than normal/V1 instruction flow |
| Active execution | `26.93x` faster than normal/V1 sequential execution |
| Receipt/input cache | `4x` fewer provider calls, a `75%` reduction |
| Small-task batching | `32x` fewer small-task calls, a `96.88%` reduction |
| Circuit breaker | `64x` fewer failure attempts, a `98.44%` reduction |
| Token economy | `76.32%` estimated savings through context compression |

Those numbers are reference data for the SIMPLICIO_PROMPT V2 execution policy.
This Hermes plugin injects that policy automatically; it does not claim to
bypass hosted-provider latency, quotas, or rate limits.

## High-Throughput Reference Knobs

The bundled runtime documents these safe-speed environment settings for local tuple-space execution:

```bash
YOOL_TUPLE_LANE_CONCURRENCY=32
YOOL_TUPLE_MAX_LANE_CONCURRENCY=64
YOOL_TUPLE_CPU_QUOTA_PCT=95
YOOL_TUPLE_QUEUE_MAXSIZE=8192
YOOL_TUPLE_COMPRESSION_THRESHOLD=1024
YOOL_TUPLE_CACHE_MAX_ENTRIES=16384
YOOL_TUPLE_CACHE_TTL_S=3600
YOOL_TUPLE_API_MAX_RETRIES=3
YOOL_TUPLE_API_BACKOFF_BASE_MS=100
YOOL_TUPLE_API_BACKOFF_MAX_MS=5000
YOOL_TUPLE_CIRCUIT_FAILURE_THRESHOLD=5
YOOL_TUPLE_CIRCUIT_COOLDOWN_S=30
YOOL_TUPLE_BATCH_SMALL_TASK_SIZE=32
YOOL_TUPLE_CONTEXT_COMPRESSION_CHARS=6000
```

Hermes keeps these as model-visible execution guidance through the overlay. Provider-facing behavior must still respect configured Hermes limits and the provider's terms.
