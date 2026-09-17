#!/usr/bin/env python3
"""Demo: name generation from the ten ancestry corpora.

Run with:

    python demos/name_generation_demo.py --seed 1

Prints, for each of the ten ancestry corpora: twelve generated names, the
corpus's coverage figures, and a before/after column showing what the old
``_remove_repetitions`` would have done to each name. That last column is the
feature's whole argument in one view -- it is kept after the fix as a
regression exhibit.

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


def old_remove_repetitions(name):
    """The pre-fix implementation: delete every 'll' and 'nn' outright."""
    result = re.sub(r"ll", "", name)
    result = re.sub(r"nn", "", result)
    return result


def max_length_for(identifier):
    return 9 if "goblin" in identifier else 11


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
    print("DEMO OK: name_generation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
