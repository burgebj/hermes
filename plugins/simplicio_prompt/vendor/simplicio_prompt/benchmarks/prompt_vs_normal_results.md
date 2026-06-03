# Prompt vs Normal Instruction Benchmark

Run date: 2026-05-21

Environment:

- Python 3.14.3
- Repository: `wesleysimplicio/simplicio-prompt`
- Benchmark script: `benchmarks/prompt_vs_normal.py`
- PDF report: `benchmarks/prompt_vs_normal_benchmark.pdf`
- YOOL profile: `YOOL_TUPLE_LANE_CONCURRENCY=32`, `YOOL_TUPLE_MAX_LANE_CONCURRENCY=64`,
  `YOOL_TUPLE_CPU_QUOTA_PCT=95`, `YOOL_TUPLE_QUEUE_MAXSIZE=8192`,
  `YOOL_TUPLE_COMPRESSION_THRESHOLD=1024`

## What Was Measured

This benchmark does not call a hosted LLM. It compares the local operational
behavior implied by two instruction styles:

- Normal instruction: flat agent materialization and sequential execution.
- Yool prompt: lazy `batch_spawn`, tuple-space routing, and `LaneWorkerPool`
  fan-out.

## Results

### Scale Representation

| Profile | Represented agents | Wall time | Peak memory |
|---|---:|---:|---:|
| Normal instruction, flat list | 131,072 | 217.11 ms | 28,749.88 KiB |
| Yool prompt, lazy `batch_spawn` | 1,048,576 | 0.16 ms | 6.32 KiB |

Observed improvement:

- Speedup: 1,397x
- Peak-memory reduction: 4,547x
- The Yool prompt represented 8x more agents while using far less memory.

Larger scale run:

| Profile | Represented agents | Wall time | Peak memory |
|---|---:|---:|---:|
| Normal instruction, flat list | 262,144 | 431.45 ms | 57,542.32 KiB |
| Yool prompt, lazy `batch_spawn` | 1,048,576 | 0.07 ms | 6.39 KiB |

Observed improvement:

- Speedup: 5,902x
- Peak-memory reduction: 9,000x

### Active Execution

Workload: simulated yool work with 2 ms latency per task.

| Profile | Tasks | Wall time | Throughput | Peak memory |
|---|---:|---:|---:|---:|
| Normal instruction, sequential | 256 | 603.98 ms | 423.9 tasks/s | 17.33 KiB |
| Yool prompt, lane fan-out | 256 | 94.87 ms | 2,698.3 tasks/s | 879.82 KiB |

Observed improvement:

- Speedup: 6.37x
- Throughput increase: 6.37x
- Tradeoff: the Yool profile used more active memory because it creates tuple
  envelopes and thread fan-out structures.

Larger active run:

| Profile | Tasks | Wall time | Throughput | Peak memory |
|---|---:|---:|---:|---:|
| Normal instruction, sequential | 512 | 1,212.88 ms | 422.1 tasks/s | 33.55 KiB |
| Yool prompt, lane fan-out | 512 | 130.28 ms | 3,929.9 tasks/s | 1,739.41 KiB |

Observed improvement:

- Speedup: 9.31x
- Throughput increase: 9.31x

## Findings Beyond Speed

- Token economy: the Yool prompt has a higher one-off bootstrap cost, but it
  stops repeated chat-context orchestration as soon as work fans out.
- Scalability: the Yool prompt can represent million-agent trees without
  enumerating every leaf. A normal instruction tends toward flat lists or vague
  "parallelize this" guidance.
- Memory behavior: Yool wins massively for dormant or planned subagents through
  lazy hierarchy and compression. For small active workloads, it spends more
  memory on tuple metadata and lane workers.
- Auditability: Yool execution emits tuples and receipts; normal instructions
  usually leave only a narrative result.
- Recovery: Yool has explicit tuple state and can resume/replay pending work.
  Normal instructions depend on chat context or ad hoc notes.
- Guardrails: Yool has named CPU, queue, compression, hookwall, and disk GC
  concepts. Normal instructions rarely enforce these unless separately stated.
- Portability: one prompt points Codex, Claude, Hermes, and local scripts at the
  same Python files and commands.
- Failure isolation: lane routing makes it clear which class of work failed.
  Normal execution often mixes planning, coding, testing, and review into one
  opaque flow.

## Token Usage and Estimated Savings

Token numbers below are deterministic local estimates using
`ceil(UTF-8 bytes / 4)`. They are not provider billing measurements. The model
compares repeated chat-context orchestration against one Yool prompt plus compact
tuple envelopes.

| Scenario | Normal tokens | Yool tokens | Savings | Savings % |
|---|---:|---:|---:|---:|
| One-off prompt bootstrap | 19 | 210 | -191 | -1005.26% |
| Scale: 1,048,576 subagents | 47,185,939 | 232 | 47,185,707 | 99.9995% |
| Active execution: 256 tasks | 11,520 | 6,610 | 4,910 | 42.62% |
| Active execution: 512 tasks | 23,040 | 13,010 | 10,030 | 43.53% |

Interpretation:

- For a single tiny request, a normal instruction spends fewer tokens because it
  carries almost no execution protocol.
- For massive work, Yool wins because `batch_spawn` replaces millions of
  repeated subagent descriptions with one compact tuple envelope.
- For active multi-task execution, Yool wins once the prompt is paid once and
  subtasks move as compact tuple envelopes.
- The break-even point depends on how much context a normal agent repeats per
  subtask. In this model, Yool starts saving tokens once there are multiple
  active subtasks or any large lazy subtree.

## Limitations

- The active-execution speedup is strongest for I/O-bound, subprocess, API, LLM,
  browser, and external-tool workloads. Pure Python CPU-bound work is limited by
  the GIL unless yools delegate to subprocesses, native extensions, or remote
  workers.
- The benchmark measures the local runtime mechanics, not provider-specific
  behavior inside Claude, Codex, or Hermes.
- Token savings are estimated from prompt/orchestration shape, not from a live
  provider token meter.
- More concurrency can increase memory and scheduler overhead. The high-speed
  defaults are aggressive and should be lowered on small laptops or tight CI.

## Commands

```bash
python benchmarks/prompt_vs_normal.py --json
python benchmarks/prompt_vs_normal.py --tasks 512 --scale-agents 262144 --sleep-ms 2 --json
python benchmarks/generate_prompt_benchmark_pdf.py
python -m ruff check benchmarks/prompt_vs_normal.py
python -m ruff format --check benchmarks/prompt_vs_normal.py
```
