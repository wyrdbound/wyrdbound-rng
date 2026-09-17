# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **`WYRDBOUND_RNG_DATA_DIR` environment override**: Point the resolver at a custom corpora directory without passing a file path.

### Changed
- **The Bayesian path never falls back to the simple algorithm**: The best candidate is now tracked across every rejection reason, not only when a candidate came in under length but below threshold. An over-length candidate is trimmed at a syllable boundary and re-checked for pronounceability instead of being discarded. When nothing meets the threshold the highest-probability candidate seen is returned; a run with no candidate at all raises rather than silently using the crudest generator.
- **Budget-aware Bayesian length control**: `max_syllables` is now derived from the loaded corpus's measured mean syllable length rather than a hardcoded three characters per syllable, and `generate_syllable_sequence` accepts a remaining-character budget. Candidates that would exceed the budget are masked out and renormalised, and the end probability scales up as the budget depletes, so longer names terminate naturally instead of being rejected and retried. Mean attempts at `max_len=5` drop from 1.66 to 1.01 (threshold disabled) with zero over-length names.
- **One source of truth for built-in name data**: Removed the vestigial root `data/` directory. `src/wyrdbound_rng/data/` is now the only data directory; it is what ships in the wheel. The resolver's dead root-`data/` fallback is replaced by the environment override.
- **Improved Bayesian Model Logging**: Converted print statements in Bayesian model to proper DEBUG level logging, allowing users to inject custom loggers and control output verbosity ([#5](https://github.com/wyrdbound/wyrdbound-rng/pull/5))
  - Print statements replaced with `logger.debug()` calls
  - Added comprehensive logging test suite (`test_bayesian_logging.py`)
  - Users can now capture, filter, and control Bayesian model diagnostic output
  - Maintains backward compatibility - no output by default, configurable via logging levels

### Fixed
- **Unpronounceable syllable junctions are rejected**: Generation now refuses names containing a run of four or more consecutive consonants (`Fjglaugr`, `Solthbaugr`, `Thjglamr`). The segmenter's onset-only syllables (`hr`, `sv`, `thj`) are legal before a vowel (`Hrafn`) and broken before a consonant; the accept condition is applied in all three algorithms. `y` counts as a vowel so Welsh names survive.
- **`_remove_repetitions` no longer deletes letters**: A run of repeated letters now collapses to a double instead of vanishing. The old implementation deleted every `ll` and `nn` outright, which mangled roughly a third of generated names for some corpora (`Sibella` -> `Sibea`, `Gestkell` -> `Gestke`). **This changes generated output for every existing corpus.**
- **Data directory resolution**: The root-`data/` fallback in `get_data_directory()` was unreachable, since the package directory is always present.

## v0.0.1 (2025-07-28)

### Added

- **Core Name Generation System** with multiple algorithms:
  - Very simple algorithm for quick generation
  - Simple algorithm with weighted syllable selection
  - Bayesian algorithm with probability analysis and statistical modeling
- **Flexible Segmentation Strategies**:
  - Fantasy name segmenter for Western fantasy names
  - Japanese name segmenter for Japanese naming patterns
- **YAML Input Format Support**:
  - YAML files with metadata support for name corpora
  - Structured data format for easy corpus management
- **Command-Line Interface** with comprehensive options:
  - Multiple generation algorithms to choose from
  - Configurable output count and formatting
  - Analysis flags including `--show-analysis` and `--probabilities`
  - Support for custom data files and segmentation strategies
- **Built-in Name Corpora**:
  - Generic fantasy names (male/female variants)
  - Japanese Sengoku period names (multiple categories)
  - Warhammer 40k Space Marine names
- **Advanced Analysis Features**:
  - Syllable breakdown and frequency statistics
  - Probability calculations for generated names
  - Multi-syllable probability analysis (comma-separated input)
  - Corpus validation and source tracking
- **Advanced Analysis Tools** in `tools/` directory:
  - `tools/analyze.py`: Comprehensive corpus analysis with syllable frequency statistics
  - `tools/generate.py`: Advanced name generation with JSON output and detailed analysis
- **Modern Python Architecture**:
  - Uses pyproject.toml for configuration
  - Supports Python 3.8+
  - Modern src/ layout structure
  - Includes comprehensive type hints and documentation
  - Thread-safe operation for concurrent use
  - Lazy loading of Bayesian models for performance optimization
  - Extensible architecture for adding new segmenters
- **Quality Assurance**:
  - Comprehensive test suite with pytest
  - Development tools integration (black, ruff)
  - Memory-efficient syllable processing
  - Comprehensive error handling and validation

### Technical Features

- **Enhanced Data Handling**: Automatic data file discovery with fallback to root `data/` directory
- **JSON Output Support**: Tools can output structured data for programmatic use
- **Bayesian Statistical Modeling**: Advanced probability analysis with `get_syllable_probability_info()` method
- **Robust Error Handling**: Graceful handling of missing syllables and invalid inputs
