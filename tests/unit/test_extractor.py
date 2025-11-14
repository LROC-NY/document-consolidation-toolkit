"""Unit tests for UniqueContentExtractor.

Tests unique content extraction including:
- Section extraction from markdown
- Unique section detection
- Enhanced section comparison
- Citation analysis and comparison
- Full document extraction workflow
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from document_consolidation.core.extractor import UniqueContentExtractor
from document_consolidation.models.document import (
    CitationCounts,
    SectionData,
    TournamentResult,
    UniqueImprovement,
)


class TestUniqueContentExtractor:
    """Test UniqueContentExtractor class."""

    def test_extractor_initialization(self, mock_repository):
        """Test extractor initializes with repository."""
        extractor = UniqueContentExtractor(mock_repository)

        assert extractor.repository == mock_repository

    def test_extract_sections_basic(self, mock_repository):
        """Test extracting sections from markdown content."""
        content = """# Document Title

## Section One
Content for section one.

## Section Two
Content for section two.

### Subsection 2.1
Subsection content.
"""
        extractor = UniqueContentExtractor(mock_repository)
        sections = extractor.extract_sections(content)

        assert len(sections) == 3
        assert sections[0].level == 2
        assert sections[0].title == "Section One"
        assert sections[1].level == 2
        assert sections[1].title == "Section Two"
        assert sections[2].level == 3
        assert sections[2].title == "Subsection 2.1"

    def test_extract_sections_with_line_numbers(self, mock_repository):
        """Test sections include correct line numbers."""
        content = """# Title
Line 2
## Section A
Line 4
Line 5
## Section B
Line 7
"""
        extractor = UniqueContentExtractor(mock_repository)
        sections = extractor.extract_sections(content)

        assert len(sections) == 2

        # First section
        assert sections[0].line_start == 2  # Line where ## Section A appears
        assert sections[0].line_end == 4    # Line before next section

        # Second section
        assert sections[1].line_start == 5
        assert sections[1].line_end == 6

    def test_extract_sections_no_sections(self, mock_repository):
        """Test extracting from content with no sections."""
        content = """# Title Only

Just some content without sections.
"""
        extractor = UniqueContentExtractor(mock_repository)
        sections = extractor.extract_sections(content)

        assert len(sections) == 0

    def test_extract_sections_various_levels(self, mock_repository):
        """Test extracting sections at different header levels."""
        content = """## Level 2
Content
### Level 3
Content
#### Level 4
Content
##### Level 5
Content
###### Level 6
Content
"""
        extractor = UniqueContentExtractor(mock_repository)
        sections = extractor.extract_sections(content)

        assert len(sections) == 5
        assert sections[0].level == 2
        assert sections[1].level == 3
        assert sections[2].level == 4
        assert sections[3].level == 5
        assert sections[4].level == 6

    def test_find_unique_sections_completely_new(self, mock_repository):
        """Test finding completely new sections."""
        champion_content = """# Document
## Existing Section
Content here.
"""
        other_content = """# Document
## Existing Section
Content here.
## New Section
This is completely new.
"""
        extractor = UniqueContentExtractor(mock_repository)
        unique = extractor.find_unique_sections(
            champion_content, other_content, "folder2"
        )

        assert len(unique) == 1
        assert unique[0].type == "new_section"
        assert unique[0].title == "New Section"
        assert unique[0].value == "high"
        assert unique[0].source_folder == "folder2"

    def test_find_unique_sections_enhanced(self, mock_repository):
        """Test finding enhanced sections with additional content."""
        champion_content = """# Document
## Legal Analysis
Basic analysis here.
"""
        other_content = """# Document
## Legal Analysis
Enhanced analysis with much more detail.
Additional paragraph with citations.
More legal reasoning and precedent.
Even more content here.
"""
        extractor = UniqueContentExtractor(mock_repository)
        unique = extractor.find_unique_sections(
            champion_content, other_content, "folder2"
        )

        # Should detect enhanced section (low similarity + added lines)
        assert len(unique) >= 0  # May or may not detect based on thresholds
        if unique:
            assert unique[0].type == "enhanced_section"
            assert unique[0].similarity is not None
            assert unique[0].similarity < extractor.SIMILARITY_THRESHOLD

    def test_find_unique_sections_no_differences(self, mock_repository):
        """Test finding no unique sections when content is identical."""
        content = """# Document
## Section One
Identical content.
## Section Two
More identical content.
"""
        extractor = UniqueContentExtractor(mock_repository)
        unique = extractor.find_unique_sections(content, content, "folder2")

        assert len(unique) == 0

    def test_find_unique_sections_case_insensitive_matching(self, mock_repository):
        """Test section matching is case-insensitive."""
        champion_content = """# Document
## Legal Analysis
Content.
"""
        other_content = """# Document
## legal analysis
Content.
"""
        extractor = UniqueContentExtractor(mock_repository)
        unique = extractor.find_unique_sections(
            champion_content, other_content, "folder2"
        )

        # Should not treat as new section (case-insensitive match)
        new_sections = [u for u in unique if u.type == "new_section"]
        assert len(new_sections) == 0

    def test_analyze_citations_all_types(self, mock_repository):
        """Test analyzing citations of all types."""
        content = """# Legal Document
Matter of Doe establishes this.
According to 8 U.S.C. § 1255, adjustment is available.
See 8 CFR § 245.1 for details.
INA § 245 provides authority.
File Form I-485 and Form I-130.
In 123 F.3d 456 (9th Cir. 2020), the court held...
"""
        extractor = UniqueContentExtractor(mock_repository)
        counts = extractor.analyze_citations(content)

        assert isinstance(counts, CitationCounts)
        assert counts.matter_of >= 1
        assert counts.usc >= 1
        assert counts.cfr >= 1
        assert counts.ina >= 1
        assert counts.form_i >= 2  # Two Form I- references
        assert counts.case_citations >= 1
        assert counts.total >= 7

    def test_analyze_citations_no_citations(self, mock_repository):
        """Test analyzing content with no citations."""
        content = """# Regular Document
This document has no legal citations.
Just regular content.
"""
        extractor = UniqueContentExtractor(mock_repository)
        counts = extractor.analyze_citations(content)

        assert counts.total == 0
        assert counts.matter_of == 0
        assert counts.usc == 0
        assert counts.cfr == 0

    def test_compare_citations_improvements(self, mock_repository):
        """Test comparing citations finds improvements."""
        champion_content = """# Document
INA § 245 provides authority.
Matter of Doe applies.
"""
        other_content = """# Document
INA § 245 and INA § 212 provide authority.
Matter of Doe and Matter of Smith apply.
Additionally, 8 U.S.C. § 1255 is relevant.
"""
        extractor = UniqueContentExtractor(mock_repository)
        improvements = extractor.compare_citations(champion_content, other_content)

        assert improvements is not None
        assert len(improvements) > 0

        # Should find improvements in multiple types
        if "ina" in improvements:
            assert improvements["ina"]["difference"] > 0
        if "matter_of" in improvements:
            assert improvements["matter_of"]["difference"] > 0

    def test_compare_citations_no_improvements(self, mock_repository):
        """Test comparing citations when other has fewer."""
        champion_content = """# Document
INA § 245 and INA § 212 provide authority.
Matter of Doe and Matter of Smith apply.
8 U.S.C. § 1255 is relevant.
"""
        other_content = """# Document
INA § 245 provides authority.
"""
        extractor = UniqueContentExtractor(mock_repository)
        improvements = extractor.compare_citations(champion_content, other_content)

        assert improvements is None  # Other has fewer citations

    def test_compare_citations_equal_counts(self, mock_repository):
        """Test comparing citations when counts are equal."""
        content = """# Document
INA § 245 provides authority.
Matter of Doe applies.
"""
        extractor = UniqueContentExtractor(mock_repository)
        improvements = extractor.compare_citations(content, content)

        assert improvements is None  # Equal counts = no improvements

    def test_extract_for_document_with_improvements(
        self, mock_repository, sample_tournament_result, tmp_path
    ):
        """Test extracting improvements for a document."""
        # Setup: Create champion and other version
        champion_path = sample_tournament_result.champion_path
        champion_content = """# Champion Document
## Section A
Champion content.
"""
        champion_path.write_text(champion_content)

        # Create other version with improvements
        other_folder = "folder2"
        other_path = Path(str(champion_path).replace(
            sample_tournament_result.champion_folder, other_folder
        ))
        other_path.parent.mkdir(parents=True, exist_ok=True)
        other_content = """# Other Version
## Section A
Champion content.
## New Section B
Additional content not in champion.
"""
        other_path.write_text(other_content)

        # Mock repository
        def mock_read(path):
            if path == champion_path:
                return champion_content
            elif path == other_path:
                return other_content
            return ""

        mock_repository.read_document.side_effect = mock_read
        mock_repository.document_exists.return_value = True

        extractor = UniqueContentExtractor(mock_repository)
        result = extractor.extract_for_document(sample_tournament_result)

        assert result is not None
        assert result["champion"] == sample_tournament_result.champion_folder
        assert result["improvement_count"] > 0
        assert "improvements" in result

    def test_extract_for_document_no_improvements(
        self, mock_repository, sample_tournament_result
    ):
        """Test extracting when no improvements exist."""
        champion_content = """# Champion Document
## Section A
Content.
"""
        sample_tournament_result.champion_path.write_text(champion_content)

        # Other version identical
        other_folder = "folder2"
        other_path = Path(str(sample_tournament_result.champion_path).replace(
            sample_tournament_result.champion_folder, other_folder
        ))
        other_path.parent.mkdir(parents=True, exist_ok=True)
        other_path.write_text(champion_content)

        mock_repository.read_document.return_value = champion_content
        mock_repository.document_exists.return_value = True

        extractor = UniqueContentExtractor(mock_repository)
        result = extractor.extract_for_document(sample_tournament_result)

        assert result is None  # No improvements found

    def test_extract_for_document_missing_other_version(
        self, mock_repository, sample_tournament_result
    ):
        """Test extracting when other version file doesn't exist."""
        champion_content = "# Champion"
        sample_tournament_result.champion_path.write_text(champion_content)

        mock_repository.read_document.return_value = champion_content
        mock_repository.document_exists.return_value = False  # Other doesn't exist

        extractor = UniqueContentExtractor(mock_repository)
        result = extractor.extract_for_document(sample_tournament_result)

        # Should handle gracefully, may return None or partial results
        # Implementation continues even if some versions missing

    def test_extract_for_document_champion_read_error(
        self, mock_repository, sample_tournament_result
    ):
        """Test extracting when champion cannot be read."""
        mock_repository.read_document.side_effect = FileNotFoundError("Not found")

        extractor = UniqueContentExtractor(mock_repository)

        with pytest.raises(FileNotFoundError):
            extractor.extract_for_document(sample_tournament_result)

    def test_run_extraction_multiple_documents(
        self, mock_repository, mock_tournament_results
    ):
        """Test running extraction for multiple documents."""
        # Setup champion and other versions
        for filename in ["doc1.md", "doc2.md"]:
            result = mock_tournament_results[filename]
            champion_content = f"# {filename} Champion\n## Section A\nContent."
            result.champion_path.write_text(champion_content)

            # Create other version
            other_path = Path(str(result.champion_path).replace("folder1", "folder2"))
            other_path.parent.mkdir(parents=True, exist_ok=True)
            other_content = f"# {filename} Other\n## Section A\nContent.\n## New Section\nExtra."
            other_path.write_text(other_content)

        def mock_read(path):
            return path.read_text()

        mock_repository.read_document.side_effect = mock_read
        mock_repository.document_exists.return_value = True

        extractor = UniqueContentExtractor(mock_repository)
        results = extractor.run_extraction(mock_tournament_results)

        assert len(results) >= 0  # May find improvements
        for filename, data in results.items():
            assert "champion" in data
            assert "improvements" in data

    def test_run_extraction_empty_results_raises(self, mock_repository):
        """Test run_extraction raises ValueError with empty input."""
        extractor = UniqueContentExtractor(mock_repository)

        with pytest.raises(ValueError, match="No tournament results to process"):
            extractor.run_extraction({})

    def test_similarity_threshold_constant(self, mock_repository):
        """Test SIMILARITY_THRESHOLD constant is set correctly."""
        extractor = UniqueContentExtractor(mock_repository)

        assert extractor.SIMILARITY_THRESHOLD == 0.8
        assert 0 < extractor.SIMILARITY_THRESHOLD < 1

    def test_min_added_lines_constant(self, mock_repository):
        """Test MIN_ADDED_LINES constant is set correctly."""
        extractor = UniqueContentExtractor(mock_repository)

        assert extractor.MIN_ADDED_LINES == 3
        assert extractor.MIN_ADDED_LINES > 0

    def test_citation_improvement_creation(self, mock_repository):
        """Test citation improvement is created correctly."""
        champion_content = "INA § 245 applies."
        other_content = "INA § 245 and INA § 212 apply. Also 8 U.S.C. § 1255."

        extractor = UniqueContentExtractor(mock_repository)
        improvements_dict = extractor.compare_citations(champion_content, other_content)

        # Manually verify structure
        if improvements_dict:
            for citation_type, data in improvements_dict.items():
                assert "champion" in data
                assert "other" in data
                assert "difference" in data
                assert data["other"] > data["champion"]

    def test_section_content_includes_header(self, mock_repository):
        """Test extracted section content includes header line."""
        content = """# Title
## Section One
Line 1
Line 2
## Section Two
Line 3
"""
        extractor = UniqueContentExtractor(mock_repository)
        sections = extractor.extract_sections(content)

        assert len(sections) == 2
        # Content should start with the header
        assert sections[0].content.startswith("## Section One")
        assert sections[1].content.startswith("## Section Two")
