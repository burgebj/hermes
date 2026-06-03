# Yool Safe-Speed Benchmark V2

Run date: 2026-05-21

This report compares three execution styles:

- Normal instruction: generic prompt, flat or repeated work, no runtime guardrails.
- V1 high-throughput: lazy `batch_spawn` and fixed `LaneWorkerPool` fan-out.
- V2 safe-speed: V1 plus cache, adaptive lanes, backoff, provider circuit breaker, batching, context compression, local routing, and idempotent speculation.

The benchmark is local. It does not call hosted LLMs or external APIs.

## Scale Representation

| Profile | Tasks | Wall ms | Throughput/s | Peak KiB | Provider calls | Cache hits | Blocked | Tokens | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| normal instruction | 131,072 | 174.49 | 751175.4 | 28751.2 | 0 | 0 | 0 | 0 | flat list materialization |
| V1 high-throughput | 1,048,576 | 0.08 | 13851731550.8 | 7.7 | 0 | 0 | 0 | 0 | lazy batch_spawn depth=4, branching=32 |
| V2 safe-speed | 1,048,576 | 0.05 | 20281939643.6 | 7.3 | 0 | 0 | 0 | 0 | lazy batch_spawn depth=4, branching=32 |

## Active Execution

| Profile | Tasks | Wall ms | Throughput/s | Peak KiB | Provider calls | Cache hits | Blocked | Tokens | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| normal instruction | 1,024 | 5615.25 | 182.4 | 0.6 | 1,024 | 0 | 0 | 0 | sequential execution |
| V1 high-throughput | 1,024 | 237.91 | 4304.2 | 3408.0 | 1,024 | 0 | 0 | 0 | lane_concurrency=32, max_lane_concurrency=32 |
| V2 safe-speed | 1,024 | 215.90 | 4742.9 | 3105.8 | 1,024 | 0 | 0 | 0 | lane_concurrency=32, max_lane_concurrency=64 |

## Cache Dedupe

| Profile | Tasks | Wall ms | Throughput/s | Peak KiB | Provider calls | Cache hits | Blocked | Tokens | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| normal instruction | 256 | 417.68 | 612.9 | 5.4 | 256 | 0 | 0 | 0 | 64 unique inputs repeated across 256 tasks |
| V1 high-throughput | 256 | 429.38 | 596.2 | 5.2 | 256 | 0 | 0 | 0 | 64 unique inputs repeated across 256 tasks |
| V2 safe-speed | 256 | 125.84 | 2034.4 | 43.0 | 64 | 192 | 0 | 0 | 64 unique inputs repeated across 256 tasks |

## Small Task Batching

| Profile | Tasks | Wall ms | Throughput/s | Peak KiB | Provider calls | Cache hits | Blocked | Tokens | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| normal instruction | 512 | 729.98 | 701.4 | 0.5 | 512 | 0 | 0 | 0 | one provider-sized call per small task |
| V1 high-throughput | 512 | 730.34 | 701.0 | 0.5 | 512 | 0 | 0 | 0 | one provider-sized call per small task |
| V2 safe-speed | 512 | 20.44 | 25043.8 | 540.6 | 16 | 0 | 0 | 0 | batch_size=32 |

## Provider Failure Control

| Profile | Tasks | Wall ms | Throughput/s | Peak KiB | Provider calls | Cache hits | Blocked | Tokens | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| normal instruction | 64 | 0.02 | 3062203.2 | 0.6 | 192 | 0 | 0 | 0 | no provider circuit breaker |
| V1 high-throughput | 64 | 0.01 | 7529406.0 | 0.6 | 192 | 0 | 0 | 0 | no provider circuit breaker |
| V2 safe-speed | 64 | 0.51 | 126033.9 | 5.5 | 3 | 0 | 63 | 0 | breaker opens after 3 provider failures |

## Context Compression

| Profile | Tasks | Wall ms | Throughput/s | Peak KiB | Provider calls | Cache hits | Blocked | Tokens | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| normal instruction | 1 | 0.10 | 10090.8 | 53.1 | 0 | 0 | 0 | 5,016 | 20000 char context |
| V1 high-throughput | 1 | 0.07 | 13440.9 | 53.1 | 0 | 0 | 0 | 5,016 | 20000 char context |
| V2 safe-speed | 1 | 0.16 | 6265.7 | 27.6 | 0 | 0 | 0 | 1,188 | 20000 char context |

## Gains

| Scenario | Baseline | Improved | Metric | Ratio | Gain |
|---|---|---|---|---:|---:|
| scale_representation | normal instruction | V2 safe-speed | wall_ms | 3375.03x | 99.97% |
| active_execution | normal instruction | V1 high-throughput | wall_ms | 23.60x | 95.76% |
| active_execution | normal instruction | V2 safe-speed | wall_ms | 26.01x | 96.16% |
| active_execution | V1 high-throughput | V2 safe-speed | wall_ms | 1.10x | 9.25% |
| cache_dedupe | normal instruction | V2 safe-speed | wall_ms | 3.32x | 69.87% |
| cache_dedupe | normal instruction | V2 safe-speed | provider_calls | 4.00x | 75.00% |
| cache_dedupe | V1 high-throughput | V2 safe-speed | wall_ms | 3.41x | 70.69% |
| cache_dedupe | V1 high-throughput | V2 safe-speed | provider_calls | 4.00x | 75.00% |
| small_task_batching | normal instruction | V2 safe-speed | wall_ms | 35.71x | 97.20% |
| small_task_batching | normal instruction | V2 safe-speed | provider_calls | 32.00x | 96.88% |
| small_task_batching | V1 high-throughput | V2 safe-speed | wall_ms | 35.72x | 97.20% |
| small_task_batching | V1 high-throughput | V2 safe-speed | provider_calls | 32.00x | 96.88% |
| provider_failure_control | normal instruction | V2 safe-speed | provider_calls | 64.00x | 98.44% |
| provider_failure_control | V1 high-throughput | V2 safe-speed | provider_calls | 64.00x | 98.44% |
| context_compression | normal instruction | V2 safe-speed | tokens | 4.22x | 76.32% |
| context_compression | V1 high-throughput | V2 safe-speed | tokens | 4.22x | 76.32% |

## Interpretation

- V2 keeps the V1 lazy million-agent scale model.
- V2 improves active fan-out by allowing lanes to grow toward the configured ceiling when backlog is high.
- Cache reduces repeated provider calls when the same `yool + data` appears again.
- Batching turns many tiny provider/API-sized operations into fewer bounded calls.
- Circuit breaker reduces hammering during provider outages, which is the anti-ban part of the speed model.
- Context compression lowers token transfer before LLM calls while preserving a digest and preview.

## Reproduce

```bash
python benchmarks/v2_safe_speed_benchmark.py --json-output benchmarks/v2_safe_speed_results.json --md-output benchmarks/v2_safe_speed_results.md
python benchmarks/generate_v2_benchmark_pdf.py
```
