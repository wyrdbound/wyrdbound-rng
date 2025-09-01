# Wyrdbound Random Name Generator Development Instructions

**ALWAYS follow these instructions first and only fallback to additional search and context gathering if the information in these instructions is incomplete or found to be in error.**

## AI Guidance and Development Principles

### Core Development Guidelines

- **Use the virtual environment**: Always activate the virtual environment in the project root (`source .venv/bin/activate && <your_command>`) before running any Python commands or tools.

- **Prefer explicit errors over fallbacks**: When fallbacks would mask issues, choose explicit errors instead. We want to identify and fix issues to maintain a stable system rather than hiding problems with workarounds.

- **No bandaid fixes**: Always respect architectural boundaries and make proper fixes rather than quick patches. Understand the root cause and address it appropriately within the existing architecture.

- **Follow good software development practices**: Adhere to SOLID principles and other established software engineering best practices. Write clean, maintainable, and well-structured code.

- **Simpler is better**: Choose the simplest solution that solves the problem effectively. Avoid over-engineering and unnecessary complexity.

## Working Effectively

### Development Environment Setup
```bash
# Set up development environment (takes ~12 seconds total)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev]"
```

### Code Quality and Testing
```bash
# Lint and format code (completes in <1 second each)
source .venv/bin/activate && ruff check src/ tests/ tools/
source .venv/bin/activate && ruff format src/ tests/ tools/

# Auto-fix linting issues
source .venv/bin/activate && ruff check --fix src/ tests/ tools/

# Run all tests (completes in ~8 seconds) - NEVER CANCEL
source .venv/bin/activate && python -m pytest tests/

# Run tests with coverage (completes in ~8 seconds) - NEVER CANCEL  
source .venv/bin/activate && python -m pytest tests/ --cov=wyrdbound_rng

# Run verbose tests to see individual test names (completes in ~1 second) - NEVER CANCEL
source .venv/bin/activate && python -m pytest tests/ -v
```

### Package Building
```bash
# Install build tools
source .venv/bin/activate && pip install build

# Build package (may fail due to network issues with PyPI)
source .venv/bin/activate && python -m build
# Note: Build may timeout due to network connectivity issues in isolated environments
# If build fails with "Read timed out" errors, this is a known network limitation
```

## Application Usage and Validation

### CLI Tool Usage
```bash
# Test CLI installation
source .venv/bin/activate && wyrdbound-rng --version

# Basic name generation
source .venv/bin/activate && wyrdbound-rng -l generic-fantasy -n 5

# Advanced generation with analysis
source .venv/bin/activate && wyrdbound-rng -l generic-fantasy -n 3 -a bayesian --show-analysis

# Japanese names with Japanese segmenter
source .venv/bin/activate && wyrdbound-rng -l japanese-sengoku -s japanese -n 3 -a bayesian --show-analysis

# Show syllable breakdown
source .venv/bin/activate && wyrdbound-rng --syllables -l generic-fantasy

# Analyze specific syllable probabilities (requires bayesian algorithm)
source .venv/bin/activate && wyrdbound-rng --probabilities "el" -l generic-fantasy -a bayesian
```

### Advanced Tools Usage
```bash
# Advanced generation tool with JSON output and verbose details
source .venv/bin/activate && python tools/generate.py -l generic-fantasy -n 2 --json -v

# Corpus analysis tool
source .venv/bin/activate && python tools/analyze.py -l generic-fantasy

# Analysis with Japanese segmenter
source .venv/bin/activate && python tools/analyze.py -l japanese-sengoku -s japanese --top-syllables 30

# JSON output for programmatic use
source .venv/bin/activate && python tools/analyze.py -l generic-fantasy --json

# Use custom YAML files
source .venv/bin/activate && python tools/generate.py -l ./data/generic-fantasy.yaml -n 5
source .venv/bin/activate && python tools/analyze.py -l ./my-custom-names.yaml
```

## CRITICAL Timing and Cancellation Guidelines

**NEVER CANCEL these operations:**

- **Virtual environment creation**: 3 seconds - NEVER CANCEL
- **Development installation**: 8 seconds - NEVER CANCEL  
- **Test execution**: 8 seconds for full suite - NEVER CANCEL, set timeout to 30+ seconds
- **Package building**: May take 15+ seconds or fail due to network issues - NEVER CANCEL, set timeout to 120+ seconds

**Fast operations** (complete in <1 second):
- Linting with ruff
- Code formatting checks
- CLI tool execution

## Validation Scenarios

**ALWAYS test these scenarios after making changes:**

### Core Functionality Validation
```bash
# Test basic name generation works
source .venv/bin/activate && wyrdbound-rng -l generic-fantasy -n 3

# Test advanced algorithms work  
source .venv/bin/activate && wyrdbound-rng -l generic-fantasy -n 3 -a bayesian --show-analysis

# Test Japanese segmentation works
source .venv/bin/activate && wyrdbound-rng -l japanese-sengoku -s japanese -n 3

# Test tools work with JSON output
source .venv/bin/activate && python tools/generate.py -l generic-fantasy -n 2 --json -v
source .venv/bin/activate && python tools/analyze.py -l generic-fantasy --json
```

### Code Quality Validation
```bash
# ALWAYS run before committing changes
source .venv/bin/activate && ruff check --fix src/ tests/ tools/
source .venv/bin/activate && ruff format src/ tests/ tools/
source .venv/bin/activate && python -m pytest tests/
```

## Available Built-in Name Lists

### Fantasy Names
- `generic-fantasy` - Mixed fantasy names (679 names)
- `generic-fantasy-female` - Female fantasy names  
- `generic-fantasy-male` - Male fantasy names

### Japanese Names (use with `-s japanese`)
- `japanese-sengoku` - Combined Sengoku period names
- `japanese-sengoku-clan` - Clan names
- `japanese-sengoku-daimyo` - Daimyo names
- `japanese-sengoku-religious` - Religious names
- `japanese-sengoku-rogue` - Rogue names 
- `japanese-sengoku-samurai` - Samurai names
- `japanese-sengoku-women` - Women's names
- `japanese-swordsmen` - Swordsmen names

### Other
- `warhammer40k-space-marine-names` - Warhammer 40k names

## Key Repository Structure

```
/home/runner/work/wyrdbound-rng/wyrdbound-rng/
├── src/wyrdbound_rng/           # Main source code
│   ├── cli.py                   # CLI implementation  
│   ├── generator.py             # Core name generation
│   ├── segmenters/              # Name segmentation logic
│   └── data/                    # Built-in name data files
├── tests/                       # Comprehensive test suite (65 tests)
├── tools/                       # Advanced CLI tools
│   ├── generate.py              # Advanced generation with JSON
│   └── analyze.py               # Corpus analysis tool
├── data/                        # External data files
└── pyproject.toml               # Project configuration
```

## Generation Algorithms

- `very_simple` - Basic random syllable selection
- `simple` - Weighted syllable selection (default)
- `bayesian` - Statistical probability-based generation with analysis

## Segmenters

- `fantasy` - For Western fantasy names (default)
- `japanese` - For Japanese naming patterns

## Common Error Scenarios

### File Not Found Errors
```bash
# These will fail with clear error messages:
source .venv/bin/activate && wyrdbound-rng -l invalid-list
source .venv/bin/activate && python tools/generate.py -l nonexistent-file
# Error: Could not resolve name source 'X' to a valid file
```

### Network Issues
- Package building may fail with "Read timed out" errors due to PyPI connectivity
- This is a known limitation in isolated network environments
- Development and testing work fine without building packages

## Development Workflow

1. **Setup**: Create venv and install dependencies (~12 seconds total)
2. **Code**: Make changes to source files  
3. **Validate**: Run ruff and tests (~9 seconds total)
4. **Test manually**: Use CLI tools to verify functionality works
5. **Commit**: Ensure all quality checks pass

## Test Coverage

Current test coverage: 73% (891 statements, 237 missed)
Test files cover:
- Name generation algorithms
- Segmentation logic  
- CLI functionality
- File loading and parsing
- Error handling

Areas with lower coverage:
- CLI module (0% - tested manually)
- Name list resolver (20% - file discovery logic)
- Cache adapters (61-73% - performance optimizations)