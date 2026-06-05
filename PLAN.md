# Plan: Split `_cmd_update_impl` into pull + post-pull phases

## Problem
After `git pull` (or ZIP extraction) overwrites source files on disk, the
running Python process still has the **old** code in `sys.modules` and
`__pycache__`. The current monolith runs post-pull steps (pip install, node
deps, skills sync, config migration, gateway restart) under stale bytecode,
which causes `ImportError` on gateway restart and subtle drift bugs.

## Solution: Two-phase update with re-exec

Split `_cmd_update_impl` into:

1. **`_cmd_update_pull_new_version`** — download new code onto disk
2. **Re-exec** into a fresh Python process
3. **`_cmd_update_post_pull`** — run all post-pull steps under the new code

The re-exec guarantees a clean `sys.modules` / `__pycache__` for phase 2.

---

## Phase 1: `_cmd_update_pull_new_version(args, gateway_mode)`

Everything up to and including "code is on disk, stash is restored":

1. Windows concurrent-hermes guard (exit 2 if locked)
2. Pre-update backup (`_run_pre_update_backup`)
3. Route detection:
   - No `.git` + Windows → `_update_files_via_zip` (download + extract only)
   - No `.git` + non-Windows + pip → **error** (pip self-update ripped out)
   - No `.git` + non-Windows → reinstall hint + exit 1
   - `.git` exists → git flow (below)
4. Git config setup (autocrlf, appendAtomically)
5. Discard lockfile churn
6. Fork detection + origin URL check
7. Fetch + branch logic + stash
8. Check for new commits (if 0, restore + "already up to date" + return)
9. Pre-update snapshot (`create_quick_snapshot`)
10. `git pull --ff-only` (or `reset --hard` on divergence)
11. Post-pull syntax guard (`_validate_critical_files_syntax`) + rollback on failure
12. Restore stashed changes
13. `_invalidate_update_cache()`
14. `_clear_bytecode_cache()`

At this point new code is on disk and the working tree is clean.
**Return `True`** to signal "re-exec needed".

### ZIP path change

`_update_files_via_zip` currently does the full pipeline (download, extract,
clear bytecode, pip install, node deps, skills sync, curator notices, kill
dashboard). We split it:

- **`_update_files_via_zip`** → rename to `_download_and_extract_zip(args)`:
  downloads + extracts + clears bytecode. Returns `True` when new code landed.
- The pip install / node deps / skills sync / etc moves to
  `_cmd_update_post_pull` (shared by both git and zip).

### Already-up-to-date fast path

If git reports 0 new commits (or zip extraction shows no changes), we return
`False` from pull — no re-exec needed. The caller prints "already up to date"
and exits cleanly.

---

## Re-exec mechanism

After `_cmd_update_pull_new_version` returns `True`:

```python
def _reexec_for_post_pull(args, gateway_mode: bool):
    """Replace this process with a fresh Python running --post-pull."""
    argv = list(sys.argv)
    # Insert --post-pull before any positional args (there shouldn't be any)
    argv.append("--post-pull")

    if gateway_mode:
        argv.append("--gateway")

    # Pass pre-update snapshot ID if we have one
    snapshot_id = getattr(args, "_pre_update_snapshot_id", None)
    if snapshot_id:
        argv.extend(["--pre-update-snapshot", snapshot_id])

    if sys.platform == "win32":
        # Windows: os.execvp internally does spawn+exit (PID changes).
        # The bootstrap installer watches the original PID via run_streamed().
        # If we execvp, the installer sees exit-0 before post-pull finishes.
        # Instead: relay through a subprocess so the parent PID stays alive
        # until the child completes. The installer's child.wait() sees the
        # real exit code.
        result = subprocess.run([sys.executable, "-m", "hermes_cli.main"] + argv)
        sys.exit(result.returncode)
    else:
        # POSIX: true exec — same PID, no stale modules.
        os.execvp(sys.executable, [sys.executable, "-m", "hermes_cli.main"] + argv)
```

### Why subprocess.run on Windows (not Popen+exit)

`Popen` + `sys.exit` has a race: if the parent exits before the child's
stdout pipe is drained, the bootstrap installer's `BufReader` gets a broken
pipe and the child may get SIGPIPE. `subprocess.run` waits for the child to
finish and properly reaps it, then we forward the exit code. This is
functionally identical to what the bootstrap installer already does when it
spawns `hermes update` directly.

### Gateway output file continuity

In gateway mode, `hermes update --gateway` writes to an output file that the
gateway watches. On POSIX, `os.execvp` inherits FDs so the output file
continues being written. On Windows, the relay subprocess inherits the
same FDs (subprocess.run passes them through). The `--gateway` flag is
passed to the child so `_install_hangup_protection` / `_finalize_update_output`
work correctly.

**However**, the gateway's spawn path (gateway/run.py) launches the update
detached with its own output redirection. The output file is opened by the
*child*, not inherited from the parent. So on the re-exec path the child
re-opens the same output path via `_install_hangup_protection` (which
already sets up the update.log mirror). No special handling needed.

### Bootstrap installer interaction

The Windows bootstrap installer (`update.rs`) calls `hermes update --yes
--gateway` via `run_streamed()`, which:

1. Spawns the hermes binary as a child process
2. Reads stdout/stderr line-by-line
3. Waits for exit via `child.wait().await`
4. Checks exit code (0 = success, 2 = concurrent lock)

Our Windows relay pattern is safe because:
- The **parent** (original `hermes update` PID) stays alive until the
  **child** (post-pull phase) exits
- `child.wait()` in the installer sees the parent exit only after the
  child finishes → correct exit code propagation
- The parent's stdout/stderr are piped to the installer's `BufReader`;
  the child inherits those FDs, so output streams continue seamlessly

---

## Phase 2: `_cmd_update_post_pull(args, gateway_mode)`

All post-pull steps, running under freshly-exec'd Python with clean
`sys.modules`. Steps are identical regardless of whether code arrived via
git or zip:

1. `_refresh_active_lazy_features()`
2. Python dependency install (uv/pip — the entire `ensure_uv` +
   `_install_python_dependencies_with_optional_fallback` block)
3. `_update_node_dependencies()`
4. `_build_web_ui`
5. Desktop app rebuild check + build
6. Skills sync (`sync_skills` + profile seed)
7. Honcho profile sync
8. Config migration (missing env, missing config, version bump, interactive prompts)
9. Cron jobs safety-net restore
10. Curator notices (first-run + recent-run)
11. FHS PATH guard
12. cua-driver refresh (macOS)
13. Gateway restart (systemd, launchd, manual processes, survivor sweep)
14. Legacy unit warning
15. Kill stale dashboard processes
16. Print "Update complete!" + tip

---

## Argparse changes

Add to `update_parser`:

```python
update_parser.add_argument(
    "--post-pull",
    action="store_true",
    default=False,
    help=argparse.SUPPRESS,  # internal flag — not for users
)
update_parser.add_argument(
    "--pre-update-snapshot",
    default=None,
    metavar="ID",
    help=argparse.SUPPRESS,  # carries snapshot ID across re-exec
)
```

## `cmd_update` dispatch changes

```python
def cmd_update(args):
    # ... existing managed/docker/check guards ...

    _update_io_state = _install_hangup_protection(gateway_mode=gateway_mode)
    try:
        if getattr(args, "post_pull", False):
            _cmd_update_post_pull(args, gateway_mode=gateway_mode)
        else:
            needs_reexec = _cmd_update_pull_new_version(args, gateway_mode=gateway_mode)
            if needs_reexec:
                _reexec_for_post_pull(args, gateway_mode=gateway_mode)
            # if not needs_reexec, we're already done (already up to date)
    finally:
        _finalize_update_output(_update_io_state)
```

**Important**: `_finalize_update_output` runs in the parent on the
non-reexec path. On the re-exec path, it runs in the parent *before*
the exec replaces the process. On Windows relay, it runs before
`subprocess.run`. The post-pull child has its own
`_install_hangup_protection` / `_finalize_update_output` cycle because
`cmd_update` is re-entered via the fresh process.

Wait — actually on the re-exec path the parent process is *replaced* (POSIX)
or *exits* (Windows relay). So `_finalize_update_output` would run in the
`finally` block *after* `_reexec_for_post_pull` returns. But on POSIX,
`os.execvp` never returns (or raises on failure). On Windows,
`sys.exit(result.returncode)` never returns. So the `finally` block only
runs if `_reexec_for_post_pull` raises (e.g. execvp fails). That's the
right behavior — cleanup only on failure.

On the post-pull path, `cmd_update` is called fresh in the new process,
so `_install_hangup_protection` + `_finalize_update_output` wrap the
post-pull phase correctly.

---

## Pip install path: RIP

`_cmd_update_pip` is removed. `cmd_update` already checks for
`is_managed()` and `detect_install_method() == "docker"` before entering
the impl. We add pip to the early-exit guards:

```python
def cmd_update(args):
    # ... existing is_managed() check ...

    if detect_install_method(PROJECT_ROOT) == "docker":
        print(format_docker_update_message())
        sys.exit(1)

    if detect_install_method(PROJECT_ROOT) == "pip":
        from hermes_cli.config import recommended_update_command
        print("✗ Self-update is not supported for pip/uv-tool installs.")
        print(f"  Run '{recommended_update_command()}' instead.")
        sys.exit(1)

    # ... --check and --post-pull dispatch ...
```

Also update `_cmd_update_check` to keep its existing pip check path
(it just checks PyPI — no code mutation, no re-exec needed).

---

## Cross-phase state

| State | Mechanism |
|-------|-----------|
| `gateway_mode` | Passed via `--gateway` flag (already exists) |
| `assume_yes` | Passed via `--yes` flag (already exists) |
| `pre_update_snapshot_id` | New `--pre-update-snapshot` arg |
| `auto_stash_ref` | NOT needed — stash is restored in phase 1 |
| `branch` | Passed via `--branch` (already exists) |
| `force` | Passed via `--force` (already exists) |
| `backup` / `no_backup` | Passed via `--backup` / `--no-backup` (already exists) |

The only new cross-phase arg is `--pre-update-snapshot`, because the
snapshot is created in phase 1 but consumed in phase 2 (cron safety net).

---

## `_update_files_via_zip` refactor

Rename current function to `_download_and_extract_zip(args) -> bool`:

- Downloads ZIP, extracts, clears bytecode
- Returns `True` if new code was written
- Does NOT do pip install, node deps, skills sync, etc.

The old post-extraction code moves to `_cmd_update_post_pull`.

---

## Test impact

| Test file | Change needed |
|-----------|--------------|
| `test_cmd_update.py` | Update mocks for two-phase flow; test `--post-pull` dispatch |
| `test_cmd_update_docker.py` | Minimal — docker bailout is unchanged |
| `test_update_autostash.py` | Stash logic stays in phase 1 — should work as-is |
| `test_update_concurrent_quarantine.py` | Concurrent check stays in phase 1 — should work as-is |
| `test_managed_installs.py` | Add pip install error test (was previously allowed) |
| `test_uv_tool_update.py` | Remove — pip/uv-tool self-update is now an error |

---

## Execution order summary

```
hermes update
  └─ cmd_update()
      ├─ is_managed? → error
      ├─ docker? → error + hint
      ├─ pip? → error + hint (NEW — was _cmd_update_pip)
      ├─ --check? → _cmd_update_check() (unchanged)
      ├─ --post-pull? → _cmd_update_post_pull() (phase 2)
      └─ else → _cmd_update_pull_new_version() (phase 1)
           ├─ download code (git pull or zip)
           ├─ validate + stash restore + clear bytecode
           └─ if new code: _reexec_for_post_pull()
                ├─ POSIX: os.execvp → same PID, fresh Python
                └─ Windows: subprocess.run + sys.exit → relay
```
