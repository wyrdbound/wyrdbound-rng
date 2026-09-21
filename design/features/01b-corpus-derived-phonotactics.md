# 01b — Corpus-Derived Phonotactics

**Status:** Not started
**Prerequisite features:** `01-corpus-quality-and-name-lists.md` complete (T-001
through T-010 landed, `9e3a83e`…`9b48053`)
**New capability:** **A validity rule the corpus writes, not one I guessed.**
`_is_pronounceable` stops counting consonants and starts asking what the corpus
actually permits.

Read `01`'s *Working rules* first — they apply unchanged. **One task per run.**

---

## Why this feature exists

T-003 shipped a rule I invented at a keyboard: *reject four or more consecutive
consonants*. Testing `ancestry-dwarf-male` turned up `Ragnrikr`, which prompted
the question of whether `gnr` is legal — and answering it properly exposed three
problems at once.

### The shipped rule is now a no-op

Measured over 400 Bayesian generations per corpus at `max_len=11`, seeded, on
current `main`:

| corpus | rejected by shipped rule |
|---|---:|
| all ten `ancestry-*` corpora | **0.0%** |

Not "low" — zero, everywhere. T-004's budget-aware generation and T-005's
removal of the simple-algorithm fallback eliminated the four-consonant names by
other means. The rule is dead weight that looks like a safety net, which is
worse than no safety net, because the next person to loosen T-004 will not know
the guard behind it has been inert for months.

### The tests encode the rule's weakness rather than the intent

`tests/test_generator.py:170`:

```python
assert self._is_pronounceable("Hrgils") is True
assert self._is_pronounceable("Svgest") is True
```

T-003's own acceptance criterion said *"`Hrgils`, `Svgest`, `Thjglamr` are
rejected."* Two of those three are asserted **accepted**. The implementation and
the test agree with each other and both contradict the task that commissioned
them: `hrg` is three consonants, so a four-consonant rule waves it through, and
the test was written to match what the code did.

This is the failure mode Working Rule 6 exists to catch, and it got through
anyway because the test was new rather than pre-existing. Worth noting in the
retro.

### The rule is measuring the wrong unit

The segmenter's "syllables" are not phonological syllables. It emits
nucleus-less fragments:

```
Hrafn      ('h','','r')  ('','a','')   ('f','','n')
Hrgils     ('h','','r')  ('g','i','')  ('l','','s')
Ragnvindr  ('r','a','g') ('n','','')   ('v','i','n')  ('d','','r')
```

`Ragn` is split across `('r','a','g')` and `('n','','')`. So any rule built on
"coda of syllable *N* plus onset of syllable *N+1*" mostly never fires — the
orphan fragments have empty `final`, so the junction test is skipped. Both
candidate rules I prototyped against this decomposition accepted `Hrgils`.

The unit that actually matters is the **inter-nuclear consonant cluster**: the
run of consonants between one vowel and the next, plus the word-initial and
word-final runs. That is what a reader stumbles over, and it is computable
directly from the name without consulting the segmenter at all.

### What the corpus says about `Ragnrikr`

`gnr` occurs nowhere in `ancestry-dwarf-male`. But `gnv` does, in `Ragnvindr`,
and the sagas have `Ragnvaldr` and `Ragnhildr`; the continental cognate
`Raginrich` is attested. So `Ragnrikr` is a legitimate novel combination — legal
by the corpus's own pattern, absent from its surface.

That distinction is the whole design question for this feature, and it is a
**policy choice, not a fact**:

- A **strict whole-cluster whitelist** (the cluster must have been observed)
  rejects `Ragnrikr`. It also rejects between 5.8% and **64.5%** of output
  depending on corpus — `ancestry-goblin-male` has a small junction inventory
  and almost every generated cluster is unseen. Unusable as-is.
- A **decomposable rule** (the cluster splits into an attested coda plus an
  attested onset) accepts `Ragnrikr` and rejects 0–1.8%. Close to permissive.

Neither number is the answer yet, because both were measured against an
inventory built from the segmenter's broken decomposition. T-010a rebuilds the
inventory correctly before anything is chosen. **The point of this feature is to
stop guessing thresholds**, so measurement is task one and the rule is task two.

### What this feature does not do

No change to generation, corpora, or the segmenter. `_is_pronounceable` is the
only behavior that changes. If the calibrated rule turns out to reject more than
a few percent on any corpus, that is a finding to report, not a reason to edit
the corpus.

---

## Task list

Task ids are suffixed per the inserted-feature convention (`01`'s last task was
T-010). Never renumber an id that has appeared in a commit message.

---

### T-010a — Measure first: the inter-nuclear cluster inventory

**Goal:** Know what the corpora actually contain before writing a rule about it.
**No behavior change in this task.**

**Files:** `tools/cluster_report.py` (new)

**Steps**

1. For a given corpus, extract every **inter-nuclear consonant cluster** by
   position class:
   - `initial` — consonants before the first vowel
   - `medial` — a run between two vowels
   - `final` — consonants after the last vowel

   Use a regex over the name (`[^aeiouy]+`, `y` as a vowel). Do **not** use the
   segmenter; §"wrong unit" above is why.
2. Report per corpus: the inventory size per position class, the full medial
   inventory with frequencies, and the count of clusters occurring exactly once
   (the hapaxes — a whitelist built on those is a whitelist built on noise).
3. Report the same for 400 seeded generations, and the set difference: which
   generated clusters are unseen in the corpus, with example names.
4. Run it across all ten `ancestry-*` corpora plus `generic-fantasy` as a
   control, and commit the output as `docs/cluster-baseline.md`.

**Notes**

- The control matters. `generic-fantasy` has one syllable per name and will have
  a near-useless cluster inventory; if the rule behaves sanely there, it will
  behave sanely on a corpus that has not been curated.
- Expect the goblin corpora to look different from the rest. Their inventory is
  deliberately small (~60 syllables), which is why the strict variant rejected
  64.5% of `ancestry-goblin-male`. Do not treat that as a bug in the corpus.

**Acceptance criteria**

- `docs/cluster-baseline.md` committed, covering eleven corpora.
- `ruff` clean. No change to `src/`.

---

### T-010b [TDD] — Replace the consonant-run heuristic

**Goal:** `_is_pronounceable` asks the corpus instead of counting letters.

**Files:** `src/wyrdbound_rng/generator.py`, `tests/test_generator.py`

**Steps**

1. **Fix the contradicting tests first**, and observe them fail:
   - `Hrgils` and `Svgest` must be **rejected**. These currently assert `True`
     at `tests/test_generator.py:170-171`. Changing them is sanctioned by this
     task; note in the commit body that they contradicted T-003's acceptance
     criterion.
   - `Hrafn`, `Thorbrandr`, `Steingrimr`, `Ragnvindr` must be accepted.
   - `Ragnrikr` must be accepted — it is a legal novel combination, and a rule
     that rejects it is over-fitted to the corpus surface.
   - `Gaukglamr`, `Kjlaugr`, `Fjglaugr`, `Thjglamr` must be rejected.
2. Build the cluster inventory at load time, from the loaded corpus, using
   T-010a's extraction. Cache it on the `Generator`.
3. Implement the **decomposable** rule: a generated cluster is legal if it was
   observed in the corpus at that position class, **or** it splits at some point
   into a suffix that occurs as an attested coda and a prefix that occurs as an
   attested onset. Reject otherwise.
4. Keep a length backstop. A cluster longer than the longest observed in the
   corpus is rejected regardless of decomposability — decomposition alone will
   happily accept an arbitrarily long chain of legal pieces.
5. Preserve the existing signature. `_is_pronounceable(self, name)` stays a
   method taking a string; all four call sites in `generator.py` are unchanged.

**Notes**

- `y` is a vowel here, or every Welsh name in `ancestry-elf-*` fails.
- A corpus with fewer than N names has too sparse an inventory to derive a rule
  from. Pick a floor, and below it fall back to the current four-consonant
  heuristic rather than rejecting everything. `generic-fantasy` from T-010a will
  tell you where that floor sits.

**Acceptance criteria**

- Every name in the two probe lists above lands on the right side.
- `python -m pytest tests/` green; `ruff` clean.
- Version bumped; `CHANGELOG.md` entry under **Changed**.

---

### T-010c [TDD] [P] — Lock the rule with a golden list

**Goal:** The next person to touch this cannot quietly re-break it.

**Files:** `tests/data/phonotactics_golden.yaml` (new),
`tests/test_phonotactics.py` (new)

**Steps**

1. A YAML file of `accept:` and `reject:` names, each with a one-line reason and
   the corpus it came from. Seed it with every probe name in this document plus
   anything T-010a's set-difference surfaced.
2. A test that asserts each one, naming the offending entry on failure.
3. **Include `Ragnrikr` with its reason recorded** — "legal novel combination;
   `gnv` attested in `Ragnvindr`, cognate `Raginrich`". The argument for
   accepting it is the part that will be forgotten.

**Acceptance criteria**

- The golden list has at least 20 entries across at least four corpora.
- `python -m pytest tests/` green; `ruff` clean.

---

### T-010d — Calibrate, and wire into the corpus regression tests

**Goal:** Know the cost of the rule on every corpus, and fail loudly if it
drifts.

**Files:** `tests/test_ancestry_corpora.py`, `tools/corpus_test.py`

**Steps**

1. Measure the rejection rate of the T-010b rule over 400 seeded generations per
   corpus. Record all ten in the commit body and in `docs/cluster-baseline.md`.
2. Add a per-corpus ceiling to `tests/test_ancestry_corpora.py`: the rule may
   reject no more than the measured rate plus headroom. Set the constant from
   the measurement, with a comment naming the date and the commit.
3. Add the rejection rate to `corpus_test.py`'s report as a line under
   **Generation**, so a corpus author sees what the rule costs them.
4. **If any corpus exceeds a few percent, stop and report it** before setting
   its ceiling. A high rate means either the rule is over-fitted or that corpus's
   inventory is too small to derive one from — both are findings, and neither is
   fixed by raising the number until it passes.

**Acceptance criteria**

- Ten measured rates recorded, none silently accepted above a few percent.
- `python -m pytest tests/` green; `ruff` clean.

---

### T-010e — Documentation

**Goal:** The record says what the rule is and why `Ragnrikr` is allowed.

**Files:** `CORPUS_REPORT.md`, `README.md`, `CHANGELOG.md`,
`design/features/01-corpus-quality-and-name-lists.md`

**Steps**

1. `CORPUS_REPORT.md`: a subsection under §5 stating the rule, its measured cost
   per corpus, and the `Ragnrikr` worked example. It is the clearest case of
   "legal but unattested" in the whole corpus set and is worth keeping.
2. `README.md`: document that generated names are validated against a
   corpus-derived cluster inventory, and that a small corpus falls back to the
   heuristic.
3. Add a closing note to `01`'s T-003 — do not edit its steps or criteria, the
   document is history — recording that the rule it specified was superseded
   here, and that its shipped tests contradicted its own acceptance criteria.
4. `CHANGELOG.md` entry.

**Acceptance criteria**

- `01` is annotated, not rewritten.
- `python -m pytest tests/` green; `ruff` clean.

---

## Demo

Extend `demos/name_generation_demo.py` rather than adding a second demo. Add a
column showing, for each generated name, the inter-nuclear clusters it contains
and whether each was attested, decomposed, or would have been rejected. Twenty
names from one corpus is enough to make the rule legible.

Still ends `DEMO OK: name_generation`.

---

## Verification script

1. `python -m pytest tests/ -q`
2. Expect: green, including `test_phonotactics.py`.
3. `python tools/cluster_report.py --list ancestry-dwarf-male`
4. Expect: a medial cluster inventory; `gnv` present, `gnr` absent.
5. `python -c "import sys; sys.path.insert(0,'src'); from wyrdbound_rng import Generator; g=Generator('ancestry-dwarf-male'); print([ (n, g._is_pronounceable(n)) for n in ['Ragnrikr','Ragnvindr','Hrgils','Svgest','Gaukglamr','Hrafn'] ])"`
6. Expect: `Ragnrikr` True, `Ragnvindr` True, `Hrafn` True; `Hrgils`, `Svgest`,
   `Gaukglamr` False.
7. `wyrdbound-rng --list ancestry-dwarf-male -n 30 -a bayesian --length 11`
8. Expect: thirty names, none with a cluster that makes you stop and re-read.
   `Ragnrikr`-shaped names are fine and expected.
9. `wyrdbound-rng --list ancestry-goblin-male -n 30 -a bayesian --length 9`
10. Expect: thirty names. The goblin register is *meant* to be harsh — `Skarguk`,
    `Thrakaz`, `Grugrit` are correct output, not failures. If the rule has
    flattened goblin toward the other ancestries, that is a regression; mark it.
11. `python tools/corpus_test.py --list ancestry-elf-female`
12. Expect: a **Generation** block that now includes a cluster-rejection rate.
13. `python demos/name_generation_demo.py --seed 1`
14. Expect: `DEMO OK: name_generation`, with the cluster column populated.

**Signed off:** _pending_

---

## Feature acceptance

**Capability:** name validity is derived from the corpus rather than from a
hardcoded consonant count, with the cost of the rule measured on every corpus.

**Gate:**

- [ ] `python -m pytest tests/` green; `ruff check` and `ruff format --check` clean
- [ ] CI green
- [ ] `docs/cluster-baseline.md` committed for eleven corpora
- [ ] The two tests contradicting T-003's acceptance criteria are corrected
- [ ] `Hrgils`, `Svgest`, `Gaukglamr`, `Kjlaugr` rejected; `Ragnrikr`,
      `Ragnvindr`, `Hrafn`, `Thorbrandr` accepted
- [ ] Golden list of ≥20 entries, `Ragnrikr` among them with its reason
- [ ] Rejection rate measured on all ten corpora and ceilinged in the suite
- [ ] Goblin output is still recognisably goblin
- [ ] `01`'s T-003 annotated as superseded, not rewritten
- [ ] Demo green
- [ ] Verification script signed off
