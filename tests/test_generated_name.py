"""
Tests for the GeneratedName class.
"""

import pytest
from wyrdbound_rng import GeneratedName, FantasyNameSegmenter


class TestGeneratedName:
    """Test cases for the GeneratedName class."""
    
    def test_generated_name_provides_source_names_array(self):
        """Test that GeneratedName provides access to source names used in generation."""
        sources = ['Thorin', 'Limdor']
        segmenter = FantasyNameSegmenter()
        name = GeneratedName('Thodor', sources, segmenter)
        
        source_names = name.source_names
        assert source_names is not None
        assert len(source_names) == 2
        assert source_names == sources
    
    def test_generated_name_inherits_from_name(self):
        """Test that GeneratedName inherits all Name functionality."""
        sources = ['Test1', 'Test2']
        segmenter = FantasyNameSegmenter()
        name = GeneratedName('Testname', sources, segmenter)
        
        # Should have all Name functionality
        assert name.name == 'Testname'
        assert len(name) == 8
        assert str(name) == 'Testname'
        assert name.syllables is not None
        assert isinstance(name.syllables, list)
    
    def test_generated_name_with_empty_sources(self):
        """Test GeneratedName with empty source list."""
        segmenter = FantasyNameSegmenter()
        name = GeneratedName('Solo', [], segmenter)
        
        assert name.source_names == []
        assert name.name == 'Solo'
    
    def test_generated_name_with_none_sources(self):
        """Test GeneratedName with None sources."""
        segmenter = FantasyNameSegmenter()
        name = GeneratedName('None', None, segmenter)
        
        assert name.source_names == []
        assert name.name == 'None'
    
    def test_generated_name_repr(self):
        """Test string representation of GeneratedName."""
        sources = ['A', 'B']
        segmenter = FantasyNameSegmenter()
        name = GeneratedName('Test', sources, segmenter)
        
        expected = "GeneratedName('Test', sources=['A', 'B'])"
        assert repr(name) == expected
