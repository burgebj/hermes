---
name: agent-learning-loop
description: "Use when turning agent traces into reviewed memory/skill proposals and SFT/DPO datasets without mutating global Hermes state."
version: 1.0.0
author: lamenting-hawthorn
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [agent-learning, self-improvement, trace-curation, memory, skills, sft, dpo, evaluation]
    related_skills: [fine-tuning-with-trl, axolotl, subagent-driven-development, requesting-code-review]
---

# Agent Learning Loop

## Overview

Use this skill to build or operate a review-first learning loop for agents: ingest completed traces, evaluate them, distill candidate memory and skill updates, review those proposals, and export supervised fine-tuning (SFT) or preference (DPO) datasets.

The core rule is separation: the learning loop should be a sidecar/export layer, not an automatic self-mutating runtime. It may read Hermes traces and produce proposals, but it should not silently write into a user's live memory, bundled skills, config, or credentials.

## When to Use

Use this skill when:

- The user wants an agent to "learn from itself" or improve from completed work
- You need to curate Hermes sessions or other agent traces into training data
- You want memory/skill candidates but need human review before applying them
- You are designing a local self-improvement pipeline around SFT, DPO, or evals
- You need a clean export path that stays separate from an existing Hermes install

Do not use this skill for:

- Directly editing live `~/.hermes/memories` or `~/.hermes/skills` without review
- Storing API keys, cookies, tokens, or private credentials in training records
- Treating every successful session as training data; curation is required
- Replacing Hermes memory or skill tools; this is a sidecar workflow

## Architecture

The recommended pipeline is:

```text
agent session / trace
  -> ingestion adapter
  -> normalized trace schema
  -> local store
  -> evaluation
  -> distillation
  -> review queue
  -> approved exports
  -> SFT / DPO JSONL
```

Keep each boundary explicit:

| Stage | Input | Output | Notes |
|---|---|---|---|
| Ingest | Hermes/session JSON, JSONL, logs | normalized trace | Preserve source metadata |
| Evaluate | normalized trace | score, tags, notes | Prefer deterministic checks first |
| Distill | trace + eval | memory/skill proposals | Proposal only, no mutation |
| Review | proposals | approved/rejected state | Human or independent verifier gate |
| Apply/export | approved proposals | markdown/JSONL artifacts | Write to project-local output |
| Train | JSONL datasets | model artifacts | Run outside Hermes core |

See `references/skillloop-architecture.md` for a more detailed reference design.

## Clean Export Boundary

For a local sidecar project, use a project root such as `./agent-learning/` and keep generated state underneath it:

```text
.agent-learning/
  learning.db
  approved/
    memory/*.md
    skill/*.md
exports/
  sft.jsonl
  dpo.jsonl
```

Do not write directly into:

```text
~/.hermes/memories
~/.hermes/skills
~/.hermes/config.yaml
~/.hermes/.env
```

If the user later wants to import approved outputs into Hermes, make that a separate explicit step with a final review.

## Normalized Trace Shape

Use a small schema that can represent multiple runtimes:

```json
{
  "id": "trace-id",
  "source": "hermes",
  "created_at": "2026-06-05T00:00:00Z",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."},
    {"role": "tool", "name": "terminal", "content": "..."}
  ],
  "metadata": {}
}
```

Keep tool calls and tool results if they are needed for evaluation, but redact secrets before writing shared datasets.

## Evaluation Signals

Start with deterministic signals before adding LLM judges:

Positive signals:

- final answer exists
- task was verified with real commands or tool output
- tests passed
- user confirmed success
- no unresolved tool failures

Negative signals:

- traceback or exception
- failed command without recovery
- user correction such as "wrong", "no", "actually", "don't do that"
- fabricated or unverified output
- unsafe credential handling

Example evaluation record:

```json
{
  "trace_id": "abc123",
  "score": 82,
  "tags": ["has_final_answer", "verified", "success_signal"],
  "notes": ["Tests passed and user accepted result."]
}
```

## Distilling Memory Proposals

Only propose memory for durable facts that will remain useful across sessions:

Good memory candidates:

- stable user preferences
- project conventions
- environment facts that are hard to rediscover
- recurring workflow constraints

Bad memory candidates:

- temporary task progress
- PR numbers, commit SHAs, issue IDs
- raw logs
- credentials or tokens
- facts that will be stale within a week

Use declarative wording:

```text
User prefers final verifier agents only at pre-push/readiness gates.
```

Avoid imperative wording:

```text
Always use verifier agents only at the end.
```

## Distilling Skill Proposals

Create skill proposals when a trace contains a reusable procedure, especially after an error was solved.

A useful skill proposal includes:

- trigger conditions
- exact steps or commands
- pitfalls encountered
- verification checklist
- boundaries and safety rules

Keep generated skills as proposals until reviewed.

## Dataset Export

### SFT

Export high-quality instruction-following conversations:

```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

Skip traces with unresolved failures unless they are intentionally used as negative examples elsewhere.

### DPO

Export preference pairs only when there is a clear chosen/rejected contrast:

```json
{"prompt": "...", "chosen": "...", "rejected": "..."}
```

Examples of valid DPO sources:

- user rejected an answer and accepted a corrected one
- reviewer identified a flawed output and a fixed output exists
- two candidate agent responses were judged against a rubric

Do not invent rejected responses.

## Review Gate

Before exporting or applying learning artifacts:

1. Run deterministic checks.
2. Scan for credentials and PII.
3. Use an independent verifier for final readiness if available.
4. Review memory and skill proposals manually.
5. Export only approved artifacts.

For Hermes coding work, use the user's verifier preference if known: reserve verifier subagents for the final pre-push/export gate unless explicitly requested earlier.

## Example Local Workflow

```bash
# 1. Export or collect traces into ./traces
mkdir -p traces exports

# 2. Ingest traces into a sidecar DB or normalized JSONL
python scripts/ingest_traces.py traces/*.jsonl --out .agent-learning/learning.db

# 3. Evaluate and distill proposals
python scripts/evaluate_traces.py --db .agent-learning/learning.db
python scripts/distill_proposals.py --db .agent-learning/learning.db

# 4. Review proposals
python scripts/review_queue.py list --db .agent-learning/learning.db
python scripts/review_queue.py approve <proposal-id>

# 5. Export datasets
python scripts/export_sft.py --db .agent-learning/learning.db --out exports/sft.jsonl
python scripts/export_dpo.py --db .agent-learning/learning.db --out exports/dpo.jsonl
```

The script names are placeholders for your sidecar implementation. Keep the workflow shape even if the implementation differs.

## Privacy and Safety Checklist

Before sharing, training, or publishing any dataset:

- [ ] No `.env`, API keys, tokens, cookies, SSH material, or auth JSON included
- [ ] No private third-party messages included without consent
- [ ] No sensitive local file paths unless necessary and sanitized
- [ ] Generated state is ignored by git
- [ ] Memory proposals are durable and non-stale
- [ ] Skill proposals are reviewed before import
- [ ] SFT records come from successful or intentionally curated traces
- [ ] DPO records have real chosen/rejected pairs

## Common Pitfalls

1. **Making the loop self-mutating too early.** Start with proposals and explicit review. Automatic memory/skill writes should be opt-in and heavily tested.

2. **Training on failures as if they were successes.** Failed traces are useful for evals and DPO only when clearly labeled.

3. **Leaking secrets through traces.** Tool outputs may contain tokens, URLs, cookies, or env values. Redact before persistence or export.

4. **Overfitting to one user's preferences.** Keep user-specific memory separate from general skills and public datasets.

5. **Skipping provenance.** Preserve source, timestamp, model, and evaluation metadata so bad records can be traced and removed later.

6. **Adding a core Hermes dependency for an experimental workflow.** Prefer an optional skill, plugin, or sidecar until the interface stabilizes.

## Verification Checklist

- [ ] Sidecar writes only inside its selected project root
- [ ] Sample trace can be ingested, evaluated, distilled, reviewed, and exported
- [ ] Generated outputs are gitignored by default
- [ ] Tests cover ingestion, evaluation, review/apply, and export
- [ ] SFT/DPO JSONL validates with a line-by-line JSON parser
- [ ] Final output is backed by real tool/test results, not synthetic claims
