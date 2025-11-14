"""Unit tests for DocumentTournament and TournamentEngine.

Tests tournament-based document ranking including:
- Scoring criteria (completeness, recency, structure, citations, arguments)
- Pairwise comparison logic
- Champion identification
- Version grouping
- Tournament execution
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from document_consolidation.core.tournament import (
    DocumentTournament,
    TournamentEngine,
)
from document_consolidation.models.document import DocumentMetadata, ScoreBreakdown


class TestDocumentTournament:
    """Test DocumentTournament scoring and ranking."""

    def test_tournament_initialization(self, sample_document_versions, mock_repository):
        """Test tournament initializes with versions and repository."""
        tournament = DocumentTournament(sample_document_versions, mock_repository)

        assert tournament.versions == sample_document_versions
        assert tournament.repository == mock_repository
        assert len(tournament.scores) == 0

    def test_score_completeness_basic(self, sample_document_versions, mock_repository):
        """Test completeness scoring based on lines and sections."""
        tournament = DocumentTournament(sample_document_versions, mock_repository)

        # folder3 has the most lines and sections
        score_folder3 = tournament.score_completeness("folder3")
        score_folder1 = tournament.score_completeness("folder1")

        assert 0 <= score_folder3 <= 10
        assert 0 <= score_folder1 <= 10
        assert score_folder3 > score_folder1  # More complete version scores higher

    def test_score_recency_newest_highest(self, sample_document_versions, mock_repository):
        """Test recency scoring - newest files score highest."""
        tournament = DocumentTournament(sample_document_versions, mock_repository)

        score_folder1 = tournament.score_recency("folder1")  # Oldest
        score_folder3 = tournament.score_recency("folder3")  # Newest

        assert 0 <= score_folder1 <= 10
        assert 0 <= score_folder3 <= 10
        assert score_folder3 > score_folder1  # Newer version scores higher

    def test_score_recency_same_age(self, mock_repository, tmp_path):
        """Test recency scoring when all versions have same modified time."""
        # Create versions with same modified time
        versions = {}
        for i, folder in enumerate(["folder1", "folder2"], start=1):
            path = tmp_path / folder / "doc.md"
            path.parent.mkdir(parents=True)
            path.write_text(f"# Document {i}")

            versions[folder] = DocumentMetadata(
                path=path,
                folder=folder,
                content=f"# Document {i}",
                line_count=5,
                modified_time=1700000000.0,  # Same time
                hash=f"hash{i}",
            )

        tournament = DocumentTournament(versions, mock_repository)

        score1 = tournament.score_recency("folder1")
        score2 = tournament.score_recency("folder2")

        assert score1 == 5.0  # All same age = 5.0
        assert score2 == 5.0

    def test_score_structure_all_elements(self, mock_repository):
        """Test structure scoring with all markdown elements."""
        content_full = """# Document Title
## Section Header
Some content here.
- List item 1
- List item 2
```python
code block
```
"""
        versions = {
            "folder1": DocumentMetadata(
                path=Path("/test.md"),
                folder="folder1",
                content=content_full,
                line_count=10,
                modified_time=1700000000.0,
            )
        }

        tournament = DocumentTournament(versions, mock_repository)
        score = tournament.score_structure("folder1")

        # Should get points for: title, headers, lists, code blocks
        assert score == 10.0  # All 4 elements = 2.5 * 4 = 10.0

    def test_score_structure_partial_elements(self, mock_repository):
        """Test structure scoring with only some elements."""
        content_partial = """# Document Title
## Section Header
Some basic content.
"""
        versions = {
            "folder1": DocumentMetadata(
                path=Path("/test.md"),
                folder="folder1",
                content=content_partial,
                line_count=5,
                modified_time=1700000000.0,
            )
        }

        tournament = DocumentTournament(versions, mock_repository)
        score = tournament.score_structure("folder1")

        # Only title and headers = 2.5 * 2 = 5.0
        assert score == 5.0

    def test_score_citations_legal_patterns(self, mock_repository):
        """Test citation scoring with various legal citation patterns."""
        content_citations = """# Legal Document
According to INA § 245(a), adjustment is available.
See 8 U.S.C. § 1255 and 8 C.F.R. § 245.1.
Matter of Doe v. Smith establishes this principle.
File Form I-485 for adjustment of status.
"""
        versions = {
            "folder1": DocumentMetadata(
                path=Path("/test.md"),
                folder="folder1",
                content=content_citations,
                line_count=5,
                modified_time=1700000000.0,
            )
        }

        tournament = DocumentTournament(versions, mock_repository)
        score = tournament.score_citations("folder1")

        assert 0 <= score <= 10
        assert score > 0  # Should find some citations

    def test_score_citations_no_citations(self, mock_repository):
        """Test citation scoring with no citations."""
        content_no_citations = """# Regular Document
This document has no legal citations.
Just regular text content.
"""
        versions = {
            "folder1": DocumentMetadata(
                path=Path("/test.md"),
                folder="folder1",
                content=content_no_citations,
                line_count=3,
                modified_time=1700000000.0,
            )
        }

        tournament = DocumentTournament(versions, mock_repository)
        score = tournament.score_citations("folder1")

        assert score == 0.0  # No citations = 0 score

    def test_score_arguments_legal_keywords(self, mock_repository):
        """Test argument scoring with legal reasoning keywords."""
        content_arguments = """# Legal Brief
Therefore, the application should be approved.
However, additional evidence is required.
Moreover, the precedent establishes this principle.
Consequently, the petitioner qualifies.
Furthermore, this demonstrates eligibility.
Accordingly, relief should be granted.
"""
        versions = {
            "folder1": DocumentMetadata(
                path=Path("/test.md"),
                folder="folder1",
                content=content_arguments,
                line_count=7,
                modified_time=1700000000.0,
            )
        }

        tournament = DocumentTournament(versions, mock_repository)
        score = tournament.score_arguments("folder1")

        assert 0 <= score <= 10
        assert score > 0  # Should find argument keywords

    def test_score_arguments_no_keywords(self, mock_repository):
        """Test argument scoring with no legal keywords."""
        content_no_args = """# Simple Document
This is basic content.
No legal reasoning here.
"""
        versions = {
            "folder1": DocumentMetadata(
                path=Path("/test.md"),
                folder="folder1",
                content=content_no_args,
                line_count=3,
                modified_time=1700000000.0,
            )
        }

        tournament = DocumentTournament(versions, mock_repository)
        score = tournament.score_arguments("folder1")

        assert score == 0.0  # No keywords = 0 score

    def test_evaluate_version_returns_breakdown(
        self, sample_document_versions, mock_repository
    ):
        """Test evaluate_version returns ScoreBreakdown."""
        tournament = DocumentTournament(sample_document_versions, mock_repository)

        breakdown = tournament.evaluate_version("folder1")

        assert isinstance(breakdown, ScoreBreakdown)
        assert 0 <= breakdown.completeness <= 10
        assert 0 <= breakdown.recency <= 10
        assert 0 <= breakdown.structure <= 10
        assert 0 <= breakdown.citations <= 10
        assert 0 <= breakdown.arguments <= 10
        assert 0 <= breakdown.total <= 50

    def test_evaluate_version_stores_score(
        self, sample_document_versions, mock_repository
    ):
        """Test evaluate_version stores score in self.scores."""
        tournament = DocumentTournament(sample_document_versions, mock_repository)

        breakdown = tournament.evaluate_version("folder2")

        assert "folder2" in tournament.scores
        assert tournament.scores["folder2"] == breakdown

    def test_run_tournament_identifies_champion(
        self, sample_document_versions, mock_repository
    ):
        """Test run_tournament identifies champion correctly."""
        tournament = DocumentTournament(sample_document_versions, mock_repository)

        champion = tournament.run_tournament()

        # folder3 should win (most complete, newest, most citations)
        assert champion == "folder3"
        assert champion in tournament.scores
        assert len(tournament.scores) == 3

    def test_run_tournament_evaluates_all_versions(
        self, sample_document_versions, mock_repository
    ):
        """Test run_tournament evaluates all versions."""
        tournament = DocumentTournament(sample_document_versions, mock_repository)

        tournament.run_tournament()

        # All versions should be scored
        assert len(tournament.scores) == len(sample_document_versions)
        for folder in sample_document_versions:
            assert folder in tournament.scores

    def test_run_tournament_empty_versions_raises(self, mock_repository):
        """Test run_tournament raises ValueError with no versions."""
        tournament = DocumentTournament({}, mock_repository)

        with pytest.raises(ValueError, match="No versions to evaluate"):
            tournament.run_tournament()

    def test_run_tournament_single_version(self, mock_repository, tmp_path):
        """Test tournament with single version."""
        path = tmp_path / "folder1" / "doc.md"
        path.parent.mkdir(parents=True)
        path.write_text("# Document")

        versions = {
            "folder1": DocumentMetadata(
                path=path,
                folder="folder1",
                content="# Document",
                line_count=1,
                modified_time=1700000000.0,
            )
        }

        tournament = DocumentTournament(versions, mock_repository)
        champion = tournament.run_tournament()

        assert champion == "folder1"

    def test_scoring_consistency(self, sample_document_versions, mock_repository):
        """Test scoring is consistent across multiple evaluations."""
        tournament = DocumentTournament(sample_document_versions, mock_repository)

        # Evaluate same version twice
        breakdown1 = tournament.evaluate_version("folder1")
        breakdown2 = tournament.evaluate_version("folder1")

        assert breakdown1.completeness == breakdown2.completeness
        assert breakdown1.recency == breakdown2.recency
        assert breakdown1.structure == breakdown2.structure
        assert breakdown1.citations == breakdown2.citations
        assert breakdown1.arguments == breakdown2.arguments


class TestTournamentEngine:
    """Test TournamentEngine for managing multiple tournaments."""

    def test_engine_initialization(self, mock_repository):
        """Test engine initializes with repository."""
        engine = TournamentEngine(mock_repository)

        assert engine.repository == mock_repository

    @patch("document_consolidation.core.tournament.settings")
    def test_group_document_versions(self, mock_settings, mock_repository, tmp_path):
        """Test grouping documents by filename across folders."""
        # Setup mock settings
        mock_settings.input_directory = tmp_path

        # Create test structure
        for folder in ["folder1", "folder2"]:
            folder_path = tmp_path / folder
            folder_path.mkdir()
            (folder_path / "doc1.md").write_text(f"# Doc1 from {folder}")
            (folder_path / "doc2.md").write_text(f"# Doc2 from {folder}")

        # Mock repository to return real documents
        def mock_find_documents(base_path, pattern):
            docs = []
            for file in base_path.glob(pattern):
                content = file.read_text()
                docs.append(
                    DocumentMetadata(
                        path=file,
                        folder=base_path.name,
                        content=content,
                        line_count=content.count("\n") + 1,
                        modified_time=file.stat().st_mtime,
                        hash="test_hash",
                    )
                )
            return docs

        mock_repository.find_documents.side_effect = mock_find_documents

        engine = TournamentEngine(mock_repository)
        version_groups = engine.group_document_versions(["folder1", "folder2"])

        # Should have 2 document families
        assert len(version_groups) == 2
        assert "doc1.md" in version_groups
        assert "doc2.md" in version_groups

        # Each family should have 2 versions
        assert len(version_groups["doc1.md"]) == 2
        assert len(version_groups["doc2.md"]) == 2

    @patch("document_consolidation.core.tournament.settings")
    def test_group_document_versions_single_version_excluded(
        self, mock_settings, mock_repository, tmp_path
    ):
        """Test single-version documents are excluded from grouping."""
        mock_settings.input_directory = tmp_path

        # Create documents: doc1 in both folders, doc2 only in folder1
        folder1 = tmp_path / "folder1"
        folder1.mkdir()
        (folder1 / "doc1.md").write_text("# Doc1")
        (folder1 / "doc2.md").write_text("# Doc2")

        folder2 = tmp_path / "folder2"
        folder2.mkdir()
        (folder2 / "doc1.md").write_text("# Doc1")
        # doc2.md not in folder2

        def mock_find_documents(base_path, pattern):
            docs = []
            for file in base_path.glob(pattern):
                content = file.read_text()
                docs.append(
                    DocumentMetadata(
                        path=file,
                        folder=base_path.name,
                        content=content,
                        line_count=1,
                        modified_time=file.stat().st_mtime,
                        hash="hash",
                    )
                )
            return docs

        mock_repository.find_documents.side_effect = mock_find_documents

        engine = TournamentEngine(mock_repository)
        version_groups = engine.group_document_versions(["folder1", "folder2"])

        # Only doc1 should be included (multi-version)
        assert len(version_groups) == 1
        assert "doc1.md" in version_groups
        assert "doc2.md" not in version_groups

    @patch("document_consolidation.core.tournament.settings")
    def test_group_document_versions_missing_folder(
        self, mock_settings, mock_repository, tmp_path
    ):
        """Test gracefully handles missing folders."""
        mock_settings.input_directory = tmp_path

        # Create only folder1, not folder2
        folder1 = tmp_path / "folder1"
        folder1.mkdir()
        (folder1 / "doc1.md").write_text("# Doc1")

        def mock_find_documents(base_path, pattern):
            if not base_path.exists():
                return []
            docs = []
            for file in base_path.glob(pattern):
                content = file.read_text()
                docs.append(
                    DocumentMetadata(
                        path=file,
                        folder=base_path.name,
                        content=content,
                        line_count=1,
                        modified_time=file.stat().st_mtime,
                        hash="hash",
                    )
                )
            return docs

        mock_repository.find_documents.side_effect = mock_find_documents

        engine = TournamentEngine(mock_repository)

        # Should not raise error, just skip missing folder
        version_groups = engine.group_document_versions(["folder1", "folder2"])

        # No multi-version docs
        assert len(version_groups) == 0

    def test_run_tournaments_creates_results(self, mock_repository, tmp_path):
        """Test run_tournaments creates TournamentResult for each family."""
        # Setup version groups
        version_groups = {}

        for doc_name in ["doc1.md", "doc2.md"]:
            versions = {}
            for i, folder in enumerate(["folder1", "folder2"], start=1):
                path = tmp_path / folder / doc_name
                path.parent.mkdir(parents=True, exist_ok=True)
                content = f"# {doc_name} from {folder}\n" * i  # folder2 has more lines
                path.write_text(content)

                versions[folder] = DocumentMetadata(
                    path=path,
                    folder=folder,
                    content=content,
                    line_count=content.count("\n") + 1,
                    modified_time=1700000000.0 + i,
                    hash=f"hash{i}",
                )

            version_groups[doc_name] = versions

        engine = TournamentEngine(mock_repository)
        results = engine.run_tournaments(version_groups)

        assert len(results) == 2
        assert "doc1.md" in results
        assert "doc2.md" in results

        # Check result structure
        for result in results.values():
            assert result.version_count == 2
            assert result.champion_folder in ["folder1", "folder2"]
            assert result.champion_score > 0
            assert len(result.runners_up) == 1

    def test_run_tournaments_empty_groups_raises(self, mock_repository):
        """Test run_tournaments raises ValueError with empty groups."""
        engine = TournamentEngine(mock_repository)

        with pytest.raises(ValueError, match="No version groups to process"):
            engine.run_tournaments({})

    def test_run_tournaments_runners_up_sorted(self, mock_repository, tmp_path):
        """Test runners-up are sorted by score (descending)."""
        # Create 3 versions with different scores
        versions = {}
        for i, folder in enumerate(["folder1", "folder2", "folder3"], start=1):
            path = tmp_path / folder / "doc.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            # More content = higher score
            content = f"# Document\n" + ("## Section\nContent\n" * i)
            path.write_text(content)

            versions[folder] = DocumentMetadata(
                path=path,
                folder=folder,
                content=content,
                line_count=content.count("\n") + 1,
                modified_time=1700000000.0 + i * 1000,  # Different times
                hash=f"hash{i}",
            )

        engine = TournamentEngine(mock_repository)
        results = engine.run_tournaments({"doc.md": versions})

        result = results["doc.md"]

        # Runners-up should be in descending order by score
        assert len(result.runners_up) == 2
        assert result.runners_up[0][1] >= result.runners_up[1][1]

    @patch("document_consolidation.core.tournament.settings")
    def test_execute_full_workflow(self, mock_settings, mock_repository, tmp_path):
        """Test execute runs full discovery + tournaments workflow."""
        mock_settings.input_directory = tmp_path
        mock_settings.source_folders = ["folder1", "folder2"]

        # Create multi-version documents
        for folder in ["folder1", "folder2"]:
            folder_path = tmp_path / folder
            folder_path.mkdir()
            (folder_path / "doc1.md").write_text(f"# Doc1 from {folder}")

        def mock_find_documents(base_path, pattern):
            docs = []
            for file in base_path.glob(pattern):
                content = file.read_text()
                docs.append(
                    DocumentMetadata(
                        path=file,
                        folder=base_path.name,
                        content=content,
                        line_count=1,
                        modified_time=file.stat().st_mtime,
                        hash="hash",
                    )
                )
            return docs

        mock_repository.find_documents.side_effect = mock_find_documents

        engine = TournamentEngine(mock_repository)
        results = engine.execute()

        assert len(results) == 1
        assert "doc1.md" in results

    @patch("document_consolidation.core.tournament.settings")
    def test_execute_no_multi_version_raises(self, mock_settings, mock_repository, tmp_path):
        """Test execute raises ValueError when no multi-version docs found."""
        mock_settings.input_directory = tmp_path
        mock_settings.source_folders = ["folder1"]

        folder1 = tmp_path / "folder1"
        folder1.mkdir()
        (folder1 / "doc1.md").write_text("# Doc1")

        mock_repository.find_documents.return_value = [
            DocumentMetadata(
                path=folder1 / "doc1.md",
                folder="folder1",
                content="# Doc1",
                line_count=1,
                modified_time=1700000000.0,
                hash="hash",
            )
        ]

        engine = TournamentEngine(mock_repository)

        with pytest.raises(ValueError, match="No multi-version documents found"):
            engine.execute()
