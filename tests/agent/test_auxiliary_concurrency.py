"""Tests for per-task concurrency limiting on auxiliary LLM calls (#23324)."""

import asyncio
import threading
import time
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from agent.auxiliary_client import (
    call_llm,
    async_call_llm,
    _acquire_sync_aux_semaphore,
    _acquire_async_aux_semaphore,
    _get_task_max_concurrency,
    _reset_aux_semaphores,
)


@pytest.fixture(autouse=True)
def _clean_semaphore_cache():
    _reset_aux_semaphores()
    yield
    _reset_aux_semaphores()


class TestGetTaskMaxConcurrency:
    def test_returns_none_for_missing_task(self):
        assert _get_task_max_concurrency(None) is None
        assert _get_task_max_concurrency("") is None

    def test_returns_none_when_unset(self):
        with patch("agent.auxiliary_client._get_auxiliary_task_config", return_value={}):
            assert _get_task_max_concurrency("title_generation") is None

    def test_returns_int_when_configured(self):
        with patch(
            "agent.auxiliary_client._get_auxiliary_task_config",
            return_value={"max_concurrency": 3},
        ):
            assert _get_task_max_concurrency("compression") == 3

    def test_returns_none_for_non_numeric(self):
        with patch(
            "agent.auxiliary_client._get_auxiliary_task_config",
            return_value={"max_concurrency": "not-a-number"},
        ):
            assert _get_task_max_concurrency("compression") is None

    def test_returns_none_for_zero_or_negative(self):
        with patch(
            "agent.auxiliary_client._get_auxiliary_task_config",
            return_value={"max_concurrency": 0},
        ):
            assert _get_task_max_concurrency("compression") is None
        with patch(
            "agent.auxiliary_client._get_auxiliary_task_config",
            return_value={"max_concurrency": -2},
        ):
            assert _get_task_max_concurrency("compression") is None


class TestSemaphoreCache:
    def test_sync_returns_none_when_unset(self):
        with patch("agent.auxiliary_client._get_auxiliary_task_config", return_value={}):
            assert _acquire_sync_aux_semaphore("title_generation") is None

    def test_sync_reuses_semaphore_for_same_limit(self):
        with patch(
            "agent.auxiliary_client._get_auxiliary_task_config",
            return_value={"max_concurrency": 2},
        ):
            sem1 = _acquire_sync_aux_semaphore("compression")
            sem2 = _acquire_sync_aux_semaphore("compression")
            assert sem1 is sem2

    def test_sync_rebuilds_when_limit_changes(self):
        cfg = {"max_concurrency": 2}
        with patch(
            "agent.auxiliary_client._get_auxiliary_task_config",
            return_value=cfg,
        ):
            sem1 = _acquire_sync_aux_semaphore("compression")
            cfg["max_concurrency"] = 5
            sem2 = _acquire_sync_aux_semaphore("compression")
            assert sem1 is not sem2

    @pytest.mark.asyncio
    async def test_async_reuses_semaphore_within_same_loop(self):
        with patch(
            "agent.auxiliary_client._get_auxiliary_task_config",
            return_value={"max_concurrency": 2},
        ):
            sem1 = _acquire_async_aux_semaphore("compression")
            sem2 = _acquire_async_aux_semaphore("compression")
            assert sem1 is sem2

    def test_async_returns_none_with_no_running_loop(self):
        with patch(
            "agent.auxiliary_client._get_auxiliary_task_config",
            return_value={"max_concurrency": 2},
        ):
            # Called outside an asyncio loop — should bail rather than crash.
            assert _acquire_async_aux_semaphore("compression") is None


class TestSyncCallEnforcesLimit:
    def test_call_llm_caps_concurrent_inflight(self):
        limit = 2
        n_callers = 6

        active = 0
        max_active = 0
        lock = threading.Lock()

        def fake_create(**kwargs):
            nonlocal active, max_active
            with lock:
                active += 1
                if active > max_active:
                    max_active = active
            try:
                time.sleep(0.05)
            finally:
                with lock:
                    active -= 1
            return MagicMock()

        client = MagicMock()
        client.base_url = "https://example.test/v1"
        client.chat.completions.create.side_effect = fake_create

        with patch(
            "agent.auxiliary_client._resolve_task_provider_model",
            return_value=("openrouter", "test-model", None, None, None),
        ), patch(
            "agent.auxiliary_client._get_cached_client",
            return_value=(client, "test-model"),
        ), patch(
            "agent.auxiliary_client._validate_llm_response",
            side_effect=lambda resp, _task: resp,
        ), patch(
            "agent.auxiliary_client._get_auxiliary_task_config",
            return_value={"max_concurrency": limit},
        ):
            threads = [
                threading.Thread(
                    target=lambda: call_llm(
                        task="title_generation",
                        messages=[{"role": "user", "content": "hi"}],
                    )
                )
                for _ in range(n_callers)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=5)

        assert max_active <= limit, f"observed {max_active} > limit {limit}"
        assert client.chat.completions.create.call_count == n_callers

    def test_call_llm_unlimited_when_not_configured(self):
        client = MagicMock()
        client.base_url = "https://example.test/v1"
        client.chat.completions.create.return_value = MagicMock()

        with patch(
            "agent.auxiliary_client._resolve_task_provider_model",
            return_value=("openrouter", "test-model", None, None, None),
        ), patch(
            "agent.auxiliary_client._get_cached_client",
            return_value=(client, "test-model"),
        ), patch(
            "agent.auxiliary_client._validate_llm_response",
            side_effect=lambda resp, _task: resp,
        ), patch(
            "agent.auxiliary_client._get_auxiliary_task_config",
            return_value={},
        ):
            # With no max_concurrency in config, no semaphore is acquired.
            call_llm(
                task="title_generation",
                messages=[{"role": "user", "content": "hi"}],
            )

        assert client.chat.completions.create.call_count == 1

    def test_semaphore_released_on_exception(self):
        """Errors inside call_llm must release the semaphore so the next call proceeds."""
        client = MagicMock()
        client.base_url = "https://example.test/v1"
        client.chat.completions.create.side_effect = RuntimeError("boom")

        with patch(
            "agent.auxiliary_client._resolve_task_provider_model",
            return_value=("openrouter", "test-model", None, None, None),
        ), patch(
            "agent.auxiliary_client._get_cached_client",
            return_value=(client, "test-model"),
        ), patch(
            "agent.auxiliary_client._validate_llm_response",
            side_effect=lambda resp, _task: resp,
        ), patch(
            "agent.auxiliary_client._get_auxiliary_task_config",
            return_value={"max_concurrency": 1},
        ):
            for _ in range(3):
                with pytest.raises(RuntimeError, match="boom"):
                    call_llm(
                        task="title_generation",
                        messages=[{"role": "user", "content": "hi"}],
                    )


class TestAsyncCallEnforcesLimit:
    @pytest.mark.asyncio
    async def test_async_call_llm_caps_concurrent_inflight(self):
        limit = 2
        n_callers = 6

        active = 0
        max_active = 0

        async def fake_create(**kwargs):
            nonlocal active, max_active
            active += 1
            if active > max_active:
                max_active = active
            try:
                await asyncio.sleep(0.05)
            finally:
                active -= 1
            return MagicMock()

        client = MagicMock()
        client.base_url = "https://example.test/v1"
        client.chat.completions.create = AsyncMock(side_effect=fake_create)

        with patch(
            "agent.auxiliary_client._resolve_task_provider_model",
            return_value=("openrouter", "test-model", None, None, None),
        ), patch(
            "agent.auxiliary_client._get_cached_client",
            return_value=(client, "test-model"),
        ), patch(
            "agent.auxiliary_client._validate_llm_response",
            side_effect=lambda resp, _task: resp,
        ), patch(
            "agent.auxiliary_client._get_auxiliary_task_config",
            return_value={"max_concurrency": limit},
        ):
            await asyncio.gather(*[
                async_call_llm(
                    task="compression",
                    messages=[{"role": "user", "content": "hi"}],
                )
                for _ in range(n_callers)
            ])

        assert max_active <= limit, f"observed {max_active} > limit {limit}"
        assert client.chat.completions.create.await_count == n_callers

    @pytest.mark.asyncio
    async def test_async_semaphore_released_on_exception(self):
        client = MagicMock()
        client.base_url = "https://example.test/v1"
        client.chat.completions.create = AsyncMock(side_effect=RuntimeError("boom"))

        with patch(
            "agent.auxiliary_client._resolve_task_provider_model",
            return_value=("openrouter", "test-model", None, None, None),
        ), patch(
            "agent.auxiliary_client._get_cached_client",
            return_value=(client, "test-model"),
        ), patch(
            "agent.auxiliary_client._validate_llm_response",
            side_effect=lambda resp, _task: resp,
        ), patch(
            "agent.auxiliary_client._get_auxiliary_task_config",
            return_value={"max_concurrency": 1},
        ):
            for _ in range(3):
                with pytest.raises(RuntimeError, match="boom"):
                    await async_call_llm(
                        task="compression",
                        messages=[{"role": "user", "content": "hi"}],
                    )
