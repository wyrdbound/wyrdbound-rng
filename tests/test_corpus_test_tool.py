"""Unit tests for the corpus quality tool.

``tools/corpus_test.py`` is a quality gate, so it needs to be as trustworthy as
the thing it measures. The estimators are tested against hand-computable
inputs, not against corpora; the smoke tests only assert the CLI contract.
"""

import json
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import build_corpora  # noqa: E402
import corpus_test  # noqa: E402

from wyrdbound_rng import Generator  # noqa: E402


class TestGoodTuringCoverage:
    def test_known_f1_and_token_count(self):
        # 3 types: one seen once, one twice, one three times -> T=6, f1=1.
        freqs = Counter({"a": 1, "b": 2, "c": 3})
        coverage, f1, f2, total = corpus_test.good_turing_coverage(freqs)
        assert (f1, f2, total) == (1, 1, 6)
        assert coverage == 1.0 - (1 / 6)

    def test_empty_table(self):
        coverage, f1, f2, total = corpus_test.good_turing_coverage(Counter())
        assert (coverage, f1, f2, total) == (0.0, 0, 0, 0)

    def test_all_hapax_gives_zero_coverage(self):
        freqs = Counter({"a": 1, "b": 1, "c": 1})
        coverage, f1, f2, total = corpus_test.good_turing_coverage(freqs)
        assert (f1, total) == (3, 3)
        assert coverage == 0.0


class TestChao1:
    def test_known_f1_and_f2(self):
        # S_obs=3, f1=1, f2=1 -> 3 + 1/(2*1) = 3.5
        freqs = Counter({"a": 1, "b": 2, "c": 3})
        assert corpus_test.chao1(freqs) == 3.5

    def test_f2_zero_branch(self):
        # S_obs=3, f1=3, f2=0 -> 3 + 3*2/2 = 6.0
        freqs = Counter({"a": 1, "b": 1, "c": 1})
        assert corpus_test.chao1(freqs) == 6.0

    def test_no_hapax_falls_back_to_s_obs(self):
        freqs = Counter({"a": 2, "b": 2})
        assert corpus_test.chao1(freqs) == 2.0


class TestFitPowerLaw:
    def test_recovers_known_parameters(self):
        a, b = 4.0, 1.5
        xs = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0]
        ys = [a * (x**-b) for x in xs]
        fit = corpus_test.fit_power_law(xs, ys)
        assert fit is not None
        got_a, got_b = fit
        assert got_a == pytest.approx(a, rel=1e-6)
        assert got_b == pytest.approx(b, rel=1e-6)

    def test_too_few_points_returns_none(self):
        assert corpus_test.fit_power_law([1.0, 2.0], [1.0, 0.5]) is None

    def test_non_positive_y_is_dropped(self):
        xs = [1.0, 2.0, 4.0, 8.0, 16.0]
        ys = [4.0, 0.0, 1.0, 0.5, 0.25]
        # Only three usable points remain; still fits or returns None cleanly.
        fit = corpus_test.fit_power_law(xs, ys)
        assert fit is None or isinstance(fit, tuple)


class TestTrim:
    """``trim`` and ``finalise`` live in the corpus builder; the tool consumes
    their output rather than reimplementing them, so they are tested there."""

    def _names(self, n=500):
        return [f"Name{i:04d}" for i in range(n)]

    def test_is_deterministic(self):
        names = self._names()
        assert build_corpora.trim(names, 100) == build_corpora.trim(names, 100)

    def test_preserves_protected_names(self):
        names = self._names() + ["Protected"]
        kept = build_corpora.trim(names, 100, keep=["Protected"])
        assert "Protected" in kept

    def test_keeps_at_most_target_plus_protected(self):
        names = self._names()
        kept = build_corpora.trim(names, 100)
        assert len(kept) <= 100


class TestGenerationReport:
    def _report(self, seed, count=50):
        # The report is reproducible because the generator is given an injected
        # random.Random(seed), not because global state is seeded.
        generator = Generator("ancestry-dwarf-male", rng=random.Random(seed))
        return corpus_test.generation_report(generator, count, "bayesian", 11, 1e-8)

    def test_seeded_report_is_reproducible(self):
        first = self._report(7)
        second = self._report(7)
        assert first["samples"] == second["samples"]
        assert first["novelty_rate"] == second["novelty_rate"]

    def test_uses_injected_rng_not_global_state(self, monkeypatch):
        # The report must not reach into the global random module: T-007 gave
        # the generator a real seam.
        def explode(*args, **kwargs):
            raise AssertionError("global random.seed was called")

        monkeypatch.setattr(random, "seed", explode)
        report = self._report(7, count=20)
        assert report["produced"] > 0


class TestCliContract:
    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(TOOLS_DIR / "corpus_test.py"), *args],
            capture_output=True,
            text=True,
        )

    def test_json_output_parses_and_has_documented_keys(self):
        result = self._run("--list", "ancestry-dwarf-male", "--json")
        # Exit 2 means "NEEDS WORK" and is a legitimate verdict, not a tool
        # failure; the CLI contract here is parseable JSON on stdout.
        assert result.returncode in (0, 2), result.stderr
        report = json.loads(result.stdout)
        for key in (
            "source",
            "structure",
            "saturation_curve",
            "recommendation",
            "generation",
            "verdict",
        ):
            assert key in report, key
        assert report["structure"]["unigram_coverage"] >= 0.93

    def test_missing_list_exits_one(self):
        result = self._run("--list", "not-a-real-list", "--json")
        assert result.returncode == 1

    def test_all_completes_without_raising(self):
        result = self._run("--all", "--count", "20")
        assert result.returncode == 0, result.stderr
        assert "ancestry-dwarf-male" in result.stdout
