# wyrdbound-rng Development Guidelines

Last updated: 2026-09-25

**Spec Kit is not used in this project.** Do not run or reference `/speckit.*`
commands. The feature documents under `design/features/` and this file are the
governing documents; author and edit them directly.

## Governing Documents

| Document | Purpose |
|---|---|
| [`design/features/`](design/features) | **Active build plan** — ordered feature documents, each with its own *Working rules* and task list. Read them before starting work. |
| [`README.md`](README.md) | User-facing documentation and API reference |
| [`CHANGELOG.md`](CHANGELOG.md) | Release history; document all changes under "Unreleased" |
| [`CORPUS_REPORT.md`](CORPUS_REPORT.md) | Corpus measurements and findings (untracked; regenerate as needed) |
| [`docs/cluster-baseline.md`](docs/cluster-baseline.md) | Phonotactic cluster inventory baseline for eleven corpora |

Each feature document carries its own *Working rules*. They apply to every task
in that feature and supersede the summary below where they differ. The
established house rules are:

1. **One task per run.** Do not start the next task in the same run.
2. **The suite is green at the end of every task.**
3. `[TDD]` tasks require the test written and **observed failing** first.
4. **Do not refactor outside the task's listed files.**
5. **Do not add dependencies.** Runtime deps are `PyYAML` only. If you think you
   need another, stop and ask.
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

## Verification Contract

Every task ends with the gate green. No exceptions.

1. **Tests pass.** `python -m pytest tests/` is green from the repo root.
2. **Lint is clean.** `ruff check src/ tests/ tools/` passes.
3. **Format is clean.** `ruff format --check src/ tests/ tools/` passes; format
   with `ruff format src/ tests/ tools/` (line length 88, from `pyproject.toml`).
4. **Docs kept in sync.** README updated for user-facing changes; CHANGELOG
   updated under "Unreleased"; docstrings on all public APIs; version bumped for
   behavior changes.
5. **A failing test blocks merge.** Never delete or weaken a test to make the
   gate green.

Work one task per run, in order, and stop rather than guessing. A task that
cannot finish without breaking the gate is a badly split task: split it
differently rather than landing a broken state.

## Core Principles

These are **non-negotiable**. When in doubt, the feature document wins, then
this file, then older history.

1. **Library-first design.** Every feature starts as a standalone,
   self-contained, independently testable module with a clear name-generation
   purpose. The core library imports only the standard library plus `PyYAML`,
   and must run on **Python 3.8–3.12+**.
2. **CLI reachability.** Every user-facing capability is reachable from the CLI:
   args → stdout, errors → stderr. The main entry point is `wyrdbound-rng`;
   advanced tools live under `tools/`. Support both human-readable and `--json`
   output where the interface already offers it.
3. **Test-first development (NON-NEGOTIABLE for `[TDD]` tasks).** Tests are
   written and observed failing before implementation (Red → Green → Refactor).
   Cover all algorithms, both segmenters, error conditions, and edge cases.
4. **Corpus fidelity.** Generated names must read as names. Validity is derived
   from the loaded corpus, not guessed: the inter-nuclear consonant-cluster
   inventory (`y` counts as a vowel) accepts a cluster observed at that position
   or one that splits into an attested onset plus an attested coda, with a
   length backstop. `Ragnrikr` is legal; a corpus below 100 names falls back to
   the four-consonant heuristic. Do not reintroduce hardcoded letter counting.
5. **Determinism and reproducibility.** Any randomness must be injectable and
   seedable via `rng=` on `Generator` (and threaded into `BayesianModel`). Same
   input + same seed = same output. Never reach for `secrets`, `os.urandom`, or
   system time in library code.
6. **Observability & debugging.** Use the `logging` module with DEBUG level for
   diagnostics; never `print()` in library code. Users can inject custom
   loggers. Errors use specific exception types (`FileLoadError`, `SegmentError`)
   with messages that help the user fix the input, not silent failures.

### Code Quality

- **Formatting**: `ruff format` (line length 88)
- **Linting**: `ruff check` (E, W, F, I, B, C4, UP; `E501` and `B008`, `C901`
  ignored — see `pyproject.toml`)
- **Typing**: public APIs carry type annotations; a `py.typed` marker ships
- **Docs**: docstrings on all public classes, methods, and functions;
  module-level docs explaining purpose
- **Errors**: specific exception types, no silent failures

### Performance Standards

- No global mutable state during generation (thread safety)
- Avoid unnecessary allocations in hot paths
- Bayesian sampling routes through the injected `rng`, never the global module
- Lazily build expensive models (Bayesian) and cache them on the `Generator`
- Simple algorithms must not return over-length names; reject and resample, or
  raise a clear error rather than leaking a bad candidate

### Security

- **No `eval()` / `exec()`** on user input; parse YAML with `yaml.safe_load`
- Validate and sanitize all user-supplied paths and syllables
- Resource limits prevent unbounded resample loops
- Core library dependencies stay limited to `PyYAML`

### Development Workflow

- **Branches**: `feature/description` or `fix/description`
- **Conventional commits REQUIRED**: `<type>[optional scope]: <description>`
  - Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `ci`,
    `build`, `style`
  - Description after `type: ` MUST start lowercase
  - Task-scoped work includes the task id in the description:
    `fix(rng): T-002 — collapse repeated letters instead of deleting them`
  - Single high-level description — no itemized bullet lists
  - Breaking changes: `!` before the colon or a `BREAKING CHANGE:` footer
- **PRs**: follow `.github/pull_request_template.md`
- **Review checklist**: tests pass · new tests added · `ruff check` and
  `ruff format --check` clean · no new dependencies · docstrings updated · README
  updated if user-facing · CHANGELOG updated · version bumped if behavior
  changed · manual CLI testing done
- **Versioning**: semver `0.MINOR.PATCH`; keep `pyproject.toml` and
  `src/wyrdbound_rng/__init__.py:__version__` in sync

### Governance

Amendments to these principles require:

1. Discussion in a GitHub issue or PR
2. Rationale documented in CHANGELOG
3. A migration plan for existing code (if breaking)
4. An update to this file or the relevant feature document

All PRs are reviewed against these principles, and complexity must be justified.

## General Working Principles

These apply to every task regardless of feature.

1. **Tests first, always** (for `[TDD]` tasks). Write the failing test before the
   implementation. Tests are the specification; they are never edited to match
   buggy behavior.
2. **The gate is green.** Do not end a task with a failing test, a lint
   violation, or unformatted code.
3. **Prefer explicit errors over fallbacks.** When a fallback would mask a
   defect, raise instead. Identify and fix the root cause.
4. **No bandaid fixes.** Respect architectural boundaries; patch the cause, not
   the symptom.
5. **Simpler is better.** Choose the simplest solution that works; do not
   over-engineer.
6. **Determinism is a feature.** Anything that samples is seedable by the end of
   T-007. Never reach for `secrets`, `os.urandom`, or system time in library code.
7. **Minimal dependencies.** Prefer the standard library. Runtime deps stay
   `PyYAML` only.
8. **No scope creep.** Do what the task asks. New features require a document
   under `design/features/` first.
9. **Explain through docs, not comments.** Code should be self-explanatory;
   public behavior belongs in docstrings and the README.
10. **Stop rather than guess.** If the task is ambiguous, ask. Do not invent
    requirements or silently drop requirements you don't understand.

## Commands

```bash
# Environment (the venv is required; the global Python may carry a stale install)
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Gate
python -m pytest tests/                              # run full suite
python -m pytest tests/ --cov=wyrdbound_rng          # with coverage
ruff check src/ tests/ tools/                        # lint
ruff format --check src/ tests/ tools/               # format check

# Format
ruff format src/ tests/ tools/                       # format
ruff check --fix src/ tests/ tools/                  # lint + autofix

# Main CLI
wyrdbound-rng --list generic-fantasy -n 5
wyrdbound-rng --list japanese-sengoku -n 3 -s japanese -a bayesian --show-analysis
wyrdbound-rng --list generic-fantasy --syllables --show-sources
wyrdbound-rng --list generic-fantasy --probabilities "ar" -a bayesian

# Advanced tools
python tools/analyze.py --list generic-fantasy --json
python tools/generate.py --list generic-fantasy -n 5 -v
python tools/corpus_test.py --list ancestry-elf-female
python tools/cluster_report.py --list ancestry-dwarf-male
python demos/name_generation_demo.py --seed 1
```

The gate runs from the repo root:
`python -m pytest tests/ && ruff check src/ tests/ tools/ && ruff format --check src/ tests/ tools/`.

CI (`.github/workflows/`) runs the lint and format checks over `src/` and
`tests/` in `ci.yml`, and over `tools/` as well in `code-quality.yml`. Run all
three directories locally so a task does not fail CI on a `tools/` nit.

## Architecture

```text
src/wyrdbound_rng/
├── __init__.py              # public API exports + __version__
├── cli.py                   # argparse CLI entry point (wyrdbound-rng)
├── generator.py             # Generator: algorithms, length control, phonotactics
├── name.py                  # Name: a name plus its syllable components
├── generated_name.py        # GeneratedName: name + syllables + sources + probability
├── syllable.py              # Syllable: initial / inner / final components
├── name_file_loader.py      # YAML loading (yaml.safe_load)
├── name_list_resolver.py    # identifier -> path; WYRDBOUND_RNG_DATA_DIR override
├── bayesian_model.py        # syllable transition probabilities
├── evaluator.py             # scoring (placeholder, mirrors the Ruby gem)
├── statistics.py            # statistics (placeholder)
├── syllable_stats.py        # syllable statistics (placeholder)
├── exceptions.py            # FileLoadError, SegmentError
├── segmenters/
│   ├── syllable_segmenter_base.py
│   ├── fantasy_name_segmenter.py
│   └── japanese_name_segmenter.py
├── cache/
│   ├── cache_adapter.py
│   └── json_cache_adapter.py
└── data/                    # built-in corpora (*.yaml) — the only data directory
```

Layering: `generator.py` orchestrates; segmentation is one-directional
(base → fantasy/japanese); `cli.py`, `tools/`, and `tests/` may import anything.
`src/wyrdbound_rng/data/` is the single source of truth for built-in corpora and
is what ships in the wheel; there is no root `data/` directory. All sampling
flows through `Generator.rng` so that a seed reproduces a whole batch.

## Project Structure

```text
src/                 # library code (wyrdbound_rng/)
tests/               # test suite (data/ holds YAML fixtures)
tools/               # CLI tools (analyze, generate, corpus_test, build_corpora, cluster_report)
demos/               # runnable demos (ends "DEMO OK: ...")
design/features/     # feature documents: specs, plans, task lists, working rules
docs/                # committed measurements (cluster-baseline.md)
```

## Domain Notes

- **Algorithms**: `very_simple` (random syllable pick), `simple` (weighted pick),
  `bayesian` (probability model with corpus-existence analysis).
- **Segmenters**: `fantasy` (Western fantasy), `japanese` (Japanese patterns).
- **Corpora**: reference built-ins by identifier (e.g. `generic-fantasy`,
  `ancestry-dwarf-male`, `japanese-sengoku`), or pass a custom YAML path. The
  resolver also honours `WYRDBOUND_RNG_DATA_DIR`.
- **Generated names are validated** against the corpus's inter-nuclear cluster
  inventory; a corpus below 100 names falls back to the heuristic. See README
  "Name validity" and `CORPUS_REPORT.md` §5.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
