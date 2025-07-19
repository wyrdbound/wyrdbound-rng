# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-18

### Added

- Initial release of Wyrdbound Random Name Generator
- Complete name generation system with multiple algorithms:
  - Very simple algorithm for quick generation
  - Simple algorithm with weighted syllable selection
  - Bayesian algorithm with probability analysis
- Flexible segmentation strategies:
  - Fantasy name segmenter for Western fantasy names
  - Japanese name segmenter for Japanese naming patterns
- Support for YAML input format:
  - YAML files with metadata support
- Command-line interface with comprehensive options
- Built-in name corpora:
  - Generic fantasy names (male/female)
  - Japanese Sengoku period names
  - Warhammer 40k Space Marine names
- Advanced analysis features:
  - Syllable breakdown and statistics
  - Probability calculations for generated names
  - Corpus validation and source tracking
- Modern Python packaging:
  - Uses pyproject.toml for configuration
  - Supports Python 3.8+
  - Includes type hints and documentation
- Comprehensive test suite with pytest
- Development tools integration (black, isort, flake8)

### Changed

- Restructured project to use modern src/ layout
- Updated package name from `rng-python` to `wyrdbound-rng`
- Improved CLI interface with better help and error messages
- Enhanced documentation with detailed examples

### Technical Details

- Thread-safe operation for concurrent use
- Lazy loading of Bayesian models for performance
- Extensible architecture for adding new segmenters
- Comprehensive error handling and validation
- Memory-efficient syllable processing

## [Unreleased]

## [1.1.0] - 2025-07-18

### Added

- **Enhanced CLI probability analysis**: `--probabilities` flag now supports multiple syllables (comma-separated)
- **Advanced analysis tools** in `tools/` directory:
  - `tools/analyze.py`: Comprehensive corpus analysis with syllable frequency statistics
  - `tools/generate.py`: Advanced name generation with JSON output and detailed analysis
- **Improved data file handling**: All CLI tools now automatically find data files in the root `data/` directory
- **Multi-syllable probability analysis**: Can analyze probability patterns for multiple syllables at once
- **JSON output support**: Tools can output structured data for programmatic use

### Changed

- **CLI flag renaming**: `--show-probability` renamed to `--show-analysis` for clarity
- **Data directory restructure**: Moved YAML data files from package to root `data/` directory for better accessibility
- **Enhanced error handling**: Better error messages and graceful handling of missing syllables
- **Improved documentation**: Updated README with comprehensive tool documentation and examples

### Fixed

- **Missing probability analysis implementation**: Implemented the previously placeholder `--probabilities` functionality
- **Data file loading in tools**: Fixed `tools/generate.py` to properly locate data files
- **Import path issues**: Updated all test imports from `rng` to `wyrdbound_rng`
- **Multi-syllable analysis**: Fixed probability analysis to handle comma-separated syllable lists

### Removed

- **CSV support**: Completely removed CSV input format in favor of YAML-only approach
- **Legacy import paths**: Cleaned up old import references

### Technical Details

- Added `get_syllable_probability_info()` method to Generator class
- Enhanced CLI with better argument parsing and validation
- Improved data file discovery with fallback to root data directory
- Added proper type hints for probability analysis methods

### Planned

- Additional segmentation strategies for other cultures
- Performance optimizations for large corpora
- Web interface for name generation
- Enhanced probability models
