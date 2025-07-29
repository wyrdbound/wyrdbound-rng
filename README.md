# Wyrdbound Random Name Generator

A comprehensive random name generator library for tabletop RPGs, designed to create authentic-sounding names by analyzing and recombining syllables from existing name corpora.

This library is designed for use in [wyrdbound](https://github.com/wyrdbound), a text-based RPG system that emphasizes narrative and player choice.

[![CI](https://github.com/wyrdbound/wyrdbound-rng/actions/workflows/ci.yml/badge.svg)](https://github.com/wyrdbound/wyrdbound-rng/actions/workflows/ci.yml)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

> 📣 This library is experimental and was built with much ❤️ and [vibe coding](https://en.wikipedia.org/wiki/Vibe_coding). Perfect for your tabletop RPG adventures, but maybe not for launching :rocket: or performing :brain: surgery! Enjoy!

## Features

### Simplified Interface

- **Built-in Name Lists**: Reference name corpora using simple identifiers
- **Auto-Discovery**: Automatically finds built-in name lists without specifying file paths
- **Flexible Input**: Supports both built-in identifiers and custom file paths
- **Help Integration**: CLI tools show available built-in name lists in help text

### Multiple Generation Algorithms

- **Very Simple**: Quick and random syllable combination
- **Simple**: Basic syllable recombination with weighted selection
- **Bayesian**: Advanced probabilistic analysis for more realistic names

### Flexible Segmentation

- **Fantasy Names**: Optimized for Western fantasy naming conventions
- **Japanese Names**: Specialized for Japanese name syllable patterns
- **Extensible**: Easy to add new segmentation strategies

### YAML Input Format

- **Built-in Name Lists**: Use simple identifiers for included corpora
- **Custom YAML Files**: Support for user-provided YAML files with metadata
- **Mixed Sources**: Combine multiple input files and built-in lists

### Advanced Analysis

- **Syllable Statistics**: Detailed breakdown of syllable patterns
- **Probability Analysis**: Bayesian probability calculations
- **Corpus Validation**: Check if generated names exist in source data
- **Source Tracking**: Track which names influenced generation

## Installation

```bash
pip install wyrdbound-rng
```

## Quick Start

```python
from wyrdbound_rng import Generator, FantasyNameSegmenter

# Create generator with built-in name list (simple identifier)
generator = Generator("generic-fantasy", segmenter=FantasyNameSegmenter())

# Generate a name using the simple algorithm
name = generator.generate_name(max_len=12, algorithm='simple')
print(name.name)  # "Aldric"

# Generate using Bayesian algorithm for more realistic results
name = generator.generate_name(max_len=12, algorithm='bayesian')
print(name.name)  # "Theron"
print(f"Probability: {name.probability:.2e}")

# You can also use custom YAML files
custom_generator = Generator("./my-custom-names.yaml")
```

## Command Line Usage

```bash
# Generate 5 names using built-in name list identifier
wyrdbound-rng --list generic-fantasy

# Generate 10 names with Bayesian algorithm
wyrdbound-rng --list japanese-sengoku -n 10 -a bayesian --segmenter japanese

# Show syllable breakdown and sources
wyrdbound-rng --list generic-fantasy --syllables --show-sources

# Show analysis info: corpus existence for all algorithms, plus probability for Bayesian
wyrdbound-rng --list generic-fantasy --show-analysis

# Bayesian algorithm with full analysis (probability + corpus existence)
wyrdbound-rng --list generic-fantasy --show-analysis -a bayesian

# Analyze probability for specific syllables
wyrdbound-rng --list generic-fantasy --probabilities "ar" -a bayesian

# You can also use custom YAML files
wyrdbound-rng --list /path/to/your/custom-names.yaml
wyrdbound-rng --list ./my-names.yaml
```

## Supported Name Corpora

The library comes with several built-in name corpora. You can reference them using simple identifiers:

### Built-in Name Lists

- `generic-fantasy` - Traditional Western fantasy names (mixed)
- `generic-fantasy-male` - Traditional Western fantasy male names
- `generic-fantasy-female` - Traditional Western fantasy female names
- `japanese-sengoku` - Historical Japanese names from the Sengoku period (mixed)
- `japanese-sengoku-clan` - Japanese Sengoku clan names
- `japanese-sengoku-daimyo` - Japanese Sengoku daimyo names
- `japanese-sengoku-religious` - Japanese Sengoku religious names
- `japanese-sengoku-rogue` - Japanese Sengoku rogue names
- `japanese-sengoku-samurai` - Japanese Sengoku samurai names
- `japanese-sengoku-women` - Japanese Sengoku women names
- `japanese-swordsmen` - Japanese swordsmen names
- `warhammer40k-space-marine-names` - Warhammer 40k Space Marine names

### Custom Files

You can also provide your own YAML files using relative or absolute paths:

- `./my-names.yaml` - Relative path
- `/absolute/path/to/names.yaml` - Absolute path

## API Reference

### Main Classes

#### `Generator`

The main entry point for name generation.

```python
Generator(name_source, segmenter=None)
```

- `name_source`: Built-in name list identifier (e.g., "generic-fantasy") or path to YAML file
- `segmenter`: Syllable segmentation strategy (optional, auto-detected from YAML metadata)

**Methods:**

- `generate_name(max_len, algorithm='simple', min_probability_threshold=1e-8)`: Generate a single name
- `generate(n, max_chars=15, algorithm='simple', min_probability_threshold=1e-8)`: Generate multiple names
- `name_exists_in_corpus(name)`: Check if a name exists in the source corpus

#### `GeneratedName`

Represents a generated name with metadata.

**Properties:**

- `name` (str): The generated name
- `syllables` (list): List of syllables used
- `source_names` (list): Names that influenced generation
- `probability` (float): Bayesian probability (if applicable)
- `exists_in_corpus` (bool): Whether name exists in source data

### Segmenters

#### `FantasyNameSegmenter`

Optimized for Western fantasy names.

#### `JapaneseNameSegmenter`

Specialized for Japanese name patterns.

### Data Format

#### YAML Format

The YAML format is used to define name corpora with metadata. Below is an example structure:

```yaml
metadata:
  description: Fantasy names from Middle-earth
  segmenter: fantasy
  sources:
    - The Lord of the Rings by J.R.R. Tolkien
  version: "1.0"
names:
  - Aragorn
  - Arwen
  - Bilbo
  - Boromir
  - Frodo
  - Gandalf
  - Gimli
  - Legolas
  - Samwise
```

Each entry in the `names` list represents a name. The `metadata` section provides additional information about the corpus, including its description, segmentation strategy, sources, and version.

## Command Line Tools

### Generate Names

```bash
wyrdbound-rng --list <name_source> [options]

Options:
  -l, --list SOURCE     Built-in name list identifier or path to YAML file (required)
  -n, --number N        Number of names to generate (default: 5)
  --length N            Maximum name length (default: 12)
  -a, --algorithm ALG   Algorithm: simple, bayesian, very_simple (default: simple)
  -s, --segmenter SEG   Segmenter: fantasy, japanese (default: fantasy)
  --show-sources        Show source names used in generation
  --show-analysis       Show analysis info: corpus existence for all algorithms, plus probability for bayesian
  --min-probability N   Minimum probability threshold (default: 1e-8)
  --syllables           Show syllable breakdown
  --probabilities SYL   Analyze probability for specific syllable(s) (comma-separated)
```

### Advanced Tools

The `tools/` directory contains additional command-line utilities for advanced analysis and generation.

#### Corpus Analysis Tool

```bash
python tools/analyze.py --list <name_source> [options]

Options:
  -l, --list SOURCE     Built-in name list identifier or path to YAML file (required)
  -s, --segmenter SEG   Segmenter: fantasy, japanese (default: fantasy)
  -v, --verbose         Show detailed analysis including name/syllable length statistics
  --top-syllables N     Number of top syllables to show (default: 20)
  --json                Output results as JSON
```

**Example:**

```bash
# Basic analysis
python tools/analyze.py --list generic-fantasy

# Detailed analysis with top 30 syllables
python tools/analyze.py --list japanese-sengoku -v --top-syllables 30 -s japanese

# JSON output for data processing
python tools/analyze.py --list generic-fantasy --json > analysis.json

# Analyze custom file
python tools/analyze.py --list ./my-names.yaml
```

#### Advanced Generation Tool

```bash
python tools/generate.py --list <name_source> [options]

Options:
  -l, --list SOURCE     Built-in name list identifier or path to YAML file (required)
  -n, --count N         Number of names to generate (default: 1)
  -a, --algorithm ALG   Algorithm: simple, bayesian, very_simple (default: simple)
  -s, --segmenter SEG   Segmenter: fantasy, japanese (default: fantasy)
  --json                Output results as JSON
  -v, --verbose         Show detailed breakdown (syllables, sources, probability)
  --min-probability N   Minimum probability threshold for bayesian generation
  --max-length N        Maximum name length (default: 12)
```

**Example:**

```bash
# Generate single name with detailed info
python tools/generate.py --list generic-fantasy -v -a bayesian

# Generate 5 names as JSON for data processing
python tools/generate.py --list japanese-sengoku -n 5 --json -s japanese

# Batch generation with custom parameters
python tools/generate.py --list generic-fantasy -n 100 -a bayesian --min-probability 1e-6

# Use custom file
python tools/generate.py --list ./my-names.yaml -n 5
```

## Examples

### Basic Usage

```python
from wyrdbound_rng import Generator, FantasyNameSegmenter

# Create generator using built-in name list
generator = Generator("generic-fantasy", segmenter=FantasyNameSegmenter())

# Generate names
for i in range(5):
    name = generator.generate_name(max_len=12, algorithm='simple')
    print(f"{i+1}. {name.name}")

# You can also use custom files
custom_generator = Generator("./my-names.yaml")
```

### Advanced Analysis

```python
# Generate with probability analysis
name = generator.generate_name(max_len=12, algorithm='bayesian', min_probability_threshold=1e-6)
print(f"Name: {name.name}")
print(f"Probability: {name.probability:.2e}")
print(f"Exists in corpus: {generator.name_exists_in_corpus(name.name)}")
if hasattr(name, 'source_names') and name.source_names:
    print(f"Source names: {[n.name for n in name.source_names]}")
```

### Multiple Corpora

```python
# Load from multiple built-in sources by creating separate generators
generator1 = Generator("generic-fantasy-male")
generator2 = Generator("generic-fantasy-female")

# Generate names from each corpus
male_names = [generator1.generate_name(max_len=12) for _ in range(5)]
female_names = [generator2.generate_name(max_len=12) for _ in range(5)]

# Mix built-in and custom sources
japanese_gen = Generator("japanese-sengoku")
custom_gen = Generator("./my-custom-names.yaml")
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/wyrdbound/wyrdbound-rng.git
cd wyrdbound-rng

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests (ensure .venv is activated)
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=wyrdbound_rng

# Run with coverage and generate HTML report
python -m pytest tests/ --cov=wyrdbound_rng --cov-report=html
```

### Code Quality

```bash
# Lint and format with Ruff (ensure .venv is activated)
ruff check src/ tests/ tools/
ruff format src/ tests/ tools/

# Or run both together
ruff check --fix src/ tests/ tools/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Areas for Contribution

- New segmentation strategies for different cultures/languages
- Additional name corpora
- Performance optimizations
- Enhanced probability models
- Documentation improvements

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the original Ruby RNG gem
- Built for the diverse naming needs of tabletop RPG systems
- Thanks to the RPG community for feedback and name corpus contributions
