"""
Tests for the Generator class.
"""

import pytest
from wyrdbound_rng import Generator, GeneratedName


class TestGenerator:
    """Test cases for the Generator class."""

    def test_generator_generates_specified_number_of_names(
        self, fantasy_names_yaml_path
    ):
        """Test that generator produces the specified number of names."""
        generator = Generator(fantasy_names_yaml_path)
        names = generator.generate(10)

        assert names is not None
        assert len(names) == 10

    def test_generator_generates_names_within_length_limit(
        self, fantasy_names_yaml_path
    ):
        """Test that generated names respect the maximum length constraint."""
        generator = Generator(fantasy_names_yaml_path)
        names = generator.generate(10, max_chars=6)

        assert names is not None
        for name in names:
            assert len(name) < 10  # Ruby test uses < 10 for max_chars=6

    def test_generator_very_simple_algorithm(self, fantasy_names_yaml_path):
        """Test name generation using the very_simple algorithm."""
        generator = Generator(fantasy_names_yaml_path)
        names = generator.generate(10, max_chars=8, algorithm="very_simple")

        assert names is not None
        for name in names:
            assert isinstance(name, GeneratedName)
            assert len(name) < 10

    def test_generator_simple_algorithm(self, fantasy_names_yaml_path):
        """Test name generation using the simple algorithm."""
        generator = Generator(fantasy_names_yaml_path)
        names = generator.generate(10, max_chars=20, algorithm="simple")

        assert names is not None
        assert len(names) == 10
        for name in names:
            assert isinstance(name, GeneratedName)
            assert len(name) <= 20

    def test_generator_bayesian_algorithm(self, fantasy_names_yaml_path):
        """Test name generation using the bayesian algorithm (falls back to simple)."""
        generator = Generator(fantasy_names_yaml_path)
        names = generator.generate(5, max_chars=15, algorithm="bayesian")

        assert names is not None
        assert len(names) == 5
        for name in names:
            assert isinstance(name, GeneratedName)
            assert len(name) <= 15

    def test_generator_loads_names_from_file(self, fantasy_names_yaml_path):
        """Test that generator loads names from the YAML file."""
        generator = Generator(fantasy_names_yaml_path)

        assert generator.names is not None
        assert len(generator.names) > 0

        # All loaded items should be Name objects
        for name in generator.names:
            assert hasattr(name, "name")
            assert hasattr(name, "syllables")

    def test_generator_single_name_generation(self, fantasy_names_yaml_path):
        """Test generating a single name."""
        generator = Generator(fantasy_names_yaml_path)
        name = generator.generate_name(max_len=10, algorithm="simple")

        assert isinstance(name, GeneratedName)
        assert len(name) <= 10
        assert name.source_names is not None

    def test_generator_with_different_segmenters(
        self, fantasy_names_yaml_path, sengoku_names_yaml_path
    ):
        """Test generator with different segmenter types."""
        from wyrdbound_rng import FantasyNameSegmenter, JapaneseNameSegmenter

        # Test fantasy segmenter
        fantasy_gen = Generator(fantasy_names_yaml_path, FantasyNameSegmenter())
        fantasy_names = fantasy_gen.generate(3)
        assert len(fantasy_names) == 3

        # Test Japanese segmenter
        japanese_gen = Generator(sengoku_names_yaml_path, JapaneseNameSegmenter())
        japanese_names = japanese_gen.generate(3)
        assert len(japanese_names) == 3
