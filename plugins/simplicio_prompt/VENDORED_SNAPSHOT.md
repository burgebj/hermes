# SIMPLICIO_PROMPT Vendored Snapshot

The plugin ships a local copy of the SIMPLICIO_PROMPT runtime so Hermes can
inject and execute the policy without fetching or reading an external GitHub
repository at runtime.

- Local root: `plugins/simplicio_prompt/vendor/simplicio_prompt/`
- Source project: `simplicio-prompt`
- Source commit: `c1df48534a6e23cacee94c8894cc4ca382aa3459`
- Hermes-local changes: the prompt source-of-truth line and plugin wrapper point
  model execution at the bundled local path, and auxiliary benchmark/legacy
  prompt examples use the same any-prompt activation semantics as the runtime
  prompt.
- Vendored files: 29 tracked files, including the prompt, spec, reference
  kernel, guardrails, examples, benchmarks, reports, and visual assets.

The vendored prompt is injected through `pre_llm_call` with a Hermes-local
preamble that forbids runtime GitHub fetches and tells the model to read the
bundled files first.
