# Document Consolidation Toolkit

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Code Style](https://img.shields.io/badge/code%20style-black-black)
![Tests](https://img.shields.io/badge/tests-pytest-orange)

**Production-ready toolkit for intelligent consolidation of legal document versions using tournament-based ranking.**

## Overview

The Document Consolidation Toolkit solves a common problem in legal practice: managing multiple versions of the same document across different folders, each containing unique improvements, citations, or arguments. Instead of manually comparing versions, this toolkit uses an intelligent tournament-based ranking system to identify the best version (champion) and automatically integrate unique content from other versions.

### Key Features

- **Tournament-Based Ranking**: Multi-criteria scoring system evaluates documents on completeness, recency, structure, citations, and legal arguments
- **Intelligent Content Extraction**: Identifies truly unique content in non-champion versions using semantic similarity analysis
- **Automated Integration**: Merges improvements into champion documents while preserving source attribution
- **Quality Verification**: Validates integrated documents for formatting, structure, and consistency
- **Production-Ready**: Comprehensive logging, error handling, progress bars, and configuration management
- **Type-Safe**: Full Pydantic validation and type hints throughout

### Use Cases

- **Legal Practice**: Consolidate multiple drafts of briefs, motions, or memoranda
- **Document Evolution**: Track and merge improvements across document versions
- **Knowledge Management**: Identify and preserve best content from multiple sources
- **Quality Assurance**: Automated verification of document structure and formatting

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Tournament Ranking System](#tournament-ranking-system)
- [CLI Usage](#cli-usage)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Installation

### From PyPI (Coming Soon)

```bash
pip install document-consolidation-toolkit
```

### From Source

```bash
# Clone the repository
git clone https://github.com/LROC-NY/document-consolidation-toolkit.git
cd document-consolidation-toolkit

# Install in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### Requirements

- Python 3.9 or higher
- Dependencies: pyyaml, pydantic>=2.0, click>=8.0, tqdm

## Quick Start

### Basic Usage

```bash
# Run full consolidation pipeline with defaults
consolidate full

# Use custom configuration file
consolidate full --config config.yaml

# Run with verbose logging
consolidate full --verbose

# Override output directory
consolidate full --output-dir ./consolidated_docs
```

### Configuration File

Create a `config.yaml` file:

```yaml
# Input settings
input_directory: ~/Documents/Legal/Cases/Case-2024-001
source_folders:
  - "Draft v1"
  - "Draft v2 - Citations Added"
  - "Final Version"

# Tournament scoring weights (0-10 scale)
tournament:
  completeness_weight: 10.0    # Document length and sections
  recency_weight: 8.0          # Modification time
  structure_weight: 9.0        # Markdown quality
  citations_weight: 10.0       # Legal citation density
  arguments_weight: 9.0        # Legal argument density

# Integration settings
integration:
  output_dir: ./output/integrated
  add_evolution_metadata: true
  preserve_source_attribution: true
  integrate_citations: true
  similarity_threshold: 0.7
  min_added_lines: 3

# Verification settings
verification:
  check_markdown_formatting: true
  check_section_numbering: true
  check_no_duplication: true
  check_document_navigability: true
  max_consecutive_blank_lines: 2

# Logging
log_level: INFO
log_dir: ./output/logs
```

### Example Output

```
=== Document Consolidation Toolkit ===

Input Directory: /Users/LROC/Documents/Legal/Cases/Case-2024-001
Output Directory: ./output/integrated

Phase 1: Tournament-based ranking
  Analyzing documents: 100%|████████████████| 100/100 [00:02<00:00, 45.23it/s]
  ✓ Tournament complete

Phase 2: Extract unique content
  Processing non-champions: 100%|████████| 100/100 [00:01<00:00, 67.89it/s]
  ✓ Extraction complete

Phase 3: Integrate improvements
  Merging content: 100%|████████████████████| 100/100 [00:01<00:00, 78.45it/s]
  ✓ Integration complete

Phase 4: Verify document quality
  Running checks: 100%|█████████████████████| 100/100 [00:00<00:00, 156.32it/s]
  ✓ Verification complete

==================================================
✓ Consolidation complete!
Output directory: ./output/integrated
```

## Tournament Ranking System

The toolkit uses a sophisticated multi-criteria tournament system to rank document versions:

### Scoring Criteria (0-10 scale each)

#### 1. Completeness (Weight: 10.0)
- **Line Count**: Longer documents score higher (normalized to max)
- **Section Count**: More `##` headers indicates better structure
- **Subsection Count**: More `###` headers shows deeper organization
- **Formula**: `(lines/max_lines * 5) + (sections/10 * 3) + (subsections/20 * 2)`

#### 2. Recency (Weight: 10.0)
- **Modification Time**: More recently modified files score higher
- **Normalization**: Scores based on range from oldest to newest
- **Formula**: `((mtime - oldest) / (newest - oldest)) * 10`

#### 3. Structure (Weight: 10.0)
- **Title Presence**: Document starts with `#` header (+2.5)
- **Headers**: Contains `##` headers (+2.5)
- **Lists**: Contains bulleted or numbered lists (+2.5)
- **Code Blocks**: Contains code fences `\`\`\`` (+2.5)

#### 4. Citations (Weight: 10.0)
- **Legal Patterns**: Counts occurrences of:
  - "Matter of " (case citations)
  - "v." (versus in case names)
  - "U.S.C." (US Code)
  - "C.F.R." (Code of Federal Regulations)
  - "INA §" (Immigration and Nationality Act)
  - "Form I-" (USCIS forms)
  - "8 CFR", "8 USC"
- **Formula**: `(citation_count / max_citations) * 10`

#### 5. Arguments (Weight: 10.0)
- **Argument Keywords**: Counts legal argument indicators:
  - "therefore", "however", "moreover", "furthermore"
  - "consequently", "accordingly", "argument"
  - "demonstrates", "establishes", "pursuant to"
- **Density Metric**: Keywords per line * 100
- **Formula**: `(density / max_density) * 10`

### Total Score Calculation

```python
total_score = (
    completeness * completeness_weight +
    recency * recency_weight +
    structure * structure_weight +
    citations * citations_weight +
    arguments * arguments_weight
) / total_weight
```

### Champion Selection

The version with the highest total score becomes the **champion**. All other versions are analyzed for unique content to integrate into the champion.

## CLI Usage

### Main Commands

#### `consolidate full`

Run the complete consolidation pipeline (all four phases):

```bash
consolidate full [OPTIONS]
```

**Options:**
- `--config PATH`: Path to YAML configuration file
- `--verbose`: Enable verbose logging (DEBUG level)
- `--quiet`: Suppress console output (WARNING level only)
- `--output-dir PATH`: Override output directory

**Example:**
```bash
consolidate full --config config.yaml --verbose
```

#### `consolidate tournament`

Run only tournament-based document ranking:

```bash
consolidate tournament [OPTIONS]
```

**Output:**
- Identifies champion version for each document
- Displays score breakdowns
- Logs tournament results

**Example:**
```bash
consolidate tournament --config config.yaml
```

#### `consolidate extract`

Extract unique content from non-champion documents:

```bash
consolidate extract [OPTIONS]
```

**Process:**
1. Loads tournament results
2. Compares non-champions to champion
3. Identifies unique sections
4. Extracts improvements

**Example:**
```bash
consolidate extract --verbose
```

#### `consolidate integrate`

Integrate unique content into champion documents:

```bash
consolidate integrate [OPTIONS]
```

**Process:**
1. Loads extracted unique content
2. Merges into champion documents
3. Adds source attribution
4. Writes integrated documents to output directory

**Example:**
```bash
consolidate integrate --output-dir ./final_docs
```

#### `consolidate verify`

Verify integrated documents for quality:

```bash
consolidate verify [OPTIONS]
```

**Checks:**
- Markdown formatting compliance
- Section numbering consistency
- Duplicate section detection
- Document navigation structure

**Example:**
```bash
consolidate verify --config config.yaml
```

### Global Options

All commands support these global options:

- `--config PATH`: Path to YAML configuration file
- `--verbose`: Enable DEBUG logging
- `--quiet`: Enable WARNING-only logging
- `--output-dir PATH`: Override output directory

### Environment Variables

Override configuration with environment variables:

```bash
# Tournament weights
export TOURNAMENT_COMPLETENESS_WEIGHT=8.0
export TOURNAMENT_RECENCY_WEIGHT=9.0
export TOURNAMENT_STRUCTURE_WEIGHT=10.0
export TOURNAMENT_CITATIONS_WEIGHT=10.0
export TOURNAMENT_ARGUMENTS_WEIGHT=9.0

# Integration settings
export INTEGRATION_ADD_EVOLUTION_METADATA=true
export INTEGRATION_PRESERVE_SOURCE_ATTRIBUTION=true
export INTEGRATION_INTEGRATE_CITATIONS=true
export INTEGRATION_SKIP_CITATION_ENHANCEMENT=false

# Verification settings
export VERIFICATION_CHECK_MARKDOWN_FORMATTING=true
export VERIFICATION_CHECK_SECTION_NUMBERING=true
export VERIFICATION_CHECK_NO_DUPLICATION=true
export VERIFICATION_CHECK_DOCUMENT_NAVIGABILITY=true
export VERIFICATION_MAX_CONSECUTIVE_BLANK_LINES=2

# Core settings
export INPUT_DIRECTORY=/path/to/documents
export LOG_LEVEL=DEBUG

# Run consolidation
consolidate full
```

## Configuration

### Configuration Hierarchy

Settings are loaded in this order (later overrides earlier):

1. **Default values** (hardcoded in `settings.py`)
2. **YAML configuration file** (via `--config` flag)
3. **Environment variables** (prefix: `TOURNAMENT_`, `INTEGRATION_`, `VERIFICATION_`)
4. **CLI arguments** (e.g., `--output-dir`, `--verbose`)

### Configuration Schema

See the [full configuration reference](CONFIGURATION.md) for detailed documentation.

### Validation

All settings are validated using Pydantic:

- **Type checking**: Ensures correct data types
- **Range validation**: Weights must be 0-10
- **Path expansion**: Handles `~` and environment variables
- **Required fields**: Validates all required settings

**Example validation error:**

```
ValidationError: 1 validation error for Settings
tournament.completeness_weight
  Input should be less than or equal to 10.0 [type=less_than_equal, input_value=15.0]
```

## Architecture

### Project Structure

```
document-consolidation-toolkit/
├── src/
│   └── document_consolidation/
│       ├── __init__.py
│       ├── __main__.py              # Entry point
│       ├── cli.py                   # Click-based CLI
│       ├── config/                  # Configuration system
│       │   ├── __init__.py
│       │   ├── settings.py          # Pydantic settings
│       │   └── logging_config.py    # Logging setup
│       ├── models/                  # Data models
│       │   ├── __init__.py
│       │   └── document.py          # Pydantic models
│       ├── core/                    # Core algorithms
│       │   ├── __init__.py
│       │   ├── tournament.py        # Tournament ranking
│       │   ├── extractor.py         # Content extraction
│       │   ├── integrator.py        # Content integration
│       │   └── verifier.py          # Quality verification
│       └── storage/                 # Data access layer
│           ├── __init__.py
│           ├── document_repository.py
│           └── filesystem_repository.py
├── tests/
│   ├── unit/                        # Unit tests
│   ├── integration/                 # Integration tests
│   └── conftest.py                  # Pytest fixtures
├── config.yaml                      # Example configuration
├── pyproject.toml                   # Package metadata
├── README.md                        # This file
├── CLAUDE.md                        # AI assistant instructions
└── LICENSE                          # MIT License
```

### Design Patterns

- **Repository Pattern**: Abstracts document storage and retrieval
- **Pydantic Models**: Type-safe data validation and serialization
- **Dependency Injection**: Settings passed through constructors
- **Single Responsibility**: Each module has one clear purpose
- **Layered Architecture**: CLI → Core → Storage

### Key Components

#### Configuration System (`config/`)
- **Pydantic-based validation**: Type safety and runtime checks
- **YAML + environment variables**: Flexible configuration sources
- **Nested settings**: Organized by subsystem (tournament, integration, verification)

#### Data Models (`models/`)
- **DocumentMetadata**: File metadata and content
- **ScoreBreakdown**: Tournament scoring details
- **TournamentResult**: Champion identification results
- **UniqueImprovement**: Extracted unique content
- **IntegrationResult**: Integration outcome
- **VerificationResult**: Quality check results

#### Core Algorithms (`core/`)
- **Tournament**: Multi-criteria document ranking
- **Extractor**: Unique content identification
- **Integrator**: Content merging and attribution
- **Verifier**: Quality assurance checks

#### Storage Layer (`storage/`)
- **DocumentRepository**: Abstract interface
- **FilesystemRepository**: File system implementation
- Supports future extensions (database, cloud storage)

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/LROC-NY/document-consolidation-toolkit.git
cd document-consolidation-toolkit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (if available)
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=document_consolidation --cov-report=html

# Run specific test file
pytest tests/unit/test_tournament.py

# Run with verbose output
pytest -v

# Run integration tests only
pytest tests/integration/
```

### Code Quality

```bash
# Format code with Black
black src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Type checking with mypy
mypy src/

# Run all quality checks
black src/ tests/ && ruff check src/ tests/ && mypy src/
```

### Project Conventions

- **Code style**: Black (line length 100)
- **Linting**: Ruff (E, F, I rules)
- **Type hints**: Required for all public APIs
- **Docstrings**: Google style for all modules, classes, functions
- **Testing**: Pytest with fixtures and parametrization
- **Logging**: Structured logging with context data

### Making Changes

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes with tests
3. Run quality checks: `black`, `ruff`, `mypy`
4. Run tests: `pytest`
5. Commit with descriptive messages
6. Push and create pull request

## Contributing

Contributions are welcome! Please follow these guidelines:

### Reporting Issues

- Use GitHub Issues
- Provide minimal reproducible example
- Include Python version, OS, and dependency versions
- Attach relevant log files

### Pull Requests

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation
6. Submit pull request with clear description

### Code Review Criteria

- Passes all tests
- Maintains or improves code coverage
- Follows project conventions
- Includes documentation updates
- Has clear commit messages

### Development Process

This project follows a phased refactoring approach:

- **Phase 1**: Configuration system (COMPLETE)
- **Phase 2**: CLI implementation (COMPLETE)
- **Phase 3**: Documentation (CURRENT)
- **Phase 4**: Core algorithms
- **Phase 5**: Integration layer
- **Phase 6**: Testing infrastructure
- **Phase 7**: Production deployment

See `REFACTORING_SUMMARY.md` for detailed status.

## License

MIT License

Copyright (c) 2024 LROC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Support

- **Documentation**: See `CLAUDE.md` for AI assistant guidance
- **Issues**: GitHub Issues
- **Email**: [Your contact email]

## Acknowledgments

- Built with [Click](https://click.palletsprojects.com/) for CLI
- Configuration via [Pydantic](https://docs.pydantic.dev/)
- Progress bars by [tqdm](https://tqdm.github.io/)
- Developed for legal practice at LROC

---

**Made with care for legal professionals who value precision and efficiency.**
