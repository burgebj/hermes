# Precedent: User's Active-Update Mandate (2026-05-12)

## Origin

During a session focused on deploying DeepSeek-V4-Pro vLLM across multi-node GPU servers, the user interrupted to correct Hermes's passive approach to skill management:

> "your entire output about skips is a missed learning opportunity ... be active ... I actually read pass and I think change is not small, it's a missed learning opportunity"

## Key Points from the User

1. **"Be active"** — The user read an explanation of why updates were skipped and considered *that explanation itself* a missed learning opportunity.
2. **"Change is not small"** — Even trivial-seeming updates have cumulative value.
3. **"Pass is a missed learning opportunity, not neutral"** — This is the core framing. A session without a skill update is a cost, not a neutral result.
4. **The user reads the output.** When the agent writes a long justification for skipping updates, the user reads it and expects action instead.

## Application

All future sessions should:
- Patch loaded skills when errors are fixed or steps discovered.
- Create/update umbrella skills when a new pattern is identified.
- At minimum, add a `references/` note documenting a precedent or lesson.

## Concrete Example from This Session

During this session, the following should have triggered skill updates (and did, after the correction):

- **`build-vllm-fork-cn`** / **`remote-70-88`** / **`remote-70-93`** skills: discovering the `GLOO_SOCKET_IFNAME` trick for multi-node TP, the `--data-parallel-address` fix, and FP8 `block_k=128` TP divisibility constraints.
- **`serving-llms-vllm`**: adding `--enable-expert-parallel`, `--enable-ep-weight-filter`, `--data-parallel-size` flags for MoE DP deployments.
- **`skill-library-maintenance`** (this skill): documenting the active-update mandate itself.

## Future Sessions

Before concluding any session, check:
1. Did I load a skill? -> Patch it if anything was learned.
2. Did I fix a bug or discover a workaround? -> Update the relevant umbrella.
3. Did the user give meta-feedback? -> Add a references/ note.
4. Have I done at least one skill write this session?
