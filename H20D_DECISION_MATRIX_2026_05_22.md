# h20d Freeze-Lift Decision Matrix — May 26, 2026

**Status:** FINAL (Evidence collection complete as of May 22)  
**Next gate:** May 26, 2026 governance decision  
**Decision authority:** Biotech screener Phase 2 governance  
**Scope:** Path A (Freeze Lift) / Path B (Hybrid Defer) / Path C (Extended Hold)

---

## Input Summary (As of May 22, 2026)

### Spec Review Verdicts (Locked May 22)

| Spec | Verdict | Status | h20d Condition |
|------|---------|--------|---|
| **Spec 072 vNext D8/D9** | CONDITIONAL ADVANCE | ranker-shadow only, post-Spec-071-audit | ✅ Ready for Path A if 071 clears |
| **Clinical Phase A** | REAFFIRM | selector closed, ranker shadow deferred | ✅ Ready for Path A |
| **Catalyst Phase A** | REAFFIRM | no new selector weight, ranker shadow deferred | ✅ Ready for Path A |

**All verdicts comply with alpha freeze.** No unconditional promotions authorized.

---

### OPS-CI-001 — Code Remediation Verified Locally (Infrastructure TBD)

**Status:** Code correctness risk = LOW | Infrastructure validation risk = MEDIUM | Governance blocker = NO

**Findings:**
- **Root cause identified:** 14 lint violations in Phase 2 Step 4 KG commits (11 unused imports, 3 f-string placeholders)
- **Remediation:** lint-only cleanup, no functional changes, all tests pass locally
- **Branch:** `fix/ops-ci-001-kg-lint-cleanup-2026-05-22` created and pushed
- **Local verification:** ✅ 52+ tests pass | ✅ pre-commit all passing | ✅ 0 test assertion changes
- **Remote CI status:** ⏸️ Blocked by GitHub Actions budget exhaustion (infrastructure issue, not code)

**Governance exception (bounded):**
- This h20d decision tolerates absent remote CI validation ONLY because:
  * Changes are lint-only (no semantic modifications)
  * Functional behavior is unchanged (test assertions identical)
  * Broad local test coverage passed (KG loader/queries/contradictions/integration + Spec 104)
  * Failure root cause independently identified and fixed
  * Branch has been pushed and will be confirmed when infrastructure is restored
- **This exception does not generalize into normal policy.** Future lint/CI issues must be resolved with full remote validation before governance decisions.

**Operational follow-up:** Re-run remote CI after GitHub Actions quota restoration to confirm (non-blocking for h20d).

---

### 13F Q1 2026 Cohort Quarantine (As of May 19)

**Status:** ✅ CLEARED

- Filing coverage: 42/48 managers (87.5%) + all three priority firms (Fairmount, Deep Track, Logos) filed by May 15
- Jaccard stability: 0.875 (threshold ≥0.70)
- All six validation gates: PASS
- Institutional distortion: RESOLVED (inst_delta_z variance stabilized May 25)

---

### Knowledge Graph Phase 2 Step 4 (As of May 21)

**Status:** ✅ COMPLETE (68/68 tests pass)

- Phase 4a (loader): 17 tests PASS
- Phase 4b (queries): 10 tests PASS
- Phase 4c (contradictions): 12 tests PASS
- Phase 4e (integration): 13 tests PASS
- Phase 1 PoC (provenance): 22 tests PASS
- **Architecture validated.** No blocking defects.

---

### Production Model Health (As of May 21)

**Status:** ✅ STABLE (no active degradation)

- Latest snapshot: May 21 09:47 UTC (QA PASS)
- Ruleset: 8887576e (v1.14.0, current)
- Selector: Coinvest-only (frozen as designed)
- Ranker: 2-feature frozen (frozen as designed)
- No production code changes authorized by alpha freeze
- Monitoring: active (shadow ranker + forward shadows stable)

---

## Decision Paths

### PATH A — FREEZE LIFT (June 1 Start)

**Conditions (ALL must be met):**

1. ✅ 13F Q1 2026 cohort clear (Jaccard ≥0.70)
2. ✅ Spec review verdicts locked (no h20d reversions)
3. ✅ OPS-CI-001 code remediation verified locally (remote CI TBD, acceptable with caveats)
4. ✅ KG Phase 2 Step 4 complete (68/68 tests, architecture validated)
5. ✅ Production snapshot stable (no QA blockers)

**Unblocks:**
- June 1: Phase 2 KG deployment to production ranker
- June 1: Phase 2 Step 5 implementation (ranker final_score gating)
- June 1: Ranker shadow test starts (post-Spec-071-audit gate)
- July 1: Phase D verdicts (clinical, catalyst, vNext ranker shadow post-30-live-days)

**Blockers (stop Path A if any occur):**
- Spec 071 Lane 1 audit shows clinical/catalyst IC >50% false-catalyst artifact
- vNext signal vanishes on live post-13F-refresh data
- Governance finding (specification, policy, or compliance violation)
- Remote CI confirms test regression when infrastructure restored

**Timeline:**
- May 26: Approve Path A (freeze lift authorized)
- May 27–31: Merge fix/ops-ci-001 PR, final pre-deployment smoke checks
- June 1: KG deployment + ranker shadow validation timeline begins
- July 1: Phase D verdicts (clinical, catalyst, vNext)

---

### PATH B — HYBRID DEFER (June 9 Re-Eval)

**Conditions (≥3 of 5 concerns borderline):**

- 13F cohort marginal (Jaccard 0.70–0.75)
- Spec 071 Lane 1 delayed past May 27
- OPS-CI-001 code remediation pending (local validation not yet complete)
- KG Phase 2 Step 4 incomplete (but on track for June 1)
- Production snapshot shows warning-level drift

**Timeline:**
- May 26: Approve Path B (defer deployment to June 9, run staging validation)
- May 27 – June 8: Staging snapshot testing (non-live ranker shadow)
- June 9: Re-evaluate with fresh evidence (13F final, Spec 071 status, KG completion)
- June 15: Ranker shadow begins (if re-eval clears)
- July 15: Phase D verdicts (deferred 2 weeks)

**Exit criteria (to Path A):** All blockers resolved by June 9 re-eval

**Exit criteria (to Path C):** Path A blockers confirmed unresolved by June 9

---

### PATH C — EXTENDED HOLD (Q3 2026)

**Conditions (≥2 critical blockers unresolved):**

- 13F Jaccard <0.70 (cohort instability persists)
- vNext signal vanishes or regresses post-13F
- Governance finding blocks freeze lift
- Spec 071 Lane 1 impact unquantified past June 1

**Timeline:**
- May 26: Approve Path C (defer all KG/ranker/vNext work to Q3)
- June 20: Mid-point re-evaluation (reassess blocker status)
- June 30: Final decision (extend hold or resume Path A/B)
- August 1: Next verdict window (if extension approved)

---

## Governance Exception Rationale (OPS-CI-001)

**Why absent remote CI is tolerable here:**

| Criterion | Evidence |
|-----------|----------|
| Scope is bounded | Lint-only (formatting, unused imports); no semantic changes |
| Behavior is unchanged | All 52+ tests passing locally; test assertions identical |
| Coverage is broad | KG loader/queries/contradictions/integration + Spec 104 + alpha signal |
| Root cause identified | 14 violations explicitly diagnosed and fixed |
| Validation path clear | Fix branch pushed; remote validation queued post-quota restoration |

**Why this is NOT generalizable:**

- This applies only to lint/formatting regressions with no code-path changes
- Future bugs/regressions must be validated remotely before h20d decisions
- Remote CI absence is acceptable ONLY because the failure cause is infrastructure (budget), not test regression
- If remote CI had shown test failures, Path A would be blocked

---

## Critical Dependencies (All Paths)

| Dependency | Owner | Due | Impact |
|------------|-------|-----|--------|
| Spec 071 Lane 1 audit (false-catalyst impact) | Biotech screener team | ~June 1 | Clinical/Catalyst ranker promotion gating |
| Spec 077 outcome binder (event_ev_p_hit wiring) | Biotech screener team | ~June 1 | Catalyst EV calibration (deferred to Q3) |
| Checklist v2 gates (FM, Bootstrap, FDR, LOSO) | Biotech screener team | Post-30-live-days | Any signal promotion to production |
| GitHub Actions quota restoration | GitHub support / account | On-demand | OPS-CI-001 remote validation (non-blocking) |

---

## Decision Template (Fill May 26)

```markdown
# h20d Freeze-Lift Approval — May 26, 2026

## Decision: [PATH A / PATH B / PATH C]

## Rationale

[Summarize why this path was chosen; reference blocking/clear conditions above]

## Evidence Reviewed

- Spec review verdicts: locked
- 13F cohort status: [current Jaccard, manager count]
- KG Phase 2 completion: [test results]
- OPS-CI-001 status: [local validation summary]
- Production health: [snapshot date, QA status]

## Conditions Met

[Checklist of required conditions for chosen path]

## Known Risks

[Any unresolved or deferred concerns]

## Next Gate

[Verdict date and success criteria]

## Sign-Off

Approved by: [Governance authority]  
Date: 2026-05-26  
Commit: [Merged commit SHA for any fixes]
```

---

## Known Unknowns / Residual Risk

The following are not blockers, but represent explicit unresolveds that governance authority should acknowledge:

### Infrastructure Validation

- **Remote CI unconfirmed (OPS-CI-001):** GitHub Actions quota exhaustion prevented final lint cleanup validation. Local coverage is strong, but infrastructure validation gap remains. Will be confirmed post-quota restoration (non-blocking for h20d, but acknowledged as unresolved).

### Production Behavioral Observability

- **Ranker shadow behavior post-unfreeze:** KG Phase 2 integration (governance gating on final_score) will be deployed live for the first time on June 1. No production observation history yet. Early live days (June 1–7) will be high-information window.

- **KG Phase 2 production integration:** Knowledge graph loader, queries, and contradiction detection validated locally (68/68 tests). Not yet production-observed. Operational surface (cron job failures, edge cases, data staleness) remains unobserved.

### Downstream Coupling Risks

- **Expectation-layer plumbing expansion:** Recent work (Spec 072 vNext, clinical/catalyst quality layers, clinical Phase A, catalyst Phase A) significantly expanded conditional expectation logic and filtering chains. Composition behavior (how multiple conditional gates interact under stress or data degradation) not yet stress-tested.

- **CLAUDE.md restructure and agent adherence:** Documentation was substantially reorganized (May 20–22). Agent skill adherence to updated instructions is assumed but not validated by any independent test. Future agent work will be first real-world validation.

### Observation Windows

- **30-live-day clock:** Spec 072, Clinical, and Catalyst verdicts all defer final promotion to post-30-live-days (July 1). The quality of live behavior during June 1–30 will determine whether evidence supports or invalidates the Checklist v2 gates.

---

## Summary

All evidence collected. OPS-CI-001 is code-correct (local validation strong) but externally unconfirmed (infrastructure quota). This is tolerable for h20d purposes with the governance exception documented above.

Known unknowns are appropriately scoped and acknowledged without blocking the decision.

**Ready for May 26 decision.**
