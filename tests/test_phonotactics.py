"""Golden-list tests for the corpus-derived phonotactics rule.

The rule is calibrated from data (see ``tools/cluster_report.py`` and
``docs/cluster-baseline.md``), but a rule that only lives in a measurement will
drift silently. This file pins the intent with named cases, each carrying the
reason it belongs on its side -- particularly ``Ragnrikr``, whose acceptance is
the whole argument for a decomposable rule and is the part most likely to be
forgotten.
"""

from pathlib import Path

import pytest
import yaml

from wyrdbound_rng import Generator

GOLDEN_PATH = Path(__file__).parent / "data" / "phonotactics_golden.yaml"


def _load():
    with GOLDEN_PATH.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data["accept"], data["reject"]


ACCEPT, REJECT = _load()
_GENERATORS: dict[str, Generator] = {}


def _generator(corpus):
    if corpus not in _GENERATORS:
        _GENERATORS[corpus] = Generator(corpus)
    return _GENERATORS[corpus]


@pytest.mark.parametrize("entry", ACCEPT, ids=[entry["name"] for entry in ACCEPT])
def test_golden_accept(entry):
    generator = _generator(entry["corpus"])
    name = entry["name"]
    assert generator._is_pronounceable(name) is True, (
        f"{name} ({entry['corpus']}) should be accepted: {entry['reason']}"
    )


@pytest.mark.parametrize("entry", REJECT, ids=[entry["name"] for entry in REJECT])
def test_golden_reject(entry):
    generator = _generator(entry["corpus"])
    name = entry["name"]
    assert generator._is_pronounceable(name) is False, (
        f"{name} ({entry['corpus']}) should be rejected: {entry['reason']}"
    )


def test_golden_list_is_substantial():
    """T-010c: at least 20 entries across at least four corpora."""
    entries = ACCEPT + REJECT
    assert len(entries) >= 20
    corpora = {entry["corpus"] for entry in entries}
    assert len(corpora) >= 4, corpora


def test_every_entry_carries_a_reason():
    for entry in ACCEPT + REJECT:
        assert entry.get("reason"), entry["name"]
        assert entry.get("corpus"), entry["name"]
