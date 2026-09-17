"""Regression tests locking the ten ancestry corpora against silent drift.

The thresholds are floors the corpora currently clear, not aspirations: the
unigram floor is 0.93 and the bigram floor 0.64, per ``CORPUS_REPORT.md`` §3.
A change to a corpus or to the generator that pushes either below its floor is
a real regression, and this file exists to say so before a playtest does.

Measurement helpers are imported from ``tools/corpus_test.py`` rather than
reimplemented, so there is exactly one definition of "coverage".
"""

import re
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import corpus_test  # noqa: E402

from wyrdbound_rng import Generator  # noqa: E402
from wyrdbound_rng.name_list_resolver import (  # noqa: E402
    get_available_name_lists,
    resolve_name_list,
)

# Floors the corpora clear. See CORPUS_REPORT.md §3 for the measurements.
MIN_UNIGRAM_COVERAGE = 0.93
MIN_BIGRAM_COVERAGE = 0.64
MIN_NAME_LENGTH = 3
MAX_NAME_LENGTH = 12
GENERATIONS = 200
MAX_GENERATED_LENGTH = 11
MIN_UNIQUENESS = 0.85
CONSONANT_RUN = re.compile(r"[^aeiouy]{4,}")

ANCESTRIES = sorted(
    identifier
    for identifier in get_available_name_lists()
    if identifier.startswith("ancestry-")
)


def test_all_ten_ancestries_are_present():
    assert len(ANCESTRIES) == 10, ANCESTRIES


@pytest.mark.parametrize("identifier", ANCESTRIES)
class TestAncestryCorpus:
    def _generator(self, identifier):
        return Generator(identifier)

    def test_resolves_and_loads(self, identifier):
        assert resolve_name_list(identifier) is not None
        generator = self._generator(identifier)
        assert generator.names

    def test_has_no_case_insensitive_duplicates(self, identifier):
        generator = self._generator(identifier)
        assert corpus_test.find_duplicates(generator) == {}

    def test_names_are_alphabetic_within_length_bounds(self, identifier):
        generator = self._generator(identifier)
        for name in generator.names:
            assert name.name.isalpha(), name.name
            assert MIN_NAME_LENGTH <= len(name.name) <= MAX_NAME_LENGTH, name.name

    def test_coverage_meets_floors(self, identifier):
        generator = self._generator(identifier)
        seqs = corpus_test.syllable_lists(generator)
        structure = corpus_test.structure_report(generator, seqs)
        assert structure["unigram_coverage"] >= MIN_UNIGRAM_COVERAGE
        assert structure["bigram_coverage"] >= MIN_BIGRAM_COVERAGE

    def test_bayesian_generations_are_well_formed(self, identifier):
        generator = self._generator(identifier)
        generator.generate_name(MAX_GENERATED_LENGTH, "bayesian")  # train

        produced = []
        for _ in range(GENERATIONS):
            name = generator.generate_name(MAX_GENERATED_LENGTH, "bayesian").name
            assert len(name) <= MAX_GENERATED_LENGTH, name
            assert CONSONANT_RUN.search(name.lower()) is None, name
            produced.append(name)

        uniqueness = len(set(produced)) / len(produced)
        assert uniqueness >= MIN_UNIQUENESS, uniqueness
