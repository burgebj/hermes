"""Reference Tuple-Space + Yool kernel.

The kernel keeps the repository intentionally dependency-free while showing the
production shape expected by the spec:

- Linda-style tuple-space primitives: out_tuple, in_tuple, rd_tuple.
- Capability-addressed yools with Hilbert-like tuple map positions.
- Hookwall capability checks.
- Hierarchical batch_spawn for 1,000,000+ virtual subagents without a flat list.
- compress_token/pruning for inactive materialized agents.
- Lane worker fan-out controlled by environment-driven runtime policy.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import threading
import time
import weakref
from collections import OrderedDict, defaultdict
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, DefaultDict, Dict, Iterable, List, Optional, Tuple


DEFAULT_LANE_CONCURRENCY = 32
DEFAULT_MAX_LANE_CONCURRENCY = 64
DEFAULT_CPU_QUOTA_PCT = 95
DEFAULT_QUEUE_MAXSIZE = 8192
DEFAULT_COMPRESSION_THRESHOLD = 1024
DEFAULT_CACHE_MAX_ENTRIES = 16384
DEFAULT_CACHE_TTL_S = 3600
DEFAULT_API_MAX_RETRIES = 3
DEFAULT_API_BACKOFF_BASE_MS = 100
DEFAULT_API_BACKOFF_MAX_MS = 5000
DEFAULT_CIRCUIT_FAILURE_THRESHOLD = 5
DEFAULT_CIRCUIT_COOLDOWN_S = 30
DEFAULT_BATCH_SMALL_TASK_SIZE = 32
DEFAULT_CONTEXT_COMPRESSION_CHARS = 6000


def _positive_int_from_env(names: Iterable[str], default: int) -> int:
    for name in names:
        value = os.getenv(name)
        if value is None or not value.strip():
            continue
        try:
            parsed = int(value)
        except ValueError:
            return default
        return parsed if parsed > 0 else default
    return default


def _positive_float_from_env(names: Iterable[str], default: float) -> float:
    for name in names:
        value = os.getenv(name)
        if value is None or not value.strip():
            continue
        try:
            parsed = float(value)
        except ValueError:
            return default
        return parsed if parsed > 0 else default
    return default


@dataclass(frozen=True)
class RuntimePolicy:
    """Host-aware runtime policy, with env aliases for adoption in agents/IDEs."""

    lane_concurrency: int = DEFAULT_LANE_CONCURRENCY
    max_lane_concurrency: int = DEFAULT_MAX_LANE_CONCURRENCY
    cpu_quota_pct: int = DEFAULT_CPU_QUOTA_PCT
    queue_maxsize: int = DEFAULT_QUEUE_MAXSIZE
    compression_threshold: int = DEFAULT_COMPRESSION_THRESHOLD
    cache_max_entries: int = DEFAULT_CACHE_MAX_ENTRIES
    cache_ttl_s: float = DEFAULT_CACHE_TTL_S
    api_max_retries: int = DEFAULT_API_MAX_RETRIES
    api_backoff_base_ms: int = DEFAULT_API_BACKOFF_BASE_MS
    api_backoff_max_ms: int = DEFAULT_API_BACKOFF_MAX_MS
    circuit_failure_threshold: int = DEFAULT_CIRCUIT_FAILURE_THRESHOLD
    circuit_cooldown_s: float = DEFAULT_CIRCUIT_COOLDOWN_S
    batch_small_task_size: int = DEFAULT_BATCH_SMALL_TASK_SIZE
    context_compression_chars: int = DEFAULT_CONTEXT_COMPRESSION_CHARS

    @classmethod
    def from_env(cls) -> "RuntimePolicy":
        requested = _positive_int_from_env(
            ("YOOL_TUPLE_LANE_CONCURRENCY", "YOOL_LANE_CONCURRENCY"),
            DEFAULT_LANE_CONCURRENCY,
        )
        max_lane = _positive_int_from_env(
            ("YOOL_TUPLE_MAX_LANE_CONCURRENCY", "YOOL_MAX_LANE_CONCURRENCY"),
            DEFAULT_MAX_LANE_CONCURRENCY,
        )
        cpu_quota = _positive_int_from_env(
            ("YOOL_TUPLE_CPU_QUOTA_PCT", "YOOL_CPU_QUOTA_PCT"),
            DEFAULT_CPU_QUOTA_PCT,
        )
        queue_size = _positive_int_from_env(
            ("YOOL_TUPLE_QUEUE_MAXSIZE", "YOOL_QUEUE_MAXSIZE"),
            DEFAULT_QUEUE_MAXSIZE,
        )
        compression = _positive_int_from_env(
            ("YOOL_TUPLE_COMPRESSION_THRESHOLD", "YOOL_COMPRESSION_THRESHOLD"),
            DEFAULT_COMPRESSION_THRESHOLD,
        )
        cache_max_entries = _positive_int_from_env(
            ("YOOL_TUPLE_CACHE_MAX_ENTRIES", "YOOL_CACHE_MAX_ENTRIES"),
            DEFAULT_CACHE_MAX_ENTRIES,
        )
        cache_ttl = _positive_float_from_env(
            ("YOOL_TUPLE_CACHE_TTL_S", "YOOL_CACHE_TTL_S"),
            DEFAULT_CACHE_TTL_S,
        )
        api_max_retries = _positive_int_from_env(
            ("YOOL_TUPLE_API_MAX_RETRIES", "YOOL_API_MAX_RETRIES"),
            DEFAULT_API_MAX_RETRIES,
        )
        backoff_base = _positive_int_from_env(
            ("YOOL_TUPLE_API_BACKOFF_BASE_MS", "YOOL_API_BACKOFF_BASE_MS"),
            DEFAULT_API_BACKOFF_BASE_MS,
        )
        backoff_max = _positive_int_from_env(
            ("YOOL_TUPLE_API_BACKOFF_MAX_MS", "YOOL_API_BACKOFF_MAX_MS"),
            DEFAULT_API_BACKOFF_MAX_MS,
        )
        circuit_threshold = _positive_int_from_env(
            ("YOOL_TUPLE_CIRCUIT_FAILURE_THRESHOLD", "YOOL_CIRCUIT_FAILURE_THRESHOLD"),
            DEFAULT_CIRCUIT_FAILURE_THRESHOLD,
        )
        circuit_cooldown = _positive_float_from_env(
            ("YOOL_TUPLE_CIRCUIT_COOLDOWN_S", "YOOL_CIRCUIT_COOLDOWN_S"),
            DEFAULT_CIRCUIT_COOLDOWN_S,
        )
        batch_size = _positive_int_from_env(
            ("YOOL_TUPLE_BATCH_SMALL_TASK_SIZE", "YOOL_BATCH_SMALL_TASK_SIZE"),
            DEFAULT_BATCH_SMALL_TASK_SIZE,
        )
        context_chars = _positive_int_from_env(
            ("YOOL_TUPLE_CONTEXT_COMPRESSION_CHARS", "YOOL_CONTEXT_COMPRESSION_CHARS"),
            DEFAULT_CONTEXT_COMPRESSION_CHARS,
        )
        return cls(
            lane_concurrency=requested,
            max_lane_concurrency=max(1, max_lane),
            cpu_quota_pct=max(1, min(100, cpu_quota)),
            queue_maxsize=max(1, queue_size),
            compression_threshold=max(1, compression),
            cache_max_entries=max(1, cache_max_entries),
            cache_ttl_s=max(0.001, cache_ttl),
            api_max_retries=max(0, api_max_retries),
            api_backoff_base_ms=max(1, backoff_base),
            api_backoff_max_ms=max(1, backoff_max),
            circuit_failure_threshold=max(1, circuit_threshold),
            circuit_cooldown_s=max(0.001, circuit_cooldown),
            batch_small_task_size=max(1, batch_size),
            context_compression_chars=max(64, context_chars),
        )

    def concurrency_for(
        self,
        queued_roots: int,
        *,
        ewma_latency_ms: float | None = None,
        error_rate: float = 0.0,
    ) -> int:
        requested = self.lane_concurrency
        if requested <= 0:
            requested = min(max(1, queued_roots), max(1, os.cpu_count() or 1))
        ceiling = max(1, min(self.max_lane_concurrency, queued_roots or 1))
        concurrency = max(1, min(requested, ceiling))
        if queued_roots > requested * 4:
            concurrency = min(ceiling, max(concurrency, requested * 2))
        if ewma_latency_ms is not None and ewma_latency_ms > 250:
            concurrency = min(ceiling, max(concurrency, concurrency * 2))
        if error_rate >= 0.2:
            concurrency = max(1, concurrency // 2)
        return max(1, concurrency)


class HilbertIndex:
    """Simplified Hilbert-style index: tuple multi-dim -> stable hashable path."""

    @staticmethod
    def compute(keys: Tuple[Any, ...]) -> Tuple[Any, ...]:
        return keys


class YoolTuple:
    """Tuple envelope: yool + map + authority + lane + source pointers + receipts."""

    def __init__(
        self,
        yool: str,
        map_index: Tuple[Any, ...],
        authority: str,
        lane: str,
        source: str,
        data: Optional[Dict[str, Any]] = None,
        *,
        parent_id: int | None = None,
        agent_id: int | None = None,
    ) -> None:
        self.id = agent_id
        self.yool = yool
        self.map = map_index
        self.authority = authority
        self.lane = lane
        self.source = source
        self.parent_id = parent_id
        self.receipts: List[str] = []
        self.data = data or {}
        self.last_active = time.monotonic()

    def touch(self) -> None:
        self.last_active = time.monotonic()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "yool": self.yool,
            "map": list(self.map),
            "authority": self.authority,
            "lane": self.lane,
            "source": self.source,
            "parent_id": self.parent_id,
            "receipts": list(self.receipts),
            "data": dict(self.data),
        }


@dataclass
class CompressToken:
    """Compact inactive agent state; enough to inspect or lazily restore later."""

    agent_id: int
    yool: str
    map_index: Tuple[Any, ...]
    authority: str
    lane: str
    source: str
    parent_id: int | None
    receipts: List[str] = field(default_factory=list)
    data_digest: str = ""
    compressed_at: float = field(default_factory=time.monotonic)


@dataclass(frozen=True)
class BatchSpawnReceipt:
    root_agent_id: int
    depth: int
    branching: int
    virtual_agents: int
    compression_threshold: int
    receipt_id: str


class CircuitOpenError(RuntimeError):
    """Raised when a provider is cooling down after repeated transient failures."""


Executor = Callable[[YoolTuple], Any]
BatchExecutor = Callable[[List[YoolTuple]], Any]


def _stable_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=repr)
    return hashlib.blake2b(raw.encode("utf-8"), digest_size=16).hexdigest()


@dataclass
class CacheEntry:
    value: Any
    created_at: float = field(default_factory=time.monotonic)
    hits: int = 0


class ReceiptCache:
    """Small LRU+TTL cache keyed by tuple receipt and deterministic input hashes."""

    def __init__(self, *, max_entries: int, ttl_s: float) -> None:
        self.max_entries = max(1, max_entries)
        self.ttl_s = max(0.001, ttl_s)
        self._items: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, keys: Iterable[str]) -> tuple[bool, Any, str | None]:
        now = time.monotonic()
        with self._lock:
            for key in keys:
                item = self._items.get(key)
                if item is None:
                    continue
                if now - item.created_at > self.ttl_s:
                    self._items.pop(key, None)
                    continue
                item.hits += 1
                self._items.move_to_end(key)
                return True, item.value, key
        return False, None, None

    def set(self, keys: Iterable[str], value: Any) -> None:
        now = time.monotonic()
        with self._lock:
            for key in keys:
                self._items[key] = CacheEntry(value=value, created_at=now)
                self._items.move_to_end(key)
            while len(self._items) > self.max_entries:
                self._items.popitem(last=False)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "entries": len(self._items),
                "max_entries": self.max_entries,
                "ttl_s": self.ttl_s,
                "hits": sum(item.hits for item in self._items.values()),
            }


@dataclass(frozen=True)
class BackoffPolicy:
    max_retries: int
    base_ms: int
    max_ms: int
    jitter_ratio: float = 0.25

    @classmethod
    def from_runtime(cls, policy: RuntimePolicy) -> "BackoffPolicy":
        return cls(
            max_retries=policy.api_max_retries,
            base_ms=policy.api_backoff_base_ms,
            max_ms=policy.api_backoff_max_ms,
        )

    def delay_s(self, attempt: int) -> float:
        capped_ms = min(self.max_ms, self.base_ms * (2**attempt))
        jitter = 1 + random.uniform(-self.jitter_ratio, self.jitter_ratio)
        return max(0.0, capped_ms * jitter / 1000)


@dataclass
class CircuitState:
    failures: int = 0
    opened_until: float = 0.0
    successes: int = 0


class ProviderCircuitBreaker:
    """Provider-level circuit breaker to avoid hammering APIs/LLMs during faults."""

    def __init__(self, *, failure_threshold: int, cooldown_s: float) -> None:
        self.failure_threshold = max(1, failure_threshold)
        self.cooldown_s = max(0.001, cooldown_s)
        self._states: DefaultDict[str, CircuitState] = defaultdict(CircuitState)
        self._lock = threading.RLock()

    def before_call(self, provider: str) -> None:
        with self._lock:
            state = self._states[provider]
            if state.opened_until > time.monotonic():
                remaining = state.opened_until - time.monotonic()
                raise CircuitOpenError(
                    f"circuit open for provider {provider!r}; retry after {remaining:.2f}s"
                )

    def record_success(self, provider: str) -> None:
        with self._lock:
            state = self._states[provider]
            state.failures = 0
            state.opened_until = 0.0
            state.successes += 1

    def record_failure(self, provider: str) -> None:
        with self._lock:
            state = self._states[provider]
            state.failures += 1
            if state.failures >= self.failure_threshold:
                state.opened_until = time.monotonic() + self.cooldown_s

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                provider: {
                    "failures": state.failures,
                    "successes": state.successes,
                    "open": state.opened_until > time.monotonic(),
                }
                for provider, state in sorted(self._states.items())
            }


@dataclass
class LaneMetrics:
    successes: int = 0
    failures: int = 0
    ewma_latency_ms: float = 0.0

    def record(self, elapsed_ms: float, *, ok: bool) -> None:
        if self.ewma_latency_ms <= 0:
            self.ewma_latency_ms = elapsed_ms
        else:
            self.ewma_latency_ms = (self.ewma_latency_ms * 0.8) + (elapsed_ms * 0.2)
        if ok:
            self.successes += 1
        else:
            self.failures += 1

    @property
    def error_rate(self) -> float:
        total = self.successes + self.failures
        return 0.0 if total == 0 else self.failures / total


class ContextCompressor:
    """Digest-preserving compression for large LLM prompt/context payloads."""

    def __init__(self, *, threshold_chars: int) -> None:
        self.threshold_chars = max(64, threshold_chars)

    def compress(self, data: Dict[str, Any]) -> tuple[Dict[str, Any], bool]:
        changed = False
        compressed: Dict[str, Any] = {}
        for key, value in data.items():
            new_value, item_changed = self._compress_value(value)
            compressed[key] = new_value
            changed = changed or item_changed
        return compressed, changed

    def _compress_value(self, value: Any) -> tuple[Any, bool]:
        if isinstance(value, str) and len(value) > self.threshold_chars:
            head = value[: self.threshold_chars // 2]
            tail = value[-self.threshold_chars // 4 :]
            return (
                {
                    "compressed": True,
                    "encoding": "sha256+head_tail",
                    "digest": hashlib.sha256(value.encode("utf-8")).hexdigest(),
                    "original_chars": len(value),
                    "preview": f"{head}\n...[compressed]...\n{tail}",
                },
                True,
            )
        if isinstance(value, list):
            changed = False
            out = []
            for item in value:
                new_item, item_changed = self._compress_value(item)
                out.append(new_item)
                changed = changed or item_changed
            return out, changed
        if isinstance(value, dict):
            compressor = ContextCompressor(threshold_chars=self.threshold_chars)
            out, changed = compressor.compress(value)
            return out, changed
        return value, False


class TupleSpace:
    """Thread-safe tuple space with indexed lanes and lazy hierarchical agents."""

    def __init__(self, *, policy: RuntimePolicy | None = None) -> None:
        self.policy = policy or RuntimePolicy.from_env()
        self.space: Dict[Tuple[Any, ...], List[YoolTuple]] = defaultdict(list)
        self.lane_index: DefaultDict[str, List[YoolTuple]] = defaultdict(list)
        self.agents: weakref.WeakValueDictionary[int, YoolTuple] = (
            weakref.WeakValueDictionary()
        )
        self.walls: DefaultDict[str, List[str]] = defaultdict(list)
        self.compressed_agents: Dict[int, CompressToken] = {}
        self.receipt_cache = ReceiptCache(
            max_entries=self.policy.cache_max_entries,
            ttl_s=self.policy.cache_ttl_s,
        )
        self.circuit_breaker = ProviderCircuitBreaker(
            failure_threshold=self.policy.circuit_failure_threshold,
            cooldown_s=self.policy.circuit_cooldown_s,
        )
        self.context_compressor = ContextCompressor(
            threshold_chars=self.policy.context_compression_chars
        )
        self.local_yools: Dict[str, Executor] = {}
        self.virtual_agent_count = 0
        self._next_agent_id = 0
        self._lock = threading.RLock()
        self._cond = threading.Condition(self._lock)

    def out_tuple(self, t: YoolTuple) -> None:
        with self._cond:
            self.space[t.map].append(t)
            self.lane_index[t.lane].append(t)
            t.receipts.append(
                f"out@{self._receipt_hash(t.map, t.yool, len(t.receipts))}"
            )
            t.touch()
            self._cond.notify_all()

    def in_tuple(
        self,
        template: Dict[str, Any],
        *,
        timeout_s: float | None = None,
    ) -> Optional[YoolTuple]:
        deadline = time.monotonic() + timeout_s if timeout_s is not None else None
        with self._cond:
            while True:
                match = self._find_match(template)
                if match is not None:
                    self._remove_tuple(match)
                    match.touch()
                    return match
                if timeout_s is None:
                    return None
                remaining = deadline - time.monotonic() if deadline is not None else 0
                if remaining <= 0:
                    return None
                self._cond.wait(timeout=remaining)

    def rd_tuple(self, template: Dict[str, Any]) -> Optional[YoolTuple]:
        with self._lock:
            match = self._find_match(template)
            if match is not None:
                match.touch()
            return match

    def register_local_yool(self, yool: str, executor: Executor) -> None:
        """Register deterministic local work to avoid unnecessary LLM/API calls."""
        with self._lock:
            self.local_yools[yool] = executor

    def execute_tuple(
        self,
        tup: YoolTuple,
        executor: Executor,
        *,
        provider: str | None = None,
        use_cache: bool = True,
        retryable: Callable[[BaseException], bool] | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> Any:
        """Execute one tuple through local routing, compression, cache, and guardrails."""
        local_executor = self.local_yools.get(tup.yool)
        if local_executor is not None:
            tup.receipts.append(f"local_route@{self._receipt_hash(tup.yool, tup.map)}")
            return local_executor(tup)

        if self._should_compress_context(tup):
            self.compress_context(tup)

        cache_keys = self.cache_keys_for_tuple(tup)
        if use_cache:
            hit, cached, key = self.receipt_cache.get(cache_keys)
            if hit:
                tup.receipts.append(f"cache_hit@{key}")
                return cached

        provider_name = provider or str(tup.data.get("provider") or "local")

        def run() -> Any:
            return executor(tup)

        if provider_name == "local":
            result = run()
        else:
            result = self.call_with_backoff(
                provider_name,
                run,
                retryable=retryable,
                sleep_fn=sleep_fn,
            )
        if use_cache:
            self.receipt_cache.set(cache_keys, result)
            tup.receipts.append(
                f"cache_store@{self._receipt_hash(provider_name, cache_keys)}"
            )
        return result

    def call_with_backoff(
        self,
        provider: str,
        fn: Callable[[], Any],
        *,
        retryable: Callable[[BaseException], bool] | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> Any:
        """Call APIs/LLMs with jittered exponential backoff and provider breaker."""
        policy = BackoffPolicy.from_runtime(self.policy)
        retryable = retryable or self._default_retryable
        attempt = 0
        while True:
            self.circuit_breaker.before_call(provider)
            try:
                result = fn()
            except BaseException as exc:
                self.circuit_breaker.record_failure(provider)
                if attempt >= policy.max_retries or not retryable(exc):
                    raise
                sleep_fn(policy.delay_s(attempt))
                attempt += 1
                continue
            self.circuit_breaker.record_success(provider)
            return result

    def compress_context(
        self, tup: YoolTuple, *, threshold_chars: int | None = None
    ) -> bool:
        compressor = (
            self.context_compressor
            if threshold_chars is None
            else ContextCompressor(threshold_chars=threshold_chars)
        )
        compressed, changed = compressor.compress(tup.data)
        if changed:
            tup.data = compressed
            tup.receipts.append(
                f"compress_context@{self._receipt_hash(tup.yool, tup.map, tup.data)}"
            )
            tup.touch()
        return changed

    def cache_keys_for_tuple(self, tup: YoolTuple) -> List[str]:
        input_key = _stable_digest({
            "yool": tup.yool,
            "data": tup.data,
        })
        receipt_key = _stable_digest({"receipts": tup.receipts, "input": input_key})
        return [f"input:{input_key}", f"receipt:{receipt_key}"]

    def scan_index(
        self,
        *,
        lane: str | None = None,
        yool: str | None = None,
        limit: int = 100,
    ) -> List[YoolTuple]:
        with self._lock:
            candidates = (
                self.lane_index.get(lane, [])
                if lane
                else [tup for values in self.space.values() for tup in values]
            )
            out: List[YoolTuple] = []
            for tup in candidates:
                if yool is None or tup.yool == yool:
                    out.append(tup)
                if len(out) >= limit:
                    break
            return out

    def spawn_agent(
        self, parent: YoolTuple, agent_yool: str, agent_data: Dict[str, Any]
    ) -> int:
        with self._lock:
            agent_id = self._allocate_agent_id()
            map_idx = HilbertIndex.compute((*parent.map, agent_id))
            new_tuple = YoolTuple(
                yool=agent_yool,
                map_index=map_idx,
                authority=f"subagent_{agent_id}",
                lane=str(agent_data.get("lane") or parent.lane),
                source=f"spawned_from_{parent.authority}",
                data=agent_data,
                parent_id=parent.id,
                agent_id=agent_id,
            )
            self.agents[agent_id] = new_tuple
            self.out_tuple(new_tuple)
            self.prune_idle(self.policy.compression_threshold)
            return agent_id

    def batch_spawn(
        self,
        parent: YoolTuple,
        agent_yool: str,
        *,
        depth: int,
        branching: int,
        compression_threshold: int | None = None,
        agent_data: Dict[str, Any] | None = None,
    ) -> BatchSpawnReceipt:
        """Create a lazy deep hierarchy without enumerating every leaf.

        Example: depth=4, branching=32 represents 1,048,576 leaf subagents while
        materializing one controller tuple plus a compressed virtual subtree.
        """
        if depth < 1:
            raise ValueError("depth must be >= 1")
        if branching < 1:
            raise ValueError("branching must be >= 1")
        threshold = compression_threshold or self.policy.compression_threshold
        virtual_agents = branching**depth
        controller_id = self.spawn_agent(
            parent,
            agent_yool,
            {
                **(agent_data or {}),
                "lazy_batch": True,
                "depth": depth,
                "branching": branching,
                "virtual_agents": virtual_agents,
                "compression_threshold": threshold,
            },
        )
        with self._lock:
            self.virtual_agent_count += virtual_agents
            receipt_id = self._receipt_hash(
                (controller_id, depth, branching), agent_yool, virtual_agents
            )
            controller = self.agents.get(controller_id)
            if controller is not None:
                controller.receipts.append(f"batch_spawn@{receipt_id}")
                if len(self.agents) > threshold:
                    self.compress_token(controller_id)
            return BatchSpawnReceipt(
                root_agent_id=controller_id,
                depth=depth,
                branching=branching,
                virtual_agents=virtual_agents,
                compression_threshold=threshold,
                receipt_id=receipt_id,
            )

    def compress_token(self, agent_id: int) -> CompressToken | None:
        with self._lock:
            tup = self.agents.get(agent_id)
            if tup is None:
                return self.compressed_agents.get(agent_id)
            digest = hashlib.sha256(
                repr(sorted(tup.data.items())).encode("utf-8")
            ).hexdigest()
            token = CompressToken(
                agent_id=agent_id,
                yool=tup.yool,
                map_index=tup.map,
                authority=tup.authority,
                lane=tup.lane,
                source=tup.source,
                parent_id=tup.parent_id,
                receipts=list(tup.receipts),
                data_digest=digest,
            )
            self._remove_tuple(tup)
            self.compressed_agents[agent_id] = token
            self.agents.pop(agent_id, None)
            return token

    def prune_idle(self, max_active: int | None = None) -> int:
        max_active = max_active or self.policy.compression_threshold
        with self._lock:
            active = [
                (agent_id, tup.last_active) for agent_id, tup in self.agents.items()
            ]
            if len(active) <= max_active:
                return 0
            active.sort(key=lambda item: item[1])
            to_compress = len(active) - max_active
            for agent_id, _ in active[:to_compress]:
                self.compress_token(agent_id)
            return to_compress

    def route_packet(self, packet: Dict[str, Any], target_lane: str) -> bool:
        target = self.rd_tuple({"lane": target_lane})
        if target is None:
            return False
        target.data.update(packet)
        target.receipts.append(
            f"route@{self._receipt_hash(target.map, target_lane, len(packet))}"
        )
        target.touch()
        return True

    def hookwall(self, wall_id: str, capability: str, action: str = "hook") -> bool:
        with self._lock:
            if action == "hook":
                if capability not in self.walls[wall_id]:
                    self.walls[wall_id].append(capability)
                return True
            if action == "check":
                return capability in self.walls.get(wall_id, [])
            if action == "unhook":
                if capability in self.walls.get(wall_id, []):
                    self.walls[wall_id].remove(capability)
                    return True
        return False

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "tuples": sum(len(items) for items in self.space.values()),
                "lanes": {
                    lane: len(items) for lane, items in sorted(self.lane_index.items())
                },
                "active_agents": len(self.agents),
                "compressed_agents": len(self.compressed_agents),
                "virtual_agents": self.virtual_agent_count,
                "total_agents": len(self.agents)
                + len(self.compressed_agents)
                + self.virtual_agent_count,
                "policy": {
                    "lane_concurrency": self.policy.lane_concurrency,
                    "max_lane_concurrency": self.policy.max_lane_concurrency,
                    "cpu_quota_pct": self.policy.cpu_quota_pct,
                    "queue_maxsize": self.policy.queue_maxsize,
                    "compression_threshold": self.policy.compression_threshold,
                    "cache_max_entries": self.policy.cache_max_entries,
                    "cache_ttl_s": self.policy.cache_ttl_s,
                    "api_max_retries": self.policy.api_max_retries,
                    "api_backoff_base_ms": self.policy.api_backoff_base_ms,
                    "api_backoff_max_ms": self.policy.api_backoff_max_ms,
                    "circuit_failure_threshold": self.policy.circuit_failure_threshold,
                    "circuit_cooldown_s": self.policy.circuit_cooldown_s,
                    "batch_small_task_size": self.policy.batch_small_task_size,
                    "context_compression_chars": self.policy.context_compression_chars,
                },
                "cache": self.receipt_cache.snapshot(),
                "circuit_breakers": self.circuit_breaker.snapshot(),
            }

    def _allocate_agent_id(self) -> int:
        agent_id = self._next_agent_id
        self._next_agent_id += 1
        return agent_id

    def _find_match(self, template: Dict[str, Any]) -> YoolTuple | None:
        if "lane" in template:
            candidates = list(self.lane_index.get(str(template["lane"]), []))
        else:
            candidates = [
                tup for tuples_list in self.space.values() for tup in tuples_list
            ]
        for tup in candidates:
            if self._matches(tup, template):
                return tup
        return None

    def _matches(self, t: YoolTuple, template: Dict[str, Any]) -> bool:
        for key, expected in template.items():
            if hasattr(t, key):
                value = getattr(t, key)
            else:
                value = t.data.get(key)
            if value != expected:
                return False
        return True

    def _remove_tuple(self, t: YoolTuple) -> None:
        tuples_list = self.space.get(t.map)
        if tuples_list:
            self.space[t.map] = [item for item in tuples_list if item is not t]
            if not self.space[t.map]:
                del self.space[t.map]
        lane_items = self.lane_index.get(t.lane)
        if lane_items:
            self.lane_index[t.lane] = [item for item in lane_items if item is not t]
            if not self.lane_index[t.lane]:
                del self.lane_index[t.lane]

    @staticmethod
    def _receipt_hash(*parts: Any) -> str:
        raw = repr(parts).encode("utf-8")
        return hashlib.blake2b(raw, digest_size=8).hexdigest()

    @staticmethod
    def _default_retryable(exc: BaseException) -> bool:
        return isinstance(exc, (TimeoutError, ConnectionError))

    @staticmethod
    def _should_compress_context(tup: YoolTuple) -> bool:
        if tup.data.get("compress_context") is False:
            return False
        if tup.data.get("compress_context") is True:
            return True
        return bool(tup.data.get("provider") or tup.data.get("llm_context"))


class LaneWorkerPool:
    """Bounded per-lane worker fan-out for tuple execution."""

    def __init__(
        self,
        space: TupleSpace,
        *,
        policy: RuntimePolicy | None = None,
        lane_concurrency: Dict[str, int] | None = None,
    ) -> None:
        self.space = space
        self.policy = policy or space.policy
        self.lane_concurrency = dict(lane_concurrency or {})
        self.lane_metrics: DefaultDict[str, LaneMetrics] = defaultdict(LaneMetrics)

    def concurrency_for(self, lane: str) -> int:
        queued = len(self.space.scan_index(lane=lane, limit=self.policy.queue_maxsize))
        configured = self.lane_concurrency.get(lane)
        metrics = self.lane_metrics[lane]
        if configured is not None:
            baseline = RuntimePolicy(
                lane_concurrency=configured,
                max_lane_concurrency=self.policy.max_lane_concurrency,
            )
            return baseline.concurrency_for(
                queued,
                ewma_latency_ms=metrics.ewma_latency_ms or None,
                error_rate=metrics.error_rate,
            )
        return self.policy.concurrency_for(
            queued,
            ewma_latency_ms=metrics.ewma_latency_ms or None,
            error_rate=metrics.error_rate,
        )

    def run_lane(
        self,
        lane: str,
        executor: Executor,
        *,
        provider: str | None = None,
        use_cache: bool = True,
        retryable: Callable[[BaseException], bool] | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        speculative_executor: Executor | None = None,
    ) -> List[Any]:
        tuples = self.space.scan_index(lane=lane, limit=self.policy.queue_maxsize)
        if not tuples:
            return []
        concurrency = self.concurrency_for(lane)
        semaphore = threading.Semaphore(concurrency)
        results: List[Any] = []
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures: List[Future[Any]] = [
                pool.submit(
                    self._execute_one,
                    lane,
                    executor,
                    semaphore,
                    provider,
                    use_cache,
                    retryable,
                    sleep_fn,
                    speculative_executor,
                )
                for _ in tuples
            ]
            for future in as_completed(futures):
                results.append(future.result())
        return results

    def run_lane_batched(
        self,
        lane: str,
        batch_executor: BatchExecutor,
        *,
        batch_size: int | None = None,
    ) -> List[Any]:
        """Drain small lane tasks in batches to reduce scheduler/API overhead."""
        concurrency_hint = self.concurrency_for(lane)
        tuples = self._drain_lane(lane)
        if not tuples:
            return []
        size = max(1, batch_size or self.policy.batch_small_task_size)
        batches = [
            tuples[index : index + size] for index in range(0, len(tuples), size)
        ]
        concurrency = min(concurrency_hint, len(batches))
        results: List[Any] = []
        with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
            futures = [
                pool.submit(self._execute_batch, lane, batch, batch_executor)
                for batch in batches
            ]
            for future in as_completed(futures):
                item = future.result()
                if isinstance(item, list):
                    results.extend(item)
                else:
                    results.append(item)
        return results

    def _execute_one(
        self,
        lane: str,
        executor: Executor,
        semaphore: threading.Semaphore,
        provider: str | None,
        use_cache: bool,
        retryable: Callable[[BaseException], bool] | None,
        sleep_fn: Callable[[float], None],
        speculative_executor: Executor | None,
    ) -> Any:
        with semaphore:
            tup = self.space.in_tuple({"lane": lane})
            if tup is None:
                return None
            return self._execute_tuple(
                lane,
                tup,
                executor,
                provider=provider,
                use_cache=use_cache,
                retryable=retryable,
                sleep_fn=sleep_fn,
                speculative_executor=speculative_executor,
            )

    def _execute_tuple(
        self,
        lane: str,
        tup: YoolTuple,
        executor: Executor,
        *,
        provider: str | None,
        use_cache: bool,
        retryable: Callable[[BaseException], bool] | None,
        sleep_fn: Callable[[float], None],
        speculative_executor: Executor | None,
    ) -> Any:
        start = time.perf_counter()
        ok = False
        try:
            if speculative_executor is not None and tup.data.get("idempotent") is True:
                result = self._speculative_execute(tup, executor, speculative_executor)
            else:
                result = self.space.execute_tuple(
                    tup,
                    executor,
                    provider=provider,
                    use_cache=use_cache,
                    retryable=retryable,
                    sleep_fn=sleep_fn,
                )
            ok = True
            return result
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.lane_metrics[lane].record(elapsed_ms, ok=ok)

    def _speculative_execute(
        self, tup: YoolTuple, primary: Executor, speculative: Executor
    ) -> Any:
        errors: List[BaseException] = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(primary, tup),
                pool.submit(speculative, tup),
            ]
            for future in as_completed(futures):
                try:
                    result = future.result()
                except BaseException as exc:
                    errors.append(exc)
                    continue
                for pending in futures:
                    if pending is not future:
                        pending.cancel()
                tup.receipts.append(
                    f"speculative_win@{self.space._receipt_hash(tup.yool, tup.map)}"
                )
                return result
        raise errors[0]

    def _drain_lane(self, lane: str) -> List[YoolTuple]:
        tuples = self.space.scan_index(lane=lane, limit=self.policy.queue_maxsize)
        drained: List[YoolTuple] = []
        for _ in tuples:
            tup = self.space.in_tuple({"lane": lane})
            if tup is not None:
                drained.append(tup)
        return drained

    def _execute_batch(
        self, lane: str, batch: List[YoolTuple], batch_executor: BatchExecutor
    ) -> Any:
        start = time.perf_counter()
        ok = False
        try:
            receipt = self.space._receipt_hash(
                lane, [tup.map for tup in batch], len(batch)
            )
            for tup in batch:
                tup.receipts.append(f"batch@{receipt}")
            result = batch_executor(batch)
            ok = True
            return result
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.lane_metrics[lane].record(elapsed_ms, ok=ok)


def build_default_space() -> tuple[TupleSpace, YoolTuple]:
    ts = TupleSpace()
    root = YoolTuple("kernel_root", HilbertIndex.compute((0,)), "root", "main", "user")
    ts.out_tuple(root)
    return ts, root


if __name__ == "__main__":
    ts, root = build_default_space()
    ts.spawn_agent(root, "hamt_builder", {"status": "ready"})
    ts.batch_spawn(
        root, "codex_worker", depth=4, branching=32, compression_threshold=128
    )
    ts.hookwall("main_wall", "capability_root", "hook")
    print(ts.snapshot())
