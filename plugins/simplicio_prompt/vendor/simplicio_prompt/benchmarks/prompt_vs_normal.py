"""Benchmark normal instruction flow vs the Yool runtime prompt flow.

This does not call a hosted LLM. It measures the operational behavior that the
prompt requires from an executor:

- normal instruction: flat planning + sequential execution;
- yool prompt: lazy batch_spawn + lane worker fan-out + tuple receipts.
"""

from __future__ import annotations

import argparse
import math
import hashlib
import json
import statistics
import sys
import time
import tracemalloc
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kernel.yool_tuple_kernel import (  # noqa: E402
    LaneWorkerPool,
    RuntimePolicy,
    TupleSpace,
    YoolTuple,
    build_default_space,
)

YOOL_PROMPT = """Use o repo canonico https://github.com/wesleysimplicio/simplicio-prompt.
Leia antes de editar: YOOL_TUPLE_HAMT.md, kernel/yool_tuple_kernel.py,
guardrails/cpu_throttle.py, guardrails/disk_gc.py, examples/python/receipts.py
e scripts/build_hamt.py.

Ao receber qualquer prompt ou mensagem X, sem exigir "Implement X": decomponha em grafo Hilbert-indexed, crie tuple raiz,
use batch_spawn(depth, branching, compression_threshold) para 1.000.000+
subagents sem enumerar, execute work ativo com spawn_agent, roteie por out/in/rd,
route_packet e scan_index, aplique hookwall, compress_token e prune_idle, e use
LaneWorkerPool respeitando YOOL_TUPLE_* env vars.

Execute:
python kernel/yool_tuple_kernel.py

Responda SEMPRE exatamente neste formato (sem variações):
[Tuple Space Snapshot]
[Active Agents/Subagents]
[Total Agents/Subagents]
[Próximo Yool a executar]
[Resultado parcial]"""

NORMAL_INSTRUCTION = (
    "Handle any prompt quickly. Use agents if useful. Report the result when finished."
)
NORMAL_REPEATED_CONTEXT = (
    NORMAL_INSTRUCTION
    + "\nSubagent {index}: carry the orchestration rules, task goal, route, status, "
    "and result summary in chat context."
)
YOOL_TUPLE_ENVELOPE = (
    '{"yool":"prompt_worker","lane":"benchmark","args":{"index":0},'
    '"receipts":[],"route":"tuple-space"}'
)
YOOL_BATCH_ENVELOPE = (
    "batch_spawn(depth=4, branching=32, compression_threshold=1024, "
    "virtual_agents=1048576)"
)


@dataclass
class BenchmarkResult:
    profile: str
    phase: str
    tasks: int
    wall_ms: float
    peak_kb: float
    active_agents: int
    compressed_agents: int
    virtual_agents: int
    total_agents: int
    receipts: int
    notes: str = ""

    @property
    def throughput_tasks_s(self) -> float:
        if self.wall_ms <= 0:
            return 0.0
        return self.tasks / (self.wall_ms / 1000)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["throughput_tasks_s"] = self.throughput_tasks_s
        return data


@dataclass
class TokenModelResult:
    scenario: str
    normal_tokens: int
    yool_tokens: int
    savings_tokens: int
    savings_pct: float
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def measure(fn: Callable[[], BenchmarkResult]) -> BenchmarkResult:
    tracemalloc.start()
    try:
        result = fn()
        _current, peak = tracemalloc.get_traced_memory()
        result.peak_kb = peak / 1024
        return result
    finally:
        tracemalloc.stop()


def simulated_yool_work(index: int, sleep_ms: float) -> str:
    if sleep_ms > 0:
        time.sleep(sleep_ms / 1000)
    payload = f"task:{index}".encode("utf-8")
    return hashlib.blake2b(payload, digest_size=8).hexdigest()


def estimate_tokens(text: str) -> int:
    """Deterministic rough estimate: about four UTF-8 chars per token."""
    return max(1, math.ceil(len(text.encode("utf-8")) / 4))


def normal_flat_scale(total_agents: int) -> BenchmarkResult:
    def run() -> BenchmarkResult:
        t0 = time.perf_counter()
        agents = [
            {"id": index, "yool": "normal_worker", "lane": "flat"}
            for index in range(total_agents)
        ]
        wall_ms = (time.perf_counter() - t0) * 1000
        return BenchmarkResult(
            profile="normal instruction",
            phase="flat materialization",
            tasks=total_agents,
            wall_ms=wall_ms,
            peak_kb=0.0,
            active_agents=len(agents),
            compressed_agents=0,
            virtual_agents=0,
            total_agents=len(agents),
            receipts=0,
            notes="flat Python list of subagents",
        )

    return measure(run)


def yool_lazy_scale(
    total_agents: int, branching: int, threshold: int
) -> BenchmarkResult:
    depth = 1
    virtual = branching
    while virtual < total_agents:
        depth += 1
        virtual *= branching

    def run() -> BenchmarkResult:
        space, root = build_default_space()
        t0 = time.perf_counter()
        receipt = space.batch_spawn(
            root,
            "prompt_worker",
            depth=depth,
            branching=branching,
            compression_threshold=threshold,
        )
        wall_ms = (time.perf_counter() - t0) * 1000
        snapshot = space.snapshot()
        return BenchmarkResult(
            profile="yool prompt",
            phase="lazy batch_spawn",
            tasks=receipt.virtual_agents,
            wall_ms=wall_ms,
            peak_kb=0.0,
            active_agents=snapshot["active_agents"],
            compressed_agents=snapshot["compressed_agents"],
            virtual_agents=snapshot["virtual_agents"],
            total_agents=snapshot["total_agents"],
            receipts=1,
            notes=f"depth={depth}, branching={branching}",
        )

    return measure(run)


def normal_sequential_execution(tasks: int, sleep_ms: float) -> BenchmarkResult:
    def run() -> BenchmarkResult:
        receipts = []
        t0 = time.perf_counter()
        for index in range(tasks):
            receipts.append(simulated_yool_work(index, sleep_ms))
        wall_ms = (time.perf_counter() - t0) * 1000
        return BenchmarkResult(
            profile="normal instruction",
            phase="sequential execution",
            tasks=tasks,
            wall_ms=wall_ms,
            peak_kb=0.0,
            active_agents=tasks,
            compressed_agents=0,
            virtual_agents=0,
            total_agents=tasks,
            receipts=len(receipts),
            notes="single worker, no lane fan-out",
        )

    return measure(run)


def yool_lane_execution(
    tasks: int, sleep_ms: float, concurrency: int, max_concurrency: int
) -> BenchmarkResult:
    def run() -> BenchmarkResult:
        t0 = time.perf_counter()
        policy = RuntimePolicy(
            lane_concurrency=concurrency,
            max_lane_concurrency=max_concurrency,
            cpu_quota_pct=95,
            queue_maxsize=8192,
            compression_threshold=1024,
        )
        space = TupleSpace(policy=policy)
        root = YoolTuple("kernel_root", (0,), "root", "runtime", "benchmark")
        space.out_tuple(root)
        for index in range(tasks):
            space.spawn_agent(
                root,
                "prompt_worker",
                {"index": index, "lane": "benchmark"},
            )

        def executor(tup: YoolTuple) -> str:
            result = simulated_yool_work(int(tup.data["index"]), sleep_ms)
            tup.receipts.append(f"ok:{result}")
            return result

        pool = LaneWorkerPool(space, policy=policy)
        receipts = [
            item for item in pool.run_lane("benchmark", executor) if item is not None
        ]
        wall_ms = (time.perf_counter() - t0) * 1000
        snapshot = space.snapshot()
        return BenchmarkResult(
            profile="yool prompt",
            phase="lane fan-out execution",
            tasks=tasks,
            wall_ms=wall_ms,
            peak_kb=0.0,
            active_agents=snapshot["active_agents"],
            compressed_agents=snapshot["compressed_agents"],
            virtual_agents=snapshot["virtual_agents"],
            total_agents=snapshot["total_agents"],
            receipts=len(receipts),
            notes=f"lane_concurrency={concurrency}, max_lane_concurrency={max_concurrency}",
        )

    return measure(run)


def summarise(results: list[BenchmarkResult]) -> dict[str, Any]:
    by_phase: dict[tuple[str, str], BenchmarkResult] = {}
    for result in results:
        by_phase[(result.profile, result.phase)] = result

    def compare(normal_phase: str, yool_phase: str) -> dict[str, Any] | None:
        normal = by_phase.get(("normal instruction", normal_phase))
        yool = by_phase.get(("yool prompt", yool_phase))
        if normal is None or yool is None:
            return None
        return {
            "speedup_x": normal.wall_ms / yool.wall_ms if yool.wall_ms else None,
            "peak_memory_reduction_x": normal.peak_kb / yool.peak_kb
            if yool.peak_kb
            else None,
            "normal_phase": normal_phase,
            "yool_phase": yool_phase,
            "normal_wall_ms": normal.wall_ms,
            "yool_wall_ms": yool.wall_ms,
            "normal_peak_kb": normal.peak_kb,
            "yool_peak_kb": yool.peak_kb,
            "normal_tasks": normal.tasks,
            "yool_tasks": yool.tasks,
        }

    comparisons: dict[str, Any] = {}
    scale = compare("flat materialization", "lazy batch_spawn")
    if scale is not None:
        comparisons["scale_representation"] = scale
    execution = compare("sequential execution", "lane fan-out execution")
    if execution is not None:
        comparisons["active_execution"] = execution

    return {
        "results": [item.to_dict() for item in results],
        "comparisons": comparisons,
        "token_model": [item.to_dict() for item in token_model()],
        "token_assumptions": {
            "method": "rough local estimate using ceil(utf8_bytes / 4)",
            "normal_instruction_tokens": estimate_tokens(NORMAL_INSTRUCTION),
            "yool_prompt_tokens": estimate_tokens(YOOL_PROMPT),
            "normal_repeated_context_tokens": estimate_tokens(
                NORMAL_REPEATED_CONTEXT.format(index=0)
            ),
            "yool_tuple_envelope_tokens": estimate_tokens(YOOL_TUPLE_ENVELOPE),
        },
        "wall_ms_median": statistics.median(item.wall_ms for item in results),
    }


def token_model() -> list[TokenModelResult]:
    prompt_tokens = estimate_tokens(YOOL_PROMPT)
    normal_instruction_tokens = estimate_tokens(NORMAL_INSTRUCTION)
    normal_repeated_tokens = estimate_tokens(NORMAL_REPEATED_CONTEXT.format(index=0))
    tuple_tokens = estimate_tokens(YOOL_TUPLE_ENVELOPE)
    batch_tokens = estimate_tokens(YOOL_BATCH_ENVELOPE)

    scale_agents = 1_048_576
    normal_scale = normal_instruction_tokens + normal_repeated_tokens * scale_agents
    yool_scale = prompt_tokens + batch_tokens

    active_tasks = 256
    normal_active = normal_repeated_tokens * active_tasks
    yool_active = prompt_tokens + tuple_tokens * active_tasks

    active_large = 512
    normal_active_large = normal_repeated_tokens * active_large
    yool_active_large = prompt_tokens + tuple_tokens * active_large

    one_off_normal = normal_instruction_tokens
    one_off_yool = prompt_tokens

    return [
        _token_result(
            "one_off_prompt_bootstrap",
            one_off_normal,
            one_off_yool,
            "One-off call: normal instruction is cheaper, but it lacks execution protocol.",
        ),
        _token_result(
            "scale_1m_subagents",
            normal_scale,
            yool_scale,
            "Normal path enumerates/repeats subagent context; Yool path sends one batch_spawn envelope.",
        ),
        _token_result(
            "active_256_tasks",
            normal_active,
            yool_active,
            "Yool prompt is paid once; active work uses compact tuple envelopes.",
        ),
        _token_result(
            "active_512_tasks",
            normal_active_large,
            yool_active_large,
            "Savings grow as repeated chat-context orchestration is replaced by tuple envelopes.",
        ),
    ]


def _token_result(
    scenario: str, normal_tokens: int, yool_tokens: int, notes: str
) -> TokenModelResult:
    savings = normal_tokens - yool_tokens
    savings_pct = (savings / normal_tokens * 100) if normal_tokens else 0.0
    return TokenModelResult(
        scenario=scenario,
        normal_tokens=normal_tokens,
        yool_tokens=yool_tokens,
        savings_tokens=savings,
        savings_pct=savings_pct,
        notes=notes,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=int, default=256)
    parser.add_argument("--scale-agents", type=int, default=131_072)
    parser.add_argument("--sleep-ms", type=float, default=2.0)
    parser.add_argument("--lane-concurrency", type=int, default=32)
    parser.add_argument("--max-lane-concurrency", type=int, default=64)
    parser.add_argument("--compression-threshold", type=int, default=1024)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = [
        normal_flat_scale(args.scale_agents),
        yool_lazy_scale(
            args.scale_agents, branching=32, threshold=args.compression_threshold
        ),
        normal_sequential_execution(args.tasks, args.sleep_ms),
        yool_lane_execution(
            args.tasks,
            args.sleep_ms,
            concurrency=args.lane_concurrency,
            max_concurrency=args.max_lane_concurrency,
        ),
    ]
    payload = summarise(results)

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("Prompt benchmark")
        for item in payload["results"]:
            print(
                f"- {item['profile']} / {item['phase']}: "
                f"{item['wall_ms']:.2f} ms, "
                f"{item['throughput_tasks_s']:.1f} tasks/s, "
                f"peak={item['peak_kb']:.1f} KiB, "
                f"total_agents={item['total_agents']}"
            )
        print(json.dumps(payload["comparisons"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
