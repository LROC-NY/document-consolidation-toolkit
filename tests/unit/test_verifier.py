"""Unit tests for DocumentVerifier.

Tests document verification including:
- Markdown formatting checks
- Section numbering validation
- Duplication detection
- Document navigability checks
- Verification reporting
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from document_consolidation.core.verifier import DocumentVerifier, ReportGenerator
from document_consolidation.models.document import (
    IntegrationResult,
    VerificationIssue,
    VerificationResult,
)


class TestDocumentVerifier:
    """Test DocumentVerifier class."""

    def test_verifier_initialization(self, mock_repository):
        """Test verifier initializes with repository."""
        verifier = DocumentVerifier(mock_repository)

        assert verifier.repository == mock_repository

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_markdown_formatting_valid(
        self, mock_settings, mock_repository, tmp_path
    ):
        """Test formatting verification passes for valid markdown."""
        mock_settings.verification.check_markdown_formatting = True
        mock_settings.verification.max_consecutive_blank_lines = 2
        mock_settings.integration.add_evolution_metadata = True

        content = """# Title

## Section One

Content here.

## Section Two

More content.

## Document Evolution

Metadata.
"""
        filepath = tmp_path / "doc.md"

        verifier = DocumentVerifier(mock_repository)
        issues = verifier.verify_markdown_formatting(filepath, content)

        assert len(issues) == 0

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_markdown_formatting_malformed_header(
        self, mock_settings, mock_repository, tmp_path
    ):
        """Test detection of malformed headers."""
        mock_settings.verification.check_markdown_formatting = True
        mock_settings.verification.max_consecutive_blank_lines = 2

        content = """# Title
##NoSpace
## Proper Header
###AlsoNoSpace
"""
        filepath = tmp_path / "doc.md"

        verifier = DocumentVerifier(mock_repository)
        issues = verifier.verify_markdown_formatting(filepath, content)

        assert len(issues) >= 2  # At least 2 malformed headers
        assert all(i.type == "formatting" for i in issues)

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_markdown_formatting_excessive_blanks(
        self, mock_settings, mock_repository, tmp_path
    ):
        """Test detection of excessive blank lines."""
        mock_settings.verification.check_markdown_formatting = True
        mock_settings.verification.max_consecutive_blank_lines = 2

        content = """# Title

## Section



Content after 3 blank lines.
"""
        filepath = tmp_path / "doc.md"

        verifier = DocumentVerifier(mock_repository)
        issues = verifier.verify_markdown_formatting(filepath, content)

        # Should detect excessive blank lines
        excessive_blanks = [i for i in issues if "blank lines" in i.message.lower()]
        assert len(excessive_blanks) > 0

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_markdown_formatting_missing_evolution(
        self, mock_settings, mock_repository, tmp_path
    ):
        """Test detection of missing evolution metadata."""
        mock_settings.verification.check_markdown_formatting = True
        mock_settings.integration.add_evolution_metadata = True

        content = """# Title
## Section
Content without evolution section.
"""
        filepath = tmp_path / "doc.md"

        verifier = DocumentVerifier(mock_repository)
        issues = verifier.verify_markdown_formatting(filepath, content)

        # Should detect missing Document Evolution section
        missing_evolution = [i for i in issues if "Evolution" in i.message]
        assert len(missing_evolution) == 1

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_markdown_formatting_disabled(
        self, mock_settings, mock_repository, tmp_path
    ):
        """Test formatting verification skipped when disabled."""
        mock_settings.verification.check_markdown_formatting = False

        content = "##BadHeader"  # Would normally fail
        filepath = tmp_path / "doc.md"

        verifier = DocumentVerifier(mock_repository)
        issues = verifier.verify_markdown_formatting(filepath, content)

        assert len(issues) == 0  # Skipped

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_section_numbering_proper_hierarchy(
        self, mock_settings, mock_repository
    ):
        """Test section numbering passes for proper hierarchy."""
        mock_settings.verification.check_section_numbering = True

        content = """# Title
## Level 2
### Level 3
#### Level 4
## Another Level 2
### Another Level 3
"""
        verifier = DocumentVerifier(mock_repository)
        issues = verifier.verify_section_numbering(content)

        assert len(issues) == 0

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_section_numbering_level_jump(
        self, mock_settings, mock_repository
    ):
        """Test detection of section level jumps."""
        mock_settings.verification.check_section_numbering = True

        content = """# Title
## Level 2
#### Level 4 (skipped level 3)
"""
        verifier = DocumentVerifier(mock_repository)
        issues = verifier.verify_section_numbering(content)

        assert len(issues) == 1
        assert issues[0].type == "numbering"
        assert "jump" in issues[0].message.lower()

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_section_numbering_disabled(
        self, mock_settings, mock_repository
    ):
        """Test numbering verification skipped when disabled."""
        mock_settings.verification.check_section_numbering = False

        content = "## Level 2\n##### Level 5"  # Bad hierarchy

        verifier = DocumentVerifier(mock_repository)
        issues = verifier.verify_section_numbering(content)

        assert len(issues) == 0  # Skipped

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_no_duplication_no_duplicates(
        self, mock_settings, mock_repository
    ):
        """Test duplication check passes when no duplicates."""
        mock_settings.verification.check_no_duplication = True

        content = """# Title
## Section One
Content.
## Section Two
More content.
"""
        verifier = DocumentVerifier(mock_repository)
        issues = verifier.verify_no_duplication(content)

        assert len(issues) == 0

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_no_duplication_duplicate_sections(
        self, mock_settings, mock_repository
    ):
        """Test detection of duplicate section titles."""
        mock_settings.verification.check_no_duplication = True

        content = """# Title
## Legal Analysis
Content for first.
## Other Section
Some content.
## Legal Analysis
Duplicate section title.
"""
        verifier = DocumentVerifier(mock_repository)
        issues = verifier.verify_no_duplication(content)

        assert len(issues) == 1
        assert issues[0].type == "duplication"
        assert "Legal Analysis" in issues[0].message

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_no_duplication_disabled(self, mock_settings, mock_repository):
        """Test duplication check skipped when disabled."""
        mock_settings.verification.check_no_duplication = False

        content = "## Same\nContent\n## Same\nDuplicate"

        verifier = DocumentVerifier(mock_repository)
        issues = verifier.verify_no_duplication(content)

        assert len(issues) == 0  # Skipped

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_document_navigability_has_sections(
        self, mock_settings, mock_repository
    ):
        """Test navigability check passes with sections."""
        mock_settings.verification.check_document_navigability = True

        content = """# Title
## Section One
Content.
## Section Two
More content.
"""
        verifier = DocumentVerifier(mock_repository)
        issues = verifier.verify_document_navigability(content)

        assert len(issues) == 0

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_document_navigability_no_sections(
        self, mock_settings, mock_repository
    ):
        """Test detection of documents without sections."""
        mock_settings.verification.check_document_navigability = True

        content = """# Title Only
Just flat content without any sections.
"""
        verifier = DocumentVerifier(mock_repository)
        issues = verifier.verify_document_navigability(content)

        assert len(issues) == 1
        assert issues[0].type == "navigation"
        assert "navigable" in issues[0].message.lower()

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_document_navigability_disabled(
        self, mock_settings, mock_repository
    ):
        """Test navigability check skipped when disabled."""
        mock_settings.verification.check_document_navigability = False

        content = "# Title\nNo sections."

        verifier = DocumentVerifier(mock_repository)
        issues = verifier.verify_document_navigability(content)

        assert len(issues) == 0  # Skipped

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_document_passes(self, mock_settings, mock_repository, tmp_path):
        """Test full document verification passes."""
        mock_settings.verification.check_markdown_formatting = True
        mock_settings.verification.check_section_numbering = True
        mock_settings.verification.check_no_duplication = True
        mock_settings.verification.check_document_navigability = True
        mock_settings.integration.add_evolution_metadata = False

        filepath = tmp_path / "doc.md"
        content = """# Valid Document

## Section One

Content here.

## Section Two

More content.
"""
        filepath.write_text(content)

        mock_repository.document_exists.return_value = True
        mock_repository.read_document.return_value = content

        verifier = DocumentVerifier(mock_repository)
        result = verifier.verify_document("doc.md", filepath)

        assert isinstance(result, VerificationResult)
        assert result.passed is True
        assert len(result.issues) == 0

    @patch("document_consolidation.core.verifier.settings")
    def test_verify_document_fails(self, mock_settings, mock_repository, tmp_path):
        """Test full document verification fails with issues."""
        mock_settings.verification.check_markdown_formatting = True
        mock_settings.verification.check_section_numbering = True
        mock_settings.verification.check_no_duplication = True
        mock_settings.verification.check_document_navigability = True

        filepath = tmp_path / "doc.md"
        content = """# Title
##BadHeader
## Section
#### Skip level
## Section
"""
        filepath.write_text(content)

        mock_repository.document_exists.return_value = True
        mock_repository.read_document.return_value = content

        verifier = DocumentVerifier(mock_repository)
        result = verifier.verify_document("doc.md", filepath)

        assert result.passed is False
        assert len(result.issues) > 0

    def test_verify_document_not_found(self, mock_repository, tmp_path):
        """Test verification raises when document doesn't exist."""
        filepath = tmp_path / "missing.md"

        mock_repository.document_exists.return_value = False

        verifier = DocumentVerifier(mock_repository)

        with pytest.raises(FileNotFoundError):
            verifier.verify_document("missing.md", filepath)

    def test_verify_document_read_error(self, mock_repository, tmp_path):
        """Test verification raises on read error."""
        filepath = tmp_path / "doc.md"

        mock_repository.document_exists.return_value = True
        mock_repository.read_document.side_effect = OSError("Read failed")

        verifier = DocumentVerifier(mock_repository)

        with pytest.raises(OSError):
            verifier.verify_document("doc.md", filepath)

    @patch("document_consolidation.core.verifier.settings")
    def test_run_verification_multiple_documents(
        self, mock_settings, mock_repository, tmp_path
    ):
        """Test verification for multiple documents."""
        mock_settings.input_directory = tmp_path
        mock_settings.integration.output_dir = Path("output")
        mock_settings.verification.check_markdown_formatting = True
        mock_settings.integration.add_evolution_metadata = False

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        integration_results = []

        for i in range(1, 3):
            filename = f"doc{i}.md"
            filepath = output_dir / f"COMPREHENSIVE_{filename}"
            content = f"# Document {i}\n## Section\nContent."
            filepath.write_text(content)

            integration_results.append(
                IntegrationResult(
                    filename=filename,
                    champion_folder="folder1",
                    champion_path=tmp_path / "folder1" / filename,
                    original_line_count=10,
                    integrated_line_count=15,
                    added_lines=5,
                    improvements_integrated=1,
                    source_folders=["folder2"],
                    integrated_content=content,
                )
            )

        mock_repository.document_exists.return_value = True

        def mock_read(path):
            return path.read_text()

        mock_repository.read_document.side_effect = mock_read

        verifier = DocumentVerifier(mock_repository)
        results = verifier.run_verification(integration_results)

        assert len(results) == 2
        assert all(isinstance(r, VerificationResult) for r in results)

    def test_run_verification_empty_raises(self, mock_repository):
        """Test run_verification raises ValueError with empty input."""
        verifier = DocumentVerifier(mock_repository)

        with pytest.raises(ValueError, match="No integration results to verify"):
            verifier.run_verification([])

    @patch("document_consolidation.core.verifier.settings")
    def test_run_verification_handles_errors(
        self, mock_settings, mock_repository, tmp_path
    ):
        """Test verification continues on individual document errors."""
        mock_settings.input_directory = tmp_path
        mock_settings.integration.output_dir = Path("output")

        integration_results = [
            IntegrationResult(
                filename="doc1.md",
                champion_folder="folder1",
                champion_path=tmp_path / "doc1.md",
                original_line_count=10,
                integrated_line_count=15,
                added_lines=5,
                improvements_integrated=1,
                source_folders=["folder2"],
                integrated_content="content",
            ),
            IntegrationResult(
                filename="doc2.md",
                champion_folder="folder1",
                champion_path=tmp_path / "doc2.md",
                original_line_count=10,
                integrated_line_count=15,
                added_lines=5,
                improvements_integrated=1,
                source_folders=["folder2"],
                integrated_content="content",
            ),
        ]

        # First succeeds, second fails
        mock_repository.document_exists.side_effect = [True, False]
        mock_repository.read_document.return_value = "# Content\n## Section\nText."

        verifier = DocumentVerifier(mock_repository)
        results = verifier.run_verification(integration_results)

        # Should have only successful verification
        assert len(results) == 1


class TestReportGenerator:
    """Test ReportGenerator class."""

    @patch("document_consolidation.core.verifier.settings")
    def test_generate_integration_report(self, mock_settings, tmp_path):
        """Test generating integration report."""
        mock_settings.source_folders = ["folder1", "folder2"]

        tournament_results = {
            "doc1.md": Mock(filename="doc1.md"),
            "doc2.md": Mock(filename="doc2.md"),
        }

        integration_results = [
            IntegrationResult(
                filename="doc1.md",
                champion_folder="folder1",
                champion_path=tmp_path / "doc1.md",
                original_line_count=100,
                integrated_line_count=150,
                added_lines=50,
                improvements_integrated=3,
                source_folders=["folder2"],
                integrated_content="content",
            ),
            IntegrationResult(
                filename="doc2.md",
                champion_folder="folder2",
                champion_path=tmp_path / "doc2.md",
                original_line_count=80,
                integrated_line_count=100,
                added_lines=20,
                improvements_integrated=2,
                source_folders=["folder1"],
                integrated_content="content",
            ),
        ]

        report = ReportGenerator.generate_integration_report(
            tournament_results, integration_results
        )

        assert "Phase 4: Tournament-Based Document Consolidation" in report
        assert "Executive Summary" in report
        assert "doc1.md" in report
        assert "doc2.md" in report
        assert "50" in report  # Added lines for doc1
        assert "folder1" in report
        assert "COMPREHENSIVE MASTER DOCUMENTS READY FOR USE" in report

    def test_generate_verification_report_all_passed(self, tmp_path):
        """Test generating verification report when all pass."""
        verification_results = [
            VerificationResult(
                filename="doc1.md",
                filepath=tmp_path / "doc1.md",
                line_count=50,
                issues=[],
                passed=True,
            ),
            VerificationResult(
                filename="doc2.md",
                filepath=tmp_path / "doc2.md",
                line_count=60,
                issues=[],
                passed=True,
            ),
        ]

        report = ReportGenerator.generate_verification_report(verification_results)

        assert "Document Verification Report" in report
        assert "Passed: 2" in report
        assert "Failed: 0" in report
        assert "All Documents Passed Verification" in report
        assert "Overall Status: PASSED" in report

    def test_generate_verification_report_with_failures(self, tmp_path):
        """Test generating verification report with failures."""
        verification_results = [
            VerificationResult(
                filename="doc1.md",
                filepath=tmp_path / "doc1.md",
                line_count=50,
                issues=[
                    VerificationIssue(
                        type="formatting",
                        severity="medium",
                        message="Malformed header",
                        line_number=10,
                    ),
                    VerificationIssue(
                        type="duplication",
                        severity="high",
                        message="Duplicate section",
                        line_number=20,
                    ),
                ],
                passed=False,
            ),
        ]

        report = ReportGenerator.generate_verification_report(verification_results)

        assert "Documents with Issues" in report
        assert "doc1.md" in report
        assert "Issues: 2" in report
        assert "Formatting Issues" in report
        assert "Duplication Issues" in report
        assert "Malformed header" in report
        assert "Overall Status: ISSUES FOUND" in report
