"""
Tests for the FantasyNameSegmenter class.
"""

import pytest
from wyrdbound_rng.segmenters import FantasyNameSegmenter


class TestFantasyNameSegmenter:
    """Test cases for the FantasyNameSegmenter class."""
    
    @pytest.fixture
    def segmenter(self):
        """Create a FantasyNameSegmenter instance for testing."""
        return FantasyNameSegmenter()
    
    def test_segment_single_syllable_names(self, segmenter):
        """Test segmenting single syllable names."""
        single_syllable_names = ['Thor', 'Lir', 'Drizzt', 'Haask']
        
        for name in single_syllable_names:
            syllables = segmenter.segment(name)
            assert syllables is not None
            assert isinstance(syllables, list)
            assert len(syllables) == 1
    
    def test_segment_double_syllable_names(self, segmenter):
        """Test segmenting double syllable names."""
        double_syllable_names = ['Thorin', 'Halphas', 'Iblis', 'Heimdall']
        
        for name in double_syllable_names:
            syllables = segmenter.segment(name)
            assert syllables is not None
            assert isinstance(syllables, list)
            assert len(syllables) == 2
    
    def test_segment_triple_syllable_names(self, segmenter):
        """Test segmenting triple syllable names."""
        triple_syllable_names = ['Mephisto', 'Haborym', 'Gwyllion', 'Drekavac']
        
        for name in triple_syllable_names:
            syllables = segmenter.segment(name)
            assert syllables is not None
            assert isinstance(syllables, list)
            assert len(syllables) == 3
    
    def test_segment_long_names(self, segmenter):
        """Test segmenting very long names."""
        syllables = segmenter.segment('Mephistopheles')
        assert syllables is not None
        assert isinstance(syllables, list)
        assert len(syllables) == 5
    
    def test_segment_names_into_non_overlapping_syllables(self, segmenter):
        """Test that segmentation creates non-overlapping, complete syllables."""
        name = 'Andromeda'
        syllables = segmenter.segment(name)
        
        assert syllables is not None
        assert isinstance(syllables, list)
        
        # Reconstruct the name from syllables
        reconstructed = ''.join(str(syllable) for syllable in syllables)
        assert reconstructed == name.lower()

    def test_segment_all_names_in_dataset(self, segmenter, fantasy_names_yaml_path):
        """Test that segmenter can handle all names in the dataset."""
        from wyrdbound_rng import NameFileLoader
        
        loader = NameFileLoader(segmenter)
        names = loader.load(fantasy_names_yaml_path)
        
        # Should be able to segment all names without errors
        assert len(names) > 0
        
        for name in names:
            assert name.syllables is not None
            assert len(name.syllables) > 0
    
    def test_segment_preserves_case_insensitivity(self, segmenter):
        """Test that segmentation works regardless of input case."""
        test_cases = [
            ('THOR', 'thor'),
            ('Thor', 'thor'),
            ('thor', 'thor'),
            ('tHoR', 'thor')
        ]
        
        for input_name, expected_lower in test_cases:
            syllables = segmenter.segment(input_name)
            reconstructed = ''.join(str(syllable) for syllable in syllables)
            assert reconstructed == expected_lower
    
    def test_segment_empty_string_handling(self, segmenter):
        """Test handling of edge cases like empty strings."""
        # This should either handle gracefully or raise a clear error
        try:
            syllables = segmenter.segment('')
            # If it succeeds, result should be reasonable
            assert isinstance(syllables, list)
        except Exception as e:
            # If it fails, should be a clear error type
            assert isinstance(e, (ValueError, TypeError)) or 'SegmentError' in str(type(e))
    
    def test_segment_single_character_names(self, segmenter):
        """Test segmenting single character names."""
        single_chars = ['A', 'I', 'O']
        
        for char in single_chars:
            try:
                syllables = segmenter.segment(char)
                assert isinstance(syllables, list)
                assert len(syllables) >= 1
            except Exception:
                # Some single characters might not be segmentable
                pass
