#!/usr/bin/env python3
"""Inter-nuclear consonant cluster inventory for a name corpus.

The segmenter's "syllables" are not phonological syllables -- it emits
nucleus-less fragments such as ``('h','','r') ('','a','') ('f','','n')`` for
``Hrafn`` and ``('r','a','g') ('n','','')`` for the ``Ragn`` of ``Ragnvindr``.
Any rule built on "coda of syllable N plus onset of syllable N+1" therefore
mostly never fires, because the orphan fragments have an empty coda.

The unit that matters is the **inter-nuclear consonant cluster**: the run of
consonants between one vowel and the next, plus the word-initial and word-final
runs. It is what a reader stumbles over, and it is computable directly from the
name without consulting the segmenter.

This tool is measurement only. It changes no behaviour; it exists so that a
validity rule can be derived from what a corpus actually contains rather than
from a guessed threshold.

Usage::

    python tools/cluster_report.py --list ancestry-dwarf-male
    python tools/cluster_report.py --all
    python tools/cluster_report.py --all --markdown docs/cluster-baseline.md
"""

from __future__ import annotations

import argparse
import os
import random
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from wyrdbound_rng import (  # noqa: E402
    FantasyNameSegmenter,
    Generator,
)

# y is a vowel, or every Welsh name in ancestry-elf-* is one long cluster.
CONSONANT_RUN = re.compile(r"[^aeiouy]+")

CORPORA = [
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
    "generic-fantasy",
]

GENERATIONS = 400
SEED = 0xC0FFEE


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def clusters_by_position(name: str) -> dict[str, list[str]]:
    """Inter-nuclear consonant clusters, by position class.

    ``initial`` is the run before the first vowel, ``final`` the run after the
    last, and ``medial`` any run between two vowels.
    """
    lowered = name.lower()
    result: dict[str, list[str]] = {"initial": [], "medial": [], "final": []}
    for match in CONSONANT_RUN.finditer(lowered):
        if match.start() == 0:
            result["initial"].append(match.group())
        elif match.end() == len(lowered):
            result["final"].append(match.group())
        else:
            result["medial"].append(match.group())
    return result


def all_clusters(name: str) -> list[str]:
    """Every inter-nuclear cluster in ``name``, in order of appearance."""
    return [match.group() for match in CONSONANT_RUN.finditer(name.lower())]


def build_inventory(names: Sequence[str]) -> dict[str, Counter]:
    """Cluster frequencies per position class over a set of names."""
    inventory: dict[str, Counter] = {
        "initial": Counter(),
        "medial": Counter(),
        "final": Counter(),
    }
    for name in names:
        for position, clusters in clusters_by_position(name).items():
            inventory[position].update(clusters)
    return inventory


def hapaxes(counter: Counter) -> int:
    """Clusters seen exactly once -- a whitelist built on these is noise."""
    return sum(1 for count in counter.values() if count == 1)


def splits(cluster: str, onset: set[str], coda: set[str]) -> bool:
    """True if ``cluster`` splits into an attested onset plus attested coda.

    Both orders are tried. ``gnr`` in ``Ragnrikr`` splits ``g|nr`` (onset ``g``
    plus coda ``nr``) and is legal because ``gnv`` is attested in ``Ragnvindr``;
    ``rkg`` in goblin names splits ``rk|g``. The feature document describes the
    split two opposite ways -- T-010b step 3 says prefix=onset / suffix=coda,
    the rationale section says prefix=coda / suffix=onset -- so this measures
    both, and the union, to settle which one the corpora support.
    """
    for k in range(1, len(cluster)):
        prefix, suffix = cluster[:k], cluster[k:]
        if (prefix in onset and suffix in coda) or (prefix in coda and suffix in onset):
            return True
    return False


def is_legal(
    name: str,
    observed: dict[str, set[str]],
    onset: set[str],
    coda: set[str],
    max_len: int,
) -> bool:
    """The decomposable rule: every cluster is observed, or decomposable."""
    for position, clusters in clusters_by_position(name).items():
        for cluster in clusters:
            if len(cluster) > max_len:
                return False
            if cluster in observed[position]:
                continue
            if not splits(cluster, onset, coda):
                return False
    return True


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def analyze(source: str, generations: int = GENERATIONS, seed: int = SEED) -> dict:
    generator = Generator(source, segmenter=FantasyNameSegmenter())
    corpus_names = [name.name for name in generator.names]
    corpus_inventory = build_inventory(corpus_names)

    rng = random.Random(seed)
    gen_generator = Generator(source, segmenter=FantasyNameSegmenter(), rng=rng)
    generated = [
        gen_generator.generate_name(11, "bayesian").name for _ in range(generations)
    ]
    generated_inventory = build_inventory(generated)

    all_corpus_clusters = set().union(
        *[set(counter) for counter in corpus_inventory.values()]
    )

    # Which generated clusters are unseen anywhere in the corpus, with an
    # example name for each.
    unseen: dict[str, str] = {}
    for name in generated:
        for cluster in all_clusters(name):
            if cluster not in all_corpus_clusters and cluster not in unseen:
                unseen[cluster] = name

    # Strict whole-cluster whitelist cost: fraction of generated names whose
    # cluster set is not entirely attested at the right position class.
    strict_rejected = 0
    for name in generated:
        by_position = clusters_by_position(name)
        legal = all(
            cluster in corpus_inventory[position]
            for position, clusters in by_position.items()
            for cluster in clusters
        )
        if not legal:
            strict_rejected += 1

    onset = set(corpus_inventory["initial"])
    coda = set(corpus_inventory["final"])
    observed = {p: set(c) for p, c in corpus_inventory.items()}
    max_len = max(
        (len(cluster) for counter in corpus_inventory.values() for cluster in counter),
        default=0,
    )
    decomposable_rejected = sum(
        1 for name in generated if not is_legal(name, observed, onset, coda, max_len)
    )

    return {
        "source": source,
        "corpus_names": len(corpus_names),
        "corpus_inventory": {
            position: dict(counter) for position, counter in corpus_inventory.items()
        },
        "corpus_sizes": {
            position: len(counter) for position, counter in corpus_inventory.items()
        },
        "corpus_hapaxes": {
            position: hapaxes(counter) for position, counter in corpus_inventory.items()
        },
        "generated": len(generated),
        "generated_sizes": {
            position: len(counter) for position, counter in generated_inventory.items()
        },
        "unseen": unseen,
        "strict_rejection_rate": strict_rejected / len(generated) if generated else 0.0,
        "decomposable_rejection_rate": (
            decomposable_rejected / len(generated) if generated else 0.0
        ),
        "max_cluster_length": max_len,
    }


def render_text(report: dict, top: int = 25) -> None:
    print(f"=== Cluster report: {report['source']} ===")
    print()
    print(f"Corpus names: {report['corpus_names']}")
    print(
        f"  inventory   initial {report['corpus_sizes']['initial']:>4}  "
        f"medial {report['corpus_sizes']['medial']:>4}  "
        f"final {report['corpus_sizes']['final']:>4}"
    )
    print(
        f"  hapaxes     initial {report['corpus_hapaxes']['initial']:>4}  "
        f"medial {report['corpus_hapaxes']['medial']:>4}  "
        f"final {report['corpus_hapaxes']['final']:>4}"
    )
    print()
    medial = sorted(
        report["corpus_inventory"]["medial"].items(), key=lambda kv: (-kv[1], kv[0])
    )
    print(f"Medial inventory (top {top} of {len(medial)}):")
    for cluster, count in medial[:top]:
        print(f"  {cluster:<8} {count}")
    print()
    print(
        f"Generated ({report['generated']}) inventory   "
        f"initial {report['generated_sizes']['initial']}  "
        f"medial {report['generated_sizes']['medial']}  "
        f"final {report['generated_sizes']['final']}"
    )
    print(f"Generated clusters unseen in corpus: {len(report['unseen'])}")
    for cluster, name in sorted(report["unseen"].items())[:top]:
        print(f"  {cluster:<8} e.g. {name}")
    print()
    print(
        f"Strict whole-cluster whitelist would reject "
        f"{report['strict_rejection_rate']:.1%} of generated names"
    )
    print(
        f"Decomposable rule (onset+coda either order) would reject "
        f"{report['decomposable_rejection_rate']:.1%} of generated names"
    )
    print()


# ---------------------------------------------------------------------------
# Markdown output
# ---------------------------------------------------------------------------


def render_markdown(reports: Sequence[dict], generations: int) -> str:
    lines = [
        "# Inter-nuclear cluster baseline",
        "",
        "Generated by `tools/cluster_report.py`, which changes no behaviour and",
        "exists so that a name-validity rule can be derived from what the corpora",
        "actually contain rather than from a guessed threshold.",
        "",
        "The unit is the **inter-nuclear consonant cluster**: the run of",
        "consonants between one vowel and the next, plus the word-initial and",
        "word-final runs. It is computed with `[^aeiouy]+` over the name, with `y`",
        "counted as a vowel. The segmenter is not consulted, because its",
        'nucleus-less fragments make "coda plus onset" tests skip the junctions',
        "that matter.",
        "",
        f"Generations: {generations} per corpus, seeded (`0xC0FFEE`), "
        "Bayesian, `max_len=11`.",
        "",
        "## Inventory sizes",
        "",
        "| corpus | names | initial | medial | final | medial hapaxes | unseen "
        "generated clusters | strict whitelist rejects | decomposable rejects |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for report in reports:
        lines.append(
            f"| {report['source']} | {report['corpus_names']} "
            f"| {report['corpus_sizes']['initial']} "
            f"| {report['corpus_sizes']['medial']} "
            f"| {report['corpus_sizes']['final']} "
            f"| {report['corpus_hapaxes']['medial']} "
            f"| {len(report['unseen'])} "
            f"| {report['strict_rejection_rate']:.1%} "
            f"| {report['decomposable_rejection_rate']:.1%} |"
        )

    lines += [
        "",
        "`strict whitelist rejects` is the cost of requiring a generated cluster",
        "to have been observed in the corpus at the same position class. It is",
        "unusable as-is, and not because any corpus is bad: a small, coherent",
        "corpus has a small junction inventory by construction, so almost every",
        "novel combination is unseen. `decomposable rejects` is the alternative",
        "chosen in T-010b: a cluster is legal if it was observed, or if it splits",
        "into an attested onset plus an attested coda in either order.",
        "",
        "## Medial inventory",
        "",
        "Medial clusters with their corpus frequencies. Hapaxes (seen once) are",
        "the part of the inventory a whitelist cannot be built on.",
        "",
    ]
    for report in reports:
        medial = sorted(
            report["corpus_inventory"]["medial"].items(),
            key=lambda kv: (-kv[1], kv[0]),
        )
        lines.append(f"### {report['source']}")
        lines.append("")
        if not medial:
            lines.append("_No medial clusters._")
            lines.append("")
            continue
        lines.append(
            "`" + "`, `".join(f"{cluster} ({count})" for cluster, count in medial) + "`"
        )
        lines.append("")

    lines += [
        "## Generated clusters unseen in the corpus",
        "",
        "The set difference between generated and corpus inventories, with one",
        "example name per unseen cluster.",
        "",
    ]
    for report in reports:
        lines.append(f"### {report['source']}")
        lines.append("")
        if not report["unseen"]:
            lines.append("_None._")
            lines.append("")
            continue
        lines.append("| cluster | example name |")
        lines.append("|---|---|")
        for cluster, name in sorted(report["unseen"].items()):
            lines.append(f"| {cluster} | {name} |")
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inter-nuclear consonant cluster inventory for a corpus",
        prog="cluster_report",
    )
    parser.add_argument(
        "-l",
        "--list",
        dest="source",
        help="Name list identifier (e.g. 'ancestry-dwarf-male')",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Report every corpus in the baseline set",
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=GENERATIONS,
        help=f"Generated names per corpus (default: {GENERATIONS})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=SEED,
        help=f"Seed for generation (default: {SEED})",
    )
    parser.add_argument(
        "--markdown",
        metavar="PATH",
        help="Write the baseline as Markdown to PATH",
    )
    args = parser.parse_args()

    if not args.source and not args.all:
        parser.error("one of --list or --all is required")

    sources = CORPORA if args.all else [args.source]
    reports = [
        analyze(source, generations=args.generations, seed=args.seed)
        for source in sources
    ]

    if args.markdown:
        path = Path(args.markdown)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_markdown(reports, args.generations), encoding="utf-8")
        print(f"Wrote {path} ({len(reports)} corpora)")
    elif not args.all:
        render_text(reports[0])
    else:
        for report in reports:
            render_text(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
