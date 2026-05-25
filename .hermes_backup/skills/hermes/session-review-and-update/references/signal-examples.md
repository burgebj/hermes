# Signal Examples — When to Create or Update a Skill

This reference catalogues concrete signals from real sessions that warrant memory or skill updates. Use it to recognize patterns during session review.

## 1. User Frustration Signals

### "Why is it so slow?"
- **Session:** DeepSeek V4 Flash throughput testing
- **Context:** Server was 9x slower than expected; `-cc.pass_config.fuse_allreduce_rms=False` disabled an essential AllReduce+RMSNorm fusion
- **Action:** Remove the broken flag, verify server matches reference script
- **Skill tip:** Add to `serving-llms-vllm` pitfalls: "Never carry over flags from multi-node configs to single-node without verification"

### "This didn't work" / "It just hangs"
- **Session:** vLLM server startup hangs on 8x DP workers with `shm_broadcast: No available shared memory`
- **Context:** This is normal during compilation — 8 workers each run torch.compile independently
- **Action:** Wait ~8 minutes. Check `/v1/models` endpoint. If it still hangs, check logs for OOM
- **Skill tip:** Add startup timeout guidance to the relevant deploy skill

### "It's still not working..."
- **Session:** Repeated failures with DP+EP server on 70.88
- **Root cause:** Inter-node DP synchronization + MoE All2All over 1 Gbps TCP
- **Action:** Switch to single-node TP-only configuration
- **Skill tip:** Add to remote-deploy skill: "Measure inter-node bandwidth first if using DP+EP"

## 2. Technique Discovery Signals

### "Use MTP (Multi-Token Prediction)"
- **Context:** MiniMax-M2.7 config has `num_mtp_modules: 3` — 3 speculative draft modules
- **Action:** Enable speculative decoding flags in the startup script
- **Skill tip:** Add MTP configuration subsection to the model's deploy skill

### "Use systemd-run for persistent background processes"
- **Context:** SSH sessions keep timing out during long benchmarks
- **Solution:** Use `systemd-run --user --scope --unit=name command` for SSH-proof background jobs, or `setsid -w` for simpler cases
- **File:** Add `scripts/persistent-runner.sh` template to the deploy skill

### "Resumable file transfer for large models"
- **Context:** 131 GB NVFP4 model copy between servers
- **Solution:** Use `rsync -avP --progress` (resumable, shows progress) over `scp -r` (not resumable)
- **Skill tip:** Add to remote-70-* skills references/model-transfer.md

## 3. Outdated Skill Corrections

### Server flag mismatch
- **Session:** Our manually-built server vs `start_vllm_no_docker.sh` reference script
- **Finding:** They were nearly identical — only difference was `--max-model-len` and `-cc.pass_config.fuse_allreduce_rms=False`
- **Action:** Verify reference script flags before diverging
- **Skill patch:** Add to deploy skill: "Always diff against reference scripts before changing flags"

### TP size FP8 constraint
- **Session:** DeepSeek V4 Flash — TP=16 fails because `q_lora_rank=1024/16=64` not divisible by FP8 block_k=128
- **Constraint:** Every TP-split dimension must be divisible by 128 for FP8 quant
- **Action:** TP=8 is max viable for Flash (1024/8/128=1); TP=16 fails
- **Skill patch:** Add FP8 divisibility check to deploy skill's pre-flight section

### GPU memory budget calculation
- **Session:** DeepSeek V4 Flash on 8×RTX 5090 (32 GB) — weights=19.84 GiB + CUDA graphs=4.77 GiB = ~24.6 GiB, leaving ~7.4 GiB
- **Variance:** RTX PRO 6000 (96 GB) vs RTX 5090 (32 GB) — model can fit entirely on one PRO, but needs careful budget on 5090
- **Action:** Document memory budget per GPU model in the deploy skill

## 4. User Teaching Signals

### "Compare to start_vllm_no_docker.sh, why is it slower?"
- **Session:** User asked to compare our server against the reference script
- **Lesson:** Always have a reference baseline to compare against
- **Action:** User identified that metrics should be comparable

### "Check what GPU is on 70.96"
- **Session:** User asked for GPU type on a node before deploying
- **Lesson:** Always check hardware capabilities before suggesting a deploy strategy
- **Skill tip:** Add to deploy skills: "Step 0: Check GPU model and memory with `nvidia-smi`"

### "Use DP+EP for MiniMax M2.7"
- **Session:** User specified exact parallelization strategy
- **Context:** Model is 256 MoE experts, NVFP4 quantized, fits in one GPU's non-expert memory
- **Action:** DP=8 + EP, TP=1 — no tensor parallelism needed
- **Skill tip:** Document which models need TP vs DP+EP in deploy skill references/

## 5. Architecture/Design Signals

### Class-level skill organization
- **Session:** User insisted on umbrella skills with sub-sections, not flat skill lists
- **Context:** Skills library should mirror class hierarchies — broad categories with inheritable patterns
- **Action:** New skills should always be umbrella/class-level; narrow skills should be absorbed
- **Signal strength:** High — user repeated this multiple times

### Skill → memory migration boundary
- **Session:** User explicitly stated "preferences should go in SKILL.md, not memory"
- **Context:** User corrections about how to save certain types of information
- **Action:** Maintain clear boundary: procedures → skills, facts → memory

### References directory structure
- **Session:** User wants each skill to have `references/`, `templates/`, `scripts/` subdirectories
- **Action:** When creating skills, always add at least `references/` with supporting documentation

## Quick Reference: Signal → Action Mapping

| Signal Type | Example Phrase | Immediate Action | Deferred Action |
|---|---|---|---|
| Command error | "That flag is wrong" | Patch loaded skill now | — |
| Performance complaint | "It's so slow" | Investigate bottleneck | Add to pitfalls |
| User teaches | "Use XYZ instead" | Create/update skill | Add references/ |
| Edge case | "Crashed when..." | Fix and restart | Document fix |
| Repeat pattern | Same 3rd time | Check if umbrella covers it | Create if not |
| User corrects behavior | "Don't ask, just do" | Save to memory now | Review skill for gaps |
| Environment discovery | "It's on WSL not Linux" | Save to memory | — |
| Reference script diff | "Check start_vllm_no_docker.sh" | Verify and align | Add baseline check |

## Anti-Patterns to Avoid

- ❌ Creating a new skill for every trivial discovery — always try to patch an existing umbrella first
- ❌ Saving step-by-step procedures to memory — they belong in skills
- ❌ Saving user preferences to skills — they belong in memory
- ❌ Creating narrow skills that could be subsections of existing ones
- ❌ Forgetting to update metadata (date, updated fields) in skills
- ❌ Letting loaded skills become stale after session — patch immediately if you find errors
