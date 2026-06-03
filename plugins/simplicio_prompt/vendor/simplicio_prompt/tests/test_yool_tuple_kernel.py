from __future__ import annotations

import threading
import time
import unittest

from kernel.yool_tuple_kernel import (
    CircuitOpenError,
    LaneWorkerPool,
    RuntimePolicy,
    TupleSpace,
    YoolTuple,
    build_default_space,
)


class TupleKernelTests(unittest.TestCase):
    def test_batch_spawn_represents_million_agents_without_flat_materialization(
        self,
    ) -> None:
        space, root = build_default_space()

        receipt = space.batch_spawn(
            root,
            "codex_worker",
            depth=4,
            branching=32,
            compression_threshold=128,
        )

        snapshot = space.snapshot()
        self.assertEqual(receipt.virtual_agents, 32**4)
        self.assertGreaterEqual(snapshot["total_agents"], 1_000_000)
        self.assertLess(snapshot["active_agents"], 128)

    def test_compress_token_removes_inactive_tuple_from_lane(self) -> None:
        space, root = build_default_space()
        agent_id = space.spawn_agent(root, "hamt_builder", {"status": "ready"})

        token = space.compress_token(agent_id)

        self.assertIsNotNone(token)
        self.assertIsNone(space.rd_tuple({"authority": f"subagent_{agent_id}"}))
        self.assertEqual(space.snapshot()["compressed_agents"], 1)

    def test_lane_worker_pool_runs_same_lane_tuples_concurrently(self) -> None:
        policy = RuntimePolicy(lane_concurrency=4, max_lane_concurrency=4)
        space = TupleSpace(policy=policy)
        root = YoolTuple("kernel_root", (0,), "root", "dev", "user")
        space.out_tuple(root)
        for index in range(4):
            space.spawn_agent(root, "dev_worker", {"index": index, "lane": "worker"})

        lock = threading.Lock()
        active = 0
        max_active = 0

        def executor(tup: YoolTuple) -> str:
            nonlocal active, max_active
            with lock:
                active += 1
                max_active = max(max_active, active)
            try:
                time.sleep(0.05)
                return tup.yool
            finally:
                with lock:
                    active -= 1

        pool = LaneWorkerPool(space, policy=policy)
        results = pool.run_lane("worker", executor)

        self.assertEqual(len([item for item in results if item is not None]), 4)
        self.assertGreaterEqual(max_active, 2)

    def test_lane_worker_pool_adapts_concurrency_by_backlog_and_errors(self) -> None:
        policy = RuntimePolicy(lane_concurrency=4, max_lane_concurrency=8)
        space = TupleSpace(policy=policy)
        root = YoolTuple("kernel_root", (0,), "root", "main", "user")
        space.out_tuple(root)
        for index in range(20):
            space.spawn_agent(root, "worker", {"index": index, "lane": "worker"})

        pool = LaneWorkerPool(space, policy=policy)
        self.assertEqual(pool.concurrency_for("worker"), 8)

        for _ in range(4):
            pool.lane_metrics["worker"].record(10, ok=False)

        self.assertEqual(pool.concurrency_for("worker"), 4)

    def test_receipt_cache_skips_repeated_work_by_input_hash(self) -> None:
        policy = RuntimePolicy(cache_ttl_s=60)
        space = TupleSpace(policy=policy)
        first = YoolTuple("llm_call", (1,), "a", "llm", "user", {"prompt": "same"})
        second = YoolTuple("llm_call", (2,), "b", "llm", "user", {"prompt": "same"})
        calls = 0

        def executor(tup: YoolTuple) -> str:
            nonlocal calls
            calls += 1
            return f"ok:{tup.data['prompt']}"

        self.assertEqual(space.execute_tuple(first, executor), "ok:same")
        self.assertEqual(space.execute_tuple(second, executor), "ok:same")

        self.assertEqual(calls, 1)
        self.assertTrue(any(item.startswith("cache_hit@") for item in second.receipts))

    def test_backoff_and_circuit_breaker_stop_repeated_provider_failures(self) -> None:
        policy = RuntimePolicy(
            api_max_retries=1,
            api_backoff_base_ms=1,
            circuit_failure_threshold=2,
            circuit_cooldown_s=60,
        )
        space = TupleSpace(policy=policy)
        sleeps: list[float] = []

        def failing_call() -> str:
            raise TimeoutError("temporary provider failure")

        with self.assertRaises(TimeoutError):
            space.call_with_backoff(
                "llm-provider",
                failing_call,
                sleep_fn=sleeps.append,
            )
        with self.assertRaises(CircuitOpenError):
            space.call_with_backoff(
                "llm-provider",
                lambda: "blocked",
                sleep_fn=sleeps.append,
            )

        self.assertEqual(len(sleeps), 1)
        self.assertTrue(space.snapshot()["circuit_breakers"]["llm-provider"]["open"])

    def test_context_compression_preserves_digest_before_llm_call(self) -> None:
        policy = RuntimePolicy(context_compression_chars=128)
        space = TupleSpace(policy=policy)
        payload = "x" * 500
        tup = YoolTuple(
            "llm_call",
            (1,),
            "root",
            "llm",
            "user",
            {"provider": "claude", "context": payload},
        )

        changed = space.compress_context(tup)

        self.assertTrue(changed)
        self.assertTrue(tup.data["context"]["compressed"])
        self.assertEqual(tup.data["context"]["original_chars"], len(payload))
        self.assertIn("digest", tup.data["context"])

    def test_local_yool_routes_simple_work_without_llm_executor(self) -> None:
        space = TupleSpace()
        tup = YoolTuple("sha256_local", (1,), "root", "local", "user", {"value": "x"})
        space.register_local_yool("sha256_local", lambda t: t.data["value"] * 2)

        result = space.execute_tuple(
            tup,
            lambda _t: (_ for _ in ()).throw(AssertionError("should not call LLM")),
        )

        self.assertEqual(result, "xx")
        self.assertTrue(any(item.startswith("local_route@") for item in tup.receipts))

    def test_batching_groups_small_lane_tasks(self) -> None:
        policy = RuntimePolicy(batch_small_task_size=3, lane_concurrency=2)
        space = TupleSpace(policy=policy)
        root = YoolTuple("kernel_root", (0,), "root", "main", "user")
        space.out_tuple(root)
        for index in range(7):
            space.spawn_agent(root, "small_task", {"index": index, "lane": "batch"})

        batch_sizes: list[int] = []

        def batch_executor(items: list[YoolTuple]) -> list[int]:
            batch_sizes.append(len(items))
            return [item.data["index"] for item in items]

        pool = LaneWorkerPool(space, policy=policy)
        results = pool.run_lane_batched("batch", batch_executor)

        self.assertEqual(sorted(results), list(range(7)))
        self.assertEqual(sorted(batch_sizes), [1, 3, 3])

    def test_speculative_executor_only_runs_for_idempotent_tasks(self) -> None:
        policy = RuntimePolicy(lane_concurrency=1)
        space = TupleSpace(policy=policy)
        root = YoolTuple("kernel_root", (0,), "root", "main", "user")
        space.out_tuple(root)
        safe_id = space.spawn_agent(
            root, "maybe_spec", {"lane": "spec", "idempotent": True, "value": "safe"}
        )
        unsafe_id = space.spawn_agent(
            root, "maybe_spec", {"lane": "spec", "idempotent": False, "value": "unsafe"}
        )
        speculative_calls = 0

        def primary(tup: YoolTuple) -> str:
            if tup.data["value"] == "safe":
                time.sleep(0.02)
            return f"primary:{tup.data['value']}"

        def speculative(tup: YoolTuple) -> str:
            nonlocal speculative_calls
            speculative_calls += 1
            return f"spec:{tup.data['value']}"

        pool = LaneWorkerPool(space, policy=policy)
        results = pool.run_lane("spec", primary, speculative_executor=speculative)

        self.assertEqual(len(results), 2)
        self.assertEqual(speculative_calls, 1)
        self.assertIsNotNone(safe_id)
        self.assertIsNotNone(unsafe_id)


if __name__ == "__main__":
    unittest.main()
