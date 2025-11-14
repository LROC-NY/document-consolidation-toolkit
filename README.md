# Document Consolidation Toolkit

**Production-ready document consolidation using tournament-based ranking**

Transform scattered document versions into comprehensive master documents using a tournament-style evaluation system inspired by March Madness.

## Features

- 🏆 **Tournament-Based Ranking**: Multi-criteria scoring (completeness, recency, structure, citations, arguments)
- 🔄 **Intelligent Integration**: Merges unique improvements from non-champion versions
- ✅ **Quality Verification**: Automated validation of markdown formatting and content integrity
- 🎯 **Citation Analysis**: Legal citation extraction and comparison (Matter of, U.S.C., C.F.R., INA §)
- 📊 **Comprehensive Reporting**: Detailed tournament results and integration statistics
- 🛠️ **Multiple Interfaces**: CLI, REST API, and Web UI
- 💾 **Database Support**: SQLAlchemy ORM with migration support
- 🧪 **Well-Tested**: 70%+ test coverage with pytest

## Installation

### Using uv (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/LROC-NY/document-consolidation-toolkit.git
cd document-consolidation-toolkit

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### Using pip

```bash
# Clone repository
git clone https://github.com/LROC-NY/document-consolidation-toolkit.git
cd document-consolidation-toolkit

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install
pip install -e ".[dev]"
```

## Quick Start

### CLI Usage

```bash
# Run tournament on document families
doc-consolidate tournament \
  --input-dirs "Markdown Document 2" "Markdown Document 3" \
  --output tournament_results.json

# Extract unique content from non-champions
doc-consolidate extract \
  --tournament-results tournament_results.json \
  --output unique_improvements.json

# Integrate improvements into comprehensive documents
doc-consolidate integrate \
  --improvements unique_improvements.json \
  --output-dir COMPREHENSIVE_Legal_Documents/

# Verify integrated documents
doc-consolidate verify \
  --input-dir COMPREHENSIVE_Legal_Documents/ \
  --output verification_results.json
```

### Python API

```python
from pathlib import Path
from document_consolidation import DocumentTournament, ContentExtractor, Integrator

# Run tournament
tournament = DocumentTournament(
    input_dirs=[
        Path("Markdown Document 2"),
        Path("Markdown Document 3"),
    ]
)
results = tournament.run()

# Extract unique content
extractor = ContentExtractor(tournament_results=results)
improvements = extractor.extract()

# Integrate improvements
integrator = Integrator(improvements=improvements)
integrator.integrate(output_dir=Path("COMPREHENSIVE_Legal_Documents"))
```

### REST API

```bash
# Start API server
uvicorn document_consolidation.api.main:app --reload

# API endpoints available at:
# - POST /api/v1/tournament - Run tournament
# - POST /api/v1/extract - Extract unique content
# - POST /api/v1/integrate - Integrate improvements
# - GET /api/v1/results/{job_id} - Get job results
```

### Web UI

```bash
# Start Streamlit interface
streamlit run src/document_consolidation/ui/app.py

# Interface available at: http://localhost:8501
```

## Tournament Scoring System

Each document version is evaluated on 5 criteria (0-10 points each, 50 points total):

| Criterion | Weight | What It Measures |
|-----------|--------|------------------|
| **Completeness** | 10 pts | Document length, section count, subsection depth |
| **Recency** | 10 pts | Modification timestamps |
| **Structure** | 10 pts | Markdown hierarchy, headers, lists, code blocks |
| **Citations** | 10 pts | Legal citations (Matter of, U.S.C., C.F.R., INA §) |
| **Arguments** | 10 pts | Legal reasoning density and quality |

**Example Scoring:**
```
opla_pd_request_letter.md:
  Markdown Document 3: 44.9/50 (CHAMPION)
  - Completeness: 10.0/10 (longest version)
  - Recency: 5.0/10
  - Structure: 10.0/10 (excellent markdown)
  - Citations: 9.9/10 (extensive legal citations)
  - Arguments: 10.0/10 (strong legal reasoning)
```

## Configuration

Create a `config.yaml` file:

```yaml
# Tournament configuration
tournament:
  criteria_weights:
    completeness: 10
    recency: 10
    structure: 10
    citations: 10
    arguments: 10

  source_folders:
    - "Markdown Document 2"
    - "Markdown Document 3"
    - "Markdown Document 4"
    - "Markdown Document 5"
    - "Markdown Document 6"

# Integration configuration
integration:
  output_dir: "COMPREHENSIVE_Legal_Documents"
  add_evolution_metadata: true
  preserve_source_attribution: true

# Verification configuration
verification:
  checks:
    - markdown_formatting
    - section_numbering
    - no_duplication
    - document_navigability
```

## Project Structure

```
document-consolidation-toolkit/
├── src/document_consolidation/
│   ├── core/                 # Business logic
│   │   ├── tournament.py     # Tournament ranking engine
│   │   ├── extractor.py      # Unique content extraction
│   │   ├── integrator.py     # Document integration
│   │   └── verifier.py       # Quality verification
│   ├── models/               # Pydantic models
│   ├── storage/              # Database layer
│   ├── api/                  # FastAPI endpoints
│   ├── ui/                   # Streamlit interface
│   └── cli/                  # Click commands
├── tests/                    # Test suite
├── docs/                     # Documentation
└── examples/                 # Example configurations
```

## Development

### Run Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit -m unit

# With coverage
pytest --cov=document_consolidation --cov-report=html
```

### Code Quality

```bash
# Linting
ruff check .

# Type checking
mypy src/

# Security audit
bandit -r src/

# Format code
ruff format .
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Real-World Example

**Before Phase 4 (Problem):**
- 55 document families scattered across 5 folders
- 174 total files to manage
- Multiple versions with different improvements
- No clear "best" version

**After Phase 4 (Solution):**
- 6 comprehensive master documents with ALL best content integrated
- 49 documents already comprehensive (champion was complete)
- ONE definitive version per topic
- 836 new lines of unique content preserved (+22.2% average growth)

**Time Savings:**
- Before: 5-10 minutes to compare versions × 55 documents = 4.5-9 hours
- After: 0 minutes - just use the comprehensive master document
- **Total time saved: 4.5-9 hours per future use**

## Documentation

- [API Reference](docs/api/README.md)
- [User Guide](docs/user-guide.md)
- [Developer Guide](docs/developer-guide.md)
- [Configuration Guide](docs/configuration.md)
- [Migration Guide](docs/migration.md)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- **Issues**: https://github.com/LROC-NY/document-consolidation-toolkit/issues
- **Discussions**: https://github.com/LROC-NY/document-consolidation-toolkit/discussions

## Acknowledgments

- Built to solve real-world legal document consolidation challenges
- Inspired by tournament ranking systems (March Madness, ELO)
- Powered by modern Python tools: Pydantic, FastAPI, Streamlit, SQLAlchemy
