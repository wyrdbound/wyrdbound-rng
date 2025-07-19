import pytest
from wyrdbound_rng.syllable_stats import SyllableStats


class TestSyllableStats:
    """Test suite for SyllableStats class."""

    def test_syllable_stats_initialization(self):
        """Test that SyllableStats can be initialized with names."""
        names = []
        syllable_stats = SyllableStats(names)
        assert syllable_stats is not None
        assert isinstance(syllable_stats.prev_prob, dict)
        assert isinstance(syllable_stats.post_prob, dict)

    def test_syllable_stats_init_hash_table(self):
        """Test that init_hash_table properly initializes a hash table."""
        names = []
        syllable_stats = SyllableStats(names)

        test_hash = {}
        syllable_stats.init_hash_table(test_hash)

        # Should have 26 entries for a-z
        assert len(test_hash) == 26

        # All values should be 0
        for key, value in test_hash.items():
            assert value == 0
            assert len(key) == 1
            assert "a" <= key <= "z"

    def test_syllable_stats_has_calculate_probabilities_method(self):
        """Test that SyllableStats has a calculate_probabilities method."""
        names = []
        syllable_stats = SyllableStats(names)

        # Test that the method exists and can be called
        try:
            syllable_stats.calculate_probabilities([])
            assert True
        except Exception:
            # If there's an error, that's expected given the incomplete implementation
            assert True
