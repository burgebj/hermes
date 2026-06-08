# Reasoning-Only Stale Detector

**Goal:** Fix session deadlock caused by models (e.g. DeepSeek V4 Flash) entering an
infinite or extremely long reasoning loop. When a model emits only `reasoning_content`
tokens indefinitely, the existing stale detector never fires because every reasoning
chunk resets the shared `last_chunk_time` timer. The session then hangs until the HTTP
timeout (default 1800 s = 30 min).

**Related issues:** #29086, hermes-web-ui#866

**Tech stack:** Python 3.11+, pytest, unittest.mock

---

## Root Cause

`agent/chat_completion_helpers.py` — streaming hot path:

```python
# line 1357-1358  (chat completions path)
for chunk in stream:
    last_chunk_time["t"] = time.time()   # reset on EVERY chunk, incl. reasoning

# line 1395-1399: reasoning chunks processed here — they DO reach line 1358
reasoning_text = getattr(delta, "reasoning_content", None) ...
if reasoning_text:
    reasoning_parts.append(reasoning_text)
    ...

# line 1953: stale check uses the same timer
_stale_elapsed = time.time() - last_chunk_time["t"]
if _stale_elapsed > _stream_stale_timeout:
    # kill stream   <-- never reached while reasoning keeps flowing
```

The same pattern exists in `_call_anthropic()` (line 1594) for the `thinking_delta`
event type.

**Reproduced:** DeepSeek V4 Flash sent 1271 reasoning chunks over 45 s before producing
any content. A continuous reasoning stream with even a 2 s stale threshold runs for 10 s
without triggering the detector (verified programmatically).

---

## Fix Design

Add a **second timer** `last_content_chunk_time` that resets **only** when real output
arrives (`delta.content` or `delta.tool_calls` for chat completions; `text_delta` or
`tool_use` block start for Anthropic). A separate stale threshold
`HERMES_REASONING_ONLY_STALE_TIMEOUT` (default **300 s**, configurable) gates a new
kill-path in the outer poll loop.

The check only activates once the model has started emitting reasoning tokens (`reasoning_seen`),
so purely slow models that haven't produced any chunks yet are unaffected — they fall
under the existing `_stream_stale_timeout` guard.

---

## Task 1 — chat completions streaming path

### File
- Modify: `agent/chat_completion_helpers.py`

### Step 1 — Add shared state near `last_chunk_time`

Around line 1265, add two new shared dicts alongside `last_chunk_time`:

```python
last_chunk_time = {"t": time.time()}
last_content_chunk_time = {"t": time.time()}   # new: reset only on real content
reasoning_seen = {"yes": False}                 # new: set on first reasoning chunk
```

### Step 2 — Update `_call_chat_completions()`

After line 1322 (`last_chunk_time["t"] = time.time()`), reset the connection-level
`last_content_chunk_time` at the start of each stream attempt (same place):

```python
# line 1322 area — reset both timers at attempt start
last_chunk_time["t"] = time.time()
last_content_chunk_time["t"] = time.time()   # new
```

Where reasoning tokens arrive (around line 1396), mark `reasoning_seen`:

```python
if reasoning_text:
    reasoning_parts.append(reasoning_text)
    reasoning_seen["yes"] = True            # new
    _fire_first_delta()
    agent._fire_reasoning_delta(reasoning_text)
```

Where content tokens arrive (around line 1402), reset `last_content_chunk_time`:

```python
if delta and delta.content:
    last_content_chunk_time["t"] = time.time()  # new
    content_parts.append(delta.content)
    ...
```

Where tool calls arrive (around line 1427), also reset `last_content_chunk_time`:

```python
if delta and delta.tool_calls:
    last_content_chunk_time["t"] = time.time()  # new
    for tc_delta in delta.tool_calls:
        ...
```

### Step 3 — Compute the threshold in the outer poll loop

After the existing `_stream_stale_timeout` is computed (around line 1925), add:

```python
_reasoning_only_stale_timeout = float(
    os.getenv("HERMES_REASONING_ONLY_STALE_TIMEOUT", 300.0)
)
```

### Step 4 — Add the reasoning-only stale check in the outer poll loop

After the existing stale-kill block (after line ~1985), add a second check:

```python
# Reasoning-only stale: model is emitting reasoning tokens but never
# producing visible content.  Kills the stream after a configurable
# threshold so the session does not hang until the 1800 s HTTP timeout.
if reasoning_seen["yes"]:
    _ro_elapsed = time.time() - last_content_chunk_time["t"]
    if _ro_elapsed > _reasoning_only_stale_timeout:
        logger.warning(
            "Reasoning-only stream for %.0fs (threshold %.0fs) — "
            "model emitting reasoning but no content. "
            "model=%s. Killing connection.",
            _ro_elapsed, _reasoning_only_stale_timeout,
            api_kwargs.get("model", "unknown"),
        )
        agent._emit_status(
            f"⚠️ Model has been reasoning for {int(_ro_elapsed)}s "
            f"without producing output "
            f"(model: {api_kwargs.get('model', 'unknown')}). "
            f"Aborting stream..."
        )
        try:
            rc = request_client_holder.get("client")
            if rc is not None:
                agent._close_request_openai_client(rc, reason="reasoning_only_stale_kill")
        except Exception:
            pass
        try:
            agent._replace_primary_openai_client(reason="reasoning_only_stale_pool_cleanup")
        except Exception:
            pass
        last_content_chunk_time["t"] = time.time()  # prevent re-fire
        reasoning_seen["yes"] = False
        agent._touch_activity(
            f"reasoning-only stale after {int(_ro_elapsed)}s, reconnecting"
        )
```

---

## Task 2 — Anthropic streaming path

### File
- Modify: `agent/chat_completion_helpers.py` (`_call_anthropic` inner function)

Apply the same pattern to `_call_anthropic()`:

- Reset `last_content_chunk_time["t"]` at attempt start (line 1571 area).
- Set `reasoning_seen["yes"] = True` on `thinking_delta` events (line 1634 area).
- Reset `last_content_chunk_time["t"]` on `text_delta` events (line 1628 area) and on
  `content_block_start` with `type == "tool_use"` (line 1616 area).

The outer poll loop check is shared — no duplication needed.

---

## Task 3 — Tests

### File
- Create: `tests/agent/test_reasoning_stale.py`

### Test 1 — reasoning-only stream kills after threshold

Mock a stream that yields only reasoning chunks indefinitely. Verify that the outer
poll loop kills the connection after `HERMES_REASONING_ONLY_STALE_TIMEOUT`.

### Test 2 — normal reasoning + content not affected

Mock a stream that yields reasoning chunks then content chunks. Verify the stale
detector does NOT fire prematurely.

### Test 3 — no reasoning, no false positive

Mock a stream with only content chunks. Verify reasoning-only check never fires.

### Test 4 — threshold configurable via env var

Set `HERMES_REASONING_ONLY_STALE_TIMEOUT=1` and verify quick kill.

---

## Acceptance Criteria

1. A stream emitting only reasoning tokens for longer than `HERMES_REASONING_ONLY_STALE_TIMEOUT`
   is killed and logged — verified by unit tests.
2. A stream emitting reasoning then content is NOT killed early — verified by unit tests.
3. The existing stale detector behaviour is unaffected.
4. All pre-existing tests continue to pass.
