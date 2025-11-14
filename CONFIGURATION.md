# Configuration System Documentation

## Overview

The document consolidation toolkit uses a production-ready configuration system built on Pydantic with support for:

- YAML configuration files
- Environment variable overrides
- Nested settings structures
- Comprehensive validation
- Type safety with type hints
- Smart defaults for legal document consolidation

## Quick Start

### Basic Usage

```python
from document_consolidation.config import settings, get_logger, setup_logging

# Setup logging
setup_logging(settings.log_dir, settings.log_level)

# Get logger for your module
logger = get_logger(__name__)

# Access configuration
logger.info(f"Scanning {len(settings.source_folders)} folders")
logger.info(f"Input directory: {settings.input_directory}")

# Access nested settings
print(f"Completeness weight: {settings.tournament.completeness_weight}")
print(f"Output directory: {settings.integration.output_dir}")
```

### Loading Custom Configuration

```python
from pathlib import Path
from document_consolidation.config import load_settings, setup_logging

# Load from YAML file
config = load_settings(Path("config.yaml"))

# Setup logging with custom config
setup_logging(config.log_dir, config.log_level)

# Use custom configuration
print(f"Tournament weights total: {config.tournament.total_weight}")
```

## Configuration Structure

### Settings Classes

#### 1. `Settings` (Root)

Main application settings with nested subsystem configurations.

**Attributes:**
- `input_directory: Path` - Base directory containing source folders (default: current directory)
- `source_folders: List[str]` - Source folders to scan (default: ["Markdown Document 2", "Markdown Document 3", "Markdown Document 4"])
- `file_pattern: str` - File pattern for discovery (default: "*.md")
- `log_level: str` - Logging level (default: "INFO")
- `log_dir: Optional[Path]` - Log directory (default: output_dir/logs)
- `tournament: TournamentSettings` - Tournament scoring config
- `integration: IntegrationSettings` - Content integration config
- `verification: VerificationSettings` - Document verification config

#### 2. `TournamentSettings`

Tournament scoring configuration.

**Attributes:**
- `completeness_weight: float` - Weight for document completeness (0-10, default: 10.0)
- `recency_weight: float` - Weight for modification recency (0-10, default: 10.0)
- `structure_weight: float` - Weight for markdown structure (0-10, default: 10.0)
- `citations_weight: float` - Weight for legal citations (0-10, default: 10.0)
- `arguments_weight: float` - Weight for legal arguments (0-10, default: 10.0)

**Properties:**
- `total_weight: float` - Sum of all weights

#### 3. `IntegrationSettings`

Content integration configuration.

**Attributes:**
- `output_dir: Path` - Output directory (default: "output")
- `add_evolution_metadata: bool` - Add evolution metadata (default: True)
- `preserve_source_attribution: bool` - Preserve source info (default: True)
- `integrate_citations: bool` - Integrate citations (default: True)
- `skip_citation_enhancement: bool` - Skip citation enhancement (default: False)
- `similarity_threshold: float` - Section similarity threshold (0-1, default: 0.7)
- `min_added_lines: int` - Minimum lines for unique content (default: 3)

#### 4. `VerificationSettings`

Document verification configuration.

**Attributes:**
- `check_markdown_formatting: bool` - Check markdown formatting (default: True)
- `check_section_numbering: bool` - Check section numbering (default: True)
- `check_no_duplication: bool` - Check for duplicates (default: True)
- `check_document_navigability: bool` - Check navigation (default: True)
- `max_consecutive_blank_lines: int` - Max consecutive blanks (default: 2)

## Configuration Methods

### YAML Configuration

Create a `config.yaml` file (see `config.example.yaml` for template):

```yaml
input_directory: "~/Documents/LegalDocs"

source_folders:
  - "Markdown Document 2"
  - "Markdown Document 3"
  - "Markdown Document 4"

tournament:
  completeness_weight: 8.0
  citations_weight: 12.0  # ERROR: Max is 10.0

integration:
  output_dir: "output"
  similarity_threshold: 0.8

verification:
  max_consecutive_blank_lines: 3
```

Load with:

```python
from document_consolidation.config import load_settings

config = load_settings(Path("config.yaml"))
```

### Environment Variables

Override settings via environment variables:

```bash
# Tournament settings
export TOURNAMENT_COMPLETENESS_WEIGHT=8.0
export TOURNAMENT_RECENCY_WEIGHT=9.0

# Integration settings
export INTEGRATION_ADD_EVOLUTION_METADATA=false
export INTEGRATION_OUTPUT_DIR=custom_output

# Verification settings
export VERIFICATION_MAX_CONSECUTIVE_BLANK_LINES=3

# Top-level settings
export INPUT_DIRECTORY=~/Documents/LegalDocs
export LOG_LEVEL=DEBUG
```

Environment variables take precedence over YAML configuration.

### Programmatic Configuration

```python
from pathlib import Path
from document_consolidation.config import Settings, TournamentSettings

# Create custom configuration
config = Settings(
    input_directory=Path("/custom/path"),
    source_folders=["folder1", "folder2"],
    tournament=TournamentSettings(
        completeness_weight=8.0,
        citations_weight=12.0,  # Will raise ValidationError
    ),
)
```

## Logging System

### Setup Logging

```python
from pathlib import Path
from document_consolidation.config import setup_logging, get_logger

# Setup with defaults (INFO level, console + file)
setup_logging()

# Setup with custom parameters
setup_logging(
    log_dir=Path("logs"),
    log_level="DEBUG",
    console_output=True,
    file_output=True,
)

# Get logger for module
logger = get_logger(__name__)
```

### Logging Output

**Console Output** (colored, INFO level):
```
INFO | document_consolidation.tournament | Starting tournament execution
WARNING | document_consolidation.extractor | Section similarity below threshold
ERROR | document_consolidation.verifier | Validation failed
```

**File Output** (`consolidation.log`, DEBUG level):
```
2024-11-14 15:03:42 | INFO     | document_consolidation.tournament | run_tournament:278 | Tournament started
2024-11-14 15:03:43 | DEBUG    | document_consolidation.tournament | score_completeness:67 | Completeness score calculated
2024-11-14 15:03:44 | WARNING  | document_consolidation.extractor | extract_sections:123 | Low similarity detected
```

**Error Log** (`errors.log`, ERROR level):
```
2024-11-14 15:03:45 | ERROR    | document_consolidation.verifier | verify_document:234 | Validation failed: Duplicate section
2024-11-14 15:03:46 | CRITICAL | document_consolidation.engine | execute:456 | Fatal error in consolidation
```

### Log Rotation

- **Max file size**: 10 MB
- **Backup count**: 5 files
- **Encoding**: UTF-8

Old logs are automatically rotated to:
- `consolidation.log.1`
- `consolidation.log.2`
- etc.

## Validation

All settings are validated on creation:

```python
from document_consolidation.config import TournamentSettings

# Valid
settings = TournamentSettings(completeness_weight=8.0)

# Invalid - raises ValidationError
settings = TournamentSettings(completeness_weight=15.0)  # > 10.0
settings = TournamentSettings(completeness_weight=-1.0)  # < 0.0
settings = TournamentSettings(completeness_weight="invalid")  # Not numeric
```

## Global Settings Instance

The config module provides a global settings instance:

```python
from document_consolidation.config import settings

# Access global settings
print(settings.input_directory)

# Reset global settings (useful for testing)
from document_consolidation.config import reset_settings
reset_settings()
```

## Examples

### Example 1: Custom Tournament Weights

Emphasize recent documents with citations:

```python
config = Settings(
    tournament=TournamentSettings(
        completeness_weight=7.0,
        recency_weight=10.0,        # Emphasize recent
        structure_weight=7.0,
        citations_weight=10.0,      # Emphasize citations
        arguments_weight=8.0,
    )
)
```

### Example 2: Minimal Integration

Skip metadata and attribution:

```python
config = Settings(
    integration=IntegrationSettings(
        add_evolution_metadata=False,
        preserve_source_attribution=False,
        integrate_citations=False,
    )
)
```

### Example 3: Strict Verification

```python
config = Settings(
    verification=VerificationSettings(
        check_markdown_formatting=True,
        check_section_numbering=True,
        check_no_duplication=True,
        check_document_navigability=True,
        max_consecutive_blank_lines=1,  # Very strict
    )
)
```

## Best Practices

1. **Use YAML for project configuration**: Keep settings in version control
2. **Use environment variables for secrets**: Never commit secrets to YAML
3. **Use environment variables for deployment**: Override settings per environment
4. **Validate early**: Load and validate settings at application startup
5. **Use type hints**: Leverage IDE autocomplete and type checking
6. **Log configuration**: Log loaded settings for debugging

## Troubleshooting

### ValidationError: Weight out of range

```python
# Error: completeness_weight must be between 0 and 10, got 15.0
```

**Solution**: Ensure all tournament weights are 0-10.

### ModuleNotFoundError: No module named 'yaml'

**Solution**: Install dependencies:
```bash
pip install pydantic pyyaml
```

### Path not found errors

**Solution**: Use absolute paths or ensure paths exist:
```python
config = Settings(
    input_directory=Path("/absolute/path/to/documents").resolve()
)
```

### Settings not updating

**Solution**: Reset global settings:
```python
from document_consolidation.config import reset_settings
reset_settings()
# Next import will reload settings
```

## API Reference

### Functions

- `load_settings(config_path: Optional[Path] = None) -> Settings`
  - Load settings from YAML file with environment overrides

- `get_settings() -> Settings`
  - Get global settings instance (lazy-loaded)

- `reset_settings() -> None`
  - Reset global settings instance

- `setup_logging(log_dir: Optional[Path] = None, log_level: str = "INFO", console_output: bool = True, file_output: bool = True) -> None`
  - Setup logging configuration

- `get_logger(name: str) -> logging.Logger`
  - Get logger instance for module

### Module Exports

```python
from document_consolidation.config import (
    # Settings classes
    Settings,
    TournamentSettings,
    IntegrationSettings,
    VerificationSettings,
    # Settings functions
    load_settings,
    get_settings,
    reset_settings,
    settings,  # Global instance
    # Logging functions
    setup_logging,
    get_logger,
)
```

## Files

- **`src/document_consolidation/config/settings.py`** (385 lines) - Settings classes and validation
- **`src/document_consolidation/config/logging_config.py`** (188 lines) - Logging configuration
- **`src/document_consolidation/config/__init__.py`** (49 lines) - Public API exports
- **`config.example.yaml`** - Example configuration file

## Testing

The configuration system includes comprehensive integration tests:

```bash
pytest tests/integration/test_configuration.py -v
```

Test coverage:
- Default settings loading
- YAML configuration loading
- Environment variable overrides
- Validation (weights, paths, types)
- Nested settings structures
- Settings persistence (round-trip)
- Edge cases (Unicode, special chars, empty values)
