"""Benchmark V2 safe-speed runtime vs V1 and normal instructions.

The benchmark stays local and deterministic enough for documentation:

- normal instruction: flat planning, sequential/repeated work, no runtime guardrails;
- V1 runtime: lazy batch_spawn and fixed LaneWorkerPool fan-out;
- V2 runtime: V1 plus adaptive lanes, receipt/input cache, batching, provider
  circuit breakers, local routing, and context compression.

It does not call hosted LLMs or external APIs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
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
    CircuitOpenError,
    LaneWorkerPool,
    RuntimePolicy,
    TupleSpace,
    YoolTuple,
    build_default_space,
)

OUT_JSON = ROOT / "benchmarks" / "v2_safe_speed_results.json"
OUT_MD = ROOT / "benchmarks" / "v2_safe_speed_results.md"


@dataclass
class ProfileResult:
    scenario: str
    profile: str
    wall_ms: float
    tasks: int
    peak_kb: float
    provider_calls: int = 0
    cache_hits: int = 0
    blocked_calls: int = 0
    total_agents: int = 0
    virtual_agents: int = 0
    tokens: int = 0
    notes: str = ""

    @property
    def throughput_tasks_s(self) -> float:
        if self.wall_ms <= 0:
            return 0.0
        return self.tasks / (self.wall_ms / 1000)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["throughput_tasks_s"] = self.throughput_tasks_s
        return payload


def measure(fn: Callable[[], ProfileResult]) -> ProfileResult:
    tracemalloc.start()
    try:
        result = fn()
        _current, peak = tracemalloc.get_traced_memory()
        result.peak_kb = peak / 1024
        return result
    finally:
        tracemalloc.stop()


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text.encode("utf-8")) / 4))


def simulated_work(index: int, sleep_ms: float) -> str:
    if sleep_ms > 0:
        time.sleep(sleep_ms / 1000)
    return hashlib.blake2b(f"task:{index}".encode("utf-8"), digest_size=8).hexdigest()


def normal_flat_scale(total_agents: int) -> ProfileResult:
    def run() -> ProfileResult:
        t0 = time.perf_counter()
        agents = [{"id": index, "lane": "flat"} for index in range(total_agents)]
        wall_ms = (time.perf_counter() - t0) * 1000
        return ProfileResult(
            scenario="scale_representation",
            profile="normal instruction",
            wall_ms=wall_ms,
            tasks=total_agents,
            peak_kb=0.0,
            total_agents=len(agents),
            notes="flat list materialization",
        )

    return measure(run)


def lazy_scale(profile: str, target_agents: int, branching: int = 32) -> ProfileResult:
    depth = 1
    virtual = branching
    while virtual < target_agents:
        depth += 1
        virtual *= branching

    def run() -> ProfileResult:
        space, root = build_default_space()
        t0 = time.perf_counter()
        receipt = space.batch_spawn(
            root,
            "prompt_worker",
            depth=depth,
            branching=branching,
            compression_threshold=1024,
        )
        wall_ms = (time.perf_counter() - t0) * 1000
        snapshot = space.snapshot()
        return ProfileResult(
            scenario="scale_representation",
            profile=profile,
            wall_ms=wall_ms,
            tasks=receipt.virtual_agents,
            peak_kb=0.0,
            total_agents=snapshot["total_agents"],
            virtual_agents=snapshot["virtual_agents"],
            notes=f"lazy batch_spawn depth={depth}, branching={branching}",
        )

    return measure(run)


def normal_sequential(tasks: int, sleep_ms: float) -> ProfileResult:
    def run() -> ProfileResult:
        t0 = time.perf_counter()
        for index in range(tasks):
            simulated_work(index, sleep_ms)
        wall_ms = (time.perf_counter() - t0) * 1000
        return ProfileResult(
            scenario="active_execution",
            profile="normal instruction",
            wall_ms=wall_ms,
            tasks=tasks,
            peak_kb=0.0,
            provider_calls=tasks,
            total_agents=tasks,
            notes="sequential execution",
        )

    return measure(run)


def lane_execution(
    profile: str,
    tasks: int,
    sleep_ms: float,
    *,
    max_lane_concurrency: int,
) -> ProfileResult:
    def run() -> ProfileResult:
        policy = RuntimePolicy(
            lane_concurrency=32,
            max_lane_concurrency=max_lane_concurrency,
            queue_maxsize=8192,
        )
        space = TupleSpace(policy=policy)
        root = YoolTuple("kernel_root", (0,), "root", "main", "benchmark")
        space.out_tuple(root)
        for index in range(tasks):
            space.spawn_agent(root, "prompt_worker", {"index": index, "lane": "exec"})

        calls = 0

        def executor(tup: YoolTuple) -> str:
            nonlocal calls
            calls += 1
            return simulated_work(int(tup.data["index"]), sleep_ms)

        t0 = time.perf_counter()
        pool = LaneWorkerPool(space, policy=policy)
        pool.run_lane("exec", executor, use_cache=False)
        wall_ms = (time.perf_counter() - t0) * 1000
        snapshot = space.snapshot()
        return ProfileResult(
            scenario="active_execution",
            profile=profile,
            wall_ms=wall_ms,
            tasks=tasks,
            peak_kb=0.0,
            provider_calls=calls,
            total_agents=snapshot["total_agents"],
            notes=f"lane_concurrency=32, max_lane_concurrency={max_lane_concurrency}",
        )

    return measure(run)


def cache_workload(
    profile: str, tasks: int, unique_inputs: int, sleep_ms: float
) -> ProfileResult:
    def run() -> ProfileResult:
        calls = 0
        space = TupleSpace(policy=RuntimePolicy(cache_ttl_s=3600))

        def executor(tup: YoolTuple) -> str:
            nonlocal calls
            calls += 1
            return simulated_work(int(tup.data["input_id"]), sleep_ms)

        t0 = time.perf_counter()
        for index in range(tasks):
            input_id = index % unique_inputs
            tup = YoolTuple(
                "llm_call",
                (index,),
                "root",
                "llm",
                "benchmark",
                {"provider": "claude", "input_id": input_id},
            )
            space.execute_tuple(tup, executor, use_cache=(profile == "V2 safe-speed"))
        wall_ms = (time.perf_counter() - t0) * 1000
        cache = space.snapshot()["cache"]
        return ProfileResult(
            scenario="cache_dedupe",
            profile=profile,
            wall_ms=wall_ms,
            tasks=tasks,
            peak_kb=0.0,
            provider_calls=calls,
            cache_hits=cache["hits"],
            notes=f"{unique_inputs} unique inputs repeated across {tasks} tasks",
        )

    return measure(run)


def batching_workload(profile: str, tasks: int, batch_size: int) -> ProfileResult:
    per_call_ms = 1.0
    per_item_ms = 0.03

    def run_v1() -> ProfileResult:
        calls = 0
        t0 = time.perf_counter()
        for index in range(tasks):
            calls += 1
            time.sleep((per_call_ms + per_item_ms) / 1000)
            simulated_work(index, 0)
        wall_ms = (time.perf_counter() - t0) * 1000
        return ProfileResult(
            scenario="small_task_batching",
            profile=profile,
            wall_ms=wall_ms,
            tasks=tasks,
            peak_kb=0.0,
            provider_calls=calls,
            notes="one provider-sized call per small task",
        )

    def run_v2() -> ProfileResult:
        calls = 0
        policy = RuntimePolicy(batch_small_task_size=batch_size, lane_concurrency=32)
        space = TupleSpace(policy=policy)
        root = YoolTuple("kernel_root", (0,), "root", "main", "benchmark")
        space.out_tuple(root)
        for index in range(tasks):
            space.spawn_agent(root, "small_task", {"index": index, "lane": "batch"})

        def batch_executor(items: list[YoolTuple]) -> list[str]:
            nonlocal calls
            calls += 1
            time.sleep((per_call_ms + per_item_ms * len(items)) / 1000)
            return [simulated_work(int(item.data["index"]), 0) for item in items]

        t0 = time.perf_counter()
        LaneWorkerPool(space, policy=policy).run_lane_batched("batch", batch_executor)
        wall_ms = (time.perf_counter() - t0) * 1000
        return ProfileResult(
            scenario="small_task_batching",
            profile=profile,
            wall_ms=wall_ms,
            tasks=tasks,
            peak_kb=0.0,
            provider_calls=calls,
            notes=f"batch_size={batch_size}",
        )

    return measure(run_v2 if profile == "V2 safe-speed" else run_v1)


def circuit_breaker_workload(profile: str, tasks: int) -> ProfileResult:
    retries = 2

    def run_v1() -> ProfileResult:
        attempts = 0
        t0 = time.perf_counter()
        for _ in range(tasks):
            for _attempt in range(retries + 1):
                attempts += 1
        wall_ms = (time.perf_counter() - t0) * 1000
        return ProfileResult(
            scenario="provider_failure_control",
            profile=profile,
            wall_ms=wall_ms,
            tasks=tasks,
            peak_kb=0.0,
            provider_calls=attempts,
            blocked_calls=0,
            notes="no provider circuit breaker",
        )

    def run_v2() -> ProfileResult:
        attempts = 0
        blocked = 0
        policy = RuntimePolicy(
            api_max_retries=retries,
            api_backoff_base_ms=1,
            circuit_failure_threshold=3,
            circuit_cooldown_s=60,
        )
        space = TupleSpace(policy=policy)

        def failing_call() -> str:
            nonlocal attempts
            attempts += 1
            raise TimeoutError("simulated provider outage")

        t0 = time.perf_counter()
        for _ in range(tasks):
            try:
                space.call_with_backoff(
                    "llm-provider", failing_call, sleep_fn=lambda _s: None
                )
            except CircuitOpenError:
                blocked += 1
            except TimeoutError:
                pass
        wall_ms = (time.perf_counter() - t0) * 1000
        return ProfileResult(
            scenario="provider_failure_control",
            profile=profile,
            wall_ms=wall_ms,
            tasks=tasks,
            peak_kb=0.0,
            provider_calls=attempts,
            blocked_calls=blocked,
            notes="breaker opens after 3 provider failures",
        )

    return measure(run_v2 if profile == "V2 safe-speed" else run_v1)


def context_compression_workload(profile: str, chars: int) -> ProfileResult:
    raw_context = "A" * chars
    payload = {"provider": "claude", "context": raw_context, "prompt": "Any prompt X"}

    def run() -> ProfileResult:
        tup = YoolTuple("llm_call", (0,), "root", "llm", "benchmark", dict(payload))
        space = TupleSpace()
        t0 = time.perf_counter()
        if profile == "V2 safe-speed":
            space.compress_context(tup)
        serialized = json.dumps(tup.data, sort_keys=True, ensure_ascii=False)
        wall_ms = (time.perf_counter() - t0) * 1000
        return ProfileResult(
            scenario="context_compression",
            profile=profile,
            wall_ms=wall_ms,
            tasks=1,
            peak_kb=0.0,
            tokens=estimate_tokens(serialized),
            notes=f"{chars} char context",
        )

    return measure(run)


def run_suite() -> dict[str, Any]:
    results = [
        normal_flat_scale(131_072),
        lazy_scale("V1 high-throughput", 1_048_576),
        lazy_scale("V2 safe-speed", 1_048_576),
        normal_sequential(1024, 5.0),
        lane_execution("V1 high-throughput", 1024, 5.0, max_lane_concurrency=32),
        lane_execution("V2 safe-speed", 1024, 5.0, max_lane_concurrency=64),
        cache_workload("normal instruction", 256, 64, 1.0),
        cache_workload("V1 high-throughput", 256, 64, 1.0),
        cache_workload("V2 safe-speed", 256, 64, 1.0),
        batching_workload("normal instruction", 512, 32),
        batching_workload("V1 high-throughput", 512, 32),
        batching_workload("V2 safe-speed", 512, 32),
        circuit_breaker_workload("normal instruction", 64),
        circuit_breaker_workload("V1 high-throughput", 64),
        circuit_breaker_workload("V2 safe-speed", 64),
        context_compression_workload("normal instruction", 20_000),
        context_compression_workload("V1 high-throughput", 20_000),
        context_compression_workload("V2 safe-speed", 20_000),
    ]
    return summarise(results)


def summarise(results: list[ProfileResult]) -> dict[str, Any]:
    by_key = {(item.scenario, item.profile): item for item in results}

    def gain(
        scenario: str,
        baseline: str,
        improved: str,
        *,
        value: str = "wall_ms",
        lower_is_better: bool = True,
    ) -> dict[str, Any]:
        base = by_key[(scenario, baseline)]
        new = by_key[(scenario, improved)]
        base_value = getattr(base, value)
        new_value = getattr(new, value)
        if lower_is_better:
            ratio = base_value / new_value if new_value else None
            pct = ((base_value - new_value) / base_value * 100) if base_value else 0.0
        else:
            ratio = new_value / base_value if base_value else None
            pct = ((new_value - base_value) / base_value * 100) if base_value else 0.0
        return {
            "scenario": scenario,
            "baseline": baseline,
            "improved": improved,
            "metric": value,
            "baseline_value": base_value,
            "improved_value": new_value,
            "ratio": ratio,
            "percent": pct,
        }

    comparisons = [
        gain("scale_representation", "normal instruction", "V2 safe-speed"),
        gain("active_execution", "normal instruction", "V1 high-throughput"),
        gain("active_execution", "normal instruction", "V2 safe-speed"),
        gain("active_execution", "V1 high-throughput", "V2 safe-speed"),
        gain("cache_dedupe", "normal instruction", "V2 safe-speed"),
        gain(
            "cache_dedupe",
            "normal instruction",
            "V2 safe-speed",
            value="provider_calls",
        ),
        gain("cache_dedupe", "V1 high-throughput", "V2 safe-speed"),
        gain(
            "cache_dedupe",
            "V1 high-throughput",
            "V2 safe-speed",
            value="provider_calls",
        ),
        gain("small_task_batching", "normal instruction", "V2 safe-speed"),
        gain(
            "small_task_batching",
            "normal instruction",
            "V2 safe-speed",
            value="provider_calls",
        ),
        gain("small_task_batching", "V1 high-throughput", "V2 safe-speed"),
        gain(
            "small_task_batching",
            "V1 high-throughput",
            "V2 safe-speed",
            value="provider_calls",
        ),
        gain(
            "provider_failure_control",
            "normal instruction",
            "V2 safe-speed",
            value="provider_calls",
        ),
        gain(
            "provider_failure_control",
            "V1 high-throughput",
            "V2 safe-speed",
            value="provider_calls",
        ),
        gain(
            "context_compression",
            "normal instruction",
            "V2 safe-speed",
            value="tokens",
        ),
        gain(
            "context_compression", "V1 high-throughput", "V2 safe-speed", value="tokens"
        ),
    ]
    return {
        "title": "Yool Safe-Speed Benchmark V2",
        "run_date": "2026-05-21",
        "environment": {
            "python": sys.version.split()[0],
            "repository": "wesleysimplicio/simplicio-prompt",
            "branch": "codex/lane-concurrency-runtime",
            "v1_definition": "high-throughput runtime with fixed lane ceiling and safe-speed controls disabled",
            "v2_definition": "V1 plus cache, adaptive lanes, backoff, circuit breaker, batching, context compression, local routing, and idempotent speculation",
        },
        "results": [item.to_dict() for item in results],
        "comparisons": comparisons,
        "median_wall_ms": statistics.median(item.wall_ms for item in results),
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    results = payload["results"]
    comparisons = payload["comparisons"]

    def rows_for(scenario: str) -> list[dict[str, Any]]:
        return [item for item in results if item["scenario"] == scenario]

    lines = [
        "# Yool Safe-Speed Benchmark V2",
        "",
        "Run date: 2026-05-21",
        "",
        "This report compares three execution styles:",
        "",
        "- Normal instruction: generic prompt, flat or repeated work, no runtime guardrails.",
        "- V1 high-throughput: lazy `batch_spawn` and fixed `LaneWorkerPool` fan-out.",
        "- V2 safe-speed: V1 plus cache, adaptive lanes, backoff, provider circuit breaker, batching, context compression, local routing, and idempotent speculation.",
        "",
        "The benchmark is local. It does not call hosted LLMs or external APIs.",
        "",
    ]

    lines.extend(
        _scenario_table("Scale Representation", rows_for("scale_representation"))
    )
    lines.extend(_scenario_table("Active Execution", rows_for("active_execution")))
    lines.extend(_scenario_table("Cache Dedupe", rows_for("cache_dedupe")))
    lines.extend(
        _scenario_table("Small Task Batching", rows_for("small_task_batching"))
    )
    lines.extend(
        _scenario_table(
            "Provider Failure Control", rows_for("provider_failure_control")
        )
    )
    lines.extend(
        _scenario_table("Context Compression", rows_for("context_compression"))
    )

    lines.extend(["## Gains", ""])
    lines.append("| Scenario | Baseline | Improved | Metric | Ratio | Gain |")
    lines.append("|---|---|---|---|---:|---:|")
    for item in comparisons:
        ratio = "n/a" if item["ratio"] is None else f"{item['ratio']:.2f}x"
        row = {**item, "ratio_label": ratio}
        lines.append(
            "| {scenario} | {baseline} | {improved} | {metric} | {ratio_label} | {percent:.2f}% |".format(
                **row,
            )
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- V2 keeps the V1 lazy million-agent scale model.",
        "- V2 improves active fan-out by allowing lanes to grow toward the configured ceiling when backlog is high.",
        "- Cache reduces repeated provider calls when the same `yool + data` appears again.",
        "- Batching turns many tiny provider/API-sized operations into fewer bounded calls.",
        "- Circuit breaker reduces hammering during provider outages, which is the anti-ban part of the speed model.",
        "- Context compression lowers token transfer before LLM calls while preserving a digest and preview.",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python benchmarks/v2_safe_speed_benchmark.py --json-output benchmarks/v2_safe_speed_results.json --md-output benchmarks/v2_safe_speed_results.md",
        "python benchmarks/generate_v2_benchmark_pdf.py",
        "```",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def _scenario_table(title: str, rows: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    lines.append(
        "| Profile | Tasks | Wall ms | Throughput/s | Peak KiB | Provider calls | Cache hits | Blocked | Tokens | Notes |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in rows:
        lines.append(
            "| {profile} | {tasks:,} | {wall_ms:.2f} | {throughput_tasks_s:.1f} | {peak_kb:.1f} | {provider_calls:,} | {cache_hits:,} | {blocked_calls:,} | {tokens:,} | {notes} |".format(
                **row
            )
        )
    lines.append("")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--md-output", type=Path, default=OUT_MD)
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()

    payload = run_suite()
    args.json_output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_markdown(payload, args.md_output)
    if args.print_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(args.json_output)
        print(args.md_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
