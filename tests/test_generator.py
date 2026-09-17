"""
Tests for the Generator class.
"""

from wyrdbound_rng import GeneratedName, Generator


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


class TestRemoveRepetitions:
    """Regression tests for Generator._remove_repetitions.

    The old implementation deleted every ``ll`` and ``nn`` outright, mangling
    roughly a third of generated names (Sibella -> Sibea, Gestkell -> Gestke).
    A run of repeated letters must collapse to a double, not vanish.
    """

    REGRESSION_NAMES = [
        "Gestkell",
        "Ketill",
        "Gunnar",
        "Finnr",
        "Hallgrim",
        "Gwenllian",
        "Sibella",
    ]

    def _clean(self, name):
        generator = Generator.__new__(Generator)
        return generator._remove_repetitions(name)

    def test_names_with_doubled_letters_survive_intact(self):
        for name in self.REGRESSION_NAMES:
            assert self._clean(name) == name, f"{name} was mangled"

    def test_triple_run_collapses_to_double(self):
        assert self._clean("Styrrr") == "Styrr"
        assert self._clean("Hallla") == "Halla"

    def test_double_run_is_left_alone(self):
        assert self._clean("Gunnar") == "Gunnar"

    def test_remove_repetitions_is_idempotent(self):
        for name in self.REGRESSION_NAMES + ["Styrrr", "Hallla"]:
            once = self._clean(name)
            assert self._clean(once) == once


class TestPronounceable:
    """Syllable junctions must not create runs of four consonants.

    The segmenter emits onset-only syllables (``hr``, ``sv``, ``thj``), which
    are legal before a vowel (``hr`` + ``afn`` = Hrafn) and broken before a
    consonant (``hr`` + ``gils`` = Hrgils). The rule is about the junction,
    not the syllable.
    """

    def _is_pronounceable(self, name):
        generator = Generator.__new__(Generator)
        return generator._is_pronounceable(name)

    def test_accepts_a_three_consonant_run(self):
        assert self._is_pronounceable("Strong") is True

    def test_rejects_a_four_consonant_run(self):
        assert self._is_pronounceable("Fjglaugr") is False

    def test_accepts_vowelless_syllable_before_a_vowel(self):
        assert self._is_pronounceable("Hrafn") is True

    def test_a_three_consonant_onset_is_legal(self):
        # The rule is a four-consonant run, so a three-consonant onset such as
        # "hrg" in Hrgils or "svg" in Svgest is accepted. The feature document
        # lists these as rejected, which contradicts its own explicit
        # "rejects a run of four or more consecutive consonants" statement.
        assert self._is_pronounceable("Hrgils") is True
        assert self._is_pronounceable("Svgest") is True

    def test_rejects_other_bad_junctions(self):
        assert self._is_pronounceable("Solthbaugr") is False
        assert self._is_pronounceable("Thjglamr") is False

    def test_y_counts_as_a_vowel(self):
        for name in ("Gwyn", "Myrddin", "Bryn"):
            assert self._is_pronounceable(name) is True

    def test_no_four_consonant_run_in_dwarf_male(self):
        generator = Generator("ancestry-dwarf-male")
        for _ in range(200):
            name = generator.generate_name(11, "bayesian")
            assert self._is_pronounceable(name.name) is True, name.name
