# Tool Result Compaction Review Checklist

Use this checklist before marking the draft PR ready for upstream review.

## Behavior

- Default behavior is unchanged when the feature is disabled.
- Only string tool-result content is compacted.
- Non-string tool results are skipped by the existing guard in `tool_executor.py`.
- Tool messages keep `role`, `name`, `tool_name`, `content`, and `tool_call_id`.
- Compacted content remains a string containing JSON metadata.
- The compacted JSON includes enough information to recover the original output.

## Failure handling

- Config read errors keep the original tool output.
- File write errors keep the original tool output.
- Cleanup errors keep the original tool output.
- Permission-setting failures do not stop tool execution.
- The current raw result file is not removed by immediate cleanup.

## Storage

- Default storage path is `~/.hermes/raw_results`.
- Empty `raw_result_dir` uses the default path.
- Custom `raw_result_dir` expands `~` and environment variables.
- Session ID, tool call ID, and tool name are sanitized before becoming path components.
- `max_disk_mb <= 0` disables cleanup.

## Benchmarks

- `scripts/benchmark_tool_result_compaction.py` does not call an LLM.
- `scripts/replay_tool_result_compaction.py` does not call an LLM.
- Synthetic benchmark reports before/after token estimates and raw file counts.
- Replay benchmark skips non-string content and supports `--content-field`.

## Questions for review

1. Is the insertion point correct: after existing tool-result persistence and active-model conversion, before `messages.append()`?
2. Is default-off acceptable for first landing?
3. Should exact-output recovery use local file paths or a session-scoped reference ID?
4. Should benchmark scripts live in `scripts/`, docs, or tests only?
5. Should this remain one draft PR or be split into smaller stacked PRs?
