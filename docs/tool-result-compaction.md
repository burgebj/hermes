# Tool Result Compaction

Tool result compaction is an opt-in feature for long, tool-heavy Hermes sessions. It reduces repeated message-history growth by saving large string tool results to local disk and replacing the message-history copy with a compact JSON reference.

The feature is disabled by default and is designed to fail open: if anything goes wrong while reading config, writing raw output, or enforcing storage limits, Hermes keeps the original tool result unchanged.

## Configuration

Add this section to `~/.hermes/config.yaml`:

```yaml
tool_result_compaction:
  enabled: false
  threshold_tokens: 5000
  raw_result_dir: ""      # empty => ~/.hermes/raw_results
  max_disk_mb: 500
  preview_chars: 1000    # first 1000 + last 1000 chars
```

A copyable example is also available at `examples/tool-result-compaction.config.yaml`.

### Fields

| Field | Default | Meaning |
|---|---:|---|
| `enabled` | `false` | Enables compaction when true. |
| `threshold_tokens` | `5000` | Minimum estimated token count before a string tool result is compacted. Hermes uses a dependency-free `chars / 4` estimate. |
| `raw_result_dir` | `""` | Directory for raw result JSON files. Empty means `~/.hermes/raw_results`. `~` and environment variables are expanded. |
| `max_disk_mb` | `500` | Disk quota for raw result files. Set `0` or a negative value to disable quota cleanup. |
| `preview_chars` | `1000` | Number of chars to keep from the start and end of the tool result in the compacted preview. |

## Behavior

When enabled and a string tool result is at or above the threshold:

1. Hermes writes the full result to a JSON file under `raw_result_dir`.
2. Hermes replaces the message-history content with a compact JSON object containing:
   - `type: "compacted_tool_result"`
   - tool name
   - tool call id
   - original char count
   - estimated original token count
   - first+last preview
   - `raw_result_path`
   - a note explaining how to recover exact output
3. Hermes enforces the disk quota by deleting the oldest raw result files until usage drops below 80% of the quota.

The current raw result file is protected from immediate quota cleanup so the compacted message never points to a file that was just deleted.

## Storage and permissions

Raw results are written as JSON files. Directories are created with private permissions (`0o700`) and raw result files are written with private permissions (`0o600`) where the operating system supports `chmod`.

Example default path:

```text
~/.hermes/raw_results/<session_id>/<tool_call_id>_<tool_name>_<timestamp>.json
```

## Recovery

If the model needs exact output later, it can read the file at `raw_result_path` and inspect the `content` field in the JSON payload.

This path-based recovery is intentionally simple for the first draft. It makes exact-output recovery possible without introducing a new lookup service or identifier resolver. A future version could replace `raw_result_path` with a session-scoped reference ID if reviewers prefer not to expose local paths in model-visible messages.

## Benchmarks

Two local, LLM-free benchmark helpers are included:

```bash
python3 scripts/benchmark_tool_result_compaction.py --tool-results 10 --result-chars 50000
```

This generates synthetic tool outputs, runs them through the real compaction path, and prints estimated before/after token pressure.

```bash
python3 scripts/replay_tool_result_compaction.py path/to/tool_results.jsonl --content-field content
```

This replays recorded JSONL tool results. Each JSONL object should contain a string field with the tool output; non-string values are skipped. Use `--content-field` if the recorded output is stored under a different key.

Both scripts use the same dependency-free `chars / 4` token estimate as the compaction module. They do not call an LLM.

## Limitations

- Only string tool-result content is compacted.
- Multimodal/list/dict tool results are skipped.
- This is not LLM summarization; it is deterministic preview + local raw storage.
- Recovery currently uses a local `raw_result_path`; remote execution modes may need a reference-ID resolver in a future iteration.
- Compaction happens after existing tool result persistence and active-model content conversion, before the tool result is appended to conversation history.
