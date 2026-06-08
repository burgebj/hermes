# Bug Report — hermes-agent-fork (Recent Commits Audit)

**Generated:** 2026-04-27
**Scope:** Last ~20 commits (since 2026-04-15) — primarily the GMI Cloud provider feature (`c53fcb01`) and its post-salvage fixes (`56724147`), plus the recent TUI Ctrl+L / forceRedraw work (`b3e7a412`, `4909b94f`, `adbd173d`).
**Files audited:** ~10 source files (the actual changed surface) + tests
**Language(s):** Python, TypeScript

> Audit scoped to recent diffs. Most of the GMI work was already cleaned up by the post-salvage commit (which itself fixed: malformed `write_text` in tests, dead `ENV_VARS_BY_VERSION[17]` entry, wrong aux model default). What remains is one minor caching gap. The TUI redraw changes look clean.

## Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | 0 |
| 🟠 Major | 0 |
| 🟡 Minor | 1 |
| ⚪ Nitpick | 2 |

---

## 🟡 Minor

### MI-1: GMI endpoint context length is never persisted to disk cache
**File:** `agent/model_metadata.py:1390-1395`

```python
if effective_provider == "gmi" and base_url:
    # GMI exposes authoritative context_length via /models, but it is not
    # in models.dev yet. Preserve that higher-fidelity endpoint lookup.
    ctx = _resolve_endpoint_context_length(model, base_url, api_key=api_key)
    if ctx is not None:
        return ctx
```

**What:** This branch returns the resolved context length but never calls `save_context_length(model, base_url, ctx)`. Compare with the Codex branch directly above (line 1381–1389), which *does* persist its result, and the local-server branch (line 1332).
**Why it matters:** `fetch_endpoint_model_metadata` has an in-process TTL cache, so within one process a refetch is cheap. But every fresh `hermes` invocation re-issues a network round-trip to `https://api.gmi-serving.com/v1/models` to recompute a value that is effectively static per (model, base_url). The persistent cache exists precisely to skip this — see `get_cached_context_length` at line 1280, which returns early on cache hits. Without `save_context_length`, the cache never warms for GMI users.
**Root cause:** Branch authored from the Codex template but the `save_context_length` line was dropped.
**Fix:**
```python
if effective_provider == "gmi" and base_url:
    ctx = _resolve_endpoint_context_length(model, base_url, api_key=api_key)
    if ctx is not None:
        save_context_length(model, base_url, ctx)
        return ctx
```

---

## ⚪ Nitpick

### N-1: GMI model catalog cross-rebrands risk silent context-length mismatches
**File:** `hermes_cli/models.py:281-288`

```python
"gmi": [
    "zai-org/GLM-5.1-FP8",
    "deepseek-ai/DeepSeek-V3.2",
    "moonshotai/Kimi-K2.5",
    "google/gemini-3.1-flash-lite-preview",
    "anthropic/claude-sonnet-4.6",
    "openai/gpt-5.4",
],
```

**What:** GMI rehosts other providers' models under their canonical slash IDs (`anthropic/claude-sonnet-4.6`, `openai/gpt-5.4`). The new `effective_provider == "gmi"` branch in `agent/model_metadata.py:1390` correctly probes GMI's own `/models` endpoint for these — but only when `base_url` reaches that branch. The Anthropic-specific branch at `model_metadata.py:1342-1348` (`provider == "anthropic" or hostname == api.anthropic.com`) gates on hostname so it won't fire here, which is good.
**Why it matters / why it's a nit:** Today this works because the Anthropic block is hostname-gated. If anyone later relaxes that gate to "any model whose name starts with `anthropic/`", users on GMI's rebranded `anthropic/claude-sonnet-4.6` would silently start hitting Anthropic's API for context-length resolution and get a different value than what GMI actually serves. Worth a comment in `_PROVIDER_MODELS["gmi"]` flagging that these IDs are rebrands, so future authors don't trip over it.

### N-2: Stylistic — blank line removed between `_PROVIDER_MODELS` close and `class ProviderEntry`
**File:** `hermes_cli/models.py:720`

The GMI commit deleted the blank line between the `_PROVIDER_MODELS` dict and the `class ProviderEntry(NamedTuple):` declaration. Two blank lines is the project (and PEP 8) standard for top-level definitions. Trivial — surfaces as a one-line ruff/flake8 fix.

---

## Modules with no bugs found

- `agent/auxiliary_client.py` — the `_compat_model` heuristic update (cached_default with `/` → accept slash forms) is correct for GMI; OpenRouter still wins via `_is_openrouter_client`, and non-aggregator clients with bare cached defaults (e.g. anthropic/`claude-haiku-4-5`) still drop slash-form requests as before.
- `hermes_cli/auth.py` — `ProviderConfig` for GMI is a clean clone of arcee's; no auth-token persistence path is exercised (GMI is API-key only), so the qwen `write_text`/`chmod` race documented in the prior audit doesn't apply.
- `hermes_cli/providers.py` — `HermesOverlay` for GMI mirrors the existing API-key providers; `extra_env_vars=("GMI_API_KEY",)` is correctly threaded into the models.dev detection path.
- `hermes_cli/doctor.py` — adds `GMI_API_KEY` to `_PROVIDER_ENV_HINTS` and a `/v1/models` connectivity check; standard pattern, test passes.
- `hermes_cli/config.py` — the post-salvage commit correctly removed the dead `ENV_VARS_BY_VERSION[17]` entry; current `_config_version` is 22 so no existing user would ever have seen the prompt anyway.
- `ui-tui/packages/hermes-ink/src/ink/root.ts` — new `forceRedraw(stdout)` export correctly delegates to the registered `Ink` instance and returns `false` when no instance is mounted; the type shim at `ui-tui/src/types/hermes-ink.d.ts:134` matches.
- `ui-tui/src/app/useInputHandlers.ts:381-385` — Ctrl+L now correctly clears selection and triggers a real redraw via `forceRedraw(terminal.stdout ?? process.stdout)`; falls back to `process.stdout` if `terminal.stdout` is missing, which matches the existing convention.
- `tests/hermes_cli/test_gmi_provider.py` — broad coverage across aliases, registry, doctor, model metadata, auxiliary client, main flow, and persistence; the post-salvage commit fixed the malformed `.env` write that previously wrote literal `'GMI_API_KEY=*** encoding='` to disk.

## Coverage gaps worth attention

- No regression test asserts that GMI's resolved context length is *cached* across processes (MI-1 above). Add a test that calls `get_model_context_length` twice with the second call seeing a `get_cached_context_length` hit, and verify `fetch_endpoint_model_metadata` was called only once.
- No test exercises the `_compat_model` slash-handling change for cached non-OpenRouter clients with slash defaults — only the OpenRouter and bare-default cases are covered.

---

# Agent Module Audit (Appended)

**Generated:** 2026-04-27
**Files audited:** `agent/credential_pool.py`, `agent/credential_sources.py`, `agent/google_oauth.py`, `agent/redact.py`, `agent/file_safety.py`, `agent/retry_utils.py`, `agent/error_classifier.py`, `agent/prompt_caching.py`, `agent/rate_limit_tracker.py`, `agent/account_usage.py`, `agent/nous_rate_guard.py`, `agent/memory_manager.py`

> Out of scope (audited earlier): `agent/auxiliary_client.py`, `agent/model_metadata.py`.

## Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | 1 |
| 🟠 Major | 5 |
| 🟡 Minor | 4 |
| ⚪ Nitpick | 3 |

---

## 🔴 Critical

### AC-1: TOCTOU window leaks Google OAuth credentials at default umask
**File:** `agent/google_oauth.py:494-502`

```python
with _credentials_lock():
    tmp_path = path.with_suffix(f".tmp.{os.getpid()}.{secrets.token_hex(4)}")
    try:
        with open(tmp_path, "w", encoding="utf-8") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp_path, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp_path, path)
```

**What:** `open(tmp_path, "w")` creates the file with the process umask (commonly 0o644 — world-readable). `os.chmod` to 0o600 happens *after* the bytes are already on disk.
**Why it matters:** Google OAuth refresh tokens grant long-lived access to the user's Google account. On a multi-user host or a container with a permissive umask, another local user can read the tokens during the brief write window. The `_lock_path` at line 181 is opened with `os.open(..., 0o600)` — credentials should be too.
**Root cause:** Two-step create-then-chmod instead of atomic restricted-mode create.
**Fix:**
```python
fd = os.open(str(tmp_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w", encoding="utf-8") as fh:
    fh.write(payload)
    fh.flush()
    os.fsync(fh.fileno())
os.replace(tmp_path, path)
```
Also add `mode=0o700` to the `mkdir` at line 491.

---

## 🟠 Major

### AMA-1: Anthropic env-token misclassified as OAuth for non-`sk-ant-api` keys
**File:** `agent/credential_pool.py:1323`

```python
auth_type = AUTH_TYPE_OAUTH if provider == "anthropic" and not token.startswith("sk-ant-api") else AUTH_TYPE_API_KEY
```

**What:** Any Anthropic token whose prefix isn't `sk-ant-api` is stamped as OAuth — including admin keys (`sk-ant-admin-…`), workspace keys, and any future API-key prefix change. OAuth-typed entries flow into `_refresh_entry` (line 575); without a refresh token they get `_mark_exhausted` immediately and the pool rotates away from a working credential.
**Why it matters:** A legitimate admin key from `ANTHROPIC_API_KEY` gets stuck in EXHAUSTED on first use.
**Fix:** Real Claude Code OAuth tokens start with `sk-ant-oat-`. Match positively, not by negation:
```python
auth_type = (
    AUTH_TYPE_OAUTH
    if provider == "anthropic" and token.startswith("sk-ant-oat")
    else AUTH_TYPE_API_KEY
)
```

### AMA-2: `.env` detection misses `export KEY=` form, breaking `auth remove`
**File:** `agent/credential_sources.py:166-169`

```python
env_in_dotenv = any(
    line.strip().startswith(f"{env_var}=")
    for line in env_path.read_text(errors="replace").splitlines()
)
```

**What:** Lines like `export OPENAI_API_KEY=…` (a common `.env` style accepted by python-dotenv and Hermes' loader) don't match. `env_in_dotenv` reports False, so `shell_exported` is True and the user is told the key lives in their shell. If `remove_env_value` doesn't strip `export` lines either, the credential persists across removals.
**Fix:**
```python
prefix = f"{env_var}="
env_in_dotenv = any(
    s.startswith(prefix) or s.startswith(f"export {prefix}")
    for s in (line.strip() for line in env_path.read_text(errors="replace").splitlines())
)
```
And verify `remove_env_value` handles the `export` form (see `hermes_cli/config.py`).

### AMA-3: `account_usage.fetch_account_usage` swallows every exception with no logging
**File:** `agent/account_usage.py:317-326`

**What:** Top-level `try / except Exception: return None` collapses real bugs (KeyError on schema drift, `raise_for_status` 401/403, malformed JSON) into the same "no usage available" outcome. Zero log output.
**Why it matters:** Upstream-API regressions in the per-provider parsers are invisible until users complain `/usage` is empty.
**Fix:** `logger.debug("Account usage fetch failed for %s: %s", normalized, exc)` in the except.

### AMA-4: Google OAuth lock silently no-ops when neither `fcntl` nor `msvcrt` is importable
**File:** `agent/google_oauth.py:218-219`

```python
except ImportError:
    acquired = True
```

**What:** On a hypothetical platform missing both POSIX `fcntl` and Windows `msvcrt`, the code claims it holds a cross-process lock without actually holding one. Two concurrent processes refreshing OAuth would both proceed and clobber each other — and Google rotates refresh tokens on use, so the loser gets `invalid_grant` and `clear_credentials()` (line 684) wipes the user's session.
**Why it matters:** Real-world impact is small (POSIX/Windows are universal), but the same site fails to provide an in-process `threading.Lock` either, so concurrent threads in one process hit the same race even on supported platforms.
**Fix:** Add a module-level `threading.Lock` as a backstop, and warn-log instead of silently setting `acquired = True`.

### AMA-5: URL credential redaction skips `ssh://`, `git+…`, `s3://`, `smtp://`, etc.
**File:** `agent/redact.py:167-169`

`_URL_USERINFO_RE` matches only `(https?|wss?|ftp)`. Tooling output containing `git+ssh://user:token@host`, `ssh://user:pass@host`, `s3://AKIA…:secret@bucket`, `smtp://user:pass@host` passes through unredacted. The DB-conn pattern at 133 only covers postgres/mysql/mongodb/redis/amqp.
**Fix:** Either broaden the scheme to a generic `[A-Za-z][A-Za-z0-9+.-]*` or extend the alternation to include `ssh|git\+\w+|s3|smtp|smtps|imap|imaps|sftp`.

---

## 🟡 Minor

### AMI-1: Empty access token can be adopted from a half-written `.credentials.json`
**File:** `agent/credential_pool.py:441-454`

`_sync_anthropic_entry_from_credentials_file` adopts `file_access` whenever `file_refresh != entry.refresh_token`, even if `file_access` is `""`. If Claude Code is mid-write (refresh updated, access cleared), Hermes wipes its in-pool access token.
**Fix:** `if file_refresh and file_access and file_refresh != entry.refresh_token:`

### AMI-2: `nous_rate_guard` cleanup races can delete another session's freshly written breaker
**File:** `agent/nous_rate_guard.py:152-169`

A reader that observes `reset_at` in the past calls `os.unlink(path)`. If another session atomic-writes a new breaker file in between read and unlink, the reader silently deletes the new record.
**Fix:** Stat-and-compare `mtime`/`inode` immediately before unlink, or skip cleanup if the file changed since the read.

### AMI-3: `_refresh_inflight` retains rotated refresh tokens as dict keys
**File:** `agent/google_oauth.py:634, 705`

The dedupe map keys on the literal `refresh_token` string. Even with `pop(rt, None)` cleanup, rotated refresh tokens linger in the in-memory keyspace.
**Fix:** Hash before use — `hashlib.sha256(rt).hexdigest()[:16]` is enough for dedupe and avoids retaining sensitive material after rotation.

### AMI-4: Duplicate `"input is too long"` pattern in `_CONTEXT_OVERFLOW_PATTERNS`
**File:** `agent/error_classifier.py:184, 195`

Same string listed twice — almost certainly a merge artifact. Harmless, but every classifier call walks both entries.
**Fix:** Delete one.

---

## ⚪ Nitpick

### AN-1: `retry_utils._jitter_counter` reseeds a fresh `random.Random` per call
**File:** `agent/retry_utils.py:53-55`

The new instance + reseed adds no meaningful entropy beyond `time.time_ns()` and is wasteful in hot retry loops. Use `random.uniform` or a single module-level `random.SystemRandom()` instance.

### AN-2: `_USAGE_LIMIT_PATTERNS` ↔ `_BILLING_PATTERNS` overlap on "quota"
**File:** `agent/error_classifier.py:91-129, 836-851`

Both lists contain quota-related strings; correct disambiguation depends on the order of checks in `_classify_by_message`. A future reorder breaks it. Add a comment pinning the dependency.

### AN-3: `prompt_caching._apply_cache_marker` aliasing safety relies on caller's deepcopy
**File:** `agent/prompt_caching.py:36-38`

The helper mutates `last["cache_control"]` directly. Today the caller deepcopies messages first, so mutation is contained — but the helper itself doesn't defend against being called on a shared list. Either copy locally or document the precondition at the helper.

---

## Modules with no bugs found

- `agent/file_safety.py`
- `agent/rate_limit_tracker.py`
- `agent/memory_manager.py` — `sanitize_context` regex coverage matches the documented threat model; metadata-mode introspection is appropriately defensive.

## Coverage gaps worth attention

- `error_classifier` patterns are not exercised against real provider error fixtures — coverage is plausible but unverified end-to-end.
- `credential_pool._upsert_entry` interaction with concurrent `load_pool` calls from sibling processes is not modeled (the pool relies on `write_credential_pool` being atomic; no per-call lock). Worth a dedicated concurrency audit.
- `google_oauth._OAuthCallbackHandler` stores `expected_state` as a class attribute — concurrent OAuth flows would clobber. In practice login is interactive and singular; flag if Hermes ever supports multi-account login.
