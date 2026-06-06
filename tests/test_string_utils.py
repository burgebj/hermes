"""Tests for string_utils module - TDD practice."""

import pytest
from tools.string_utils import reverse_string, capitalize_words


class TestReverseString:
    """Test suite for reverse_string function."""
    
    def test_reverse_simple_string(self):
        """Should reverse a simple string correctly."""
        result = reverse_string("hello")
        assert result == "olleh"
    
    def test_reverse_empty_string(self):
        """Should handle empty string."""
        result = reverse_string("")
        assert result == ""
    
    def test_reverse_single_character(self):
        """Should handle single character string."""
        result = reverse_string("a")
        assert result == "a"
    
    def test_reverse_with_spaces(self):
        """Should preserve spaces when reversing."""
        result = reverse_string("hello world")
        assert result == "dlrow olleh"
    
    def test_reverse_with_special_chars(self):
        """Should handle special characters."""
        result = reverse_string("abc!@#")
        assert result == "#@!cba"


class TestCapitalizeWords:
    """Test suite for capitalize_words function."""
    
    def test_capitalize_single_word(self):
        """Should capitalize a single word."""
        result = capitalize_words("hello")
        assert result == "Hello"
    
    def test_capitalize_multiple_words(self):
        """Should capitalize each word in a sentence."""
        result = capitalize_words("hello world")
        assert result == "Hello World"
    
    def test_capitalize_empty_string(self):
        """Should handle empty string."""
        result = capitalize_words("")
        assert result == ""
    
    def test_capitalize_with_extra_spaces(self):
        """Should handle multiple spaces between words."""
        result = capitalize_words("hello   world")
        assert result == "Hello   World"
    
    def test_capitalize_mixed_case(self):
        """Should handle mixed case input."""
        result = capitalize_words("hELLo WoRLd")
        assert result == "Hello World"
    
    def test_capitalize_preserves_leading_trailing_spaces(self):
        """Should preserve leading and trailing spaces."""
        result = capitalize_words("  hello world  ")
        assert result == "  Hello World  "
