"""
Tests for the Syllable class.
"""

import pytest

from wyrdbound_rng import Syllable


class TestSyllable:
    """Test cases for the Syllable class."""

    def test_syllable_creation(self):
        """Test creating a syllable with initial, inner, and final sounds."""
        syllable = Syllable("TH", "O", "R")

        assert str(syllable) == "thor"
        assert syllable.initial == "th"
        assert syllable.inner == "o"
        assert syllable.final == "r"

    def test_syllable_defaults_final_to_empty_string(self):
        """Test that final sound defaults to empty string."""
        syllable = Syllable("FL", "O")

        assert str(syllable) == "flo"
        assert syllable.initial == "fl"
        assert syllable.inner == "o"
        assert syllable.final == ""

    def test_syllable_lowercase_conversion(self):
        """Test that all components are converted to lowercase."""
        syllable = Syllable("BR", "EE", "TH")

        assert syllable.initial == "br"
        assert syllable.inner == "ee"
        assert syllable.final == "th"
        assert str(syllable) == "breeth"

    def test_syllable_repr(self):
        """Test string representation of syllable."""
        syllable = Syllable("k", "a", "t")
        expected = "Syllable('k', 'a', 't')"
        assert repr(syllable) == expected
