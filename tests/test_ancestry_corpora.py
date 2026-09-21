"""Regression tests locking the ten ancestry corpora against silent drift.

The thresholds are floors the corpora currently clear, not aspirations: the
unigram floor is 0.93 and the bigram floor 0.64, per ``CORPUS_REPORT.md`` §3.
A change to a corpus or to the generator that pushes either below its floor is
a real regression, and this file exists to say so before a playtest does.

Measurement helpers are imported from ``tools/corpus_test.py`` rather than
reimplemented, so there is exactly one definition of "coverage".
"""

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

# The phonotactic rule is an accept condition inside generation, so emitted
# names are legal by construction. The number that matters a corpus author is
# the share of raw model *candidates* it throws away.
#
# Measured 2026-09-21 (commit for T-010b, the corpus-derived rule), seeded
# (0xC0FFEE), 200 generations per corpus at max_len=11. These are the true
# costs, not targets: the rule rejects far more than the ~2% the feature
# document predicted, because it requires a cluster to have been observed or
# to decompose, and a coherent corpus deliberately has few junk clusters. A
# ceiling is recorded so a later change cannot silently make it worse.
#
# Ceiling = measured rate + 5 points of headroom.
MAX_CLUSTER_REJECTION = {
    "ancestry-dwarf-male": 0.48,
    "ancestry-dwarf-female": 0.33,
    "ancestry-elf-male": 0.29,
    "ancestry-elf-female": 0.24,
    "ancestry-halfling-male": 0.36,
    "ancestry-halfling-female": 0.26,
    "ancestry-human-male": 0.20,
    "ancestry-human-female": 0.32,
    "ancestry-goblin-male": 0.22,
    "ancestry-goblin-female": 0.21,
}
CLUSTER_SEED = 0xC0FFEE

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
            assert generator._is_pronounceable(name), name
            produced.append(name)

        uniqueness = len(set(produced)) / len(produced)
        assert uniqueness >= MIN_UNIQUENESS, uniqueness

    def test_cluster_rejection_cost_is_ceilinged(self, identifier):
        import random

        generator = Generator(identifier, rng=random.Random(CLUSTER_SEED))
        cost = corpus_test.cluster_rejection_cost(
            generator,
            GENERATIONS,
            "bayesian",
            MAX_GENERATED_LENGTH,
            1e-8,
        )
        assert cost is not None, "ancestry corpus should have a cluster inventory"
        ceiling = MAX_CLUSTER_REJECTION[identifier]
        assert cost <= ceiling, (
            f"{identifier}: phonotactic rule rejects {cost:.1%} of candidates, "
            f"ceiling {ceiling:.0%}. A rising cost means the rule or the corpus "
            f"drifted; see CORPUS_REPORT.md §5 and docs/cluster-baseline.md."
        )
