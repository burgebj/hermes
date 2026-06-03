# Yool Tuple Space Kernel

Reference Python kernel for Tuple-Space + Yool Architecture.

Core file: `kernel/yool_tuple_kernel.py`.

## Primitives

- `out_tuple`, `in_tuple`, `rd_tuple`
- `spawn_agent`
- `batch_spawn(depth, branching, compression_threshold)`
- `route_packet`
- `scan_index`
- `hookwall`
- `compress_token`
- `prune_idle`
- `ReceiptCache` for receipt/input-hash dedupe
- `ProviderCircuitBreaker` and jittered backoff for API/LLM calls
- `ContextCompressor` for large prompt/context payloads
- `LaneWorkerPool` for adaptive per-lane fan-out and small-task batching

## Scale model

Use `batch_spawn(root, "codex_worker", depth=4, branching=32)` to represent
1,048,576 subagents without materializing a flat million-item Python list. The
kernel stores a lazy batch controller tuple plus compressed virtual-agent
accounting, then materializes only active work.

Inactive materialized agents can be compacted with `compress_token(agent_id)`.
`prune_idle(max_active)` automatically compresses the oldest active subagents.

## Safe speed model

The reference kernel increases throughput without provider-ban risk by avoiding
repeat work and by slowing down safely when providers fail:

- `TupleSpace.execute_tuple(...)` checks registered local yools first, compresses
  large LLM context, hits `ReceiptCache`, then calls the provider with jittered
  backoff and a provider-level circuit breaker.
- `LaneWorkerPool.concurrency_for(lane)` adapts from lane queue depth, latency,
  failures, and env ceilings instead of using one fixed worker count forever.
- `LaneWorkerPool.run_lane_batched(...)` groups small lane tasks into bounded
  batches.
- `speculative_executor` is only used when the tuple data explicitly sets
  `idempotent=True`.

## Runtime policy

Environment aliases:

- `YOOL_TUPLE_LANE_CONCURRENCY` / `YOOL_LANE_CONCURRENCY`, default `32`
- `YOOL_TUPLE_MAX_LANE_CONCURRENCY` / `YOOL_MAX_LANE_CONCURRENCY`, default `64`
- `YOOL_TUPLE_CPU_QUOTA_PCT` / `YOOL_CPU_QUOTA_PCT`, default `95`
- `YOOL_TUPLE_QUEUE_MAXSIZE` / `YOOL_QUEUE_MAXSIZE`, default `8192`
- `YOOL_TUPLE_COMPRESSION_THRESHOLD` / `YOOL_COMPRESSION_THRESHOLD`, default `1024`
- `YOOL_TUPLE_CACHE_MAX_ENTRIES` / `YOOL_CACHE_MAX_ENTRIES`, default `16384`
- `YOOL_TUPLE_CACHE_TTL_S` / `YOOL_CACHE_TTL_S`, default `3600`
- `YOOL_TUPLE_API_MAX_RETRIES` / `YOOL_API_MAX_RETRIES`, default `3`
- `YOOL_TUPLE_API_BACKOFF_BASE_MS` / `YOOL_API_BACKOFF_BASE_MS`, default `100`
- `YOOL_TUPLE_API_BACKOFF_MAX_MS` / `YOOL_API_BACKOFF_MAX_MS`, default `5000`
- `YOOL_TUPLE_CIRCUIT_FAILURE_THRESHOLD` / `YOOL_CIRCUIT_FAILURE_THRESHOLD`, default `5`
- `YOOL_TUPLE_CIRCUIT_COOLDOWN_S` / `YOOL_CIRCUIT_COOLDOWN_S`, default `30`
- `YOOL_TUPLE_BATCH_SMALL_TASK_SIZE` / `YOOL_BATCH_SMALL_TASK_SIZE`, default `32`
- `YOOL_TUPLE_CONTEXT_COMPRESSION_CHARS` / `YOOL_CONTEXT_COMPRESSION_CHARS`, default `6000`

## Usage

```python
from kernel.yool_tuple_kernel import build_default_space

space, root = build_default_space()
receipt = space.batch_spawn(root, "codex_worker", depth=4, branching=32)
print(receipt.virtual_agents)  # 1048576
print(space.snapshot())
```

Run:

```bash
python kernel/yool_tuple_kernel.py
python -m unittest discover -s tests -p "test_*.py"
```
