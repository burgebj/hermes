"""Regression tests for the 2026-05-30 compression-huddle fixes.

Covers the four items implemented from
``Vaults/handoffs/compression-fix-handover.md`` against the live compressor:

  P0-2  append-only segment summarization (no summary-of-summary degradation)
  P1-5  calibrated token accountant (rough -> provider ratio learning)
  P1-3  absolute-reserve trigger cap + floor-awareness
  P1-4  softened SUMMARY_PREFIX (anaphora-preserving, no "discard" over-correction)
  P0-1  tool_use / tool_result pairing held across compaction boundaries

P0-1 was already implemented in the live code (``_align_boundary_*``,
``_sanitize_tool_pairs``); these add boundary stress cases the handoff asked for.
"""

import pytest
from unittest.mock import MagicMock, patch

from agent.context_compressor import (
    ContextCompressor,
    SUMMARY_PREFIX,
    _COMPRESSION_RESERVE_TOKENS,
    _HISTORICAL_SUMMARY_PREFIXES,
    _SEGMENT_MERGE_THRESHOLD,
)


def _make(**kwargs):
    ctx = kwargs.pop("_ctx", 100_000)
    defaults = dict(model="test/model", quiet_mode=True, protect_first_n=2, protect_last_n=2)
    defaults.update(kwargs)
    with patch("agent.context_compressor.get_model_context_length", return_value=ctx):
        return ContextCompressor(**defaults)


def _summary_response(text="summary text"):
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = text
    return resp


# ---------------------------------------------------------------------------
# P1-5: calibrated token accountant
# ---------------------------------------------------------------------------

class TestTokenCalibration:
    def test_cold_start_returns_rough_unchanged(self):
        c = _make()
        assert c.calibrated_estimate(90_000) == 90_000

    def test_zero_or_negative_returns_input(self):
        c = _make()
        c._record_token_calibration(100, 50)
        assert c.calibrated_estimate(0) == 0
        assert c.calibrated_estimate(-5) == -5

    def test_median_ratio_applied(self):
        c = _make()
        # Real consistently ~half of rough → median ratio 0.5.
        for _ in range(3):
            c._record_token_calibration(rough_tokens=100_000, real_tokens=50_000)
        assert c.calibrated_estimate(90_000) == 45_000

    def test_insane_ratios_ignored(self):
        c = _make()
        c._record_token_calibration(100_000, 5)        # ratio 0.00005 → ignored
        c._record_token_calibration(100, 100_000)      # ratio 1000   → ignored
        assert c._token_calibration.get((c.provider, c.model)) is None
        assert c.calibrated_estimate(90_000) == 90_000

    def test_window_capped_at_20(self):
        c = _make()
        for _ in range(30):
            c._record_token_calibration(100_000, 80_000)
        assert len(c._token_calibration[(c.provider, c.model)]["ratios"]) == 20

    def test_update_from_response_records_when_not_post_compression(self):
        c = _make()
        c.awaiting_real_usage_after_compression = False
        c._last_preflight_rough = 100_000
        c.update_from_response({"prompt_tokens": 70_000})
        ratios = c._token_calibration[(c.provider, c.model)]["ratios"]
        assert ratios == [0.7]
        assert c._last_preflight_rough == 0  # consumed

    def test_update_from_response_skips_after_compression(self):
        c = _make()
        c.awaiting_real_usage_after_compression = True  # compaction just ran
        c._last_preflight_rough = 100_000
        c.update_from_response({"prompt_tokens": 70_000})
        assert c._token_calibration.get((c.provider, c.model)) is None

    def test_should_compress_uses_calibrated_estimate(self):
        # threshold_percent 0.85 on 100K → threshold 85K; effective trigger 85K.
        c = _make(threshold_percent=0.85)
        # Uncalibrated: 90K rough trips the trigger.
        assert c.should_compress(prompt_tokens=90_000) is True
        # Learn that this provider runs ~0.5x the rough estimate.
        for _ in range(3):
            c._record_token_calibration(100_000, 50_000)
        # Now the same 90K rough calibrates to 45K and should NOT trip.
        assert c.should_compress(prompt_tokens=90_000) is False
        # And should_compress remembered the raw rough for ratio learning.
        assert c._last_preflight_rough == 90_000


# ---------------------------------------------------------------------------
# P1-3: absolute-reserve trigger cap + floor awareness
# ---------------------------------------------------------------------------

class TestReserveAndFloor:
    def test_trigger_is_percentage_on_normal_window(self):
        # 100K / 85% → 85K threshold; reserve cap is 100K-7120=92880, so no-op.
        c = _make(threshold_percent=0.85)
        assert c._effective_trigger_tokens() == 85_000

    def test_trigger_capped_on_small_window(self):
        # 70K context, 50% → threshold floored to MIN 64K, but reserve cap
        # 70000-7120=62880 is lower, so the trigger is pulled down to leave room.
        c = _make(_ctx=70_000, threshold_percent=0.50)
        assert c.threshold_tokens == 64_000
        assert c._effective_trigger_tokens() == 70_000 - _COMPRESSION_RESERVE_TOKENS

    def test_trigger_falls_back_when_reserve_exceeds_context(self):
        c = _make(_ctx=5_000)  # smaller than the reserve itself
        assert c._effective_trigger_tokens() == c.threshold_tokens

    def test_incompressible_floor(self):
        c = _make()
        assert c._estimate_incompressible_floor() == c.tail_token_budget + c.max_summary_tokens

    def test_over_reserve_flag_false_on_normal_compaction(self):
        c = _make()
        msgs = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(8)]
        with patch("agent.context_compressor.call_llm", return_value=_summary_response()):
            c.compress(msgs, current_tokens=90_000)
        assert c._last_compress_over_reserve is False

    def test_over_reserve_flag_set_when_result_exceeds_ceiling(self):
        c = _make()  # ceiling = 100000 - 7120 = 92880
        msgs = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(8)]
        with patch("agent.context_compressor.call_llm", return_value=_summary_response()), \
             patch("agent.context_compressor.estimate_messages_tokens_rough", return_value=95_000):
            c.compress(msgs, current_tokens=99_000)
        assert c._last_compress_over_reserve is True

    def test_over_reserve_flag_reset_each_call(self):
        c = _make()
        c._last_compress_over_reserve = True
        msgs = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(8)]
        with patch("agent.context_compressor.call_llm", return_value=_summary_response()):
            c.compress(msgs, current_tokens=90_000)
        assert c._last_compress_over_reserve is False


# ---------------------------------------------------------------------------
# P1-4: softened SUMMARY_PREFIX
# ---------------------------------------------------------------------------

class TestSoftenedPrefix:
    def test_no_aggressive_discard_directives(self):
        # The handoff explicitly asks that these over-corrections be gone.
        for banned in ("resume exactly", "## Active Task", "WINS", "discard those"):
            assert banned not in SUMMARY_PREFIX, f"{banned!r} should not be in SUMMARY_PREFIX"

    def test_preserves_anaphora_resolution(self):
        # The whole point of P1-4: keep info so "continue"/"do the next one" resolve.
        assert "continue" in SUMMARY_PREFIX
        assert "do NOT discard" in SUMMARY_PREFIX

    def test_preserves_memory_authority_line(self):
        # Dropping this would be a regression independent of the huddle.
        assert "MEMORY.md" in SUMMARY_PREFIX and "authoritative" in SUMMARY_PREFIX

    def test_still_discourages_blind_resumption(self):
        # Anti-hijack intent (#35344) must survive the softening.
        assert "unless the latest message explicitly asks" in SUMMARY_PREFIX

    def test_previous_hardened_prefix_is_stripped_on_renormalization(self):
        old_hardened = _HISTORICAL_SUMMARY_PREFIXES[0]
        renormalized = ContextCompressor._with_summary_prefix(f"{old_hardened}\nbody text")
        assert renormalized == f"{SUMMARY_PREFIX}\nbody text"
        # The aggressive directive must not survive embedded in the body.
        assert "WINS" not in renormalized

    def test_pre_35344_prefix_still_stripped(self):
        pre_35344 = _HISTORICAL_SUMMARY_PREFIXES[-1]
        renormalized = ContextCompressor._with_summary_prefix(f"{pre_35344}\nbody text")
        assert renormalized == f"{SUMMARY_PREFIX}\nbody text"
        assert "resume exactly" not in renormalized

    def test_old_prefixed_summary_is_detected_as_summary(self):
        old_hardened = _HISTORICAL_SUMMARY_PREFIXES[0]
        assert ContextCompressor._is_context_summary_content(f"{old_hardened}\nbody")


# ---------------------------------------------------------------------------
# P0-1: tool pairing across compaction boundaries (boundary stress)
# ---------------------------------------------------------------------------

class TestToolPairingBoundaries:
    @staticmethod
    def _assert_well_formed(result):
        call_ids = set()
        for m in result:
            if m.get("role") == "assistant":
                for tc in m.get("tool_calls") or []:
                    cid = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                    if cid:
                        call_ids.add(cid)
        result_ids = {m.get("tool_call_id") for m in result if m.get("role") == "tool"}
        result_ids.discard(None)
        # Every surviving tool result has a matching assistant tool_call.
        assert result_ids <= call_ids, f"orphan tool results: {result_ids - call_ids}"
        # Every surviving assistant tool_call has a matching result.
        assert call_ids <= result_ids, f"unanswered tool_calls: {call_ids - result_ids}"

    def test_tool_group_straddling_tail_boundary(self):
        """A multi-call assistant turn whose results sit right at the tail cut
        must not leave dangling ids after compaction."""
        c = _make(protect_first_n=2, protect_last_n=2)
        msgs = [
            {"role": "user", "content": "start"},
            {"role": "assistant", "content": "ok"},
            {"role": "user", "content": "middle work"},
            {"role": "assistant", "content": "", "tool_calls": [
                {"id": "c1", "type": "function", "function": {"name": "read", "arguments": "{}"}},
                {"id": "c2", "type": "function", "function": {"name": "read", "arguments": "{}"}},
            ]},
            {"role": "tool", "tool_call_id": "c1", "content": "r1" * 200},
            {"role": "tool", "tool_call_id": "c2", "content": "r2" * 200},
            {"role": "assistant", "content": "done with middle"},
            {"role": "user", "content": "tail q"},
            {"role": "assistant", "content": "tail a"},
            {"role": "user", "content": "latest"},
        ]
        with patch("agent.context_compressor.call_llm", return_value=_summary_response()):
            result = c.compress(msgs, current_tokens=90_000)
        self._assert_well_formed(result)

    def test_orphan_tool_result_whose_call_is_summarized(self):
        """If only the tool result (not its assistant call) would survive a cut,
        the sanitizer must drop the orphan result."""
        c = _make(protect_first_n=2, protect_last_n=2)
        msgs = [
            {"role": "user", "content": "start"},
            {"role": "assistant", "content": "ok"},
            {"role": "assistant", "content": "", "tool_calls": [
                {"id": "mid", "type": "function", "function": {"name": "x", "arguments": "{}"}},
            ]},
            {"role": "tool", "tool_call_id": "mid", "content": "y" * 400},
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
            {"role": "user", "content": "latest"},
        ]
        with patch("agent.context_compressor.call_llm", return_value=_summary_response()):
            result = c.compress(msgs, current_tokens=90_000)
        self._assert_well_formed(result)

    def test_sanitizer_stubs_unanswered_calls_directly(self):
        c = _make()
        msgs = [
            {"role": "assistant", "content": "", "tool_calls": [
                {"id": "lonely", "type": "function", "function": {"name": "x", "arguments": "{}"}},
            ]},
            {"role": "user", "content": "next"},
        ]
        sanitized = c._sanitize_tool_pairs(msgs)
        tool_ids = {m.get("tool_call_id") for m in sanitized if m.get("role") == "tool"}
        assert "lonely" in tool_ids  # a stub result was inserted


# ---------------------------------------------------------------------------
# P0-2: append-only segment summarization (no summary-of-summary)
# ---------------------------------------------------------------------------

class TestSegmentSummarization:
    def _msgs(self, n=10):
        return [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"}
            for i in range(n)
        ]

    def test_first_compaction_creates_one_segment(self):
        c = _make()
        assert c._summary_segments == []
        with patch("agent.context_compressor.call_llm", return_value=_summary_response("seg0")):
            c.compress(self._msgs(), current_tokens=90_000)
        assert len(c._summary_segments) == 1
        assert c._summary_segments[0]["text"] == "seg0"

    def test_second_compaction_adds_segment_not_replaces(self):
        """Each compress() call appends a new segment — old segments survive."""
        c = _make()
        with patch("agent.context_compressor.call_llm", return_value=_summary_response("first")):
            c.compress(self._msgs(), current_tokens=90_000)
        assert len(c._summary_segments) == 1

        # Simulate more content arriving and a second compaction.
        c._turns_seen = 0  # reset so second compress has something to do
        c._previous_summary = "first"
        with patch("agent.context_compressor.call_llm", return_value=_summary_response("second")):
            c.compress(self._msgs(), current_tokens=90_000)
        # Both segments survive — no replacement.
        assert len(c._summary_segments) == 2
        texts = [s["text"] for s in c._summary_segments]
        assert "first" in texts
        assert "second" in texts

    def test_second_compaction_prompt_uses_prior_context_not_full_rewrite(self):
        """The delta path must show PRIOR CONTEXT (old segment) and ask for
        NEW TURNS only — never 'PREVIOUS SUMMARY:' (old iterative-rewrite path)."""
        c = _make()
        c._summary_segments = [{"start": 0, "end": 5, "text": "FACTUAL-PRIOR-SEGMENT"}]
        c._previous_summary = "FACTUAL-PRIOR-SEGMENT"

        with patch("agent.context_compressor.call_llm", return_value=_summary_response("new")) as mock:
            c.compress(self._msgs(), current_tokens=90_000)

        prompt = mock.call_args.kwargs["messages"][0]["content"]
        assert "PRIOR CONTEXT" in prompt
        assert "NEW TURNS TO SUMMARIZE" in prompt
        # Must not use the old iterative-rewrite label.
        assert "PREVIOUS SUMMARY:" not in prompt
        # The old segment content appears once (as context, not as input turns).
        assert prompt.count("FACTUAL-PRIOR-SEGMENT") == 1

    def test_render_segments_labels_older_entries(self):
        c = _make()
        c._summary_segments = [
            {"start": 0, "end": 10, "text": "old-facts"},
            {"start": 10, "end": 20, "text": "new-facts"},
        ]
        rendered = c._render_summary_from_segments()
        assert "old-facts" in rendered
        assert "new-facts" in rendered
        # Only the older segment gets a label; newest is verbatim.
        assert "Earlier context" in rendered
        # The newest segment has no label prefix.
        lines = rendered.splitlines()
        last_nonempty = next(l for l in reversed(lines) if l.strip())
        assert last_nonempty == "new-facts"

    def test_render_empty_segments_returns_empty(self):
        c = _make()
        assert c._render_summary_from_segments() == ""

    def test_compact_merges_oldest_when_threshold_exceeded(self):
        c = _make()
        # Add _SEGMENT_MERGE_THRESHOLD + 1 segments to trigger compaction.
        for i in range(_SEGMENT_MERGE_THRESHOLD + 1):
            c._summary_segments.append({"start": i * 10, "end": (i + 1) * 10, "text": f"seg{i}"})
        c._compact_old_segments()
        assert len(c._summary_segments) == _SEGMENT_MERGE_THRESHOLD
        # The first entry is the merged pair covering seg0+seg1.
        merged = c._summary_segments[0]
        assert "seg0" in merged["text"]
        assert "seg1" in merged["text"]
        assert merged["start"] == 0
        assert merged["end"] == 20

    def test_compact_noop_at_threshold(self):
        c = _make()
        for i in range(_SEGMENT_MERGE_THRESHOLD):
            c._summary_segments.append({"start": i, "end": i + 1, "text": f"seg{i}"})
        c._compact_old_segments()
        assert len(c._summary_segments) == _SEGMENT_MERGE_THRESHOLD

    def test_legacy_previous_summary_bootstraps_segment(self):
        """On first re-compaction after resume, legacy _previous_summary must
        be bootstrapped into _summary_segments so the delta path fires."""
        from agent.context_compressor import SUMMARY_PREFIX
        old_body = "LEGACY-BODY unique facts"
        msgs = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": f"{SUMMARY_PREFIX}\n{old_body}"},
            {"role": "assistant", "content": "ack"},
            {"role": "user", "content": "new1"},
            {"role": "assistant", "content": "ans1"},
            {"role": "user", "content": "new2"},
            {"role": "assistant", "content": "ans2"},
            {"role": "user", "content": "active"},
        ]
        c = _make(protect_first_n=1, protect_last_n=1)
        assert c._summary_segments == []
        with patch("agent.context_compressor.call_llm", return_value=_summary_response("new-seg")):
            c.compress(msgs, current_tokens=90_000)
        # Segments: the bootstrapped legacy one + the new one.
        assert len(c._summary_segments) >= 1
        texts = [s["text"] for s in c._summary_segments]
        assert "new-seg" in texts

    def test_previous_summary_kept_in_sync(self):
        """_previous_summary is always the rendered view of all segments
        (for fallback code paths that read it directly)."""
        c = _make()
        with patch("agent.context_compressor.call_llm", return_value=_summary_response("alpha")):
            c.compress(self._msgs(), current_tokens=90_000)
        # _previous_summary = rendered form of segments.
        assert "alpha" in c._previous_summary
        rendered = c._render_summary_from_segments()
        assert c._previous_summary == rendered

    def test_on_session_reset_clears_segments(self):
        c = _make()
        c._summary_segments = [{"start": 0, "end": 10, "text": "stuff"}]
        c._turns_seen = 10
        c.on_session_reset()
        assert c._summary_segments == []
        assert c._turns_seen == 0
        assert c._previous_summary is None
