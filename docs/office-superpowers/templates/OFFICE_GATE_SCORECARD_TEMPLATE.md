# Office Gate Scorecard Template

Use this artifact before handoff/closeout for Agent Office work. Keep all secrets, tokens, cookies, phone numbers, emails, raw user IDs, and private keys out of this file; redact as `[REDACTED]`.

```json office_gate_scorecard
{
  "schema_version": 1,
  "task_id": "t_xxxxxxxx",
  "policy_version": "office-superpowers-v1",
  "created_at": "YYYY-MM-DDTHH:MM:SSZ",
  "gates": [
    {
      "gate": "Acceptance gate name",
      "command_or_check": "exact command/check run",
      "exit_code_or_artifact": "exit code 0 or artifact inspection result",
      "artifact_paths": ["relative/or/absolute/safe/path.json"],
      "verdict": "PASS",
      "rationale": "Why this evidence satisfies the gate. Benchmark/performance/release/deploy/GPU claims require a real artifact path."
    }
  ],
  "scope_change_requests": []
}
```

Allowed verdicts: `PASS`, `FAIL`, `PARTIAL`, `BLOCKED`, `NOT_APPLICABLE`, `PASS_WITH_CAVEAT`.

Heavy evidence rule: if the gate mentions benchmark, performance, latency, throughput, QPS/RPS, GPU, CUDA, Colab, release, deploy, production, model metric, accuracy, F1, AUC, or speedup, include a real artifact path such as Criterion output, k6 JSON, pytest report, benchmark JSON, release evidence, or Colab notebook/log export.

Scope change rule: do not silently reduce scope. If a requirement cannot be satisfied after a serious attempt, add a parseable `SCOPE_CHANGE_REQUEST` block to the Kanban comment and mark the affected gate `BLOCKED` or `PARTIAL`.
