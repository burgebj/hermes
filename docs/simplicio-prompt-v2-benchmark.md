# SIMPLICIO_PROMPT V2 Benchmark

![YOOL V2 Safe-Speed Runtime reference infographic](../website/static/img/simplicio-prompt/yool-v2-safe-speed-infographic-en.png)

This report compares three local message-preparation paths for the Hermes
SIMPLICIO_PROMPT plugin. It does not call a hosted model, so it does not claim
provider-side latency, quality, or tool-success improvements. It measures the
part this PR changes directly: pre-LLM prompt injection and token footprint.
In this PR, V2 means the bundled `SIMPLICIO_PROMPT` runtime snapshot under
`plugins/simplicio_prompt/vendor/simplicio_prompt`. The comparison baselines are
normal instructions in this local plugin microbenchmark, plus the bundled report
data for normal instruction and V1 high-throughput baselines. The manual row is
only the earlier per-message adoption path, not a separate V2 target.
The PR includes the prompt, spec, kernel, guardrails, examples, benchmarks, PDFs,
and image assets locally so Hermes does not need an external repository lookup.

Command:

```bash
python scripts/benchmark_simplicio_prompt.py --iterations 10000
```

## Results

| Case | Meaning | Median ms/build | p95 ms/build | Rough input tokens | Chars |
|---|---|---:|---:|---:|---:|
| normal_instruction | Normal instruction baseline with no overlay | 0.000100 | 0.000200 | 28 | 112 |
| manual_simplicio_prompt_per_message | Earlier per-message manual SIMPLICIO_PROMPT adoption path pasted into the user prompt | 0.000300 | 0.000500 | 438 | 1,754 |
| simplicio_prompt_plugin_always_on | Automatic always-on SIMPLICIO_PROMPT overlay loaded from the bundled runtime snapshot | 0.000400 | 0.000700 | 1,804 | 7,217 |

## Deltas

| Comparison | Result |
|---|---:|
| Automatic vendored SIMPLICIO_PROMPT plugin vs earlier manual SIMPLICIO_PROMPT prompt path | 311.87% more rough input tokens |
| SIMPLICIO_PROMPT plugin vs normal instruction baseline | 6342.86% more rough input tokens |
| Plugin local preprocessing overhead vs normal instruction baseline | ~0.0003 ms median absolute delta |
| Extra model calls introduced by plugin | 0 |
| External GitHub fetches introduced by plugin | 0 |

## Interpretation

`normal_instruction` is the normal instruction baseline. It is the fastest and
cheapest local path because it carries no execution overlay. It also gives the
model no tuple-space policy, no SIMPLICIO_PROMPT V2 safe-speed rules, and no
stable reporting contract.

`manual_simplicio_prompt_per_message` gives the model the SIMPLICIO_PROMPT policy
by manually pasting local bundle paths into the message. It represents the earlier
per-message manual adoption path: the user has to paste it or remember it each turn. In this
benchmark it costs about 438 rough input tokens.

`simplicio_prompt_plugin_always_on` gives the model the same SIMPLICIO_PROMPT policy
automatically through `pre_llm_call`, loaded from the bundled local runtime
snapshot. The vendored plugin intentionally carries more context than the compact
manual prompt because it includes the local source-of-truth instruction and file
map needed to run without consulting an external GitHub repository. That costs
1,804 rough input tokens in this local benchmark, but it adds no external calls
and no provider calls. The local preprocessing cost is effectively noise
relative to network/model latency; sub-millisecond timing values can vary between
local runs, while the rough token and character footprint remains stable.
Activation is config-driven rather than
text-driven: once enabled, the hook injects the overlay for every main-agent
turn and every prompt/message, including questions, commands, normal chat, code
snippets, and messages that do not contain "Implement" or any other trigger
word.

## SIMPLICIO_PROMPT V2 Coverage

| SIMPLICIO_PROMPT V2 improvement | Plugin behaviour |
|---|---|
| Bundled runtime snapshot | All source files needed by the prompt are copied under `plugins/simplicio_prompt/vendor/simplicio_prompt/`. |
| Cache by receipt/input hash | Included in the overlay as a required execution policy for repeat work. |
| Adaptive lane pool | Included as adaptive lanes in the safe-speed rules. |
| Backoff with jitter | Included and paired with provider-limit compliance. |
| Circuit breaker | Included as required provider safety. |
| Batching tiny tasks | Included to reduce tool/model turn overhead. |
| Prompt/context compression | Included before expensive model calls. |
| Local routing before LLM | Included for deterministic/simple work. |
| Idempotent-only speculation | Included explicitly; unsafe speculation is disallowed. |

The plugin is an execution-policy overlay, not a provider throttle bypass. It
does not attempt to evade rate limits, account limits, or terms of service.

## Bundled SIMPLICIO_PROMPT V2 Report Data

The bundled `plugins/simplicio_prompt/vendor/simplicio_prompt/README.md`
describes the broader SIMPLICIO_PROMPT V2 safe-speed runtime as a tuple-space
execution policy with lazy `batch_spawn`, adaptive lanes, cache, batching,
circuit breakers, backoff with jitter, context compression, local yool routing,
and idempotent-only speculation.

Bundled README highlights compare SIMPLICIO_PROMPT V2 against normal/V1
baselines:

| Area | Reported SIMPLICIO_PROMPT V2 result vs normal/V1 |
|---|---:|
| Scale representation | `2,833.75x` faster than a normal/V1 instruction flow |
| Active execution | `26.93x` faster than normal/V1 sequential execution |
| Cache | `4x` fewer provider calls, a `75%` reduction |
| Batching | `32x` fewer small-task calls, a `96.88%` reduction |
| Circuit breaker | `64x` fewer failure attempts, a `98.44%` reduction |
| Token economy | `76.32%` estimated savings through context compression |

Those broader numbers are included as reference data for the SIMPLICIO_PROMPT V2
policy this plugin injects. The Hermes benchmark above remains intentionally
narrower: it measures the automatic pre-LLM overlay path introduced by this PR.
