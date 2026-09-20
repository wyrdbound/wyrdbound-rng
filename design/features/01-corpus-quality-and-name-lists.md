# 01 — Corpus Quality, Length Handling, and Ancestry Name Lists

**Status:** Not started
**Prerequisite features:** none — first feature document in this repository
**New capability:** **Generated names you would actually ship.** The library
stops mangling its own output, stops chaining syllables past the length cap, and
gains ten measured ancestry corpora plus the tooling to prove a corpus is good.

Read the *Working rules* section below before starting. **One task per run.**

---

## Why this feature exists

`bea3dc4` landed ten ancestry name corpora, a corpus quality tool
(`tools/corpus_test.py`) and the generator that builds the corpora
(`tools/build_corpora.py`). Measuring those corpora exposed a set of defects in
the *generator*, not the data — and the largest of them silently damages roughly
a third of everything the library emits.

This feature fixes the generator, settles the duplicated data directory, and
puts the new tooling under test.

### The defect that matters most

`Generator._remove_repetitions` deletes letters rather than collapsing runs:

```python
result = re.sub(r"ll", "", name)    # deletes "ll" outright
result = re.sub(r"nn", "", result)  # deletes "nn" outright
```

It runs on every generated name in every algorithm. Measured over 500 generated
names per corpus at `max_len=11`:

| corpus | names altered | examples |
|---|---:|---|
| `ancestry-halfling-female` | **55%** | `Sibella → Sibea`, `Millisa → Miisa` |
| `ancestry-dwarf-female` | 40% | `Ragnafinn → Ragnafi`, `Hakfinna → Hakfia` |
| `ancestry-dwarf-male` | 29% | `Torfinnr → Torfir`, `Gunnasul → Guasul` |

It also affects 7.5% of corpus names at comparison time, so
`name_exists_in_corpus` is matching mangled strings against clean ones and the
novelty metric is wrong in the corpus report.

Every "truncation artifact" in `CORPUS_REPORT.md` §5 traces here — `Svgestke` is
`Gestkell` with its `ll` deleted, `Hjstei` is `Hjsteinn`. This is almost
certainly a mistranslation of a Ruby `gsub` that collapsed runs. It is a
one-line fix and it is T-002 for a reason.

### The other three

**Junctions are never validated.** The segmenter emits onset-only syllables —
`Hrafn → ['hr','a','fn']`, `Svanmodr → ['sv','an','mo','dr']` — so `hr`, `sv`,
`thj`, `kj` are inventory items, and **19.1% of Bayesian start probability mass
sits on a syllable with no vowel**. That is correct before a vowel (`hr`+`afn` =
Hrafn) and broken before a consonant (`hr`+`gils` = Hrgils). It is a junction
rule, not a reason to drop those syllables.

**Length control is open-loop.** `max_syllables = max(2, max_len // 3)`
hardcodes three characters per syllable; the ancestry corpora average **2.45**.
The model generates a whole sequence, joins it, checks the length, and discards
the work on a miss — rejection sampling with no feedback, up to 500 times.

**The fallback runs the worst algorithm.** After those 500 attempts,
`_generate_name_bayesian` calls `_generate_name_simple`, which has none of the
quality controls. `best_name` is only populated when a candidate came in *under*
length but *below* threshold, so a run where everything was too long falls
through to the crudest generator available. The hardest cases get the worst
answer.

### The duplicated data directory

`data/` and `src/wyrdbound_rng/data/` are byte-identical, both tracked, 22 files
each. The investigation:

- `[tool.setuptools.package-data] wyrdbound_rng = ["data/*.yaml"]` packages
  `src/wyrdbound_rng/data/`. The built wheel confirms it: every data file is at
  `wyrdbound_rng/data/*.yaml`. **This is the one that ships.**
- `MANIFEST.in`'s `recursive-include data *.yaml` adds the root copy to the
  **sdist only**, where it lands at the archive root and is never importable.
  It does nothing for any installed user.
- `name_list_resolver.get_data_directory()` prefers the package directory and
  falls back to root `data/` "for development mode" — but the package directory
  is committed, so it always exists, so **the fallback is unreachable**.

Root `data/` is vestigial: a leftover from the move to a src-layout that nothing
except the tests and one CI workflow still points at. T-001 removes it.

Two alternatives were considered and rejected. *Keep root as the source and copy
at build time* needs a build hook and leaves editable installs reading a stale
copy. *Symlink* breaks on Windows and does not survive sdist packaging.

### What is already landed

Do not redo these. `bea3dc4` committed:

- the ten `data/ancestry-{dwarf,elf,halfling,human,goblin}-{male,female}.yaml`
  corpora, in both data directories
- `tools/corpus_test.py` — corpus coverage, saturation and sizing measurement
- `tools/build_corpora.py` — deterministic rebuild from name-element stock
- `CORPUS_REPORT.md` — method, measurements and findings

The `--json` stdout pollution reported in `CORPUS_REPORT.md` §5 **is already
fixed** on main by `58def61`; that section is wrong and T-010 corrects it.

### What this feature does not do

No new corpora beyond the ten. No new segmenter. No change to the YAML schema.
No API redesign — every change here is additive or behavior-preserving at the
call site, except `_remove_repetitions`, which is a bug fix that necessarily
changes output.

---

## Working rules

1. **One task per run.** Do not start the next.
2. **The suite is green at the end of every task.** `python -m pytest tests/`
   passes; `ruff check src/ tests/ tools/` and `ruff format --check src/ tests/
   tools/` are clean.
3. `[TDD]` tasks require the test written and **observed failing** first.
4. **Do not refactor outside the task's listed files.**
5. **Do not add dependencies.** The library's runtime deps are `PyYAML` only.
   If you think you need another, stop and ask.
6. **Never weaken or delete a passing test** to make a task pass. A test that
   contradicts intended new behavior is changed only by the task that says so,
   naming the reason.
7. **Bump `version` in `pyproject.toml`** on any task that changes behavior, and
   add a `CHANGELOG.md` entry. Semver, `0.x`, no major bump.
8. **One commit per task**, conventional style with the task id:
   `fix(rng): T-002 — collapse repeated letters instead of deleting them`.
9. **Determinism is a feature.** Anything that samples must be reproducible from
   a seed by the end of T-007.
10. **If a task is ambiguous, stop and ask** rather than guessing.

---

## Task list

`[TDD]` = test written and observed failing first. `[P]` = runnable in parallel
with others marked `[P]`.

---

### T-001 — One source of truth for built-in name data

**Goal:** Delete the duplicate. `src/wyrdbound_rng/data/` is the only data
directory.

**Files:** `data/` (removed), `MANIFEST.in`,
`src/wyrdbound_rng/name_list_resolver.py`, `tests/test_yaml_loader.py`,
`.github/workflows/cli-tools.yml`, `.github/copilot-instructions.md`

**Steps**

1. Confirm the two directories are still identical before deleting anything:
   `diff -rq data src/wyrdbound_rng/data` must print nothing. If it does not,
   **stop and ask** — someone has edited one copy only, and which one is
   authoritative is not yours to guess.
2. `git rm -r data/`.
3. Remove `recursive-include data *.yaml` from `MANIFEST.in`. The package data
   is already covered by `[tool.setuptools.package-data]`; this line only ever
   populated the sdist root.
4. Update the three relative paths in `tests/test_yaml_loader.py` to resolve the
   packaged directory rather than a path relative to the working directory.
   Use `get_data_directory()` so the test breaks loudly if resolution breaks,
   rather than hardcoding `src/wyrdbound_rng/data/…`.
5. Update the four `data/…` paths in `.github/workflows/cli-tools.yml`. That
   workflow currently guards each with `if [ -f … ]`, so it has been **silently
   skipping** these steps whenever the path was wrong — replace the guards with
   unguarded commands using built-in identifiers (`-l generic-fantasy`), so a
   broken resolution fails CI instead of passing it quietly.
6. Fix the tree diagram in `.github/copilot-instructions.md`, which documents
   both directories.
7. Decide the fallback in `get_data_directory()`. Prefer **replacing** the dead
   root-`data/` branch with an environment override:

   ```python
   override = os.environ.get("WYRDBOUND_RNG_DATA_DIR")
   if override and Path(override).is_dir():
       return override
   ```

   That gives the "development mode" intent a form that actually works, and lets
   a consumer (Ascension) point at its own corpora without a file path. If you
   prefer to simply delete the branch, that is acceptable — but do not leave
   unreachable code with a comment claiming it runs.

**Notes**

- `python -m build` then inspect the wheel: it must still contain twenty-two
  `wyrdbound_rng/data/*.yaml` entries. This is the check that proves the
  deletion was safe.

**Acceptance criteria**

- `git ls-files | grep -c '^data/'` returns 0.
- A freshly built wheel contains all twenty-two data files.
- `python -m pytest tests/` green; `ruff` clean.
- `wyrdbound-rng --list generic-fantasy -n 3` works from a directory that is not
  the repository root.

---

### T-002 [TDD] — Collapse repeated letters instead of deleting them

**Goal:** Stop destroying a third of all generated names. The highest-value
change in this feature.

**Files:** `src/wyrdbound_rng/generator.py`,
`tests/test_generator.py`

**Steps**

1. Tests first, in a new `TestRemoveRepetitions` class:
   - `Gestkell` survives intact; `Ketill`, `Gunnar`, `Finnr`, `Hallgrim`,
     `Gwenllian`, `Sibella` all survive intact. These are the regression cases —
     every one of them is currently mangled.
   - A triple run collapses to a double: `Styrrr → Styrr`, `Hallla → Halla`.
   - A double run is left alone: `Gunnar → Gunnar`.
   - The function is idempotent: applying it twice equals applying it once.
   - Observe them fail. Four of the six will.
2. Replace the body with a single substitution:

   ```python
   return re.sub(r"(.)\1{2,}", r"\1\1", name)
   ```

   This is what "remove repetitions" was always meant to mean. It also fixes
   `Styrrr`, which the current implementation does not touch at all because it
   only knows about `l` and `n`.
3. Re-run the full suite. Any test that depended on the old deletion behavior is
   asserting a bug — change it, and say so in the commit body.

**Notes**

- This changes the output of every algorithm for every corpus. That is the
  point, and it is why this task lands before the corpora are re-baselined in
  T-008.
- It also changes `name_exists_in_corpus` results, and therefore every novelty
  figure in `CORPUS_REPORT.md`. Do not update the report here; T-010 does it
  once, after all generator changes have landed.

**Acceptance criteria**

- All six regression names survive unmodified.
- `python -m pytest tests/` green; `ruff` clean.
- Version bumped, `CHANGELOG.md` entry under **Fixed**.

---

### T-003 [TDD] [P] — Reject unpronounceable syllable junctions

**Goal:** Stop emitting `Hrgils`, `Fjglaugr`, `Solthbaugr`.

**Files:** `src/wyrdbound_rng/generator.py`, `tests/test_generator.py`

**Steps**

1. Tests first:
   - A predicate `_is_pronounceable(name)` rejects a name containing a run of
     four or more consecutive consonants and accepts one with three.
   - `Hrafn` is accepted — a vowel-less syllable is legal before a vowel, and a
     rule that rejects `Hrafn` is too strict.
   - `Hrgils`, `Svgest`, `Thjglamr` are rejected.
   - Over 200 Bayesian generations from `ancestry-dwarf-male`, **no** result
     contains a four-consonant run. This is the test that would have caught the
     defect.
2. Implement the predicate and apply it as an additional accept condition in
   `_generate_name_bayesian`'s attempt loop, alongside the length and
   probability checks. Treat a rejection as a failed attempt and resample.
3. Apply it in `_generate_name_simple` and `_generate_name_very_simple` too —
   they assemble from the same inventory and have the same failure.

**Notes**

- `y` counts as a vowel for this purpose, or every Welsh name in
  `ancestry-elf-*` is rejected (`Gwyn`, `Myrddin`, `Bryn`).
- Do **not** filter vowel-less syllables out of the inventory instead. They are
  19% of start mass and carry the Norse and Welsh character; the sequence is
  what is wrong, not the syllable.

**Acceptance criteria**

- Zero four-consonant runs across 200 generations from each ancestry corpus.
- `python -m pytest tests/` green; `ruff` clean.

---

### T-004 [TDD] — Budget-aware Bayesian length control

**Goal:** Steer generation to fit the length cap instead of sampling and
discarding.

**Files:** `src/wyrdbound_rng/generator.py`,
`src/wyrdbound_rng/bayesian_model.py`, `tests/test_generator.py`

**Steps**

1. Tests first:
   - The syllable budget is derived from the loaded corpus's mean syllable
     length, not from a hardcoded 3. Assert that a corpus whose mean syllable is
     ~2.4 characters gets a larger `max_syllables` at `max_len=11` than a corpus
     whose mean is ~3.6.
   - `generate_syllable_sequence(max_syllables, max_chars=N)` never returns a
     sequence whose joined length exceeds `N`.
   - Over 200 generations at `max_len=9`, every returned name is ≤ 9 characters
     **and** the mean attempt count is materially lower than the current
     implementation's. Record the before figure in the commit body.
2. Implement in two parts:
   - In `Generator`, compute the mean syllable length once at load and use it for
     `max_syllables` instead of `max_len // 3`.
   - In `BayesianModel.generate_syllable_sequence`, accept a remaining-character
     budget. At each step, mask the candidate distribution to syllables that fit
     the budget, renormalise, and scale `end_probs` upward as the budget
     depletes so the sequence terminates naturally rather than by truncation.
3. If masking empties the candidate set, end the sequence — do not fall through
   to the uniform distribution, which is what currently produces the incoherent
   tail syllables.

**Notes**

- This is rejection sampling becoming constrained sampling. The learned
  distribution is still respected; it is conditioned on the budget rather than
  filtered after the fact.
- Keep `max_syllables` as a parameter. Some callers want a syllable ceiling
  independent of the character ceiling.

**Acceptance criteria**

- No generated name exceeds `max_len` at any tested cap.
- Mean attempts per name measurably lower than before; state both numbers.
- `python -m pytest tests/` green; `ruff` clean.

---

### T-005 [TDD] — Never fall back to the simple algorithm

**Goal:** The hardest cases stop getting the worst generator.

**Files:** `src/wyrdbound_rng/generator.py`, `tests/test_generator.py`

**Steps**

1. Tests first:
   - `best_name` is retained when a candidate fails **any** criterion, not only
     when it was under length and under threshold. Drive this with a corpus and
     a `max_len` small enough that most candidates are rejected.
   - A Bayesian call never returns a name produced by `_generate_name_simple`.
     Assert by patching `_generate_name_simple` to raise, then generating 200
     names at a punishing `max_len` and threshold.
   - When nothing meets the threshold, the returned name is still the
     highest-probability candidate seen.
2. Track the best candidate across all rejection reasons. When the best
   candidate is over length, trim it at a **syllable boundary** rather than
   mid-syllable, then re-check pronounceability.
3. Remove the `_generate_name_simple` fallback path entirely.

**Acceptance criteria**

- `_generate_name_simple` is never reached from the Bayesian path.
- `python -m pytest tests/` green; `ruff` clean.

---

### T-006 [TDD] [P] — Minimum length, and the state leak in the simple algorithms

**Goal:** Stop returning `Ays`, `Iei`, `Ona`. Stop using an oversized syllable
after the length loop gives up.

**Files:** `src/wyrdbound_rng/generator.py`, `tests/test_generator.py`

**Steps**

1. Tests first:
   - `generate_name(..., min_len=4)` never returns a name shorter than 4.
   - `min_len` defaults to a value that preserves current behavior for existing
     callers — pick `3` and state why in a comment.
   - `min_len > max_len` raises rather than silently ranging backwards.
   - In `_generate_name_simple`, when no beginning syllable satisfies the length
     constraint within 100 attempts, the result does **not** contain an
     oversized beginning. Currently `beginning` keeps the last attempted value
     regardless of whether it passed.
2. Add `min_len` to `generate_name` and `generate`, threaded to all three
   algorithms as an accept condition.
3. Fix the state leak: reset the candidate on a failed check, and raise a clear
   exception if the loop exhausts without a valid syllable — a corpus that
   cannot produce a legal starting syllable at this length is a caller error
   worth reporting, not something to paper over.

**Acceptance criteria**

- No name below `min_len` across 200 generations per corpus.
- `python -m pytest tests/` green; `ruff` clean.

---

### T-007 [TDD] — Injectable RNG

**Goal:** Reproducible generation. Required by any consumer that needs a seeded
stream — Ascension's character generation among them.

**Files:** `src/wyrdbound_rng/generator.py`,
`src/wyrdbound_rng/bayesian_model.py`, `tests/test_generator.py`

**Steps**

1. Tests first:
   - `Generator(source, rng=random.Random(42))` and a second generator with the
     same seed produce identical name sequences.
   - Two different seeds produce different sequences.
   - Omitting `rng` preserves today's behavior (module-level `random`), so no
     existing caller changes.
   - No module in `src/` calls `random.choice`, `random.random`, `random.randint`
     or `random.sample` at module scope after this task. Assert with a source
     grep in the test, so a future regression is caught mechanically.
2. Accept an optional `rng: random.Random | None` on `Generator.__init__`,
   default `None` meaning the module-level `random`. Store it and route every
   sampling call through it, including inside `BayesianModel` — pass the
   instance down at train time.

**Notes**

- This is what lets `tools/corpus_test.py` drop its `random.seed()` workaround,
  which reaches into global state precisely because there is no seam. T-009
  removes it.
- Prefer accepting a `random.Random` over an integer seed: a consumer with its
  own derived streams needs to inject an instance, not ask the library to make
  one.

**Acceptance criteria**

- Identical seeds produce identical output across processes.
- `python -m pytest tests/` green; `ruff` clean.

---

### T-008 — Re-baseline and regression-test the ancestry corpora

**Goal:** Prove the ten corpora still load, still measure well, and lock them
against silent drift.

**Files:** `tests/test_ancestry_corpora.py` (new),
`data/…` → `src/wyrdbound_rng/data/…` (regenerate only if T-002 changed them)

**Steps**

1. A parametrised test over all ten ancestry identifiers asserting, for each:
   - it resolves as a built-in identifier and loads without error
   - it has no duplicate names, case-insensitively
   - every name is alphabetic, 3–12 characters
   - unigram coverage ≥ 0.93 and bigram coverage ≥ 0.64 — the floors the corpora
     currently clear, so the test catches regression rather than restating
     aspiration
   - 200 Bayesian generations produce zero four-consonant runs, zero names over
     `max_len`, and ≥ 85% uniqueness
2. Import the measurement helpers from `tools/corpus_test.py` rather than
   reimplementing them. If that import is awkward, that is a signal the metrics
   belong in `src/wyrdbound_rng/` — if you move them, move them wholesale and
   leave `corpus_test.py` as a thin CLI over the library.
3. Re-run `python tools/build_corpora.py` and confirm the output is byte-identical
   to what is committed. If it is not, the builder has drifted from the data and
   **that** is the bug — fix the builder, do not overwrite the corpora silently.

**Notes**

- Keep the thresholds as named constants at the top of the test file with a
  comment pointing at `CORPUS_REPORT.md` §3, so the next person changing them
  knows what they are arguing with.

**Acceptance criteria**

- All ten corpora pass; the suite runs in under 60 seconds.
- `python -m pytest tests/` green; `ruff` clean.

---

### T-009 [P] — Put the corpus tool under test and into CI

**Goal:** `corpus_test.py` is a quality gate, so it needs to be as trustworthy
as the thing it measures.

**Files:** `tests/test_corpus_test_tool.py` (new), `tools/corpus_test.py`,
`.github/workflows/cli-tools.yml`

**Steps**

1. Unit-test the estimators against hand-computable inputs, not against corpora:
   - `good_turing_coverage` on a frequency table with known f1 and token count
   - `chao1` on a table with known f1 and f2, including the `f2 == 0` branch
   - `fit_power_law` recovers known `a` and `b` from synthetic points
   - `trim` is deterministic and preserves protected names
2. A smoke test that `--json` parses and carries the documented keys, and that
   `--all` completes without raising on any built-in list.
3. Remove the `random.seed(seed)` workaround in `generation_report` now that
   T-007 provides a real seam, and pass a `random.Random(seed)` to the
   `Generator` instead. Keep reports reproducible.
4. Add a `corpus` job to `.github/workflows/cli-tools.yml` running
   `python tools/corpus_test.py --list ancestry-dwarf-male --json` and asserting
   exit 0 and parseable JSON.

**Notes**

- `corpus_test.py` returns exit 2 for a `NEEDS WORK` verdict. That is deliberate
  and useful in CI, but it means `set -e` scripts must handle it — say so in the
  workflow.

**Acceptance criteria**

- Estimator tests pass without loading any corpus.
- `python -m pytest tests/` green; `ruff` clean.

---

### T-010 — Documentation, and correcting the record

**Goal:** The docs describe behavior that actually exists.

**Files:** `README.md`, `TTRPG_CORPUS_GUIDE.md`, `CORPUS_REPORT.md`,
`CHANGELOG.md`

**Steps**

1. `README.md`: add the ten ancestry lists to the **Built-in Name Lists** table.
   Document `min_len`, the `rng` parameter, and `WYRDBOUND_RNG_DATA_DIR` if
   T-001 added it.
2. `TTRPG_CORPUS_GUIDE.md` is the most misleading document in the repository and
   needs real surgery:
   - It advertises `corpus_test.py`, `practical_corpus_analysis.py` and
     `example_threshold_api.py` under **Support Resources**. Only the first now
     exists; the other two never did — `git log --all --diff-filter=D` finds no
     trace. Remove them.
   - Its size table and "Key Findings" are attributed to "empirical testing"
     performed with those non-existent tools. Either re-derive the numbers with
     `corpus_test.py --all` or mark the table as a rule of thumb. Do not leave
     unsourced numbers presented as measurements.
   - Its **85%+ Novelty Rate** target is actively harmful and must be corrected.
     Cite the measurement: on one corpus at one length cap, `simple` scores 95%
     novelty (`Warwaaibald`, `Gugomarger`) against `bayesian`'s 69%
     (`Guilhard`, `Adalward`, `Lambert`). Chasing novelty selects the worse
     generator.
   - Its headline claim that 679 mixed names is a success is contradicted by its
     own successor metric: `generic-fantasy` carries 685 unique syllables across
     679 names and reaches only 0.42 bigram coverage. Replace the guidance with
     the coherence finding from `CORPUS_REPORT.md` §1.
3. `CORPUS_REPORT.md`: remove the "`--json` is broken on every tool" claim in §5
   — `58def61` fixed it before the report was written, and the report was
   measuring a stale installed package. Re-run the §3 metrics table after T-002
   through T-007 and record both the before and after figures; the novelty
   column in particular will move once names stop being mangled.
4. `CHANGELOG.md`: one entry per behavioral task, grouped **Fixed** / **Added** /
   **Changed**, calling out that `_remove_repetitions` changes generated output
   for every existing corpus.

**Acceptance criteria**

- No document references a file that does not exist.
- No metric is presented as measured unless it was measured by a committed tool.
- `python -m pytest tests/` green; `ruff` clean.

---

## Demo

`demos/name_generation_demo.py` (new, created by T-010 or as its own task if you
prefer — say which).

Honouring `--seed` and exiting 0, it prints for each of the ten ancestry
corpora: twelve generated names, the corpus's coverage figures, and a
before/after column showing what `_remove_repetitions` would have done to each
name under the old implementation. That last column is the feature's whole
argument in one view, and it is worth keeping after the fix as a regression
exhibit.

Ends `DEMO OK: name_generation`.

---

## Verification script

Run these in a real terminal and either sign off or report **the number of the
first failing step**.

1. `pip install -e ".[dev]"` then `python -m pytest tests/ -q`.
2. Expect: green, including the new ancestry and estimator tests.
3. `ls data 2>&1`.
4. Expect: "No such file or directory". The duplicate is gone.
5. `python -c "import wyrdbound_rng, pathlib; print(len(list((pathlib.Path(wyrdbound_rng.__file__).parent/'data').glob('*.yaml'))))"`
6. Expect: `22`.
7. `wyrdbound-rng --list ancestry-halfling-female -n 15 -a bayesian --length 11`
8. Expect: fifteen names. **None contains a doubled letter that has been eaten** —
   you should see `Sibella`-shaped names, not `Sibea`-shaped ones. This is the
   step that proves T-002.
9. `wyrdbound-rng --list ancestry-dwarf-male -n 20 -a bayesian --length 11`
10. Expect: twenty names, none with four consecutive consonants, none longer
    than 11 characters, none shorter than 3. No `Hrgils`, no `Styrrr`.
11. `wyrdbound-rng --list ancestry-goblin-male -n 20 -a bayesian --length 9`
12. Expect: twenty short harsh names, all ≤ 9 characters.
13. Run step 9 again.
14. Expect: a *different* twenty names — the default path is still unseeded.
15. `python -c "import random; from wyrdbound_rng import Generator; g=lambda: [Generator('ancestry-elf-female', rng=random.Random(7)).generate_name(11,'bayesian').name for _ in range(5)]; print(g()); print(g())"`
16. Expect: the two lists are identical. This proves T-007.
17. `python tools/corpus_test.py --all`
18. Expect: a ranked table of twenty-two corpora; the ten `ancestry-*` lists all
    at unigram coverage ≥ 0.93.
19. `python tools/corpus_test.py --list ancestry-dwarf-male --json | python -m json.tool > /dev/null`
20. Expect: no output and exit 0 — clean, parseable JSON.
21. `python demos/name_generation_demo.py --seed 1`
22. Expect: `DEMO OK: name_generation`, and the before/after column visibly
    showing names the old implementation would have damaged.

**Signed off:** 2026-09-20 — all 22 steps pass in the project venv
(`source .venv/bin/activate`; the global asdf Python 3.11.9 still carries a
stale non-editable wyrdbound-rng 0.0.1 and must not be used).

Recorded results:

- Steps 1–2: `python -m pytest tests/ -q` → **166 passed**.
- Steps 3–4: `ls data` → *No such file or directory*.
- Steps 5–6: packaged data dir → **22** YAML files.
- Steps 7–8: `ancestry-halfling-female -n 15` → doubled letters survive
  (`Hawielle`, `Godellagen`, `Levellallen`, `Ibbenletta`).
- Steps 9–10: `ancestry-dwarf-male -n 20` → 20 names, zero over 11 chars, zero
  under 3, zero four-consonant runs; `Helgkell`/`Finnridr` intact.
- Steps 11–12: `ancestry-goblin-male -n 20 --length 9` → 20 names, all ≤ 9,
  zero four-consonant runs.
- Steps 13–14: repeated unseeded run → *different* names.
- Steps 15–16: seeded `Generator(..., rng=random.Random(7))` → identical.
  (The doc's one-liner rebuilds a generator per name, so it repeats the first
  draw; a single generator advances normally —
  `Braneuni, Angona, Argerona, Arianys, ...`.)
- Steps 17–18: `corpus_test.py --all` → 22-corpus ranked table; all ten
  `ancestry-*` at unigram coverage ≥ 0.933.
- Steps 19–20: `--json | python -m json.tool` → exit 0, no output.
- Steps 21–22: `python demos/name_generation_demo.py --seed 1` →
  `DEMO OK: name_generation`, before/after column present.

---

## Feature acceptance

**Capability:** the library generates names worth shipping — nothing mangled,
nothing unpronounceable, nothing over length — from ten measured ancestry
corpora, reproducibly from an injected seed.

**Gate:**

- [x] `python -m pytest tests/` green; `ruff check` and `ruff format --check` clean
- [x] CI green, including the new `corpus` job
- [x] `data/` deleted; the wheel still ships all twenty-two corpora
- [x] `_remove_repetitions` collapses rather than deletes; the six regression
      names survive
- [x] Zero four-consonant runs and zero over-length names across 200 generations
      per corpus
- [x] The Bayesian path never falls back to `_generate_name_simple`
- [x] Identical seeds produce identical names
- [x] Every corpus meets its coverage floor under test
- [x] No document references a tool that does not exist, and no unsourced number
      is presented as a measurement
- [x] Demo green
- [x] Verification script signed off
