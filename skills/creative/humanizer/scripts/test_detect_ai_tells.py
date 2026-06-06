#!/usr/bin/env python3
"""Regression tests for humanizer AI-tell detector.

Run: python3 test_detect_ai_tells.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import detect_ai_tells as dt


# ===================================================================
# Sample texts
# ===================================================================

AI_HEAVY_TEXT = """
I hope this email finds you well! I wanted to reach out to discuss some
groundbreaking developments in our project. It's worth noting that our team
has been leveraging cutting-edge technology to navigate the complexities
of the modern landscape.

Furthermore, the innovative approach we've taken is a testament to the
multifaceted nature of our endeavor. At its core, this represents a
paradigm shift in how we utilize our resources. The rich tapestry of
solutions we've developed is truly transformative.

Additionally, I want to be transparent with you \u2014 the results have been
nothing short of remarkable. Our holistic, robust, and scalable platform
delivers seamless integration. Moreover, it fosters collaboration across
all teams in ways that are both pivotal and commendable.

In conclusion, I hope this helps! Let me know if you have any questions.
Don't hesitate to reach out \u2014 I'm here if you need anything. Happy to help!
"""

HUMAN_TEXT = """
Hey, wanted to give you a quick update on the project. We switched the
database last week, which cut query times roughly in half. Still some
edge cases with the migration script but nothing blocking.

The new API is live on staging. A couple of the endpoints need better
error messages, and the auth flow has a bug where tokens expire too
early. Mike's looking into that.

Should have the staging fixes done by Thursday. Let me know if you
want to do a walkthrough before we push to prod.
"""

HEDGING_HEAVY = """
It's possible that the new system could potentially improve performance.
One might argue that the benefits outweigh the risks. It could be argued
that this approach has merit. To some extent, the results support this
hypothesis. In some ways, the data suggests a positive trend. It's worth
mentioning that we should consider all options carefully.
"""

EM_DASH_HEAVY = """
The project \u2014 which started last month \u2014 has made progress. Our team
\u2014 consisting of five developers \u2014 delivered the prototype. The results
\u2014 while preliminary \u2014 look promising. We expect \u2014 based on current
trends \u2014 to finish by Friday.
"""

PERFORMED_AUTH_TEXT = """
Great question! I want to be honest with you. I hear you, and I
understand your concern. If I'm being honest, the timeline is tight.
I appreciate your patience. To be honest, we need more resources.
Thank you for your understanding. I may be wrong, but I think we
can still deliver on time. Absolutely!
"""

TAUTOLOGY_TEXT = """
First and foremost, we need to review the basic fundamentals. Based on
past experience, the end result of advance planning is always better.
Each and every team member should contribute their personal opinion.
The general consensus is that the future plans look good.
"""

RULE_OF_THREE_TEXT = """
Our platform is powerful, flexible, and intuitive. The team is dedicated,
experienced, and passionate. We deliver fast, reliable, and secure solutions.
The product is modern, elegant, and user-friendly.
"""

EMOJI_HEAVY = """
Great news! \U0001F389 We launched the new feature \U0001F680 and the results
are amazing \U0001F525\U0001F525\U0001F525! The team did an incredible job
\u2B50\u2B50\u2B50. Check out the dashboard \U0001F4CA for details \U0001F60A.
"""

FILLER_TRANSITIONS_TEXT = """
The system processes data in real time. Furthermore, it handles errors
gracefully. Moreover, the logging is comprehensive. Additionally, the
monitoring dashboard shows key metrics. In conclusion, the system is
production-ready. To summarize, all tests pass.
"""

INVISIBLE_UNICODE_TEXT = "Before fence\u200B```python\nprint('hi')\n```"


# ===================================================================
# Test: Filler phrases exceed threshold
# ===================================================================

class TestFillerThreshold(unittest.TestCase):
    """Repeated filler phrases must be detected when exceeding threshold."""

    def test_filler_transitions_detected(self):
        result = dt.scan(FILLER_TRANSITIONS_TEXT)
        fillers = [f for f in result['findings'] if f['category'] == 'filler_transition']
        self.assertGreaterEqual(len(fillers), 3,
                                "Should detect at least 3 filler transitions")

    def test_heavy_ai_has_fillers(self):
        result = dt.scan(AI_HEAVY_TEXT)
        fillers = [f for f in result['findings'] if f['category'] == 'filler_transition']
        self.assertGreater(len(fillers), 0,
                           "Heavy AI text should contain filler transitions")

    def test_human_text_minimal_fillers(self):
        result = dt.scan(HUMAN_TEXT)
        fillers = [f for f in result['findings'] if f['category'] == 'filler_transition']
        self.assertEqual(len(fillers), 0,
                         "Human-sounding text should have no filler transitions")


# ===================================================================
# Test: Recurrence-set phrases detected
# ===================================================================

class TestRecurrenceSet(unittest.TestCase):
    """All recurrence-set phrases/structures must be flagged."""

    def test_stock_openers_detected(self):
        result = dt.scan(AI_HEAVY_TEXT)
        openers = [f for f in result['findings'] if f['category'] == 'stock_opener']
        self.assertGreater(len(openers), 0, "Stock openers not detected")

    def test_stock_closers_detected(self):
        result = dt.scan(AI_HEAVY_TEXT)
        closers = [f for f in result['findings'] if f['category'] == 'stock_closer']
        self.assertGreater(len(closers), 0, "Stock closers not detected")

    def test_stock_hedges_detected(self):
        result = dt.scan(AI_HEAVY_TEXT)
        hedges = [f for f in result['findings'] if f['category'] == 'stock_hedge']
        self.assertGreater(len(hedges), 0, "Stock hedges not detected")

    def test_ai_signature_words_detected(self):
        result = dt.scan(AI_HEAVY_TEXT)
        sigs = [f for f in result['findings'] if f['category'] == 'ai_signature_word']
        # Should detect: groundbreaking, leveraging, cutting-edge, landscape,
        # innovative, testament, multifaceted, endeavor, paradigm, tapestry,
        # transformative, holistic, robust, scalable, seamless, fosters, pivotal,
        # commendable, utilize, navigate
        self.assertGreaterEqual(len(sigs), 10,
                                f"Should detect 10+ AI signature words, got {len(sigs)}")

    def test_specific_words_detected(self):
        """Check specific Wikipedia-documented AI signature words."""
        for word in ["delve", "tapestry", "multifaceted", "landscape",
                     "pivotal", "endeavor", "vibrant", "bustling",
                     "holistic", "paramount", "meticulous", "commendable"]:
            text = f"The {word} nature of the project is clear."
            result = dt.scan(text)
            sigs = [f for f in result['findings'] if f['category'] == 'ai_signature_word']
            self.assertGreater(len(sigs), 0,
                               f"AI signature word '{word}' not detected")

    def test_delve_all_forms(self):
        for form in ["delve", "delves", "delved"]:
            result = dt.scan(f"We {form} into the topic.")
            sigs = [f for f in result['findings'] if f['category'] == 'ai_signature_word']
            self.assertGreater(len(sigs), 0, f"'{form}' not detected")

    def test_leverage_detected(self):
        result = dt.scan("We leverage machine learning to improve results.")
        sigs = [f for f in result['findings'] if f['category'] == 'ai_signature_word']
        self.assertGreater(len(sigs), 0, "'leverage' not detected")

    def test_utilize_detected(self):
        result = dt.scan("We utilize advanced algorithms.")
        sigs = [f for f in result['findings'] if f['category'] == 'ai_signature_word']
        self.assertGreater(len(sigs), 0, "'utilize' not detected")


# ===================================================================
# Test: Performed authenticity
# ===================================================================

class TestPerformedAuthenticity(unittest.TestCase):
    """Performed authenticity markers must be flagged."""

    def test_all_markers_detected(self):
        result = dt.scan(PERFORMED_AUTH_TEXT)
        auth = [f for f in result['findings'] if f['category'] == 'performed_authenticity']
        # Should find: great question, want to be honest, i hear you,
        # understand your concern, if i'm being honest, appreciate your patience,
        # to be honest, thank you for your understanding, i may be wrong but
        self.assertGreaterEqual(len(auth), 5,
                                f"Should detect 5+ performed authenticity markers, got {len(auth)}")

    def test_transparent_detected(self):
        result = dt.scan("I want to be transparent with you about this issue.")
        openers = [f for f in result['findings'] if f['category'] == 'stock_opener']
        self.assertGreater(len(openers), 0, "'transparent' opener not detected")


# ===================================================================
# Test: Em dash overuse
# ===================================================================

class TestEmDashOveruse(unittest.TestCase):
    """Em dash overuse must be detected."""

    def test_heavy_em_dashes_flagged(self):
        result = dt.scan(EM_DASH_HEAVY)
        em = [f for f in result['findings'] if f['category'] == 'em_dash_overuse']
        self.assertGreater(len(em), 0, "Em dash overuse not detected")
        self.assertTrue(result['scores']['em_dash_over_threshold'])

    def test_normal_text_no_em_dash_flag(self):
        result = dt.scan(HUMAN_TEXT)
        em = [f for f in result['findings'] if f['category'] == 'em_dash_overuse']
        self.assertEqual(len(em), 0, "Normal text should not flag em dashes")

    def test_em_dash_count_accurate(self):
        text = "one \u2014 two \u2014 three"
        result = dt.scan(text)
        self.assertEqual(result['scores']['em_dashes'], 2)


# ===================================================================
# Test: Rule of three
# ===================================================================

class TestRuleOfThree(unittest.TestCase):
    """Rule-of-three patterns must be detected."""

    def test_multiple_triples_detected(self):
        result = dt.scan(RULE_OF_THREE_TEXT)
        rot = [f for f in result['findings'] if f['category'] == 'rule_of_three_instance']
        self.assertGreaterEqual(len(rot), 3,
                                f"Should detect 3+ rule-of-three instances, got {len(rot)}")

    def test_single_triple_not_flagged_as_overuse(self):
        text = "The solution is fast, reliable, and secure."
        result = dt.scan(text)
        rot_over = [f for f in result['findings'] if f['category'] == 'rule_of_three']
        # Single instance shouldn't trigger the overuse pattern (needs 2+)
        self.assertEqual(len(rot_over), 0)


# ===================================================================
# Test: Hedging density
# ===================================================================

class TestHedgingDensity(unittest.TestCase):
    """Heavy hedging must be detected."""

    def test_hedging_heavy_detected(self):
        result = dt.scan(HEDGING_HEAVY)
        hedges = [f for f in result['findings'] if f['category'] == 'stock_hedge']
        self.assertGreaterEqual(len(hedges), 4,
                                f"Should detect 4+ hedges, got {len(hedges)}")

    def test_human_text_no_hedging(self):
        result = dt.scan(HUMAN_TEXT)
        hedges = [f for f in result['findings'] if f['category'] == 'stock_hedge']
        self.assertEqual(len(hedges), 0, "Human text should have no stock hedges")


# ===================================================================
# Test: Tautologies
# ===================================================================

class TestTautologies(unittest.TestCase):
    """Tautologies must be detected."""

    def test_tautology_text(self):
        result = dt.scan(TAUTOLOGY_TEXT)
        taut = [f for f in result['findings'] if f['category'] == 'tautology']
        # first and foremost, basic fundamentals, past experience, end result,
        # advance planning, each and every, personal opinion, general consensus,
        # future plans
        self.assertGreaterEqual(len(taut), 6,
                                f"Should detect 6+ tautologies, got {len(taut)}")

    def test_specific_tautologies(self):
        cases = [
            "each and every person",
            "first and foremost",
            "the basic fundamentals",
            "based on past experience",
            "the end result was good",
            "advance planning is key",
            "in close proximity",
        ]
        for text in cases:
            result = dt.scan(text)
            taut = [f for f in result['findings'] if f['category'] == 'tautology']
            self.assertGreater(len(taut), 0,
                               f"Tautology not detected in: '{text}'")


# ===================================================================
# Test: Emoji overuse
# ===================================================================

class TestEmojiOveruse(unittest.TestCase):
    """Emoji overuse must be detected."""

    def test_emoji_heavy_flagged(self):
        result = dt.scan(EMOJI_HEAVY)
        emoji = [f for f in result['findings'] if f['category'] == 'emoji_overuse']
        self.assertGreater(len(emoji), 0, "Emoji overuse not detected")

    def test_normal_text_no_emoji_flag(self):
        result = dt.scan(HUMAN_TEXT)
        emoji = [f for f in result['findings'] if f['category'] == 'emoji_overuse']
        self.assertEqual(len(emoji), 0)


# ===================================================================
# Test: Invisible Unicode
# ===================================================================

class TestInvisibleUnicode(unittest.TestCase):
    """Invisible Unicode escape characters must be surfaced."""

    def test_invisible_unicode_detected(self):
        result = dt.scan(INVISIBLE_UNICODE_TEXT)
        findings = [f for f in result['findings'] if f['category'] == 'invisible_unicode']
        self.assertGreater(len(findings), 0, "Invisible Unicode not detected")
        self.assertGreaterEqual(result['scores']['invisible_unicode'], 1)

    def test_bidi_override_detected(self):
        result = dt.scan("safe text \u202Egnp.exe")
        findings = [f for f in result['findings'] if f['category'] == 'invisible_unicode']
        self.assertGreater(len(findings), 0, "Bidi override not detected")
        self.assertIn("RIGHT-TO-LEFT OVERRIDE", findings[0]['match'])

    def test_bidi_isolate_detected(self):
        result = dt.scan("safe text \u2067hidden\u2069")
        findings = [f for f in result['findings'] if f['category'] == 'invisible_unicode']
        self.assertGreater(len(findings), 0, "Bidi isolate not detected")
        self.assertGreaterEqual(result['scores']['invisible_unicode'], 2)

    def test_clean_text_has_no_invisible_unicode(self):
        result = dt.scan(HUMAN_TEXT)
        self.assertEqual(result['scores']['invisible_unicode'], 0)


# ===================================================================
# Test: AI-tell score (Turing test heuristic)
# ===================================================================

class TestAITellScore(unittest.TestCase):
    """AI-tell score should reliably distinguish AI from human writing."""

    def test_heavy_ai_high_score(self):
        result = dt.scan(AI_HEAVY_TEXT)
        self.assertGreaterEqual(result['ai_tell_score'], 50,
                                f"Heavy AI text scored only {result['ai_tell_score']}")

    def test_human_text_low_score(self):
        result = dt.scan(HUMAN_TEXT)
        self.assertLessEqual(result['ai_tell_score'], 15,
                             f"Human text scored {result['ai_tell_score']}")

    def test_empty_text_zero_score(self):
        result = dt.scan("")
        self.assertEqual(result['ai_tell_score'], 0)

    def test_score_range(self):
        result = dt.scan(AI_HEAVY_TEXT)
        self.assertGreaterEqual(result['ai_tell_score'], 0)
        self.assertLessEqual(result['ai_tell_score'], 100)

    def test_performed_auth_boosts_score(self):
        result = dt.scan(PERFORMED_AUTH_TEXT)
        self.assertGreaterEqual(result['ai_tell_score'], 30,
                                "Performed authenticity should boost score significantly")

    def test_hedging_boosts_score(self):
        result = dt.scan(HEDGING_HEAVY)
        self.assertGreaterEqual(result['ai_tell_score'], 20)


# ===================================================================
# Test: Change log requirement (findings must be non-empty when edits exist)
# ===================================================================

class TestChangeLogPresence(unittest.TestCase):
    """Findings list must be non-empty when AI tells are present."""

    def test_findings_present_for_ai_text(self):
        result = dt.scan(AI_HEAVY_TEXT)
        self.assertGreater(len(result['findings']), 0,
                           "Findings must be present for AI-heavy text")

    def test_findings_empty_for_clean_text(self):
        result = dt.scan("The cat sat on the mat.")
        # Very short, clean text should have minimal/no findings
        stock = [f for f in result['findings']
                if f['category'] in ('stock_opener', 'stock_transition',
                                     'stock_hedge', 'stock_closer',
                                     'performed_authenticity')]
        self.assertEqual(len(stock), 0)

    def test_summary_always_present(self):
        for text in [AI_HEAVY_TEXT, HUMAN_TEXT, "", "Hello."]:
            result = dt.scan(text)
            self.assertIn('summary', result)
            self.assertTrue(len(result['summary']) > 0)


# ===================================================================
# Test: Meaning preservation examples
# ===================================================================

class TestMeaningPreservation(unittest.TestCase):
    """Detector must not flag factual or technical content as AI tells."""

    def test_technical_text_not_over_flagged(self):
        text = (
            "The server runs PostgreSQL 15 on Ubuntu 22.04. The primary "
            "database has 2.3 million rows. Replication lag averages 12ms. "
            "We deploy via GitHub Actions with a 4-minute build time."
        )
        result = dt.scan(text)
        self.assertLessEqual(result['ai_tell_score'], 10,
                             "Technical facts should not score as AI")

    def test_numbers_not_flagged(self):
        text = "Revenue grew 23% to $4.2M in Q3 2024. Costs were $1.8M."
        result = dt.scan(text)
        self.assertEqual(result['ai_tell_score'], 0)

    def test_genuine_use_of_moreover(self):
        """'Moreover' at start of sentence IS flagged (that's correct behavior).
        The rewriter decides context; the detector just flags."""
        text = "Moreover, the data shows a clear trend."
        result = dt.scan(text)
        fillers = [f for f in result['findings'] if f['category'] == 'filler_transition']
        self.assertGreater(len(fillers), 0,
                           "'Moreover' should be flagged for review")


# ===================================================================
# Test: Exclamation overuse
# ===================================================================

class TestExclamationOveruse(unittest.TestCase):
    """Exclamation mark overuse must be detected."""

    def test_exclamation_heavy(self):
        text = "Great news! The launch was a success! Everyone loved it! Amazing results! Wow!"
        result = dt.scan(text)
        excl = [f for f in result['findings'] if f['category'] == 'exclamation_overuse']
        self.assertGreater(len(excl), 0, "Exclamation overuse not detected")

    def test_single_exclamation_ok(self):
        text = "The project launched successfully! " + ("x " * 200)
        result = dt.scan(text)
        excl = [f for f in result['findings'] if f['category'] == 'exclamation_overuse']
        self.assertEqual(len(excl), 0,
                         "Single exclamation in long text should not flag")


# ===================================================================
# Test: Structural patterns
# ===================================================================

class TestStructuralPatterns(unittest.TestCase):
    """Structural AI patterns must be detected."""

    def test_signposting_detected(self):
        result = dt.scan(AI_HEAVY_TEXT)
        transitions = [f for f in result['findings']
                       if f['category'] in ('stock_transition', 'filler_transition')]
        self.assertGreater(len(transitions), 0,
                           "Over-signposting transitions not detected")

    def test_sentence_start_repetition(self):
        text = (
            "The system handles errors. The system logs events. "
            "The system processes data. The system sends alerts. "
            "The system monitors health."
        )
        result = dt.scan(text)
        rep = [f for f in result['findings'] if f['category'] == 'sentence_start_repetition']
        self.assertGreater(len(rep), 0,
                           "Sentence-start repetition not detected")


# ===================================================================
# Test: Output format
# ===================================================================

class TestOutputFormat(unittest.TestCase):
    """Output format must be correct."""

    def test_text_format_has_sections(self):
        result = dt.scan(AI_HEAVY_TEXT)
        output = dt.format_text(result)
        self.assertIn("## AI-Tell Score", output)
        self.assertIn("## Findings", output)
        self.assertIn("## Scores", output)

    def test_json_format_valid(self):
        import json
        result = dt.scan(AI_HEAVY_TEXT)
        output = dt.format_json(result)
        data = json.loads(output)
        self.assertIn('findings', data)
        self.assertIn('scores', data)
        self.assertIn('ai_tell_score', data)
        self.assertIn('summary', data)

    def test_scores_dict_complete(self):
        result = dt.scan(AI_HEAVY_TEXT)
        required_keys = [
            'stock_phrases', 'ai_signature_words', 'hedges',
            'performed_authenticity', 'filler_transitions', 'tautologies',
            'em_dashes', 'exclamation_marks', 'emojis', 'invisible_unicode',
            'rule_of_three_instances', 'ai_tell_score',
        ]
        for key in required_keys:
            self.assertIn(key, result['scores'], f"Missing score key: {key}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
