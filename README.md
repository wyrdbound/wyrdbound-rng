# Wyrdbound Random Name Generator

A comprehensive random name generator library for tabletop RPGs, designed to create authentic-sounding names by analyzing and recombining syllables from existing name corpora.

This library is designed for use in [wyrdbound](https://github.com/wyrdbound), a text-based RPG system that emphasizes narrative and player choice.

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 📣 This library is experimental and was built with much ❤️ and [vibe coding](https://en.wikipedia.org/wiki/Vibe_coding). Perfect for your tabletop RPG adventures, but maybe not for launching :rocket: or performing :brain: surgery! Enjoy!

## Features

### Multiple Generation Algorithms

- **Very Simple**: Quick and random syllable combination
- **Simple**: Basic syllable recombination with weighted selection
- **Bayesian**: Advanced probabilistic analysis for more realistic names

### Flexible Segmentation

- **Fantasy Names**: Optimized for Western fantasy naming conventions
- **Japanese Names**: Specialized for Japanese name syllable patterns
- **Extensible**: Easy to add new segmentation strategies

### YAML Input Format

- **YAML**: Structured data with metadata support
- **Mixed Sources**: Combine multiple input files

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

# Create generator with fantasy name segmenter
generator = Generator("generic-fantasy-names.yaml", segmenter=FantasyNameSegmenter())

# Generate a name using the simple algorithm
name = generator.generate_name(max_len=12, algorithm='simple')
print(name.name)  # "Aldric"

# Generate using Bayesian algorithm for more realistic results
name = generator.generate_name(max_len=12, algorithm='bayesian')
print(name.name)  # "Theron"
print(f"Probability: {name.probability:.2e}")
```

## Command Line Usage

```bash
# Generate 5 names from a built-in YAML file (just use the filename)
wyrdbound-rng generic-fantasy-names.yaml

# Generate 10 names with Bayesian algorithm
wyrdbound-rng japanese-sengoku-names.yaml -n 10 -a bayesian

# Show syllable breakdown and sources
wyrdbound-rng generic-fantasy-names.yaml --syllables --show-sources

# Show analysis info: corpus existence for all algorithms, plus probability for Bayesian
wyrdbound-rng generic-fantasy-names.yaml --show-analysis

# Bayesian algorithm with full analysis (probability + corpus existence)
wyrdbound-rng generic-fantasy-names.yaml --show-analysis -a bayesian

# Analyze probability for specific syllables
wyrdbound-rng generic-fantasy-names.yaml --probabilities "ar" -a bayesian

# You can also use full paths to your own YAML files
wyrdbound-rng /path/to/your/custom-names.yaml
```

## Supported Name Corpora

The library comes with several built-in name corpora located in the `data/` directory:

- **Generic Fantasy**: Traditional Western fantasy names (male/female)
- **Japanese Sengoku**: Historical Japanese names from the Sengoku period
- **Warhammer 40k**: Space Marine chapter names
- **Extensible**: Easy to add your own YAML files

## API Reference

### Main Classes

#### `Generator`

The main entry point for name generation.

```python
Generator(filename, segmenter=None)
```

- `filename`: Path to YAML file containing names
- `segmenter`: Syllable segmentation strategy (optional)

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
wyrdbound-rng <names_file> [options]

Options:
  -n, --number N        Number of names to generate (default: 5)
  -l, --length N        Maximum name length (default: 12)
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
python tools/analyze.py <names_file> [options]

Options:
  -s, --segmenter SEG   Segmenter: fantasy, japanese (default: fantasy)
  -v, --verbose         Show detailed analysis including name/syllable length statistics
  --top-syllables N     Number of top syllables to show (default: 20)
  --json                Output results as JSON
```

**Example:**

```bash
# Basic analysis
python tools/analyze.py generic-fantasy-names.yaml

# Detailed analysis with top 30 syllables
python tools/analyze.py japanese-sengoku-names.yaml -v --top-syllables 30 -s japanese

# JSON output for data processing
python tools/analyze.py generic-fantasy-names.yaml --json > analysis.json
```

#### Advanced Generation Tool

```bash
python tools/generate.py <names_file> [options]

Options:
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
python tools/generate.py generic-fantasy-names.yaml -v -a bayesian

# Generate 5 names as JSON for data processing
python tools/generate.py japanese-sengoku-names.yaml -n 5 --json -s japanese

# Batch generation with custom parameters
python tools/generate.py generic-fantasy-names.yaml -n 100 -a bayesian --min-probability 1e-6
```

## Examples

### Basic Usage

```python
from wyrdbound_rng import Generator, FantasyNameSegmenter

# Create generator
generator = Generator("generic-fantasy-names.yaml", segmenter=FantasyNameSegmenter())

# Generate names
for i in range(5):
    name = generator.generate_name(max_len=12, algorithm='simple')
    print(f"{i+1}. {name.name}")
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
# Load from multiple sources by creating separate generators
generator1 = Generator("generic-fantasy-male.yaml")
generator2 = Generator("generic-fantasy-female.yaml")

# Generate names from each corpus
male_names = [generator1.generate_name(max_len=12) for _ in range(5)]
female_names = [generator2.generate_name(max_len=12) for _ in range(5)]
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/wyrdbound/wyrdbound-rng.git
cd wyrdbound-rng

# Install with development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=wyrdbound_rng

# Run with coverage and generate HTML report
python -m pytest tests/ --cov=wyrdbound_rng --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/ tools/

# Sort imports
isort src/ tests/ tools/

# Lint code
flake8 src/ tests/ tools/
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
