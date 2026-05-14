"""Tests for LCM refusal detection."""
from plugins.context_engine.lcm.refusal import contains_refusal

class TestContainsRefusal:
    def test_detects_i_cannot(self):
        assert contains_refusal("I cannot assist with that request.") is True

    def test_detects_as_an_ai(self):
        assert contains_refusal("As an AI language model, I don't have access to that.") is True

    def test_detects_im_sorry(self):
        assert contains_refusal("I'm sorry, but I can't help with that.") is True

    def test_detects_unable(self):
        assert contains_refusal("I'm unable to provide that information.") is True

    def test_detects_against_guidelines(self):
        assert contains_refusal("That goes against my guidelines.") is True

    def test_passes_clean_summary(self):
        assert contains_refusal("The user discussed Python async patterns and error handling.") is False

    def test_passes_code_content(self):
        assert contains_refusal("def calculate_total(items): return sum(i.price for i in items)") is False

    def test_case_insensitive(self):
        assert contains_refusal("I CANNOT fulfill that request") is True

    def test_empty_string(self):
        assert contains_refusal("") is False
