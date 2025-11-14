"""Shared test fixtures for document-consolidation-toolkit.

Provides reusable fixtures for unit and integration tests including:
- Mock and real document repositories
- Sample document content
- Test configurations
- Temporary file structures
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock

import pytest

from document_consolidation.config.settings import (
    IntegrationSettings,
    Settings,
    TournamentSettings,
    VerificationSettings,
)
from document_consolidation.models.document import (
    CitationCounts,
    DocumentMetadata,
    IntegrationResult,
    ScoreBreakdown,
    SectionData,
    TournamentResult,
    UniqueImprovement,
    VerificationIssue,
    VerificationResult,
)
from document_consolidation.storage.document_repository import DocumentRepository
from document_consolidation.storage.filesystem_repository import FileSystemRepository


# ============================================================================
# Sample Document Content Fixtures
# ============================================================================


@pytest.fixture
def sample_markdown_basic() -> str:
    """Basic markdown document for testing."""
    return """# Basic Document

## Introduction

This is a basic introduction section with some content.

## Main Section

Some main content here with:
- List item 1
- List item 2
- List item 3

### Subsection

Additional details in a subsection.

## Conclusion

Final thoughts and summary.
"""


@pytest.fixture
def sample_markdown_with_citations() -> str:
    """Markdown document with legal citations."""
    return """# Legal Document

## Overview

This document discusses immigration law matters.

## Legal Authority

According to INA § 245(a), adjustment of status is available.
The regulation 8 CFR § 245.1 provides implementation details.
Additionally, 8 U.S.C. § 1255 provides statutory authority.

## Case Law

In Matter of Doe, 25 I&N Dec. 1 (BIA 2009), the Board held...
The case at 123 F.3d 456 (9th Cir. 2020) establishes precedent.

## Forms

File Form I-485 for adjustment of status.
Also submit Form I-130 for family-based petitions.

## Arguments

Therefore, the applicant qualifies under this provision.
However, further analysis demonstrates additional requirements.
Moreover, the evidence establishes eligibility.
"""


@pytest.fixture
def sample_markdown_enhanced() -> str:
    """Enhanced version with additional sections."""
    return """# Legal Document

## Overview

This document discusses immigration law matters with enhanced details.

## Legal Authority

According to INA § 245(a), adjustment of status is available.
The regulation 8 CFR § 245.1 provides implementation details.
Additionally, 8 U.S.C. § 1255 provides statutory authority.

Furthermore, recent policy guidance clarifies implementation.

## Case Law

In Matter of Doe, 25 I&N Dec. 1 (BIA 2009), the Board held...
The case at 123 F.3d 456 (9th Cir. 2020) establishes precedent.
In Matter of Smith, 26 I&N Dec. 10 (BIA 2010), additional guidance.

## Forms

File Form I-485 for adjustment of status.
Also submit Form I-130 for family-based petitions.
Form I-864 affidavit of support is also required.

## Additional Analysis

This section provides extra analysis not in the basic version.
It includes additional legal reasoning and precedent.

## Arguments

Therefore, the applicant qualifies under this provision.
However, further analysis demonstrates additional requirements.
Moreover, the evidence establishes eligibility.
Consequently, approval is warranted under applicable law.
"""


@pytest.fixture
def sample_documents_dict() -> Dict[str, str]:
    """Dictionary of sample documents by version."""
    return {
        "version1": """# Document v1
## Section A
Content for section A in version 1.
## Section B
Content for section B in version 1.
""",
        "version2": """# Document v2
## Section A
Enhanced content for section A in version 2 with more details.
## Section B
Content for section B in version 2.
## Section C
New section C only in version 2.
""",
        "version3": """# Document v3
## Section A
Content for section A in version 3.
Updated with references to INA § 245 and 8 U.S.C. § 1255.
Form I-485 must be filed. Matter of Doe applies.
## Section B
Content for section B in version 3.
""",
    }


# ============================================================================
# Document Metadata Fixtures
# ============================================================================


@pytest.fixture
def sample_document_metadata(tmp_path: Path) -> DocumentMetadata:
    """Sample DocumentMetadata object."""
    filepath = tmp_path / "test_doc.md"
    content = "# Test Document\n\nSample content"
    filepath.write_text(content)

    return DocumentMetadata(
        path=filepath,
        folder="test_folder",
        content=content,
        line_count=3,
        modified_time=1700000000.0,
        hash="abc123def456",
    )


@pytest.fixture
def sample_document_versions(tmp_path: Path) -> Dict[str, DocumentMetadata]:
    """Multiple document versions for tournament testing."""
    versions = {}

    # Version 1: Basic (oldest)
    v1_path = tmp_path / "folder1" / "document.md"
    v1_path.parent.mkdir(parents=True)
    v1_content = """# Document
## Section One
Basic content here.
"""
    v1_path.write_text(v1_content)
    versions["folder1"] = DocumentMetadata(
        path=v1_path,
        folder="folder1",
        content=v1_content,
        line_count=v1_content.count("\n") + 1,
        modified_time=1700000000.0,
        hash="hash1",
    )

    # Version 2: Enhanced with citations (newer)
    v2_path = tmp_path / "folder2" / "document.md"
    v2_path.parent.mkdir(parents=True)
    v2_content = """# Document
## Section One
Enhanced content with INA § 245 citation.
Matter of Doe establishes this principle.
## Section Two
Additional section with Form I-485 reference.
Therefore, the application should be approved.
"""
    v2_path.write_text(v2_content)
    versions["folder2"] = DocumentMetadata(
        path=v2_path,
        folder="folder2",
        content=v2_content,
        line_count=v2_content.count("\n") + 1,
        modified_time=1700010000.0,
        hash="hash2",
    )

    # Version 3: Comprehensive (newest, most complete)
    v3_path = tmp_path / "folder3" / "document.md"
    v3_path.parent.mkdir(parents=True)
    v3_content = """# Document
## Section One
Comprehensive content with INA § 245 and 8 U.S.C. § 1255 citations.
Matter of Doe and Matter of Smith establish these principles.
## Section Two
Additional section with Form I-485 and Form I-130 references.
Therefore, the application should be approved.
Moreover, the evidence demonstrates eligibility.
## Section Three
Even more content with code examples:
```python
def example():
    pass
```
### Subsection 3.1
Subsection content here.
"""
    v3_path.write_text(v3_content)
    versions["folder3"] = DocumentMetadata(
        path=v3_path,
        folder="folder3",
        content=v3_content,
        line_count=v3_content.count("\n") + 1,
        modified_time=1700020000.0,
        hash="hash3",
    )

    return versions


# ============================================================================
# Repository Fixtures
# ============================================================================


@pytest.fixture
def mock_repository() -> Mock:
    """Mock DocumentRepository for unit testing."""
    repo = Mock(spec=DocumentRepository)

    # Configure default return values
    repo.read_document.return_value = "# Test Document\n\nSample content"
    repo.document_exists.return_value = True
    repo.find_documents.return_value = []
    repo.list_folders.return_value = ["folder1", "folder2", "folder3"]

    return repo


@pytest.fixture
def temp_repository(tmp_path: Path) -> tuple[FileSystemRepository, Path]:
    """Real FileSystemRepository with temporary directory."""
    repo = FileSystemRepository()

    # Create sample directory structure
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    # Create sample folders with documents
    for i, folder_name in enumerate(["folder1", "folder2", "folder3"], start=1):
        folder = input_dir / folder_name
        folder.mkdir()

        # Create sample markdown files
        (folder / "doc1.md").write_text(
            f"# Document 1 - {folder_name}\n\nContent from {folder_name}"
        )
        (folder / "doc2.md").write_text(
            f"# Document 2 - {folder_name}\n\nMore content from {folder_name}"
        )

    return repo, input_dir


# ============================================================================
# Model Fixtures
# ============================================================================


@pytest.fixture
def sample_score_breakdown() -> ScoreBreakdown:
    """Sample ScoreBreakdown object."""
    return ScoreBreakdown(
        completeness=8.5,
        recency=7.0,
        structure=9.0,
        citations=6.5,
        arguments=7.5,
    )


@pytest.fixture
def sample_tournament_result(tmp_path: Path) -> TournamentResult:
    """Sample TournamentResult object."""
    champion_path = tmp_path / "folder1" / "document.md"
    champion_path.parent.mkdir(parents=True)
    champion_path.write_text("# Champion Document")

    return TournamentResult(
        filename="document.md",
        champion_folder="folder1",
        champion_path=champion_path,
        champion_score=38.5,
        champion_breakdown=ScoreBreakdown(
            completeness=8.5,
            recency=7.0,
            structure=9.0,
            citations=6.5,
            arguments=7.5,
        ),
        all_scores={
            "folder1": ScoreBreakdown(
                completeness=8.5, recency=7.0, structure=9.0, citations=6.5, arguments=7.5
            ),
            "folder2": ScoreBreakdown(
                completeness=7.0, recency=8.0, structure=7.5, citations=5.0, arguments=6.0
            ),
        },
        version_count=2,
        runners_up=[("folder2", 33.5)],
    )


@pytest.fixture
def sample_section_data() -> SectionData:
    """Sample SectionData object."""
    return SectionData(
        level=2,
        title="Sample Section",
        content="## Sample Section\n\nThis is the section content.",
        line_start=5,
        line_end=10,
    )


@pytest.fixture
def sample_unique_improvement() -> UniqueImprovement:
    """Sample UniqueImprovement object."""
    return UniqueImprovement(
        type="new_section",
        title="Additional Analysis",
        level=2,
        content="## Additional Analysis\n\nExtra content not in champion.",
        lines="20-25",
        source_folder="folder2",
        value="high",
        reason="Section not present in champion version",
    )


@pytest.fixture
def sample_integration_result(tmp_path: Path) -> IntegrationResult:
    """Sample IntegrationResult object."""
    champion_path = tmp_path / "folder1" / "document.md"
    champion_path.parent.mkdir(parents=True)

    return IntegrationResult(
        filename="document.md",
        champion_folder="folder1",
        champion_path=champion_path,
        original_line_count=50,
        integrated_line_count=75,
        added_lines=25,
        improvements_integrated=3,
        source_folders=["folder2", "folder3"],
        integrated_content="# Integrated Document\n\nComprehensive content...",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
    )


@pytest.fixture
def sample_verification_result(tmp_path: Path) -> VerificationResult:
    """Sample VerificationResult object."""
    filepath = tmp_path / "document.md"
    filepath.write_text("# Test Document")

    return VerificationResult(
        filename="document.md",
        filepath=filepath,
        line_count=50,
        issues=[],
        passed=True,
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
    )


@pytest.fixture
def sample_verification_issues() -> List[VerificationIssue]:
    """Sample verification issues."""
    return [
        VerificationIssue(
            type="formatting",
            severity="medium",
            message="Malformed header: ###NoSpace",
            line_number=10,
        ),
        VerificationIssue(
            type="duplication",
            severity="high",
            message="Duplicate section title: Legal Analysis",
            line_number=25,
        ),
        VerificationIssue(
            type="navigation",
            severity="low",
            message="Document may not be navigable",
        ),
    ]


@pytest.fixture
def sample_citation_counts() -> CitationCounts:
    """Sample CitationCounts object."""
    return CitationCounts(
        matter_of=5,
        usc=3,
        cfr=2,
        ina=4,
        form_i=2,
        case_citations=1,
    )


# ============================================================================
# Settings Fixtures
# ============================================================================


@pytest.fixture
def tournament_settings() -> TournamentSettings:
    """Tournament configuration for testing."""
    return TournamentSettings(
        completeness_weight=10,
        recency_weight=10,
        structure_weight=10,
        citations_weight=10,
        arguments_weight=10,
    )


@pytest.fixture
def integration_settings(tmp_path: Path) -> IntegrationSettings:
    """Integration configuration for testing."""
    return IntegrationSettings(
        output_dir=tmp_path / "output",
        add_evolution_metadata=True,
        preserve_source_attribution=True,
        integrate_citations=True,
        skip_citation_enhancement=False,
    )


@pytest.fixture
def verification_settings() -> VerificationSettings:
    """Verification configuration for testing."""
    return VerificationSettings(
        check_markdown_formatting=True,
        check_section_numbering=True,
        check_no_duplication=True,
        check_document_navigability=True,
        max_consecutive_blank_lines=2,
    )


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Complete test settings."""
    return Settings(
        input_directory=tmp_path / "input",
        source_folders=["folder1", "folder2", "folder3"],
        tournament=TournamentSettings(),
        integration=IntegrationSettings(output_dir=tmp_path / "output"),
        verification=VerificationSettings(),
    )


# ============================================================================
# Complex Test Data Fixtures
# ============================================================================


@pytest.fixture
def populated_test_directory(tmp_path: Path) -> Path:
    """Create fully populated test directory structure."""
    input_dir = tmp_path / "test_documents"
    input_dir.mkdir()

    # Create three folders with different versions of the same documents
    folders = ["Markdown Document 2", "Markdown Document 3", "Markdown Document 4"]

    for i, folder_name in enumerate(folders, start=1):
        folder = input_dir / folder_name
        folder.mkdir()

        # Document 1: Immigration Brief
        (folder / "immigration_brief.md").write_text(
            f"""# Immigration Adjustment Brief - Version {i}

## Introduction
{'Enhanced ' if i > 1 else ''}Brief regarding adjustment of status under INA § 245(a).

## Legal Authority
Pursuant to INA § 245(a) and 8 U.S.C. § 1255, adjustment is available.
{f'Additionally, 8 CFR § 245.1 provides regulatory guidance.' if i > 1 else ''}

## Case Law
Matter of Doe, 25 I&N Dec. 1 (BIA 2009) establishes the standard.
{f'Matter of Smith, 26 I&N Dec. 10 (BIA 2010) provides further guidance.' if i > 2 else ''}

## Forms Required
File Form I-485 for adjustment of status.
{f'Submit Form I-130 for family-based petitions.' if i > 1 else ''}

{f'''## Additional Analysis
Therefore, eligibility is established under applicable law.
Moreover, the evidence demonstrates all requirements are met.
''' if i > 2 else ''}

## Conclusion
Therefore, the application should be granted.
"""
        )

        # Document 2: Waiver Analysis
        (folder / "waiver_analysis.md").write_text(
            f"""# I-601A Waiver Analysis - Version {i}

## Overview
Analysis of provisional waiver under INA § 212(a)(9)(B).

## Unlawful Presence Bar
{f'The 10-year bar applies under INA § 212(a)(9)(B)(i)(II).' if i > 1 else 'Bar analysis required.'}

## Extreme Hardship
{f'Consequently, extreme hardship to qualifying relative must be demonstrated.' if i > 2 else 'Hardship showing required.'}
"""
        )

    return input_dir


@pytest.fixture
def mock_tournament_results(tmp_path: Path) -> Dict[str, TournamentResult]:
    """Mock tournament results for integration testing."""
    results = {}

    for filename in ["doc1.md", "doc2.md"]:
        champion_path = tmp_path / "folder1" / filename
        champion_path.parent.mkdir(parents=True, exist_ok=True)
        champion_path.write_text(f"# {filename} Champion")

        results[filename] = TournamentResult(
            filename=filename,
            champion_folder="folder1",
            champion_path=champion_path,
            champion_score=40.0,
            champion_breakdown=ScoreBreakdown(
                completeness=8.0,
                recency=8.0,
                structure=8.0,
                citations=8.0,
                arguments=8.0,
            ),
            all_scores={
                "folder1": ScoreBreakdown(8.0, 8.0, 8.0, 8.0, 8.0),
                "folder2": ScoreBreakdown(7.0, 7.0, 7.0, 7.0, 7.0),
            },
            version_count=2,
            runners_up=[("folder2", 35.0)],
        )

    return results
