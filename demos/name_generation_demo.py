#!/usr/bin/env python3
"""Demo: name generation from the ten ancestry corpora.

Run with:

    python demos/name_generation_demo.py --seed 1

For each of the ten ancestry corpora it prints twelve generated names, the
corpus's coverage figures, and a before/after column showing what the old
``_remove_repetitions`` would have done to each name.

It then shows, for one corpus, the inter-nuclear cluster of every name in a
batch with how the corpus-derived phonotactic rule classified it: ``observed``
(attested at that position), ``decomposed`` (an attested onset plus an attested
coda), or ``REJECT`` (which generation would have resampled).

Ends ``DEMO OK: name_generation``.
"""

import argparse
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import corpus_test  # noqa: E402

from wyrdbound_rng import Generator  # noqa: E402

ANCESTRIES = [
    "ancestry-dwarf-male",
    "ancestry-dwarf-female",
    "ancestry-elf-male",
    "ancestry-elf-female",
    "ancestry-halfling-male",
    "ancestry-halfling-female",
    "ancestry-human-male",
    "ancestry-human-female",
    "ancestry-goblin-male",
    "ancestry-goblin-female",
]

NAMES_PER_CORPUS = 12
CLUSTER_CORPUS = "ancestry-dwarf-male"
CLUSTER_NAMES = 20


def old_remove_repetitions(name):
    """The pre-fix implementation: delete every 'll' and 'nn' outright."""
    result = re.sub(r"ll", "", name)
    result = re.sub(r"nn", "", result)
    return result


def max_length_for(identifier):
    return 9 if "goblin" in identifier else 11


def classify_clusters(generator, name):
    """Label each inter-nuclear cluster in ``name`` for the phonotactic rule.

    Returns a list of ``(cluster, verdict)`` where verdict is ``observed``,
    ``decomposed`` or ``REJECT``.
    """
    inventory = generator._cluster_inventory
    labels = []
    for position, clusters in generator._clusters_by_position(name).items():
        for cluster in clusters:
            if cluster in inventory["observed"][position]:
                verdict = "observed"
            elif generator._cluster_is_legal(cluster, position):
                verdict = "decomposed"
            else:
                verdict = "REJECT"
            labels.append((cluster, verdict))
    return labels


def print_cluster_section(seed):
    rng = random.Random(seed) if seed is not None else random
    generator = Generator(CLUSTER_CORPUS, rng=rng)
    max_len = max_length_for(CLUSTER_CORPUS)

    # Emitted names are legal by construction (the rule is an accept condition),
    # so a REJECT verdict would never appear on them. Capture the raw candidates
    # instead, so all three verdicts are visible.
    real_is_pronounceable = generator._is_pronounceable
    candidates = []

    def capture(name):
        candidates.append(name)
        return True

    generator._is_pronounceable = capture
    try:
        for _ in range(CLUSTER_NAMES * 2):
            generator.generate_name(max_len, "bayesian")
    finally:
        generator._is_pronounceable = real_is_pronounceable

    print(f"=== phonotactics: {CLUSTER_CORPUS} ===")
    print("  Each inter-nuclear cluster, and how the corpus-derived rule read it.")
    print()
    print(f"  {'candidate':<16} {'verdict':<10} clusters")
    print(f"  {'-' * 16} {'-' * 10} {'-' * 40}")
    shown = 0
    for name in candidates:
        labels = classify_clusters(generator, name)
        rejected = any(verdict == "REJECT" for _, verdict in labels)
        rendered = ", ".join(f"{cluster} ({verdict})" for cluster, verdict in labels)
        print(f"  {name:<16} {'reject' if rejected else 'accept':<10} {rendered}")
        shown += 1
        if shown >= CLUSTER_NAMES:
            break
    print()
    print(
        "  observed   = the cluster is attested in the corpus at that position\n"
        "  decomposed = an attested onset plus an attested coda in either order\n"
        "  REJECT     = generation would have resampled this candidate\n"
        "  (candidates are shown raw; generation emits only accept rows)"
    )
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for reproducible generation (default: unseeded)",
    )
    args = parser.parse_args()

    any_damaged = False
    for identifier in ANCESTRIES:
        rng = random.Random(args.seed) if args.seed is not None else random
        generator = Generator(identifier, rng=rng)
        seqs = corpus_test.syllable_lists(generator)
        structure = corpus_test.structure_report(generator, seqs)
        max_len = max_length_for(identifier)

        print(f"=== {identifier} ===")
        print(
            f"  coverage   unigram {structure['unigram_coverage']:.3f}  "
            f"bigram {structure['bigram_coverage']:.3f}  "
            f"({structure['total_names']} names, "
            f"{structure['unique_syllables']} syllables)"
        )
        print()
        print(f"  {'generated':<16} {'old implementation':<20}")
        print(f"  {'-' * 16} {'-' * 20}")
        for _ in range(NAMES_PER_CORPUS):
            name = generator.generate_name(max_len, "bayesian").name
            damaged = old_remove_repetitions(name)
            note = damaged if damaged != name else ""
            if damaged != name:
                any_damaged = True
            print(f"  {name:<16} {note:<20}")
        print()

    print(
        "  (old-implementation column shows names the pre-fix code would have damaged)"
    )
    if not any_damaged:
        print("  No names were damaged in this run; try a different --seed.")
    print()

    print_cluster_section(args.seed)

    print("DEMO OK: name_generation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
