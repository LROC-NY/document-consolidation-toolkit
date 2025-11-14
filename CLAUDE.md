# CLAUDE.md - Document Consolidation Toolkit

Project-specific guidance for Claude Code when working on this repository.

## Project Overview

**Purpose**: Production-ready document consolidation using tournament-based ranking to transform scattered document versions into comprehensive master documents.

**Origin**: Migrated from Google Drive scripts (Phase 4 completion) to production repository.

**Tech Stack**:
- **Language**: Python 3.12+
- **Package Manager**: uv (preferred) or pip
- **Framework**: Click (CLI), FastAPI (API), Streamlit (Web UI)
- **ORM**: SQLAlchemy with Alembic migrations
- **Testing**: pytest with 70%+ coverage target
- **Code Quality**: ruff (linter/formatter), mypy (type checker), bandit (security)

## Repository Structure

```
document-consolidation-toolkit/
├── src/document_consolidation/     # Main package
│   ├── core/                       # Business logic (tournament, extractor, integrator, verifier)
│   ├── models/                     # Pydantic models and dataclasses
│   ├── storage/                    # Database layer (SQLAlchemy, repositories)
│   ├── api/                        # FastAPI endpoints
│   ├── ui/                         # Streamlit web interface
│   ├── cli/                        # Click command-line interface
│   └── config/                     # Configuration management
├── tests/                          # Test suite
│   ├── unit/                       # Unit tests (fast, isolated)
│   ├── integration/                # Integration tests (database, API)
│   └── performance/                # Performance benchmarks
├── docs/                           # Documentation
├── examples/                       # Example configurations and usage
└── scripts/                        # Utility scripts

```

## Development Commands

### Common Operations

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies (development mode)
uv pip install -e ".[dev]"

# Run all tests
pytest

# Run specific test types
pytest tests/unit -m unit               # Unit tests only
pytest tests/integration -m integration # Integration tests
pytest tests/performance -m performance # Performance tests

# Code quality checks
ruff check .                            # Linting
ruff format .                           # Formatting
mypy src/                               # Type checking
bandit -r src/                          # Security audit

# Coverage report
pytest --cov=document_consolidation --cov-report=html
# View at: htmlcov/index.html

# Run CLI
doc-consolidate --help
doc-consolidate tournament --input-dirs "path1" "path2"

# Run API server
uvicorn document_consolidation.api.main:app --reload

# Run Web UI
streamlit run src/document_consolidation/ui/app.py

# Database migrations
alembic revision --autogenerate -m "Add tables"
alembic upgrade head
alembic downgrade -1
```

### Git Workflow

```bash
# Feature development
git checkout -b feature/citation-integration
# ... make changes ...
git add .
git commit -m "feat: add citation extraction to integrator"
git push -u origin feature/citation-integration

# Create PR
gh pr create --title "Add citation integration" --body "..."

# After merge
git checkout main
git pull origin main
git branch -d feature/citation-integration
```

## Architecture Patterns

### 1. Configuration Management

**Pattern**: Pydantic Settings with YAML support

```python
# src/document_consolidation/config/settings.py
from pydantic_settings import BaseSettings
from pathlib import Path

class TournamentSettings(BaseSettings):
    completeness_weight: int = 10
    recency_weight: int = 10
    structure_weight: int = 10
    citations_weight: int = 10
    arguments_weight: int = 10

    class Config:
        env_prefix = "TOURNAMENT_"  # Read from TOURNAMENT_* env vars

# Usage
settings = TournamentSettings()
```

**Why**: Eliminates hardcoded paths and magic numbers. Supports environment variables, YAML files, and validation.

### 2. Repository Pattern

**Pattern**: Database abstraction layer

```python
# src/document_consolidation/storage/repositories/tournament.py
from abc import ABC, abstractmethod

class TournamentRepository(ABC):
    @abstractmethod
    async def save_result(self, result: TournamentResult) -> int:
        pass

    @abstractmethod
    async def get_result(self, result_id: int) -> TournamentResult:
        pass

class SQLAlchemyTournamentRepository(TournamentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_result(self, result: TournamentResult) -> int:
        # Implementation using SQLAlchemy
        ...
```

**Why**: Decouples business logic from database implementation. Enables testing with mock repositories.

### 3. Type Safety

**Pattern**: Full type hints with mypy strict mode

```python
from typing import List, Dict, Optional
from pathlib import Path

def score_completeness(
    content: str,
    versions: Dict[str, DocumentVersion]
) -> float:
    """Score document completeness.

    Args:
        content: Document content to score
        versions: All versions for comparison

    Returns:
        Completeness score (0.0-10.0)
    """
    ...
```

**Why**: Catches bugs at development time. Improves IDE autocomplete. Self-documenting code.

### 4. Structured Logging

**Pattern**: Replace `print()` with structured logging

```python
import logging
from document_consolidation.config import get_logger

logger = get_logger(__name__)

# Bad (original scripts)
print(f"✓ Loaded {len(results)} results")

# Good (production)
logger.info(
    "Tournament results loaded",
    extra={
        "results_count": len(results),
        "duration_ms": elapsed_time,
    }
)
```

**Why**: Enables filtering, log levels, structured data for analysis. Essential for production debugging.

### 5. Progress Indicators

**Pattern**: tqdm for long-running operations

```python
from tqdm import tqdm

for filename, data in tqdm(results.items(), desc="Integrating documents"):
    integrate_document(filename, data)
```

**Why**: User feedback for long operations. Better UX than silent processing.

## Testing Strategy

### Unit Tests (Fast, Isolated)

```python
# tests/unit/core/test_tournament.py
from document_consolidation.core import DocumentTournament

def test_score_completeness():
    """Test completeness scoring algorithm."""
    tournament = DocumentTournament(input_dirs=[])

    # Arrange
    content = "# Header\n\n## Section 1\n\nContent..."
    versions = {
        "v1": {"lines": 100, "content": "short"},
        "v2": {"lines": 200, "content": "longer"},
    }

    # Act
    score = tournament.score_completeness(content, versions)

    # Assert
    assert 0.0 <= score <= 10.0
    assert score > 5.0  # Should be above average
```

### Integration Tests (Database, API)

```python
# tests/integration/api/test_tournament_endpoint.py
import pytest
from httpx import AsyncClient

@pytest.mark.integration
async def test_run_tournament_endpoint(client: AsyncClient):
    """Test tournament API endpoint end-to-end."""
    response = await client.post(
        "/api/v1/tournament",
        json={
            "input_dirs": ["test_data/folder1", "test_data/folder2"],
        }
    )

    assert response.status_code == 202  # Accepted
    job_id = response.json()["job_id"]

    # Poll for completion
    result = await client.get(f"/api/v1/results/{job_id}")
    assert result.status_code == 200
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_documents(tmp_path: Path):
    """Create sample markdown documents for testing."""
    folder1 = tmp_path / "folder1"
    folder1.mkdir()

    (folder1 / "test.md").write_text(
        "# Test Document\n\n## Section 1\n\nContent..."
    )

    yield {"folder1": folder1}
```

## Code Review Checklist

Before submitting PR, ensure:

- [ ] **Type hints**: All public functions have type annotations
- [ ] **Logging**: Replace `print()` with `logger.info/debug/warning/error()`
- [ ] **Configuration**: No hardcoded paths or magic numbers
- [ ] **Tests**: 70%+ coverage, all new code has tests
- [ ] **Documentation**: Docstrings for public APIs
- [ ] **Error handling**: Proper exception handling with context
- [ ] **Code quality**: `ruff check .` passes
- [ ] **Type safety**: `mypy src/` passes
- [ ] **Security**: `bandit -r src/` passes

## Migration From Google Drive Scripts

### Original Scripts Location

```
/Users/LROC/Library/CloudStorage/GoogleDrive-lroc@callcabrera.com/My Drive/
├── document_tournament.py       → src/document_consolidation/core/tournament.py
├── extract_unique_content.py    → src/document_consolidation/core/extractor.py
├── integrate_improvements.py    → src/document_consolidation/core/integrator.py
└── verify_and_document.py       → src/document_consolidation/core/verifier.py
```

### Key Refactoring Changes

1. **Hardcoded Paths** → **Configuration**
   ```python
   # Before
   GDRIVE_DIR = Path("/Users/LROC/Library/CloudStorage/...")

   # After
   from document_consolidation.config import settings
   input_dir = settings.input_directory
   ```

2. **Print Statements** → **Structured Logging**
   ```python
   # Before
   print(f"✓ Loaded {len(results)} results")

   # After
   logger.info("Results loaded", extra={"count": len(results)})
   ```

3. **Main Functions** → **Classes with Dependency Injection**
   ```python
   # Before
   def main():
       results = run_tournament()
       save_results(results)

   # After
   class TournamentRunner:
       def __init__(self, config: TournamentConfig, repository: TournamentRepository):
           self.config = config
           self.repository = repository

       async def run(self) -> TournamentResult:
           results = await self._run_tournament()
           await self.repository.save_result(results)
           return results
   ```

4. **No Tests** → **Comprehensive Test Suite**
   - Unit tests for all scoring algorithms
   - Integration tests for database operations
   - Performance tests for large document sets

## Known Issues and Workarounds

### Issue: Citation Integration Not Implemented

**Status**: Phase 2 feature (currently skipped in original `integrate_improvements.py` lines 149-152)

**Location**: `src/document_consolidation/core/integrator.py`

**Workaround**: Citation enhancements are identified but not integrated. They're logged for manual review.

**Fix Plan**: Implement citation merging logic in Phase 2.

```python
# Current code (skips citations)
if improvement['type'] == 'citation_enhancement':
    logger.info("Skipping citation enhancement", extra={"source": improvement['source_folder']})
    continue

# Planned fix
if improvement['type'] == 'citation_enhancement':
    self._integrate_citations(content, improvement)
```

### Issue: Potential IndexError in Metadata Removal

**Status**: Edge case in original `verify_and_document.py` lines 184-196

**Location**: `src/document_consolidation/core/integrator.py:add_evolution_metadata()`

**Workaround**: Add bounds checking before list slicing.

**Fix Plan**: Implement safe metadata removal in Phase 2.

## Performance Considerations

### Large Document Sets (100+ documents)

- **Use streaming**: Process documents one at a time instead of loading all into memory
- **Parallel processing**: Use `asyncio` or `multiprocessing` for tournament scoring
- **Database indexing**: Add indexes on `document_name`, `tournament_id` columns

### Memory Usage

- **Original scripts**: ~500MB for 55 documents
- **Target**: <200MB through streaming processing

## Production Deployment

### Environment Variables

```bash
# Required
export DATABASE_URL="postgresql://user:pass@localhost/consolidation"
export LOG_LEVEL="INFO"

# Optional
export TOURNAMENT_COMPLETENESS_WEIGHT=10
export INTEGRATION_OUTPUT_DIR="/data/comprehensive"
```

### Docker Deployment

```bash
# Build image
docker build -t document-consolidation-toolkit .

# Run API server
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  document-consolidation-toolkit \
  uvicorn document_consolidation.api.main:app --host 0.0.0.0

# Run CLI
docker run -v /data:/data \
  document-consolidation-toolkit \
  doc-consolidate tournament --input-dirs /data/folder1 /data/folder2
```

## Troubleshooting

### Issue: Import Errors

```bash
# Symptom
ImportError: No module named 'document_consolidation'

# Solution
# Ensure installed in editable mode
uv pip install -e ".[dev]"

# Or reinstall
uv pip uninstall document-consolidation-toolkit
uv pip install -e ".[dev]"
```

### Issue: Test Failures

```bash
# Symptom
pytest: ModuleNotFoundError: No module named 'document_consolidation'

# Solution
# Tests must be run from repository root
cd ~/Documents/GitHub/document-consolidation-toolkit/
pytest
```

### Issue: Type Errors

```bash
# Symptom
mypy: error: Argument 1 has incompatible type "str"; expected "Path"

# Solution
# Use Path objects consistently
from pathlib import Path
input_dir = Path(input_dir_str)
```

## Resources

- **Original Phase 4 Complete**: `/Users/LROC/Library/CloudStorage/GoogleDrive-lroc@callcabrera.com/My Drive/PHASE_4_COMPLETE.md`
- **Tournament Results**: `/Users/LROC/Library/CloudStorage/GoogleDrive-lroc@callcabrera.com/My Drive/tournament_results.json`
- **Code Review Report**: See Phase 4.2 code review (Grade D → Target: B+)

## Next Steps

See `docs/roadmap.md` for planned features:
- Phase 2: Core refactoring with configuration and citation integration
- Phase 3: Test infrastructure (70%+ coverage)
- Phase 4: CLI implementation
- Phase 5: Database integration
- Phase 6: FastAPI backend
- Phase 7: Streamlit web UI
- Phase 8: CI/CD pipeline
- Phase 9: Documentation
- Phase 10: Migration and verification
