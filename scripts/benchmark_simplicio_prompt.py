#!/usr/bin/env python
"""Local benchmark for the SIMPLICIO_PROMPT plugin overlay.

This benchmark intentionally does not call a hosted model. It measures the
local pre-LLM message preparation cost and rough token footprint for:

1. a normal/V1 instruction baseline with no overlay,
2. the earlier per-message manual SIMPLICIO_PROMPT adoption path with local file
   paths,
3. the automatic always-on SIMPLICIO_PROMPT plugin overlay loaded from the vendored
   runtime snapshot.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from plugins.simplicio_prompt import SIMPLICIO_PROMPT_CONTEXT


USER_MESSAGE = (
    "Refactor the dashboard layout, update tests, and report the benchmark difference."
)

MANUAL_SIMPLICIO_PROMPT = """Use the bundled local SIMPLICIO_PROMPT snapshot under
plugins/simplicio_prompt/vendor/simplicio_prompt. Do not fetch an external
repository at runtime.
Read before editing:
plugins/simplicio_prompt/vendor/simplicio_prompt/YOOL_TUPLE_HAMT.md,
plugins/simplicio_prompt/vendor/simplicio_prompt/kernel/yool_tuple_kernel.py,
plugins/simplicio_prompt/vendor/simplicio_prompt/guardrails/cpu_throttle.py,
plugins/simplicio_prompt/vendor/simplicio_prompt/guardrails/disk_gc.py,
plugins/simplicio_prompt/vendor/simplicio_prompt/examples/python/receipts.py,
and plugins/simplicio_prompt/vendor/simplicio_prompt/scripts/build_hamt.py.

For any prompt or message, not only "Implement X", decompose the user's intent
into a Hilbert-indexed graph, create a root tuple, use batch_spawn(depth,
branching, compression_threshold) for 1,000,000+ subagents without enumeration,
execute active work with spawn_agent, route by out/in/rd, route_packet and
scan_index, apply hookwall, compress_token and prune_idle, and use
LaneWorkerPool respecting YOOL_TUPLE_* environment variables.

SIMPLICIO_PROMPT V2 safe-speed policy: cache aggressively by receipt/input hash,
use adaptive lane pools, apply backoff with jitter, maintain circuit breakers per
provider, batch small tasks, compress prompt/context before expensive model
calls, route simple deterministic work to local code before an LLM, and use
speculative execution only for idempotent work. Respect rate limits and provider
terms.

Respond exactly with:
[Tuple Space Snapshot]
[Active Agents/Subagents]
[Total Agents/Subagents]
[Próximo Yool a executar]
[Resultado parcial]"""


def _rough_tokens(messages: List[Dict[str, str]]) -> int:
    chars = sum(len(str(message)) for message in messages)
    return max(1, chars // 4)


def _normal_messages() -> List[Dict[str, str]]:
    return [{"role": "user", "content": USER_MESSAGE}]


def _manual_prompt_messages() -> List[Dict[str, str]]:
    return [
        {"role": "user", "content": MANUAL_SIMPLICIO_PROMPT + "\n\n" + USER_MESSAGE}
    ]


def _plugin_prompt_messages() -> List[Dict[str, str]]:
    return [
        {
            "role": "user",
            "content": USER_MESSAGE + "\n\n" + SIMPLICIO_PROMPT_CONTEXT,
        }
    ]


def _measure(
    builder: Callable[[], List[Dict[str, str]]], iterations: int
) -> Dict[str, float]:
    samples_ns: list[int] = []
    messages: List[Dict[str, str]] = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        messages = builder()
        samples_ns.append(time.perf_counter_ns() - start)

    samples_ms = [sample / 1_000_000 for sample in samples_ns]
    return {
        "median_ms": statistics.median(samples_ms),
        "p95_ms": statistics.quantiles(samples_ms, n=100)[94],
        "rough_tokens": float(_rough_tokens(messages)),
        "chars": float(sum(len(str(message)) for message in messages)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=10_000)
    args = parser.parse_args()

    cases = {
        "normal_instruction": _normal_messages,
        "manual_simplicio_prompt_per_message": _manual_prompt_messages,
        "simplicio_prompt_plugin_always_on": _plugin_prompt_messages,
    }
    results = {
        name: _measure(builder, args.iterations) for name, builder in cases.items()
    }

    normal = results["normal_instruction"]["rough_tokens"]
    manual = results["manual_simplicio_prompt_per_message"]["rough_tokens"]
    plugin = results["simplicio_prompt_plugin_always_on"]["rough_tokens"]
    savings_vs_manual = ((manual - plugin) / manual * 100.0) if manual else 0.0
    overhead_vs_normal = ((plugin - normal) / normal * 100.0) if normal else 0.0

    print("SIMPLICIO_PROMPT local benchmark")
    print(f"iterations: {args.iterations}")
    print(
        "baseline_note: V2 means the bundled SIMPLICIO_PROMPT runtime snapshot; "
        "local comparisons use normal instruction and manual per-message adoption paths."
    )
    print("")
    print("| case | median ms/build | p95 ms/build | rough input tokens | chars |")
    print("|---|---:|---:|---:|---:|")
    for name, data in results.items():
        print(
            f"| {name} | {data['median_ms']:.6f} | {data['p95_ms']:.6f} | "
            f"{int(data['rough_tokens'])} | {int(data['chars'])} |"
        )
    print("")
    print(f"plugin_token_delta_vs_manual_simplicio_pct: {savings_vs_manual:.2f}")
    print(f"plugin_token_overhead_vs_normal_pct: {overhead_vs_normal:.2f}")
    print(
        "note: hosted model latency, output quality, and tool success rate are not measured here."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
