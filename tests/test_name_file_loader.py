"""
Tests for the NameFileLoader class.
"""

import pytest
import tempfile
import os
from wyrdbound_rng import NameFileLoader, FantasyNameSegmenter, JapaneseNameSegmenter
from wyrdbound_rng.exceptions import FileLoadError


class TestNameFileLoader:
    """Test cases for the NameFileLoader class."""
    
    def test_load_fantasy_names_successfully(self, fantasy_names_yaml_path):
        """Test loading fantasy names with FantasyNameSegmenter."""
        loader = NameFileLoader(FantasyNameSegmenter())
        names = loader.load(fantasy_names_yaml_path)
        
        assert names is not None
        assert len(names) > 0

    def test_load_japanese_names_successfully(self, sengoku_names_yaml_path):
        """Test loading Japanese names with JapaneseNameSegmenter."""
        loader = NameFileLoader(JapaneseNameSegmenter())
        names = loader.load(sengoku_names_yaml_path)

        assert names is not None
        assert len(names) > 0
    
    def test_load_raises_error_for_invalid_path(self):
        """Test that loading an invalid file path raises FileLoadError."""
        loader = NameFileLoader()
        
        with pytest.raises(FileLoadError):
            loader.load('foobar.yaml')
    
    def test_load_names_are_sorted_alphabetically(self, fantasy_names_yaml_path):
        """Test that loaded names are sorted alphabetically."""
        loader = NameFileLoader()
        names = loader.load(fantasy_names_yaml_path)
        
        name_strings = [name.name for name in names]
        assert name_strings == sorted(name_strings)
    
    def test_load_ignores_header_row(self):
        """Test that the loader ignores YAML header metadata."""
        # Create a temporary YAML file with metadata
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("metadata:\n")
            f.write("  description: Test names\n")
            f.write("  segmenter: fantasy\n")
            f.write("names:\n")
            f.write("  - Thor\n")
            f.write("  - Loki\n")
            temp_path = f.name
        
        try:
            loader = NameFileLoader()
            names = loader.load(temp_path)
            
            assert len(names) == 2
            name_strings = [name.name for name in names]
            assert 'Thor' in name_strings
            assert 'Loki' in name_strings
        finally:
            os.unlink(temp_path)
    
    def test_load_ignores_empty_lines(self):
        """Test that the loader ignores empty entries in YAML."""
        # Create a temporary YAML file with empty entries
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("names:\n")
            f.write("  - Thor\n")
            f.write("  - ''\n")  # Empty name
            f.write("  - Loki\n")
            f.write("  - '   '\n")  # Whitespace only
            temp_path = f.name
        
        try:
            loader = NameFileLoader()
            names = loader.load(temp_path)
            
            assert len(names) == 2
            name_strings = [name.name for name in names]
            assert 'Thor' in name_strings
            assert 'Loki' in name_strings
        finally:
            os.unlink(temp_path)
    
    def test_load_with_default_segmenter(self, fantasy_names_yaml_path):
        """Test that loader uses FantasyNameSegmenter by default."""
        loader = NameFileLoader()  # No segmenter specified
        names = loader.load(fantasy_names_yaml_path)
        
        assert names is not None
        assert len(names) > 0
        
        # Should be able to segment names (indicating segmenter is working)
        for name in names[:3]:  # Test first few names
            assert name.syllables is not None
            assert len(name.syllables) > 0
    
    def test_load_capitalizes_names_properly(self):
        """Test that names are properly capitalized."""
        # Create a temporary YAML with various capitalizations
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("names:\n")
            f.write("  - thor\n")  # lowercase
            f.write("  - LOKI\n")  # uppercase
            f.write("  - oDiN\n")  # mixed case
            temp_path = f.name
        
        try:
            loader = NameFileLoader()
            names = loader.load(temp_path)
            
            name_strings = [name.name for name in names]
            assert 'Thor' in name_strings
            assert 'Loki' in name_strings  
            assert 'Odin' in name_strings
        finally:
            os.unlink(temp_path)
