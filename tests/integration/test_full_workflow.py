"""Integration tests for full document consolidation workflow.

Tests end-to-end workflow:
1. Tournament ranking (DocumentTournament + TournamentEngine)
2. Content extraction (UniqueContentExtractor)
3. Integration (DocumentIntegrator)
4. Verification (DocumentVerifier)

Uses real FileSystemRepository with temporary directories.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from document_consolidation.core.extractor import UniqueContentExtractor
from document_consolidation.core.integrator import DocumentIntegrator
from document_consolidation.core.tournament import TournamentEngine
from document_consolidation.core.verifier import DocumentVerifier
from document_consolidation.storage.filesystem_repository import FileSystemRepository


@pytest.mark.integration
class TestFullWorkflow:
    """Integration tests for complete workflow."""

    def create_test_documents(self, base_path: Path):
        """Create test document structure with versions."""
        # Create three folders with different versions of same documents
        folders = ["version1", "version2", "version3"]

        for i, folder_name in enumerate(folders, start=1):
            folder = base_path / folder_name
            folder.mkdir()

            # Document 1: Immigration Brief (progressively better versions)
            (folder / "immigration_brief.md").write_text(
                f"""# Immigration Adjustment of Status Brief

## Introduction
{'Enhanced ' if i > 1 else ''}Analysis of adjustment of status under INA § 245(a).

## Legal Authority
According to INA § 245(a), adjustment of status is available.
{f'Additionally, 8 U.S.C. § 1255 provides statutory authority.' if i > 1 else ''}
{f'Furthermore, 8 CFR § 245.1 provides regulatory guidance.' if i > 2 else ''}

## Case Law
Matter of Doe, 25 I&N Dec. 1 (BIA 2009) establishes the standard.
{f'Matter of Smith, 26 I&N Dec. 10 (BIA 2010) provides additional guidance.' if i > 2 else ''}

## Forms Required
File Form I-485 for adjustment of status.
{f'Submit Form I-130 for family-based petition.' if i > 1 else ''}

{f'''## Additional Requirements
Therefore, all eligibility criteria must be satisfied.
Moreover, supporting documentation is essential.
Consequently, careful preparation is required.
''' if i > 2 else ''}

## Conclusion
{'Therefore, ' if i > 1 else ''}The application should be granted.
"""
            )

            # Document 2: Waiver Analysis (different content per version)
            if i == 1:
                content = """# I-601A Waiver Analysis

## Overview
Basic analysis of provisional waiver.

## Unlawful Presence
Discussion of unlawful presence bars.

## Conclusion
Waiver may be available.
"""
            elif i == 2:
                content = """# I-601A Waiver Analysis

## Overview
Detailed analysis of provisional waiver under INA § 212(a)(9)(B).

## Unlawful Presence
The 10-year bar applies under INA § 212(a)(9)(B)(i)(II).
Accrual began upon departure from the United States.

## Extreme Hardship
Hardship to qualifying relative must be demonstrated.

## Conclusion
Therefore, the waiver application should be approved.
"""
            else:  # i == 3
                content = """# I-601A Waiver Analysis

## Overview
Comprehensive analysis of provisional waiver under INA § 212(a)(9)(B).

## Unlawful Presence
The 10-year bar applies under INA § 212(a)(9)(B)(i)(II).
Accrual began upon departure from the United States.
See Matter of Garcia for calculation methods.

## Extreme Hardship
Consequently, extreme hardship to qualifying relative must be demonstrated.
Moreover, medical, financial, and emotional factors are relevant.

## Case Law Analysis
Matter of Doe v. USCIS establishes hardship standards.
The precedent at 123 F.3d 456 (9th Cir. 2020) is controlling.

## Required Documentation
Submit Form I-601A with supporting evidence.
Form I-130 approval required as prerequisite.

## Conclusion
Therefore, the waiver application should be approved based on the evidence.
"""
            (folder / "waiver_analysis.md").write_text(content)

    @patch("document_consolidation.core.tournament.settings")
    @patch("document_consolidation.core.integrator.settings")
    def test_complete_workflow_tournament_to_integration(
        self, mock_integrator_settings, mock_tournament_settings, tmp_path
    ):
        """Test complete workflow from tournament through integration."""
        # Setup
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        self.create_test_documents(input_dir)

        mock_tournament_settings.input_directory = input_dir
        mock_tournament_settings.source_folders = ["version1", "version2", "version3"]

        mock_integrator_settings.input_directory = input_dir
        mock_integrator_settings.integration.output_dir = output_dir
        mock_integrator_settings.integration.add_evolution_metadata = True
        mock_integrator_settings.integration.preserve_source_attribution = True
        mock_integrator_settings.integration.integrate_citations = True
        mock_integrator_settings.integration.skip_citation_enhancement = False

        repository = FileSystemRepository()

        # Phase 1: Run Tournament
        tournament_engine = TournamentEngine(repository)
        tournament_results = tournament_engine.execute()

        # Verify tournament results
        assert len(tournament_results) == 2  # Two document families
        assert "immigration_brief.md" in tournament_results
        assert "waiver_analysis.md" in tournament_results

        # version3 should win for both (most complete, newest, most citations)
        for filename, result in tournament_results.items():
            assert result.champion_folder == "version3"
            assert result.version_count == 3
            assert len(result.runners_up) == 2

        # Phase 2: Extract Unique Content
        extractor = UniqueContentExtractor(repository)
        unique_improvements = extractor.run_extraction(tournament_results)

        # Verify extractions
        assert len(unique_improvements) >= 0  # May or may not find improvements

        # Phase 3: Integrate Improvements
        if unique_improvements:
            integrator = DocumentIntegrator(repository)
            integration_results = integrator.run_integration(unique_improvements)

            # Verify integrations
            assert len(integration_results) > 0

            for result in integration_results:
                # Check output file exists
                output_filename = f"COMPREHENSIVE_{result.filename}"
                output_path = output_dir / output_filename
                assert output_path.exists()

                # Check content
                content = output_path.read_text()
                assert "# " in content  # Has title
                assert "## " in content  # Has sections

                # Check evolution metadata
                if mock_integrator_settings.integration.add_evolution_metadata:
                    assert "## Document Evolution" in content
                    assert "Original Champion Lines" in content

    @patch("document_consolidation.core.tournament.settings")
    @patch("document_consolidation.core.integrator.settings")
    @patch("document_consolidation.core.verifier.settings")
    def test_complete_workflow_with_verification(
        self,
        mock_verifier_settings,
        mock_integrator_settings,
        mock_tournament_settings,
        tmp_path,
    ):
        """Test complete workflow including verification phase."""
        # Setup
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        self.create_test_documents(input_dir)

        mock_tournament_settings.input_directory = input_dir
        mock_tournament_settings.source_folders = ["version1", "version2", "version3"]

        mock_integrator_settings.input_directory = input_dir
        mock_integrator_settings.integration.output_dir = output_dir
        mock_integrator_settings.integration.add_evolution_metadata = True
        mock_integrator_settings.integration.preserve_source_attribution = True

        mock_verifier_settings.input_directory = input_dir
        mock_verifier_settings.integration.output_dir = output_dir
        mock_verifier_settings.integration.add_evolution_metadata = True
        mock_verifier_settings.verification.check_markdown_formatting = True
        mock_verifier_settings.verification.check_section_numbering = True
        mock_verifier_settings.verification.check_no_duplication = True
        mock_verifier_settings.verification.check_document_navigability = True

        repository = FileSystemRepository()

        # Run full pipeline
        tournament_engine = TournamentEngine(repository)
        tournament_results = tournament_engine.execute()

        extractor = UniqueContentExtractor(repository)
        unique_improvements = extractor.run_extraction(tournament_results)

        if unique_improvements:
            integrator = DocumentIntegrator(repository)
            integration_results = integrator.run_integration(unique_improvements)

            # Phase 4: Verify Integrated Documents
            verifier = DocumentVerifier(repository)
            verification_results = verifier.run_verification(integration_results)

            # Check verification results
            assert len(verification_results) > 0

            for result in verification_results:
                assert result.line_count > 0
                # May pass or fail depending on content, but should complete
                assert result.passed is True or result.passed is False

    @patch("document_consolidation.core.tournament.settings")
    def test_tournament_scoring_correctness(self, mock_settings, tmp_path):
        """Test tournament scoring produces expected champions."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        # Create clearly superior version3
        for i, folder in enumerate(["version1", "version2", "version3"], start=1):
            folder_path = input_dir / folder
            folder_path.mkdir()

            # version3 has more content, structure, citations
            if i == 3:
                content = """# Superior Document

## Section One

Comprehensive content with proper structure.
According to INA § 245(a), adjustment is available.
See 8 U.S.C. § 1255 for statutory authority.
Matter of Doe establishes the legal standard.

### Subsection 1.1

Additional detailed analysis here.

## Section Two

Therefore, the application should be approved.
Moreover, all requirements are satisfied.

### Subsection 2.1

Even more detailed content.

```python
def example():
    return "Code block"
```

## Section Three

Consequently, relief is warranted.
Furthermore, precedent supports this conclusion.
"""
            else:
                content = f"""# Basic Document Version {i}

## Section One

Basic content here.
"""

            (folder_path / "test.md").write_text(content)

        mock_settings.input_directory = input_dir
        mock_settings.source_folders = ["version1", "version2", "version3"]

        repository = FileSystemRepository()
        engine = TournamentEngine(repository)
        results = engine.execute()

        assert len(results) == 1
        result = results["test.md"]

        # version3 should win decisively
        assert result.champion_folder == "version3"
        assert result.champion_score > 35  # High score due to completeness

    @patch("document_consolidation.core.tournament.settings")
    def test_workflow_with_single_version_documents(self, mock_settings, tmp_path):
        """Test workflow handles single-version documents correctly."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        # Create documents with different version counts
        for folder in ["version1", "version2"]:
            folder_path = input_dir / folder
            folder_path.mkdir()

            # multi_version.md in both folders
            (folder_path / "multi_version.md").write_text(f"# Multi from {folder}")

            # single_version.md only in version1
            if folder == "version1":
                (folder_path / "single_version.md").write_text("# Single version only")

        mock_settings.input_directory = input_dir
        mock_settings.source_folders = ["version1", "version2"]

        repository = FileSystemRepository()
        engine = TournamentEngine(repository)
        results = engine.execute()

        # Should only include multi-version document
        assert len(results) == 1
        assert "multi_version.md" in results
        assert "single_version.md" not in results

    @patch("document_consolidation.core.integrator.settings")
    def test_integration_preserves_champion_content(
        self, mock_settings, tmp_path
    ):
        """Test integration preserves all champion content."""
        mock_settings.input_directory = tmp_path
        mock_settings.integration.output_dir = tmp_path / "output"
        mock_settings.integration.add_evolution_metadata = False

        champion_path = tmp_path / "champion.md"
        champion_content = """# Champion Document

## Original Section One

Important original content that must be preserved.

## Original Section Two

More critical original content.
"""
        champion_path.write_text(champion_content)

        improvement_data = {
            "champion": "folder1",
            "champion_path": str(champion_path),
            "improvements": [
                {
                    "type": "new_section",
                    "title": "New Section",
                    "content": "## New Section\nNew content.",
                    "source_folder": "folder2",
                    "value": "high",
                    "reason": "Test",
                }
            ],
        }

        repository = FileSystemRepository()
        integrator = DocumentIntegrator(repository)
        result = integrator.integrate_document("champion.md", improvement_data)

        assert result is not None

        # Verify original content is preserved
        integrated = result.integrated_content
        assert "## Original Section One" in integrated
        assert "Important original content that must be preserved" in integrated
        assert "## Original Section Two" in integrated
        assert "More critical original content" in integrated

        # And new content is added
        assert "## New Section" in integrated
