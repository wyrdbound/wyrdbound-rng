# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.1] - 2025-07-28

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
