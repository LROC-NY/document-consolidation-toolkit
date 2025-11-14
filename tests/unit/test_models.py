"""Unit tests for Pydantic data models.

Tests all 9 Pydantic models in document_consolidation.models.document:
- DocumentMetadata
- ScoreBreakdown
- TournamentResult
- SectionData
- UniqueImprovement
- IntegrationResult
- VerificationIssue
- VerificationResult
- CitationCounts
"""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

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


class TestDocumentMetadata:
    """Test DocumentMetadata model."""

    def test_valid_metadata_creation(self, tmp_path: Path):
        """Test creating valid DocumentMetadata."""
        filepath = tmp_path / "test.md"
        filepath.write_text("# Test")

        metadata = DocumentMetadata(
            path=filepath,
            folder="test_folder",
            content="# Test Document",
            line_count=10,
            modified_time=1700000000.0,
            hash="abc123",
        )

        assert metadata.path == filepath
        assert metadata.folder == "test_folder"
        assert metadata.content == "# Test Document"
        assert metadata.line_count == 10
        assert metadata.modified_time == 1700000000.0
        assert metadata.hash == "abc123"

    def test_path_string_conversion(self):
        """Test automatic string to Path conversion."""
        metadata = DocumentMetadata(
            path="/path/to/doc.md",  # String path
            folder="folder",
            content="content",
            line_count=5,
            modified_time=1234567890.0,
        )

        assert isinstance(metadata.path, Path)
        assert metadata.path == Path("/path/to/doc.md")

    def test_optional_hash_field(self):
        """Test that hash field is optional."""
        metadata = DocumentMetadata(
            path=Path("/test.md"),
            folder="folder",
            content="content",
            line_count=5,
            modified_time=1234567890.0,
            # hash not provided
        )

        assert metadata.hash is None

    def test_arbitrary_types_allowed(self, tmp_path: Path):
        """Test that Path objects work with arbitrary_types_allowed."""
        filepath = tmp_path / "test.md"

        metadata = DocumentMetadata(
            path=filepath,
            folder="folder",
            content="content",
            line_count=5,
            modified_time=1234567890.0,
        )

        assert isinstance(metadata.path, Path)


class TestScoreBreakdown:
    """Test ScoreBreakdown model."""

    def test_valid_score_breakdown(self):
        """Test creating valid ScoreBreakdown."""
        breakdown = ScoreBreakdown(
            completeness=8.5,
            recency=7.0,
            structure=9.0,
            citations=6.5,
            arguments=7.5,
        )

        assert breakdown.completeness == 8.5
        assert breakdown.recency == 7.0
        assert breakdown.structure == 9.0
        assert breakdown.citations == 6.5
        assert breakdown.arguments == 7.5

    def test_total_score_calculation(self):
        """Test total property calculates sum correctly."""
        breakdown = ScoreBreakdown(
            completeness=8.0,
            recency=7.0,
            structure=9.0,
            citations=6.0,
            arguments=8.0,
        )

        assert breakdown.total == 38.0

    def test_score_boundary_validation_min(self):
        """Test scores cannot be below 0."""
        with pytest.raises(ValidationError) as exc_info:
            ScoreBreakdown(
                completeness=-1.0,  # Invalid
                recency=5.0,
                structure=5.0,
                citations=5.0,
                arguments=5.0,
            )

        assert "greater than or equal to 0.0" in str(exc_info.value)

    def test_score_boundary_validation_max(self):
        """Test scores cannot exceed 10."""
        with pytest.raises(ValidationError) as exc_info:
            ScoreBreakdown(
                completeness=11.0,  # Invalid
                recency=5.0,
                structure=5.0,
                citations=5.0,
                arguments=5.0,
            )

        assert "less than or equal to 10.0" in str(exc_info.value)

    def test_perfect_score(self):
        """Test maximum possible score."""
        breakdown = ScoreBreakdown(
            completeness=10.0,
            recency=10.0,
            structure=10.0,
            citations=10.0,
            arguments=10.0,
        )

        assert breakdown.total == 50.0

    def test_zero_score(self):
        """Test minimum possible score."""
        breakdown = ScoreBreakdown(
            completeness=0.0,
            recency=0.0,
            structure=0.0,
            citations=0.0,
            arguments=0.0,
        )

        assert breakdown.total == 0.0


class TestTournamentResult:
    """Test TournamentResult model."""

    def test_valid_tournament_result(self, tmp_path: Path):
        """Test creating valid TournamentResult."""
        champion_path = tmp_path / "champion.md"
        champion_path.write_text("# Champion")

        result = TournamentResult(
            filename="document.md",
            champion_folder="folder1",
            champion_path=champion_path,
            champion_score=38.5,
            champion_breakdown=ScoreBreakdown(8.0, 7.5, 9.0, 7.0, 7.0),
            all_scores={
                "folder1": ScoreBreakdown(8.0, 7.5, 9.0, 7.0, 7.0),
                "folder2": ScoreBreakdown(7.0, 6.0, 8.0, 6.5, 6.0),
            },
            version_count=2,
            runners_up=[("folder2", 33.5)],
        )

        assert result.filename == "document.md"
        assert result.champion_folder == "folder1"
        assert result.champion_path == champion_path
        assert result.champion_score == 38.5
        assert result.version_count == 2
        assert len(result.runners_up) == 1
        assert result.runners_up[0] == ("folder2", 33.5)

    def test_path_string_conversion(self):
        """Test champion_path string to Path conversion."""
        result = TournamentResult(
            filename="doc.md",
            champion_folder="folder1",
            champion_path="/path/to/champion.md",  # String
            champion_score=40.0,
            champion_breakdown=ScoreBreakdown(8.0, 8.0, 8.0, 8.0, 8.0),
            all_scores={"folder1": ScoreBreakdown(8.0, 8.0, 8.0, 8.0, 8.0)},
            version_count=1,
            runners_up=[],
        )

        assert isinstance(result.champion_path, Path)

    def test_multiple_runners_up(self, tmp_path: Path):
        """Test tournament with multiple runners-up."""
        result = TournamentResult(
            filename="doc.md",
            champion_folder="folder1",
            champion_path=tmp_path / "champion.md",
            champion_score=45.0,
            champion_breakdown=ScoreBreakdown(9.0, 9.0, 9.0, 9.0, 9.0),
            all_scores={
                "folder1": ScoreBreakdown(9.0, 9.0, 9.0, 9.0, 9.0),
                "folder2": ScoreBreakdown(8.0, 8.0, 8.0, 8.0, 8.0),
                "folder3": ScoreBreakdown(7.0, 7.0, 7.0, 7.0, 7.0),
            },
            version_count=3,
            runners_up=[("folder2", 40.0), ("folder3", 35.0)],
        )

        assert len(result.runners_up) == 2
        assert result.version_count == 3


class TestSectionData:
    """Test SectionData model."""

    def test_valid_section_data(self):
        """Test creating valid SectionData."""
        section = SectionData(
            level=2,
            title="Legal Analysis",
            content="## Legal Analysis\n\nDetailed analysis here.",
            line_start=10,
            line_end=20,
        )

        assert section.level == 2
        assert section.title == "Legal Analysis"
        assert section.line_start == 10
        assert section.line_end == 20

    def test_level_boundary_validation_min(self):
        """Test level must be at least 2."""
        with pytest.raises(ValidationError) as exc_info:
            SectionData(
                level=1,  # Invalid (must be 2-6)
                title="Title",
                content="Content",
                line_start=1,
                line_end=5,
            )

        assert "greater than or equal to 2" in str(exc_info.value)

    def test_level_boundary_validation_max(self):
        """Test level cannot exceed 6."""
        with pytest.raises(ValidationError) as exc_info:
            SectionData(
                level=7,  # Invalid (must be 2-6)
                title="Title",
                content="Content",
                line_start=1,
                line_end=5,
            )

        assert "less than or equal to 6" in str(exc_info.value)

    def test_all_header_levels(self):
        """Test all valid header levels (2-6)."""
        for level in range(2, 7):
            section = SectionData(
                level=level,
                title=f"Level {level} Header",
                content=f"{'#' * level} Content",
                line_start=1,
                line_end=5,
            )
            assert section.level == level


class TestUniqueImprovement:
    """Test UniqueImprovement model."""

    def test_new_section_improvement(self):
        """Test new section type improvement."""
        improvement = UniqueImprovement(
            type="new_section",
            title="Additional Analysis",
            level=2,
            content="## Additional Analysis\n\nNew content.",
            lines="20-25",
            source_folder="folder2",
            value="high",
            reason="Section not present in champion version",
        )

        assert improvement.type == "new_section"
        assert improvement.title == "Additional Analysis"
        assert improvement.level == 2
        assert improvement.value == "high"
        assert improvement.source_folder == "folder2"

    def test_enhanced_section_improvement(self):
        """Test enhanced section type improvement."""
        improvement = UniqueImprovement(
            type="enhanced_section",
            title="Legal Authority",
            level=2,
            content="Enhanced content",
            lines="10-15",
            source_folder="folder3",
            value="medium",
            reason="Section has 5 additional lines not in champion",
            similarity=0.75,
            additions_preview="+ Additional line 1\n+ Additional line 2",
        )

        assert improvement.type == "enhanced_section"
        assert improvement.similarity == 0.75
        assert improvement.additions_preview is not None

    def test_citation_enhancement_improvement(self):
        """Test citation enhancement type improvement."""
        improvement = UniqueImprovement(
            type="citation_enhancement",
            source_folder="folder2",
            value="high",
            reason="Contains additional legal citations not in champion",
            citations={
                "matter_of": {"champion": 2, "other": 4, "difference": 2},
                "ina": {"champion": 1, "other": 3, "difference": 2},
            },
        )

        assert improvement.type == "citation_enhancement"
        assert improvement.citations is not None
        assert "matter_of" in improvement.citations
        assert improvement.citations["matter_of"]["difference"] == 2

    def test_optional_fields_none(self):
        """Test optional fields can be None."""
        improvement = UniqueImprovement(
            type="citation_enhancement",
            source_folder="folder1",
            value="medium",
            reason="Test reason",
        )

        assert improvement.title is None
        assert improvement.level is None
        assert improvement.content is None
        assert improvement.lines is None
        assert improvement.similarity is None


class TestIntegrationResult:
    """Test IntegrationResult model."""

    def test_valid_integration_result(self, tmp_path: Path):
        """Test creating valid IntegrationResult."""
        champion_path = tmp_path / "champion.md"

        result = IntegrationResult(
            filename="document.md",
            champion_folder="folder1",
            champion_path=champion_path,
            original_line_count=50,
            integrated_line_count=75,
            added_lines=25,
            improvements_integrated=3,
            source_folders=["folder2", "folder3"],
            integrated_content="# Integrated Document\n\nContent...",
        )

        assert result.filename == "document.md"
        assert result.original_line_count == 50
        assert result.integrated_line_count == 75
        assert result.added_lines == 25
        assert result.improvements_integrated == 3
        assert len(result.source_folders) == 2

    def test_growth_percentage_calculation(self, tmp_path: Path):
        """Test growth_percentage property calculation."""
        result = IntegrationResult(
            filename="doc.md",
            champion_folder="folder1",
            champion_path=tmp_path / "doc.md",
            original_line_count=100,
            integrated_line_count=150,
            added_lines=50,
            improvements_integrated=2,
            source_folders=["folder2"],
            integrated_content="content",
        )

        assert result.growth_percentage == 50.0

    def test_growth_percentage_zero_original(self, tmp_path: Path):
        """Test growth_percentage handles zero original lines."""
        result = IntegrationResult(
            filename="doc.md",
            champion_folder="folder1",
            champion_path=tmp_path / "doc.md",
            original_line_count=0,
            integrated_line_count=10,
            added_lines=10,
            improvements_integrated=1,
            source_folders=["folder2"],
            integrated_content="content",
        )

        assert result.growth_percentage == 0.0

    def test_timestamp_auto_generation(self, tmp_path: Path):
        """Test timestamp is auto-generated if not provided."""
        result = IntegrationResult(
            filename="doc.md",
            champion_folder="folder1",
            champion_path=tmp_path / "doc.md",
            original_line_count=10,
            integrated_line_count=15,
            added_lines=5,
            improvements_integrated=1,
            source_folders=["folder2"],
            integrated_content="content",
        )

        assert isinstance(result.timestamp, datetime)
        assert result.timestamp.year >= 2024


class TestVerificationIssue:
    """Test VerificationIssue model."""

    def test_valid_verification_issue_with_line(self):
        """Test creating issue with line number."""
        issue = VerificationIssue(
            type="formatting",
            severity="medium",
            message="Malformed header",
            line_number=42,
        )

        assert issue.type == "formatting"
        assert issue.severity == "medium"
        assert issue.message == "Malformed header"
        assert issue.line_number == 42

    def test_verification_issue_without_line(self):
        """Test creating issue without line number."""
        issue = VerificationIssue(
            type="navigation",
            severity="low",
            message="Document may not be navigable",
        )

        assert issue.line_number is None

    def test_all_issue_types(self):
        """Test different issue types."""
        types = ["formatting", "numbering", "duplication", "navigation"]

        for issue_type in types:
            issue = VerificationIssue(
                type=issue_type,
                severity="medium",
                message=f"Test {issue_type} issue",
            )
            assert issue.type == issue_type

    def test_severity_levels(self):
        """Test different severity levels."""
        severities = ["low", "medium", "high"]

        for severity in severities:
            issue = VerificationIssue(
                type="formatting",
                severity=severity,
                message=f"Test {severity} severity",
            )
            assert issue.severity == severity


class TestVerificationResult:
    """Test VerificationResult model."""

    def test_verification_passed(self, tmp_path: Path):
        """Test verification result that passed."""
        filepath = tmp_path / "doc.md"
        filepath.write_text("# Document")

        result = VerificationResult(
            filename="doc.md",
            filepath=filepath,
            line_count=50,
            issues=[],
            passed=True,
        )

        assert result.filename == "doc.md"
        assert result.passed is True
        assert len(result.issues) == 0
        assert result.issue_count == 0

    def test_verification_failed_with_issues(self, tmp_path: Path):
        """Test verification result that failed."""
        filepath = tmp_path / "doc.md"

        issues = [
            VerificationIssue(
                type="formatting",
                severity="medium",
                message="Issue 1",
                line_number=10,
            ),
            VerificationIssue(
                type="duplication",
                severity="high",
                message="Issue 2",
                line_number=20,
            ),
        ]

        result = VerificationResult(
            filename="doc.md",
            filepath=filepath,
            line_count=50,
            issues=issues,
            passed=False,
        )

        assert result.passed is False
        assert result.issue_count == 2

    def test_issue_count_property(self, tmp_path: Path):
        """Test issue_count property calculation."""
        filepath = tmp_path / "doc.md"

        issues = [
            VerificationIssue(type="formatting", severity="low", message="Issue 1"),
            VerificationIssue(type="formatting", severity="low", message="Issue 2"),
            VerificationIssue(type="formatting", severity="low", message="Issue 3"),
        ]

        result = VerificationResult(
            filename="doc.md",
            filepath=filepath,
            line_count=50,
            issues=issues,
            passed=False,
        )

        assert result.issue_count == 3
        assert len(result.issues) == 3

    def test_timestamp_auto_generation(self, tmp_path: Path):
        """Test timestamp is auto-generated."""
        filepath = tmp_path / "doc.md"

        result = VerificationResult(
            filename="doc.md",
            filepath=filepath,
            line_count=50,
            issues=[],
            passed=True,
        )

        assert isinstance(result.timestamp, datetime)


class TestCitationCounts:
    """Test CitationCounts model."""

    def test_valid_citation_counts(self):
        """Test creating valid CitationCounts."""
        counts = CitationCounts(
            matter_of=5,
            usc=3,
            cfr=2,
            ina=4,
            form_i=2,
            case_citations=1,
        )

        assert counts.matter_of == 5
        assert counts.usc == 3
        assert counts.cfr == 2
        assert counts.ina == 4
        assert counts.form_i == 2
        assert counts.case_citations == 1

    def test_total_citation_count(self):
        """Test total property calculation."""
        counts = CitationCounts(
            matter_of=5,
            usc=3,
            cfr=2,
            ina=4,
            form_i=2,
            case_citations=1,
        )

        assert counts.total == 17

    def test_default_zero_counts(self):
        """Test all fields default to 0."""
        counts = CitationCounts()

        assert counts.matter_of == 0
        assert counts.usc == 0
        assert counts.cfr == 0
        assert counts.ina == 0
        assert counts.form_i == 0
        assert counts.case_citations == 0
        assert counts.total == 0

    def test_partial_citation_counts(self):
        """Test creating counts with only some fields."""
        counts = CitationCounts(
            matter_of=3,
            ina=2,
            # Others default to 0
        )

        assert counts.matter_of == 3
        assert counts.ina == 2
        assert counts.usc == 0
        assert counts.total == 5
