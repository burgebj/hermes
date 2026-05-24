# May 22 Spec Review Verdicts — FINAL

**Date:** 2026-05-22  
**Reviewer:** Biotech screener Phase 2 governance  
**Scope:** Spec 072 vNext D8/D9, Clinical Phase A, Catalyst Phase A  
**Constraint:** Alpha freeze active; no production changes authorized  

---

## Spec 072 — vNext D8/D9 Clinical Quality Candidate

### Verdict: CONDITIONAL ADVANCE

**Decision:** Approve `clinical_score_v2_z` for **ranker-only shadow test** post-h20d decision (May 26). No production deployment. Explicit Checklist v2 requirement.

---

### Evidence Summary

**Load-bearing numbers (confirmed):**
- `clinical_score_v2_z` D9 IC: +0.202 (bin-residualized)
- Raw t-stat: +5.05
- NW-adjusted t (estimated): ~+3.0 (after lag correction on n=245 effective obs)
- Confidence: Significant at α=0.01 after correction

**Architecture validation (confirmed):**
- D7 orthogonality test: PASS (no coinvest leakage)
- D8 within-quintile IC: +0.173 (consistent across τ)
- D9 bin-residual: +0.202 (survives conditional gating)

**Prerequisite conditions (status):**
1. ✅ At least 1 distinct signal cluster post-dedup — clinical_score family = ONE cluster
2. ✅ Cohort-quarantine window closed (2026-05-15) AND signal survives post-window subset
3. ✅ Cross-feature correlations computed within L3 — clinical_score_v2_z selected as representative
4. ⏳ **Spec 071 Lane 1 shipped** — FALSE-CATALYST IMPACT STILL UNQUANTIFIED

---

### Prerequisites / Blockers

**MUST SATISFY before ranker shadow test begins (post-h20d):**

1. **Spec 071 Lane 1 delivery** (false-catalyst audit, 17.6% error rate)
   - Impact on L3 holdout set must be quantified
   - If clinical_score IC is ≥50% artifact → signal downgraded to DEFER
   - Status: Ship date TBD; assumed mid-June per Spec 071 roadmap

2. **Checklist v2 full compliance**
   - Forward Monte Carlo (FM) ✓ (not required for shadow, but gate for promotion)
   - Bootstrap IC ✓ (not required for shadow, but gate for promotion)
   - FDR control ⏳ (post-30-live-days; June 1 start, verdict July 1)
   - LOSO ⏳ (cross-snapshot validation; post-30-live-days)
   - Year stability ⏳ (requires 1 year forward data; not applicable)

3. **Spec 072 phase sequence** (must not skip steps)
   - Phase A (audit): ✅ COMPLETE (this verdict)
   - Phase B (shadow design): ✅ APPROVED (single-feature, ranker-only)
   - Phase C (shadow implementation): ⏳ POST-H20D (June 1 start)
   - Phase D (live test): ⏳ GATED on FM + Bootstrap + 30 live days (July 1 decision)

---

### Explicitly NOT Authorized

🚫 **Do NOT:**
- Promote to production selector or sizing
- Combine clinical_score with endpoint_strength or readout_curve (EES v3 trap)
- Tune L3 trap thresholds to make more clinical features pass
- Run ranker shadow test before Spec 071 Lane 1 audit impact is quantified
- Use this signal for any alpha claims until Checklist v2 gates are cleared
- Shadow-ship a clinical-ranked top-30 (architecture freeze in place)
- Broaden ranker test to other clinical features without explicit Phase D gate

✅ **Explicitly ALLOWED:**
- Code development for ranker shadow (does not require approval)
- Monitoring/logging of clinical_score behavior on live snapshots
- Spec 071 hygiene audit of L3 holdout set (dependency work)
- Preparation for Checklist v2 FM + Bootstrap runs (parallel work)

---

### h20d Implication (May 26)

**This verdict UNBLOCKS:**
- Spec 072 Phase B ranker-shadow architecture decision (post-h20d)
- Spec 100 IC tooling integration for ranker final_score (post-h20d)
- Ranker shadow validation timeline: June 1 start (conditional on h20d freeze lift)

**This verdict DEFERS:**
- Spec 072 Phase D (live test) → July 1 verdict (post-30-live-days, post-Spec-071-audit)
- Clinical promotion → Q3 2026 (post-Checklist-v2 gates)

**Critical gate for h20d:**
- If h20d chooses Path A (FREEZE LIFT): Ranker shadow can start June 1 immediately
- If h20d chooses Path B (HYBRID DEFER): Ranker shadow staging starts June 9 (1-week slip)
- If h20d chooses Path C (EXTENDED HOLD): Ranker shadow deferred to Q3

---

## Clinical Phase A — Role Boundaries

### Verdict: REAFFIRM PHASE A AUDIT — SELECTOR CLOSED / RANKER SHADOW DEFERRED

**Decision:** No selector changes. Confirm `clinical_design_quality` as single ranker-shadow candidate. EV transmission non-evaluable pending spec_077 outcome binder.

---

### Evidence Summary

**Selector audit (reconfirmed):**
- ρ(clinical, selector_score) = −0.16 median (13/17 snapshots negatively correlated)
- Unconditional IC: −0.068 (anti-predictive)
- Conditional IC (Spec 057): +0.103 within coinvest tertile (real, but conditional only)
- **Finding:** Clinical is independent but wrong direction for selection; lane closed.

**Ranker shadow candidate (reconfirmed):**
- `clinical_design_quality` ρ = +0.084 within top-coinvest tertile (13/17 snaps positive)
- Cleanest single feature; no spurious correlation with selector
- **Finding:** Viable ranker tiebreaker, NOT selector replacement.

**EV transmission (diagnosis):**
- 64 drops, 0 gains over 16 snapshots (concerning, but data quality issue)
- Outcome binder unfinished (spec_077 scoped 2026-05-06)
- **Finding:** Non-evaluable until wiring complete; do not draw conclusions from current data.

---

### Prerequisites / Blockers

**SATISFIED:**
1. ✅ Selector correlation audit complete (confirms NO_GO)
2. ✅ Ranker candidate identification (single feature locked: `clinical_design_quality`)
3. ✅ Independence check (clinical != coinvest/inst_delta/financial)

**OUTSTANDING:**
1. ⏳ Spec 072 Phase A reconfirmation post-13F refresh (13F Jaccard must stay ≥0.70)
2. ⏳ Outcome binder (spec_077) — required for EV calibration (~June 2026)
3. ⏳ Checklist v2 gates (FM, Bootstrap, FDR, LOSO) — required for promotion

---

### Explicitly NOT Authorized

🚫 **Do NOT:**
- Add any new clinical feature to selector (lane permanently closed)
- Promote clinical_design_quality to ranker before Spec 072 approval
- Use `clinical_score` or `clinical_score_v2_z` in ranker without dedup / single-feature lock
- Broaden ranker shadow to other clinical features (endpoint_strength, biomarker_context, etc.)
- Make decisions based on EV transmission data (outcome binder is broken)
- Claim clinical is a selector-level signal (it isn't)

✅ **Explicitly ALLOWED:**
- Spec 072 Phase A re-run post-13F refresh (dependency check)
- Monitor clinical_design_quality behavior on live snapshots
- Outcome binder development (spec_077)
- Preparation for Checklist v2 FM + Bootstrap (parallel work)

---

### h20d Implication (May 26)

**This verdict UNBLOCKS:**
- Spec 072 Phase B ranker-shadow if vNext D8/D9 advances (dependent gate)
- Clinical ranker shadow timeline tied to Spec 072 (June 1 start, conditional)

**This verdict CONFIRMS:**
- Selector lane closure (permanent until evidence of degradation)
- Clinical is a ranker-tiebreaker role, not selector or standalone alpha
- EV transmission is diagnostic-only (outcome binder not ready)

---

## Catalyst Phase A — Existing Signal + New Candidates

### Verdict: REAFFIRM PHASE A AUDIT — SELECTOR ACTIVE / NO_MORE_WEIGHT / RANKER SHADOW DEFERRED

**Decision:** No selector changes (existing 0.25 weight via `selector_catalyst_block` is optimal). Ranker shadow on `catalyst_score` deferred pending false-catalyst hygiene (Spec 071 Lane 1). EV calibration blocked until n ≥ 30 live days (~July 1).

---

### Evidence Summary

**Selector audit (reconfirmed):**
- `selector_catalyst_block` 0.25 weight: ρ = +0.27 vs final_score
- Top-30% representation: FLAT across catalyst proximity buckets (0-30/31-60/61-120/120+/no-cat all ≈30%)
- Production already absorbs catalyst signal optimally via decay function
- **Finding:** Existing selector weight is correct; no new weight needed.

**Ranker shadow candidate (reconfirmed):**
- `catalyst_score` ρ = +0.19 within top-coinvest (17/17 snaps positive)
- More stable than clinical's +0.08 (but overlaps mechanically with selector)
- **Finding:** Real signal, but harder to isolate from selector; requires false-catalyst audit first.

**EV calibration (diagnosis):**
- 43 HIT/MISS resolved; 81% aggregate hit rate (event-occurred definition, not stock-direction)
- `prediction_composite_score` binder WRONG field (stock-quality composite, not event-likelihood)
- Correct field: `event_ev_p_hit` from event_ev outcome_model
- **Finding:** Non-evaluable now; Spec_077 will wire correct field forward-only (backfill unsafe, 30% match rate).

---

### Prerequisites / Blockers

**SATISFIED:**
1. ✅ Selector weight audit (confirms NO_MORE_WEIGHT)
2. ✅ Ranker candidate identification (single feature locked: `catalyst_score`)
3. ✅ False-catalyst problem identified (18.8% contamination at universe)

**OUTSTANDING:**
1. ⏳ **Spec 071 Lane 1** — false-catalyst hygiene audit impact on ranker signal (CRITICAL)
2. ⏳ Spec 077 outcome binder — wire correct field (`event_ev_p_hit`) forward-only
3. ⏳ Checklist v2 gates (FM, Bootstrap, FDR, LOSO) — required for promotion
4. ⏳ 30 live trading days post-ranker-shadow-start → ~July 1 EV calibration threshold

---

### Explicitly NOT Authorized

🚫 **Do NOT:**
- Add new selector weight (has_catalyst, proximity_bucket, catalyst_in_window, etc.)
- Run ranker shadow test before Spec 071 Lane 1 false-catalyst audit is complete
- Combine `catalyst_score` with `catalyst_in_window` (mechanical overlap)
- Use `prediction_composite_score` for any EV calibration or decision (wrong field)
- Claim the EV signal is proven (81% hit rate is definitional, not predictive power)
- Promote catalyst_score to ranker without Checklist v2 gates

✅ **Explicitly ALLOWED:**
- Spec 071 Lane 1 development (false-catalyst audit on L3 holdout)
- Monitor catalyst_score behavior on live snapshots
- Spec 077 outcome binder development (wire correct field)
- Preparation for Checklist v2 FM + Bootstrap (parallel work)
- `CORPORATE_UPDATE` negative signal flagging (0/6 hit rate, n=8 too small for verdict, but monitor)

---

### h20d Implication (May 26)

**This verdict UNBLOCKS:**
- Spec 071 Lane 1 audit → catalyst/clinical hygiene gates → ranker shadow can begin (June 1, conditional on h20d freeze lift)
- Ranker shadow timeline tied to Spec 071 completion (dependency)

**This verdict CONFIRMS:**
- Selector lane closure (catalyst weight is at optimal 0.25; no new weight)
- Catalyst is both selector AND ranker candidate (different mechanisms)
- EV transmission is diagnostic-only until Spec 077 binds correct field

---

## Summary: h20d Gate Implications (May 26)

### What These Verdicts Enable

✅ **If h20d Path A (FREEZE LIFT):**
- Spec 072 vNext ranker shadow begins June 1 (FM bootstrap begins immediately)
- Spec 071 Lane 1 audit progresses in parallel (gates false-catalyst impact)
- Clinical/Catalyst ranker shadows queue behind Spec 072 (dependency ordering)
- 30-live-day clock starts June 1; verdicts due July 1

✅ **If h20d Path B (HYBRID DEFER):**
- Spec 072 ranker shadow staging (non-live snapshot testing)
- FM bootstrap staging; re-eval June 9
- 30-live-day clock deferred; verdicts due July 15

❌ **If h20d Path C (EXTENDED HOLD):**
- Spec 072/Clinical/Catalyst shadows all deferred to Q3
- Spec 071 Lane 1 audit continues; impact not applied to ranker decisions
- All ranker signal validation deferred 4–6 weeks

---

### Critical Dependencies (All h20d Paths)

1. **Spec 071 Lane 1 hygiene audit** — blocks final clinical/catalyst ranker promotion
2. **Spec 077 outcome binder** — blocks EV calibration (Catalyst, deferred to Q3)
3. **Checklist v2 gates (FM, Bootstrap, FDR, LOSO)** — blocks any promotion to production

---

### No Alpha Freeze Violations

✅ **These verdicts comply with alpha freeze:**
- No new alpha claims (vNext/Clinical/Catalyst are shadow candidates, not signals)
- No unconditional promotions (all deferred to post-Checklist-v2)
- No architecture changes (selector/ranker/sizing remain frozen)
- No scoring changes (production model unchanged)
- All deferrals are evidence-based, not arbitrary

---

## Sign-Off

**Verdict Status:** FINAL  
**Date:** 2026-05-22 (May 22 spec review)  
**Next Gate:** h20d decision (May 26)  
**Commit Hash:** [GIT SHA TBD — to be added after h20d decision]

**Approved constraints:**
- Spec 072 vNext: CONDITIONAL ADVANCE (ranker-shadow only, post-Spec-071-audit, Checklist v2 required)
- Clinical Phase A: REAFFIRM (selector closed, ranker shadow on single feature only)
- Catalyst Phase A: REAFFIRM (no new selector weight, ranker shadow deferred pending false-catalyst audit)

**Disposition:** All three specs cleared for ranker shadow investigation post-h20d. No production model changes authorized today.

