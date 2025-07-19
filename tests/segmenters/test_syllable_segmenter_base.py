import pytest

from wyrdbound_rng.segmenters.syllable_segmenter_base import SyllableSegmenterBase
from wyrdbound_rng.syllable import Syllable


class DummySegmenter(SyllableSegmenterBase):
    """Dummy segmenter for testing the base class functionality."""

    _initials = ["r", "n", "m", "g", "th"]
    _inners = ["a", "e", "i", "o", "ie"]
    _finals = ["n", "l", "g", "r", "b", "th", ""]

    @classmethod
    def initials(cls):
        return cls._initials

    @classmethod
    def inners(cls):
        return cls._inners

    @classmethod
    def finals(cls):
        return cls._finals


class TestSyllableSegmenterBase:
    """Test suite for SyllableSegmenterBase, ported from Ruby specs."""

    def test_init_longest_matching_sorts_longest_to_shortest(self):
        """Test that init_longest_matching sorts syllables from longest to shortest."""
        syllables = ["a", "abb", "ch"]
        result = DummySegmenter.init_longest_matching(syllables)
        assert result == ["abb", "ch", "a"]

    def test_init_longest_matching_modifies_original_array(self):
        """Test that init_longest_matching actually modifies the original array."""
        syllables = ["a", "abb", "ch"]
        original = syllables.copy()
        DummySegmenter.init_longest_matching(syllables)
        assert syllables != original

    def test_init_shortest_matching_sorts_shortest_to_longest(self):
        """Test that init_shortest_matching sorts syllables from shortest to longest."""
        syllables = ["a", "abb", "ch"]
        result = DummySegmenter.init_shortest_matching(syllables)
        assert result == ["a", "ch", "abb"]

    def test_init_shortest_matching_modifies_original_array(self):
        """Test that init_shortest_matching actually modifies the original array."""
        syllables = ["a", "abb", "ch"]
        original = syllables.copy()
        DummySegmenter.init_shortest_matching(syllables)
        assert syllables != original

    def test_init_syllable_matching_initializes_syllable_orderings(self):
        """Test that init_syllable_matching initializes syllable orderings from longest to shortest."""
        orig_initials = DummySegmenter.initials().copy()
        orig_inners = DummySegmenter.inners().copy()
        orig_finals = DummySegmenter.finals().copy()

        DummySegmenter.init_syllable_matching(
            DummySegmenter._initials, DummySegmenter._inners, DummySegmenter._finals
        )

        assert DummySegmenter._initials != orig_initials
        assert DummySegmenter._inners != orig_inners
        assert DummySegmenter._finals != orig_finals

    def test_extract_last_syllable(self):
        """Test extracting the last syllable from various names."""
        # Initialize syllable matching first
        DummySegmenter.init_syllable_matching(
            DummySegmenter._initials, DummySegmenter._inners, DummySegmenter._finals
        )

        test_cases = {
            "Thorin": Syllable("r", "i", "n"),
            "Abareth": Syllable("r", "e", "th"),
            "Gilthoniel": Syllable("n", "ie", "l"),
            "Magena": Syllable("n", "a", ""),
        }

        for name, expected_syllable in test_cases.items():
            result = DummySegmenter.extract_last_syllable(name)
            assert result.initial == expected_syllable.initial
            assert result.inner == expected_syllable.inner
            assert result.final == expected_syllable.final

    def test_extract_first_syllable(self):
        """Test extracting the first syllable from various names."""
        test_cases = {
            "Thorin": Syllable("th", "o", "r"),
            "Abareth": Syllable("", "a", "b"),
            "Gilthoniel": Syllable("g", "i", "l"),
            "Magena": Syllable("m", "a", "g"),
        }

        for name, expected_syllable in test_cases.items():
            result = DummySegmenter.extract_first_syllable(name)
            assert result.initial == expected_syllable.initial
            assert result.inner == expected_syllable.inner
            assert result.final == expected_syllable.final
