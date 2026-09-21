#!/usr/bin/env python3
"""
Corpus quality and sizing tool for name generation.

Answers two questions a corpus author actually has:

  1. "Is this corpus good enough yet?"
  2. "If not, roughly how many more names do I need?"

It answers them from the syllable inventory rather than from a rule of thumb,
because the syllable inventory is what the generator actually samples from. A
corpus of 800 names that all share the same 40 syllables is a worse generator
input than 200 names with 300 syllables between them, and a size threshold
alone cannot tell those apart.

Metrics
-------

Structure
    Name count, unique syllables, syllables per name, name length spread, and
    the number of exact/case duplicates that snuck in.

Coverage (Good-Turing)
    The probability that the *next* name added to the corpus would introduce a
    syllable the generator has never seen. Estimated as f1 / T, where f1 is the
    number of syllables occurring exactly once and T is the total syllable
    token count. Coverage = 1 - f1/T. This is the single best "am I done yet"
    number: high coverage means the corpus has stopped surprising itself.

    Reported for unigrams (individual syllables) and for bigrams (ordered
    syllable pairs, including the ^START and END$ boundaries). Bigram coverage
    is the harder target and the one the Bayesian algorithm depends on, so it
    is the one the verdict is keyed to.

Richness (Chao1)
    A lower-bound estimate of how many distinct syllables the *style* this
    corpus is drawn from contains, given what has been observed so far.
    S_obs + f1^2 / (2*f2). The gap between observed and estimated is how much
    of the style is still missing.

Saturation curve
    Unique syllables found in random subsamples of increasing size. The
    marginal yield at the end of the curve -- new syllables per 50 names added
    -- is the practical stopping signal. Under ~3 new syllables per 50 names,
    you are paying full price for names that teach the generator nothing.

Sizing recommendation
    (1 - coverage) decays as a power law in corpus size. The tool fits that
    decay on the observed subsamples and inverts it to estimate the corpus
    size needed to hit a target coverage. Extrapolations beyond 2x the current
    size are flagged, because that is where the fit stops being trustworthy.

Generation quality
    Generates a batch and measures novelty (not already in the corpus),
    uniqueness (distinct within the batch), length conformance, and -- for the
    Bayesian algorithm -- the probability distribution of what came out.

Usage
-----

    python tools/corpus_test.py --list generic-fantasy
    python tools/corpus_test.py --list ./data/ancestry-dwarf-male.yaml -v
    python tools/corpus_test.py --list japanese-sengoku -s japanese
    python tools/corpus_test.py --list generic-fantasy --json > report.json
    python tools/corpus_test.py --all           # every built-in list, ranked
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from collections import Counter
from typing import Sequence

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from wyrdbound_rng import (  # noqa: E402
    FantasyNameSegmenter,
    Generator,
    JapaneseNameSegmenter,
)
from wyrdbound_rng.name_list_resolver import (  # noqa: E402
    format_available_lists,
    get_available_name_lists,
)

# ---------------------------------------------------------------------------
# Thresholds
#
# These are the defaults the verdict is judged against. They are deliberately
# expressed as coverage and marginal-yield rather than as a name count: a count
# cannot distinguish a rich corpus from a repetitive one. See TTRPG_CORPUS_GUIDE.md
# for the corresponding rules of thumb in raw name counts.
# ---------------------------------------------------------------------------

DEFAULT_TARGET_UNIGRAM_COVERAGE = 0.93
DEFAULT_TARGET_BIGRAM_COVERAGE = 0.65

# TTRPG_CORPUS_GUIDE.md asks for 85%+ novelty. Measured against the Bayesian
# algorithm, that target is actively harmful: novelty and name quality trade off
# inversely, because the high-probability syllable transitions that produce
# plausible names are the same ones the corpus already spent on real names.
#
# On the same corpus, at the same length cap:
#
#   simple     95% novel   Warwaaibald, Gugomarger, Lameramfred, Foethelm
#   bayesian   69% novel   Guilhard, Adalward, Lambert, Engelwig, Bertgleif
#
# Chasing 85% selects the top row. Uniqueness is the metric that actually
# protects the player experience -- it is what stops the same name recurring in
# one session -- and it stays high in both. Novelty is kept as a check against
# a corpus so small the generator can only regurgitate it, which is the real
# failure it was meant to catch, so the bar is set where it catches that and
# nothing else.
DEFAULT_MIN_NOVELTY = 0.60
DEFAULT_MIN_UNIQUENESS = 0.85
DEFAULT_SATURATION_YIELD = 6.0  # new syllables per 50 names added

BOUNDARY_START = "^"
BOUNDARY_END = "$"


# ---------------------------------------------------------------------------
# Estimators
# ---------------------------------------------------------------------------


def good_turing_coverage(freqs: Counter) -> tuple[float, int, int, int]:
    """Good-Turing sample coverage for a frequency table.

    Returns (coverage, f1, f2, total_tokens). Coverage is 1 - f1/T: the
    estimated probability that the next observed token is of a type already
    seen. f1 and f2 are the counts of types seen exactly once and exactly
    twice, which the Chao1 estimator also needs.
    """
    total = sum(freqs.values())
    if total == 0:
        return 0.0, 0, 0, 0
    f1 = sum(1 for c in freqs.values() if c == 1)
    f2 = sum(1 for c in freqs.values() if c == 2)
    return 1.0 - (f1 / total), f1, f2, total


def chao1(freqs: Counter) -> float:
    """Chao1 lower-bound estimate of true type richness.

    S_obs + f1^2 / (2*f2), with the bias-corrected form used when f2 == 0 so
    the estimator does not divide by zero on a very small or very flat corpus.
    """
    s_obs = len(freqs)
    f1 = sum(1 for c in freqs.values() if c == 1)
    f2 = sum(1 for c in freqs.values() if c == 2)
    if f2 > 0:
        return s_obs + (f1 * f1) / (2.0 * f2)
    return s_obs + (f1 * (f1 - 1)) / 2.0


def fit_power_law(
    xs: Sequence[float], ys: Sequence[float]
) -> tuple[float, float] | None:
    """Least-squares fit of y = a * x^(-b) in log-log space.

    Returns (a, b), or None when there are too few usable points. Points with a
    non-positive y are dropped: those are corpora that have already reached
    perfect coverage at that subsample size, where the log is undefined.
    """
    pts = [(math.log(x), math.log(y)) for x, y in zip(xs, ys) if x > 0 and y > 0]
    if len(pts) < 3:
        return None
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    num = sum((p[0] - mx) * (p[1] - my) for p in pts)
    den = sum((p[0] - mx) ** 2 for p in pts)
    if den == 0:
        return None
    slope = num / den
    intercept = my - slope * mx
    return math.exp(intercept), -slope


# ---------------------------------------------------------------------------
# Corpus inspection
# ---------------------------------------------------------------------------


def syllable_lists(generator: Generator) -> list[list[str]]:
    """The corpus as a list of syllable sequences, one per name."""
    return [[str(s) for s in name.syllables] for name in generator.names]


def unigram_counts(seqs: Sequence[Sequence[str]]) -> Counter:
    return Counter(syl for seq in seqs for syl in seq)


def bigram_counts(seqs: Sequence[Sequence[str]]) -> Counter:
    """Ordered syllable pairs with explicit word boundaries.

    The boundaries matter: 'which syllables can start a name' and 'which can
    end one' are exactly the distributions the Bayesian generator needs, and a
    corpus can have plenty of interior variety while offering only six possible
    openings.
    """
    counts: Counter = Counter()
    for seq in seqs:
        padded = [BOUNDARY_START, *seq, BOUNDARY_END]
        for a, b in zip(padded, padded[1:]):
            counts[(a, b)] += 1
    return counts


def find_duplicates(generator: Generator) -> dict[str, list[str]]:
    """Exact and case-insensitive duplicate names in the source corpus."""
    seen: dict[str, list[str]] = {}
    for name in generator.names:
        seen.setdefault(name.name.lower(), []).append(name.name)
    return {k: v for k, v in seen.items() if len(v) > 1}


def structure_report(generator: Generator, seqs: Sequence[Sequence[str]]) -> dict:
    lengths = [len(n.name) for n in generator.names]
    syl_counts = [len(s) for s in seqs]
    uni = unigram_counts(seqs)
    big = bigram_counts(seqs)

    uni_cov, uni_f1, uni_f2, uni_t = good_turing_coverage(uni)
    big_cov, big_f1, big_f2, big_t = good_turing_coverage(big)

    starts = {seq[0] for seq in seqs if seq}
    ends = {seq[-1] for seq in seqs if seq}

    return {
        "total_names": len(generator.names),
        "unique_syllables": len(uni),
        "syllable_tokens": uni_t,
        "unique_bigrams": len(big),
        "bigram_tokens": big_t,
        "distinct_initial_syllables": len(starts),
        "distinct_final_syllables": len(ends),
        "name_length": {
            "min": min(lengths) if lengths else 0,
            "max": max(lengths) if lengths else 0,
            "mean": (sum(lengths) / len(lengths)) if lengths else 0.0,
        },
        "syllables_per_name": {
            "min": min(syl_counts) if syl_counts else 0,
            "max": max(syl_counts) if syl_counts else 0,
            "mean": (sum(syl_counts) / len(syl_counts)) if syl_counts else 0.0,
        },
        "unigram_coverage": uni_cov,
        "unigram_hapax": uni_f1,
        "unigram_doubletons": uni_f2,
        "unigram_chao1": chao1(uni),
        "bigram_coverage": big_cov,
        "bigram_hapax": big_f1,
        "bigram_doubletons": big_f2,
        "bigram_chao1": chao1(big),
    }


# ---------------------------------------------------------------------------
# Saturation
# ---------------------------------------------------------------------------


def saturation_curve(
    seqs: Sequence[Sequence[str]],
    trials: int = 12,
    rng: random.Random | None = None,
) -> list[dict]:
    """Rarefaction: what a corpus of size k drawn from this one would look like.

    For each sample size k, draws `trials` random subsets and averages the
    unique-syllable count and the Good-Turing coverage. This is what makes the
    sizing recommendation an extrapolation of measured behaviour rather than a
    guess.
    """
    rng = rng or random.Random(0xC0FFEE)
    n = len(seqs)
    if n == 0:
        return []

    sizes = sorted(
        {s for s in (25, 50, 75, 100, 150, 200, 300, 400, 500, 750, 1000) if s < n}
    )
    sizes.append(n)

    curve = []
    indices = list(range(n))
    for k in sizes:
        uni_types, big_types, covs, bcovs = [], [], [], []
        runs = 1 if k == n else trials
        for _ in range(runs):
            sample = seqs if k == n else [seqs[i] for i in rng.sample(indices, k)]
            u = unigram_counts(sample)
            b = bigram_counts(sample)
            uni_types.append(len(u))
            big_types.append(len(b))
            covs.append(good_turing_coverage(u)[0])
            bcovs.append(good_turing_coverage(b)[0])
        curve.append(
            {
                "names": k,
                "unique_syllables": sum(uni_types) / len(uni_types),
                "unique_bigrams": sum(big_types) / len(big_types),
                "unigram_coverage": sum(covs) / len(covs),
                "bigram_coverage": sum(bcovs) / len(bcovs),
            }
        )
    return curve


def marginal_yield(curve: Sequence[dict], per: int = 50) -> float | None:
    """New unique syllables per `per` names added, measured at the top of the curve."""
    if len(curve) < 2:
        return None
    a, b = curve[-2], curve[-1]
    span = b["names"] - a["names"]
    if span <= 0:
        return None
    return (b["unique_syllables"] - a["unique_syllables"]) / span * per


def recommend_size(
    curve: Sequence[dict],
    current: int,
    key: str,
    target: float,
) -> dict:
    """Estimate the corpus size needed to reach `target` coverage.

    Fits (1 - coverage) = a * n^(-b) across the measured subsamples and solves
    for n. The fit is honest about its own reach: anything past 2x the current
    corpus is returned with extrapolated=True, and the caller is expected to
    say so rather than quote it as a number to hit.
    """
    achieved = curve[-1][key] if curve else 0.0
    if achieved >= target:
        return {
            "target": target,
            "achieved": achieved,
            "needed": current,
            "additional": 0,
            "extrapolated": False,
            "reliable": True,
        }

    fit = fit_power_law(
        [c["names"] for c in curve],
        [max(1.0 - c[key], 1e-9) for c in curve],
    )
    if not fit:
        return {
            "target": target,
            "achieved": achieved,
            "needed": None,
            "additional": None,
            "extrapolated": True,
            "reliable": False,
        }

    a, b = fit
    if b <= 0:
        # Coverage is not improving with size. More names of this kind will not
        # help; the corpus needs more varied names, not more names.
        return {
            "target": target,
            "achieved": achieved,
            "needed": None,
            "additional": None,
            "extrapolated": True,
            "reliable": False,
            "note": "coverage is flat or worsening with size - add variety, not volume",
        }

    needed = int(math.ceil((a / (1.0 - target)) ** (1.0 / b)))
    return {
        "target": target,
        "achieved": achieved,
        "needed": needed,
        "additional": max(0, needed - current),
        "extrapolated": needed > 2 * current,
        "reliable": needed <= 2 * current,
        "fit": {"a": a, "b": b},
    }


# ---------------------------------------------------------------------------
# Generation quality
# ---------------------------------------------------------------------------


def cluster_rejection_cost(
    generator: Generator,
    count: int,
    algorithm: str,
    max_length: int,
    min_probability: float,
) -> float | None:
    """Fraction of raw generated candidates the phonotactic rule rejects.

    The rule is an accept condition inside generation, so emitted names are
    legal by construction and measuring them says nothing. The cost a corpus
    author actually pays is on the *candidates* the model proposes, so the
    rule is neutralised for one batch and the batch is then judged. Returns
    None when the generator has no cluster inventory (small-corpus fallback).
    """
    if not getattr(generator, "_cluster_inventory", None):
        return None

    real = generator._is_pronounceable
    candidates: list[str] = []

    def capture(name):
        candidates.append(name)
        return True

    generator._is_pronounceable = capture
    try:
        generator.generate(
            count, max_length, algorithm, min_probability_threshold=min_probability
        )
    finally:
        generator._is_pronounceable = real

    if not candidates:
        return None
    rejected = sum(1 for name in candidates if not real(name))
    return rejected / len(candidates)


def generation_report(
    generator: Generator,
    count: int,
    algorithm: str,
    max_length: int,
    min_probability: float,
) -> dict:
    generated = generator.generate(
        count, max_length, algorithm, min_probability_threshold=min_probability
    )
    produced = [g.name for g in generated if g and g.name]
    if not produced:
        return {"algorithm": algorithm, "requested": count, "produced": 0}

    novel = [n for n in produced if not generator.name_exists_in_corpus(n)]
    probs = [g.probability for g in generated if getattr(g, "probability", None)]
    lengths = [len(n) for n in produced]

    report = {
        "algorithm": algorithm,
        "requested": count,
        "produced": len(produced),
        "novelty_rate": len(novel) / len(produced),
        "uniqueness_rate": len(set(produced)) / len(produced),
        "over_length": sum(1 for n in produced if len(n) > max_length),
        "length": {
            "min": min(lengths),
            "max": max(lengths),
            "mean": sum(lengths) / len(lengths),
        },
        "samples": produced[:20],
    }
    cost = cluster_rejection_cost(
        generator, count, algorithm, max_length, min_probability
    )
    if cost is not None:
        report["cluster_rejection_rate"] = cost
    if probs:
        ordered = sorted(probs)
        report["probability"] = {
            "min": ordered[0],
            "median": ordered[len(ordered) // 2],
            "max": ordered[-1],
            "geometric_mean": math.exp(sum(math.log(p) for p in probs) / len(probs)),
        }
    return report


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------


def build_verdict(structure: dict, curve: Sequence[dict], gen: dict, args) -> dict:
    checks = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    uni_cov = structure["unigram_coverage"]
    big_cov = structure["bigram_coverage"]
    check(
        "unigram coverage",
        uni_cov >= args.target_unigram_coverage,
        f"{uni_cov:.3f} vs target {args.target_unigram_coverage:.2f}",
    )
    check(
        "bigram coverage",
        big_cov >= args.target_bigram_coverage,
        f"{big_cov:.3f} vs target {args.target_bigram_coverage:.2f}",
    )

    my = marginal_yield(curve)
    if my is not None:
        check(
            "saturation",
            my <= args.saturation_yield,
            f"{my:.1f} new syllables per 50 names "
            f"(saturated at <= {args.saturation_yield:.0f})",
        )

    if gen.get("produced"):
        check(
            "novelty",
            gen["novelty_rate"] >= args.min_novelty,
            f"{gen['novelty_rate']:.1%} vs target {args.min_novelty:.0%}",
        )
        check(
            "uniqueness",
            gen["uniqueness_rate"] >= args.min_uniqueness,
            f"{gen['uniqueness_rate']:.1%} vs target {args.min_uniqueness:.0%}",
        )
        check(
            "yield",
            gen["produced"] >= 0.95 * gen["requested"],
            f"{gen['produced']}/{gen['requested']} names produced at threshold "
            f"{args.min_probability:g}",
        )

    check(
        "no duplicate names",
        structure.get("duplicate_count", 0) == 0,
        f"{structure.get('duplicate_count', 0)} duplicate(s)",
    )

    passed = sum(1 for c in checks if c["pass"])
    if passed == len(checks):
        status = "READY"
    elif passed >= len(checks) - 1:
        status = "NEARLY"
    else:
        status = "NEEDS WORK"

    return {"status": status, "passed": passed, "total": len(checks), "checks": checks}


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render(report: dict, args) -> None:
    s = report["structure"]
    curve = report["saturation_curve"]
    v = report["verdict"]

    print(f"=== Corpus Report: {report['source']} ===")
    print()
    print("Structure")
    print(f"  Names                   {s['total_names']}")
    print(
        f"  Unique syllables        {s['unique_syllables']} "
        f"({s['syllable_tokens']} tokens)"
    )
    print(f"  Unique syllable pairs   {s['unique_bigrams']}")
    print(f"  Distinct name openings  {s['distinct_initial_syllables']}")
    print(f"  Distinct name endings   {s['distinct_final_syllables']}")
    print(
        f"  Name length             {s['name_length']['min']}-{s['name_length']['max']}"
        f" (mean {s['name_length']['mean']:.1f})"
    )
    print(
        f"  Syllables per name      {s['syllables_per_name']['min']}-"
        f"{s['syllables_per_name']['max']} (mean {s['syllables_per_name']['mean']:.2f})"
    )
    if s.get("duplicate_count"):
        print(f"  Duplicates              {s['duplicate_count']}  <-- remove these")
    print()

    print("Coverage  (probability the next name adds nothing new)")
    print(
        f"  Unigram   {s['unigram_coverage']:.3f}   "
        f"{s['unigram_hapax']} syllables seen only once"
    )
    print(
        f"  Bigram    {s['bigram_coverage']:.3f}   "
        f"{s['bigram_hapax']} pairs seen only once"
    )
    print(
        f"  Richness  {s['unique_syllables']} observed / "
        f"{s['unigram_chao1']:.0f} estimated (Chao1) - "
        f"{max(0, s['unigram_chao1'] - s['unique_syllables']):.0f} syllables of this "
        f"style still unseen"
    )
    print()

    if curve:
        print("Saturation")
        print(
            f"  {'names':>7}  {'syllables':>10}  {'pairs':>7}  "
            f"{'uni cov':>8}  {'bi cov':>7}"
        )
        for row in curve:
            print(
                f"  {row['names']:>7}  {row['unique_syllables']:>10.0f}  "
                f"{row['unique_bigrams']:>7.0f}  {row['unigram_coverage']:>8.3f}  "
                f"{row['bigram_coverage']:>7.3f}"
            )
        my = marginal_yield(curve)
        if my is not None:
            print(f"  Marginal yield: {my:.1f} new syllables per 50 names added")
        print()

    print("Sizing")
    for label, key in (("unigram", "unigram"), ("bigram", "bigram")):
        rec = report["recommendation"][key]
        if rec["achieved"] >= rec["target"]:
            print(
                f"  {label:<8} target {rec['target']:.2f} met at "
                f"{s['total_names']} names"
            )
        elif rec.get("needed") is None:
            note = rec.get("note", "could not fit a reliable curve")
            print(f"  {label:<8} target {rec['target']:.2f} not met - {note}")
        else:
            qualifier = (
                " (extrapolated - re-measure as you grow)"
                if rec["extrapolated"]
                else ""
            )
            print(
                f"  {label:<8} target {rec['target']:.2f} needs ~{rec['needed']} names "
                f"(+{rec['additional']}){qualifier}"
            )
    print()

    g = report["generation"]
    if g.get("produced"):
        print(
            f"Generation  ({g['algorithm']}, {g['produced']}/{g['requested']} produced)"
        )
        print(f"  Novelty      {g['novelty_rate']:.1%}  (not already in corpus)")
        print(f"  Uniqueness   {g['uniqueness_rate']:.1%}  (distinct within the batch)")
        print(
            f"  Length       {g['length']['min']}-{g['length']['max']} "
            f"(mean {g['length']['mean']:.1f})"
        )
        if "cluster_rejection_rate" in g:
            print(
                f"  Phonotactics {g['cluster_rejection_rate']:.1%} of raw candidates "
                f"rejected by the corpus-derived cluster rule"
            )
        if "probability" in g:
            p = g["probability"]
            print(
                f"  Probability  geo-mean {p['geometric_mean']:.2e}  "
                f"median {p['median']:.2e}"
            )
        print(f"  Samples      {', '.join(g['samples'][:12])}")
    else:
        print(
            f"Generation  ({g['algorithm']}) produced nothing - "
            f"threshold {args.min_probability:g} may be too strict for this corpus"
        )
    print()

    print(f"Verdict: {v['status']}  ({v['passed']}/{v['total']} checks)")
    for c in v["checks"]:
        print(f"  [{'x' if c['pass'] else ' '}] {c['name']:<20} {c['detail']}")

    if args.verbose and report.get("duplicates"):
        print()
        print("Duplicate names:")
        for _, names in sorted(report["duplicates"].items()):
            print(f"  {names[0]}  (x{len(names)})")

    if args.verbose and report.get("top_syllables"):
        print()
        print("Most common syllables:")
        for syl, n in report["top_syllables"]:
            print(f"  {syl:<12} {n}")


def render_summary_row(report: dict) -> str:
    s = report["structure"]
    v = report["verdict"]
    g = report["generation"]
    novelty = f"{g['novelty_rate']:.0%}" if g.get("produced") else "-"
    return (
        f"{report['source'][:34]:<34} {s['total_names']:>6} {s['unique_syllables']:>7} "
        f"{s['unigram_coverage']:>8.3f} {s['bigram_coverage']:>7.3f} {novelty:>8} "
        f"{v['status']:>11}"
    )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def analyze(source: str, args) -> dict:
    segmenter = (
        JapaneseNameSegmenter()
        if args.segmenter == "japanese"
        else FantasyNameSegmenter()
    )
    generator = Generator(source, segmenter=segmenter, rng=random.Random(args.seed))
    seqs = syllable_lists(generator)

    structure = structure_report(generator, seqs)
    duplicates = find_duplicates(generator)
    structure["duplicate_count"] = sum(len(v) - 1 for v in duplicates.values())

    curve = saturation_curve(seqs, trials=args.trials, rng=random.Random(args.seed))
    gen = generation_report(
        generator,
        args.count,
        args.algorithm,
        args.max_length,
        args.min_probability,
    )

    report = {
        "source": source,
        "structure": structure,
        "duplicates": duplicates,
        "saturation_curve": curve,
        "recommendation": {
            "unigram": recommend_size(
                curve,
                structure["total_names"],
                "unigram_coverage",
                args.target_unigram_coverage,
            ),
            "bigram": recommend_size(
                curve,
                structure["total_names"],
                "bigram_coverage",
                args.target_bigram_coverage,
            ),
        },
        "generation": gen,
    }
    report["verdict"] = build_verdict(structure, curve, gen, args)

    if args.verbose:
        report["top_syllables"] = unigram_counts(seqs).most_common(args.top_syllables)

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure corpus quality and estimate the corpus size a style needs",
        prog="corpus_test",
        epilog=format_available_lists(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-l",
        "--list",
        dest="source",
        help="Name list identifier (e.g. 'generic-fantasy') or path to a YAML file",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Test every built-in name list and print a ranked summary table",
    )
    parser.add_argument(
        "-s",
        "--segmenter",
        choices=["fantasy", "japanese"],
        default="fantasy",
        help="Segmentation method (default: fantasy)",
    )
    parser.add_argument(
        "-a",
        "--algorithm",
        choices=["simple", "bayesian", "very_simple"],
        default="bayesian",
        help="Generation algorithm to exercise (default: bayesian)",
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=200,
        help="Names to generate for the quality sample (default: 200)",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=15,
        help="Maximum generated name length (default: 15)",
    )
    parser.add_argument(
        "--min-probability",
        type=float,
        default=1e-8,
        help="Bayesian minimum probability threshold (default: 1e-8)",
    )
    parser.add_argument(
        "--target-unigram-coverage",
        type=float,
        default=DEFAULT_TARGET_UNIGRAM_COVERAGE,
        help=f"Target syllable coverage (default: {DEFAULT_TARGET_UNIGRAM_COVERAGE})",
    )
    parser.add_argument(
        "--target-bigram-coverage",
        type=float,
        default=DEFAULT_TARGET_BIGRAM_COVERAGE,
        help=(
            f"Target syllable-pair coverage (default: {DEFAULT_TARGET_BIGRAM_COVERAGE})"
        ),
    )
    parser.add_argument(
        "--min-novelty",
        type=float,
        default=DEFAULT_MIN_NOVELTY,
        help=f"Minimum acceptable novelty rate (default: {DEFAULT_MIN_NOVELTY})",
    )
    parser.add_argument(
        "--min-uniqueness",
        type=float,
        default=DEFAULT_MIN_UNIQUENESS,
        help=f"Minimum acceptable uniqueness rate (default: {DEFAULT_MIN_UNIQUENESS})",
    )
    parser.add_argument(
        "--saturation-yield",
        type=float,
        default=DEFAULT_SATURATION_YIELD,
        help="New syllables per 50 names at which a corpus counts as saturated "
        f"(default: {DEFAULT_SATURATION_YIELD})",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=12,
        help="Subsamples averaged per point on the saturation curve (default: 12)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0xC0FFEE,
        help="Seed for subsampling, so reports are reproducible",
    )
    parser.add_argument(
        "--top-syllables",
        type=int,
        default=20,
        help="Syllables to list in verbose mode (default: 20)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detail")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")

    args = parser.parse_args()

    if not args.source and not args.all:
        parser.error("one of --list or --all is required")

    if args.all:
        reports = []
        for name in get_available_name_lists():
            seg = "japanese" if name.startswith("japanese") else args.segmenter
            saved, args.segmenter = args.segmenter, seg
            try:
                reports.append(analyze(name, args))
            except Exception as exc:  # noqa: BLE001 - a bad list should not abort the sweep
                print(f"  {name}: FAILED - {exc}", file=sys.stderr)
            finally:
                args.segmenter = saved

        if args.json:
            print(json.dumps(reports, indent=2, default=str))
            return 0

        print(
            f"{'corpus':<34} {'names':>6} {'syls':>7} {'uni cov':>8} {'bi cov':>7} "
            f"{'novelty':>8} {'verdict':>11}"
        )
        print("-" * 86)
        for r in sorted(reports, key=lambda r: -r["structure"]["bigram_coverage"]):
            print(render_summary_row(r))
        return 0

    try:
        report = analyze(args.source, args)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print(file=sys.stderr)
        print(format_available_lists(), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        render(report, args)

    return 0 if report["verdict"]["status"] != "NEEDS WORK" else 2


if __name__ == "__main__":
    sys.exit(main())
