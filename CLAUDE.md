# CLAUDE.md

AI assistant instructions for working with the Document Consolidation Toolkit.

## Project Overview

This is a **production-ready Python toolkit** for consolidating multiple versions of legal documents using tournament-based ranking. The project is in Phase 3 of a 7-phase refactoring process.

**Current Status**: Phases 1-2 complete (configuration system + CLI). Phase 3 in progress (documentation).

**Technology Stack**:
- Python 3.9+
- Pydantic 2.0+ (settings and models)
- Click 8.0+ (CLI framework)
- PyYAML (configuration)
- tqdm (progress bars)
- pytest (testing)

## Critical Architecture Principles

### 1. Configuration Philosophy

**Pydantic-Based Settings System** (`src/document_consolidation/config/settings.py`):
- All settings defined as Pydantic models with validation
- Nested settings: `TournamentSettings`, `IntegrationSettings`, `VerificationSettings`
- Configuration hierarchy: defaults → YAML file → environment variables → CLI args
- Path expansion: Handles `~`, environment variables, absolute/relative paths
- Type safety: Runtime validation, auto-conversion, range checking

**Key Pattern**:
```python
# Load settings
from document_consolidation.config import load_settings, Settings
settings = load_settings(config_path)  # Validates and merges all sources

# Access nested settings
settings.tournament.completeness_weight  # Type-safe access
settings.integration.output_dir  # Path object, expanded/resolved
```

**Never bypass the settings system**. Always use `Settings` objects, never raw dicts or globals.

### 2. Data Model Philosophy

**All data structures are Pydantic models** (`src/document_consolidation/models/document.py`):
- `DocumentMetadata`: File content and metadata
- `ScoreBreakdown`: Tournament scoring details
- `TournamentResult`: Champion identification
- `UniqueImprovement`: Extracted content
- `IntegrationResult`: Integration outcome
- `VerificationResult`: Quality verification

**Key Pattern**:
```python
from document_consolidation.models import TournamentResult, ScoreBreakdown

result = TournamentResult(
    filename="brief.md",
    champion_folder="v3",
    champion_score=42.5,
    # ... Pydantic validates all fields
)

# Type-safe access
print(result.champion_score)  # float
print(result.champion_path)   # Path object
```

**Always use Pydantic models, never raw dicts**. This gives us validation, type safety, and serialization.

### 3. Logging Philosophy

**Structured logging with context** (`src/document_consolidation/config/logging_config.py`):
- Standard library `logging` module
- File + console handlers
- Structured extra data in log records
- Log levels: DEBUG, INFO, WARNING, ERROR

**Key Pattern**:
```python
from document_consolidation.config import get_logger

logger = get_logger(__name__)

# Log with structured context
logger.info(
    "Tournament complete",
    extra={
        "champion": champion_folder,
        "score": score.total,
        "versions": len(versions),
    }
)
```

**Never use print statements**. Always use the logger with structured context data.

### 4. Repository Pattern

**Abstract storage layer** (`src/document_consolidation/storage/`):
- `DocumentRepository`: Abstract base class (ABC)
- `FilesystemRepository`: Concrete implementation
- Future: Database, cloud storage, etc.

**Key Pattern**:
```python
from document_consolidation.storage import FilesystemRepository

repo = FilesystemRepository()
documents = repo.find_documents(folder_path, "*.md")
# Returns List[DocumentMetadata] with validation
```

**Always use repository interface, never direct file I/O**. This allows swapping storage backends.

### 5. Error Handling Philosophy

**Comprehensive error handling**:
- Validate inputs early (Pydantic does this)
- Catch specific exceptions, not bare `except:`
- Log errors with context before raising
- User-friendly CLI error messages (Click)

**Key Pattern**:
```python
try:
    result = some_operation()
except ValueError as e:
    logger.error("Operation failed", extra={"error": str(e)}, exc_info=True)
    click.secho(f"Error: {e}", fg="red", err=True)
    sys.exit(1)
```

## Project Structure Guide

### Source Code Organization

```
src/document_consolidation/
├── __init__.py              # Package exports
├── __main__.py              # Entry point (python -m document_consolidation)
├── cli.py                   # Click-based CLI (main commands)
├── config/                  # Configuration subsystem
│   ├── __init__.py          # Exports: load_settings, Settings, get_logger
│   ├── settings.py          # Pydantic settings models
│   └── logging_config.py    # Logging setup
├── models/                  # Data models
│   ├── __init__.py          # Model exports
│   └── document.py          # All Pydantic models
├── core/                    # Core algorithms (Phase 4-5)
│   ├── __init__.py
│   ├── tournament.py        # Tournament ranking (Phase 4.1-4.2)
│   ├── extractor.py         # Content extraction (Phase 4.3)
│   ├── integrator.py        # Content integration (Phase 4.4)
│   └── verifier.py          # Quality verification (Phase 4.5)
└── storage/                 # Data access layer
    ├── __init__.py
    ├── document_repository.py    # Abstract repository
    └── filesystem_repository.py  # File system implementation
```

### Test Organization

```
tests/
├── conftest.py              # Pytest fixtures (shared)
├── unit/                    # Unit tests
│   ├── test_models.py       # Pydantic model tests
│   ├── test_tournament.py   # Tournament algorithm tests
│   ├── test_extractor.py    # Extractor tests
│   ├── test_integrator.py   # Integrator tests
│   ├── test_verifier.py     # Verifier tests
│   └── test_repository.py   # Repository tests
└── integration/             # Integration tests
    ├── test_configuration.py    # Config loading tests
    └── test_full_workflow.py    # End-to-end tests
```

## Development Workflow

### Making Changes

1. **Read existing code first**: Understand patterns before adding new code
2. **Follow existing patterns**: Match style, logging, error handling
3. **Add tests**: Unit tests for logic, integration tests for workflows
4. **Update docs**: Keep README.md and CLAUDE.md in sync
5. **Run quality checks**: `black`, `ruff`, `mypy`, `pytest`

### Testing Strategy

**Unit Tests** (`tests/unit/`):
- Test individual functions/methods in isolation
- Use fixtures for setup (see `conftest.py`)
- Mock external dependencies
- Fast execution (<1 second per test)

**Integration Tests** (`tests/integration/`):
- Test component interactions
- Use real file system (temp directories)
- Test configuration loading
- Test full workflows

**Example Test Pattern**:
```python
import pytest
from document_consolidation.core.tournament import DocumentTournament
from document_consolidation.models import DocumentMetadata

def test_tournament_scoring(sample_documents):
    """Test tournament scoring with sample documents."""
    tournament = DocumentTournament(sample_documents, mock_repo)

    score = tournament.score_completeness("v1")

    assert 0 <= score <= 10
    assert isinstance(score, float)
```

### Code Style Guidelines

**Black Formatting** (line length 100):
```bash
black src/ tests/
```

**Ruff Linting**:
```bash
ruff check src/ tests/
```

**Type Hints**:
- Required for all public functions/methods
- Use `from typing import` for generics
- Pydantic models provide runtime validation

**Docstrings** (Google style):
```python
def score_completeness(self, version_key: str) -> float:
    """Score based on document length and section count.

    Args:
        version_key: Folder name key

    Returns:
        Completeness score (0-10)

    Raises:
        ValueError: If version_key not found
    """
```

## Common Pitfalls and Solutions

### Pitfall 1: Bypassing Settings System

**Wrong**:
```python
# Hardcoded paths
output_dir = Path("./output")

# Global variables
COMPLETENESS_WEIGHT = 10.0
```

**Right**:
```python
from document_consolidation.config import load_settings

settings = load_settings(config_path)
output_dir = settings.integration.output_dir
weight = settings.tournament.completeness_weight
```

### Pitfall 2: Using Raw Dicts Instead of Models

**Wrong**:
```python
result = {
    "filename": "brief.md",
    "champion": "v3",
    "score": 42.5,
}
```

**Right**:
```python
from document_consolidation.models import TournamentResult

result = TournamentResult(
    filename="brief.md",
    champion_folder="v3",
    champion_score=42.5,
    # Pydantic validates types and required fields
)
```

### Pitfall 3: Direct File I/O

**Wrong**:
```python
with open("document.md", "r") as f:
    content = f.read()
```

**Right**:
```python
from document_consolidation.storage import FilesystemRepository

repo = FilesystemRepository()
documents = repo.find_documents(folder_path, "*.md")
# Returns validated DocumentMetadata objects
```

### Pitfall 4: Using print() Instead of Logging

**Wrong**:
```python
print(f"Processing {filename}")
print(f"Score: {score}")
```

**Right**:
```python
from document_consolidation.config import get_logger

logger = get_logger(__name__)
logger.info(
    "Processing document",
    extra={"filename": filename, "score": score}
)
```

### Pitfall 5: Bare Exception Handling

**Wrong**:
```python
try:
    result = process()
except:
    pass
```

**Right**:
```python
try:
    result = process()
except ValueError as e:
    logger.error("Processing failed", extra={"error": str(e)}, exc_info=True)
    raise
except FileNotFoundError as e:
    logger.error("File not found", extra={"path": str(path)})
    raise
```

## Debugging Tips

### Enable Debug Logging

```bash
# Via CLI
consolidate full --verbose

# Via environment variable
export LOG_LEVEL=DEBUG
consolidate full

# Via config file
log_level: DEBUG
```

### Check Log Files

```bash
# Default location: output/logs/
tail -f output/logs/document_consolidation.log

# View structured log data
grep "Tournament complete" output/logs/document_consolidation.log
```

### Common Debug Scenarios

**Configuration not loading**:
```python
# Verify config file is valid YAML
import yaml
with open("config.yaml") as f:
    print(yaml.safe_load(f))

# Check settings object
from document_consolidation.config import load_settings
settings = load_settings(Path("config.yaml"))
print(settings.model_dump())
```

**Tournament scoring issues**:
```python
# Enable debug logging for specific module
import logging
logging.getLogger("document_consolidation.core.tournament").setLevel(logging.DEBUG)

# Check score breakdown
tournament = DocumentTournament(versions, repo)
breakdown = tournament.evaluate_version("v1")
print(f"Completeness: {breakdown.completeness}")
print(f"Recency: {breakdown.recency}")
print(f"Total: {breakdown.total}")
```

**Path resolution issues**:
```python
# Check path expansion
from pathlib import Path
import os

path = Path("~/Documents/Cases").expanduser().resolve()
print(f"Expanded: {path}")
print(f"Exists: {path.exists()}")
```

## File Navigation Quick Reference

### Configuration System
- `src/document_consolidation/config/settings.py:19-82` - TournamentSettings
- `src/document_consolidation/config/settings.py:83-130` - IntegrationSettings
- `src/document_consolidation/config/settings.py:160-238` - Main Settings class
- `src/document_consolidation/config/settings.py:240-275` - load_settings function
- `src/document_consolidation/config/logging_config.py:18-107` - setup_logging

### CLI Implementation
- `src/document_consolidation/cli.py:26-104` - Main CLI group
- `src/document_consolidation/cli.py:107-204` - full command
- `src/document_consolidation/cli.py:206-242` - tournament command
- `src/document_consolidation/cli.py:244-277` - extract command
- `src/document_consolidation/cli.py:279-314` - integrate command
- `src/document_consolidation/cli.py:316-351` - verify command

### Data Models
- `src/document_consolidation/models/document.py:13-35` - DocumentMetadata
- `src/document_consolidation/models/document.py:37-56` - ScoreBreakdown
- `src/document_consolidation/models/document.py:58-82` - TournamentResult
- `src/document_consolidation/models/document.py:84-92` - SectionData
- `src/document_consolidation/models/document.py:94-112` - UniqueImprovement
- `src/document_consolidation/models/document.py:114-147` - IntegrationResult
- `src/document_consolidation/models/document.py:149-187` - VerificationResult

### Core Algorithms
- `src/document_consolidation/core/tournament.py:24-312` - DocumentTournament class
- `src/document_consolidation/core/tournament.py:42-77` - score_completeness
- `src/document_consolidation/core/tournament.py:79-106` - score_recency
- `src/document_consolidation/core/tournament.py:107-142` - score_structure
- `src/document_consolidation/core/tournament.py:143-186` - score_citations
- `src/document_consolidation/core/tournament.py:187-246` - score_arguments
- `src/document_consolidation/core/tournament.py:314-486` - TournamentEngine class

### Storage Layer
- `src/document_consolidation/storage/document_repository.py:14-69` - DocumentRepository ABC
- `src/document_consolidation/storage/filesystem_repository.py:16-125` - FilesystemRepository

## Phase-Specific Guidance

### Phase 1 (COMPLETE): Configuration System
- Pydantic settings with validation ✓
- YAML configuration loading ✓
- Environment variable overrides ✓
- Logging configuration ✓

### Phase 2 (COMPLETE): CLI Implementation
- Click-based command structure ✓
- Global options and flags ✓
- Progress bars with tqdm ✓
- Error handling and exit codes ✓

### Phase 3 (CURRENT): Documentation
- **Focus**: README.md, CLAUDE.md, pyproject.toml
- **Goal**: Production-ready documentation
- **Status**: In progress

### Phase 4 (UPCOMING): Core Algorithms
- Tournament ranking (existing code needs refactoring)
- Content extraction
- Content integration
- Quality verification
- **Key**: Connect to settings system, add comprehensive logging

### Phase 5 (UPCOMING): Integration Layer
- Wire up CLI commands to core algorithms
- Remove placeholder code in cli.py
- Add progress reporting
- Integration tests

### Phase 6 (UPCOMING): Testing Infrastructure
- Expand unit test coverage
- Add integration tests
- Add fixtures for test data
- Setup CI/CD

### Phase 7 (UPCOMING): Production Deployment
- Package for PyPI
- Setup GitHub Actions
- Add pre-commit hooks
- Performance optimization

## Best Practices Checklist

When adding new code, ensure:

- [ ] Uses Pydantic models for all data structures
- [ ] Loads settings via `load_settings()` or dependency injection
- [ ] Uses `get_logger(__name__)` for logging
- [ ] Includes structured context in log records
- [ ] Has type hints on all public functions/methods
- [ ] Includes Google-style docstrings
- [ ] Has unit tests with >80% coverage
- [ ] Follows Black formatting (line length 100)
- [ ] Passes Ruff linting (E, F, I rules)
- [ ] Passes mypy type checking (strict mode)
- [ ] Uses repository pattern for file access
- [ ] Handles errors with specific exceptions
- [ ] Has CLI integration (if user-facing)
- [ ] Updates documentation (README.md, CLAUDE.md)

## Key Design Decisions

### Why Pydantic 2.0?
- Runtime validation catches configuration errors early
- Type safety without runtime overhead (Rust core)
- Automatic JSON/dict serialization
- Model composition (nested settings)

### Why Click for CLI?
- Industry standard for Python CLIs
- Automatic help text generation
- Nested command groups
- Argument validation and type conversion
- Context passing between commands

### Why Repository Pattern?
- Abstracts storage implementation
- Enables testing with mock repositories
- Future-proof for database/cloud storage
- Separates business logic from data access

### Why Structured Logging?
- Machine-parseable log records
- Rich context for debugging
- Integration with log aggregation tools
- Better than string concatenation

## Quick Command Reference

```bash
# Development setup
pip install -e ".[dev]"

# Run full pipeline
consolidate full --config config.yaml --verbose

# Run tests
pytest                              # All tests
pytest tests/unit/                  # Unit tests only
pytest --cov=document_consolidation # With coverage

# Code quality
black src/ tests/                   # Format
ruff check src/ tests/              # Lint
mypy src/                           # Type check

# Debugging
consolidate full --verbose          # Debug logging
export LOG_LEVEL=DEBUG              # Environment variable
tail -f output/logs/*.log          # Watch logs
```

## When You Get Stuck

1. **Check existing patterns**: Look at how other modules do it
2. **Read the tests**: Tests show usage examples
3. **Enable debug logging**: `--verbose` flag or `LOG_LEVEL=DEBUG`
4. **Check log files**: `output/logs/document_consolidation.log`
5. **Validate configuration**: Print `settings.model_dump()`
6. **Use type checking**: `mypy` catches many issues
7. **Read the models**: Pydantic validation errors are very specific

## Remember

This is a **production-ready legal tool**. Code quality, error handling, logging, and documentation are not optional. Every line of code should be:

- Type-safe (Pydantic + mypy)
- Validated (Pydantic models)
- Logged (structured context)
- Tested (unit + integration)
- Documented (docstrings + README)

The extra effort pays off in maintainability, debuggability, and user trust.
