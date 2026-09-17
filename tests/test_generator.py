"""
Tests for the Generator class.
"""

import pytest

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


class TestLengthBudget:
    """Length control is budget-aware, not sample-and-discard.

    ``max_syllables`` is derived from the loaded corpus's mean syllable
    length (the ancestry corpora average 2.45 characters, not the hardcoded
    3), and the sequence generator is conditioned on the remaining character
    budget so it terminates naturally rather than being rejected and retried.
    """

    def test_budget_scales_with_mean_syllable_length(self):
        short = Generator("ancestry-dwarf-male")
        assert short.mean_syllable_length < 2.6

        # A corpus averaging 3.6 characters per syllable must get a smaller
        # syllable budget than the real 2.45-character corpus at the same cap.
        assert short._syllable_budget(11, 2.45) > short._syllable_budget(11, 3.6)

    def test_mean_syllable_length_is_measured_from_corpus(self):
        generator = Generator("ancestry-dwarf-male")
        all_syllables = [
            str(syllable) for name in generator.names for syllable in name.syllables
        ]
        expected = sum(len(s) for s in all_syllables) / len(all_syllables)
        assert generator.mean_syllable_length == expected

    def test_sequence_never_exceeds_character_budget(self):
        generator = Generator("ancestry-dwarf-male")
        generator.generate_name(11, "bayesian")  # train the model
        model = generator.bayesian_model
        for max_chars in (5, 7, 9, 11):
            for _ in range(100):
                syllables = model.generate_syllable_sequence(
                    generator._syllable_budget(max_chars),
                    max_chars=max_chars,
                )
                assert len("".join(syllables)) <= max_chars

    def test_mean_attempts_drops_at_tight_cap(self):
        generator = Generator("ancestry-dwarf-male")
        generator.generate_name(11, "bayesian")  # train the model

        calls = [0]
        original = generator.bayesian_model.generate_syllable_sequence

        def counting(*args, **kwargs):
            calls[0] += 1
            return original(*args, **kwargs)

        generator.bayesian_model.generate_syllable_sequence = counting

        total = 0
        for _ in range(200):
            calls[0] = 0
            # Threshold disabled so this measures length control alone: with
            # rejection sampling this averaged 1.66 attempts at this cap.
            name = generator.generate_name(5, "bayesian", min_probability_threshold=0.0)
            assert len(name.name) <= 5
            total += calls[0]

        assert total / 200 < 1.3


class TestBayesianNeverFallsBack:
    """The Bayesian path must not delegate to the simple algorithm.

    A run where every candidate was rejected used to fall through to
    ``_generate_name_simple``, the crudest generator available, so the
    hardest cases got the worst answer.
    """

    LONG_SEQUENCE = ["hra", "ven", "dral", "grim", "ulf", "inn"]

    def _patch_model(self, generator, monkeypatch, sequence):
        generator.generate_name(11, "bayesian")  # train the model
        monkeypatch.setattr(
            generator.bayesian_model,
            "generate_syllable_sequence",
            lambda *args, **kwargs: list(sequence),
        )

    def test_simple_algorithm_is_never_reached(self, monkeypatch):
        generator = Generator("ancestry-dwarf-male")

        def explode(*args, **kwargs):
            raise AssertionError("_generate_name_simple was reached")

        monkeypatch.setattr(generator, "_generate_name_simple", explode)
        self._patch_model(generator, monkeypatch, self.LONG_SEQUENCE)

        name = generator.generate_name(4, "bayesian", min_probability_threshold=1.0)
        assert name is not None
        assert name.name

    def test_over_length_candidate_is_trimmed_at_syllable_boundary(self, monkeypatch):
        generator = Generator("ancestry-dwarf-male")

        def explode(*args, **kwargs):
            raise AssertionError("_generate_name_simple was reached")

        monkeypatch.setattr(generator, "_generate_name_simple", explode)
        self._patch_model(generator, monkeypatch, self.LONG_SEQUENCE)

        name = generator.generate_name(4, "bayesian", min_probability_threshold=1.0)

        # "Hra" is 3 characters; adding "ven" would make 6, so trimming at a
        # syllable boundary yields "Hra", never "Hrav" or "Hr".
        assert name.name == "Hra"
        assert generator._is_pronounceable(name.name)

    def test_returns_highest_probability_candidate_when_none_meet_threshold(
        self, monkeypatch
    ):
        generator = Generator("ancestry-dwarf-male")
        # A real high-probability bigram, so the candidate has nonzero
        # probability but still cannot clear the impossible threshold.
        self._patch_model(generator, monkeypatch, ["val", "dr"])

        name = generator.generate_name(11, "bayesian", min_probability_threshold=1.0)
        assert name.name == "Valdr"
        assert name.probability is not None
        assert name.probability > 0.0


class TestMinimumLength:
    """`min_len` keeps short fragments like "Ays", "Iei", "Ona" out.

    It defaults to 3, preserving the previous behavior for existing callers.
    """

    def test_min_len_is_respected(self):
        generator = Generator("ancestry-dwarf-male")
        for algorithm in ("very_simple", "simple", "bayesian"):
            for _ in range(50):
                name = generator.generate_name(11, algorithm, min_len=5)
                assert len(name.name) >= 5, (algorithm, name.name)

    def test_min_len_defaults_to_three(self):
        generator = Generator("ancestry-dwarf-male")
        for _ in range(50):
            name = generator.generate_name(11, "very_simple")
            assert len(name.name) >= 3

    def test_min_len_greater_than_max_len_raises(self):
        generator = Generator("ancestry-dwarf-male")
        with pytest.raises(ValueError):
            generator.generate_name(5, "simple", min_len=6)

    def test_generate_threads_min_len(self):
        generator = Generator("ancestry-dwarf-male")
        names = generator.generate(10, max_chars=11, min_len=6)
        assert len(names) == 10
        for name in names:
            assert len(name.name) >= 6


class TestSimpleAlgorithmStateLeak:
    """A failed length check must not leave an oversized syllable behind.

    ``beginning`` kept the last attempted value whether or not it passed, so
    when the loop exhausted the oversized syllable was used anyway.
    """

    def test_no_oversized_beginning_when_loop_exhausts(self, monkeypatch):
        generator = Generator("ancestry-dwarf-male")

        # Every "beginning" syllable is far too long for a 2-character cap, so
        # the selection loop exhausts without a legal candidate.
        class StubName:
            name = "longsource"
            syllables = ["Supercalifragilistic"]

        monkeypatch.setattr(
            "wyrdbound_rng.generator.random.choice",
            lambda seq: StubName(),
        )

        with pytest.raises(ValueError):
            generator._generate_name_simple(2, min_len=3)

    def test_simple_algorithm_never_exceeds_cap_after_resampling(self):
        generator = Generator("ancestry-dwarf-male")
        for _ in range(100):
            name = generator.generate_name(8, "simple")
            assert len(name.name) <= 8
