"""Tournament-based document ranking engine.

Implements Phase 4.1-4.2 of the intelligent cleanup workflow:
- Tournament-style ranking of document versions
- Multi-criteria scoring (completeness, recency, structure, citations, arguments)
- Champion identification for each document family
"""

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from document_consolidation.config import get_logger, settings
from document_consolidation.models.document import (
    DocumentMetadata,
    ScoreBreakdown,
    TournamentResult,
)
from document_consolidation.storage.document_repository import DocumentRepository

logger = get_logger(__name__)


class DocumentTournament:
    """Tournament-style ranking of document versions using multi-criteria scoring."""

    def __init__(
        self,
        versions: Dict[str, DocumentMetadata],
        repository: DocumentRepository,
    ):
        """Initialize tournament with document versions.

        Args:
            versions: Dictionary mapping folder name to DocumentMetadata
            repository: Document repository for storage operations
        """
        self.versions = versions
        self.repository = repository
        self.scores: Dict[str, ScoreBreakdown] = {}

    def score_completeness(self, version_key: str) -> float:
        """Score based on document length and section count.

        Args:
            version_key: Folder name key

        Returns:
            Completeness score (0-10)
        """
        version = self.versions[version_key]
        lines = version.line_count
        content = version.content

        # Count markdown sections
        sections = content.count("\n##")
        subsections = content.count("\n###")

        # Normalize to 0-10 scale
        max_lines = max(v.line_count for v in self.versions.values())
        line_score = (lines / max_lines) * 5 if max_lines > 0 else 0
        section_score = min(sections / 10, 1) * 3
        subsection_score = min(subsections / 20, 1) * 2

        total = line_score + section_score + subsection_score

        logger.debug(
            "Completeness score calculated",
            extra={
                "version": version_key,
                "lines": lines,
                "sections": sections,
                "score": total,
            },
        )

        return total

    def score_recency(self, version_key: str) -> float:
        """Score based on modification time.

        Args:
            version_key: Folder name key

        Returns:
            Recency score (0-10)
        """
        version = self.versions[version_key]
        mtimes = [v.modified_time for v in self.versions.values()]
        oldest = min(mtimes)
        newest = max(mtimes)

        if newest == oldest:
            return 5.0  # All same age

        # Normalize to 0-10 scale
        normalized = (version.modified_time - oldest) / (newest - oldest)
        score = normalized * 10

        logger.debug(
            "Recency score calculated",
            extra={"version": version_key, "mtime": version.modified_time, "score": score},
        )

        return score

    def score_structure(self, version_key: str) -> float:
        """Score based on markdown structure quality.

        Args:
            version_key: Folder name key

        Returns:
            Structure score (0-10)
        """
        version = self.versions[version_key]
        content = version.content

        # Check for proper hierarchy
        has_title = content.strip().startswith("#")
        has_headers = "##" in content
        has_lists = any(marker in content for marker in ["- ", "* ", "1. "])
        has_code_blocks = "```" in content

        structure_score = 0.0
        structure_score += 2.5 if has_title else 0
        structure_score += 2.5 if has_headers else 0
        structure_score += 2.5 if has_lists else 0
        structure_score += 2.5 if has_code_blocks else 0

        logger.debug(
            "Structure score calculated",
            extra={
                "version": version_key,
                "has_title": has_title,
                "has_headers": has_headers,
                "score": structure_score,
            },
        )

        return structure_score

    def score_citations(self, version_key: str) -> float:
        """Score based on legal citations and references.

        Args:
            version_key: Folder name key

        Returns:
            Citations score (0-10)
        """
        version = self.versions[version_key]
        content = version.content

        # Legal citation patterns
        citation_patterns = [
            "Matter of ",
            "v.",  # versus in case names
            "U.S.C.",  # US Code
            "C.F.R.",  # Code of Federal Regulations
            "INA §",  # Immigration and Nationality Act
            "Form I-",
            "8 CFR",
            "8 USC",
        ]

        citation_count = sum(content.count(pattern) for pattern in citation_patterns)

        max_citations = (
            max(
                sum(v.content.count(pattern) for pattern in citation_patterns)
                for v in self.versions.values()
            )
            or 1
        )

        # Normalize to 0-10 scale
        score = min(citation_count / max_citations, 1) * 10

        logger.debug(
            "Citations score calculated",
            extra={"version": version_key, "citations": citation_count, "score": score},
        )

        return score

    def score_arguments(self, version_key: str) -> float:
        """Score based on legal argument density.

        Args:
            version_key: Folder name key

        Returns:
            Arguments score (0-10)
        """
        version = self.versions[version_key]
        content = version.content

        # Argument indicators
        argument_keywords = [
            "therefore",
            "however",
            "moreover",
            "furthermore",
            "consequently",
            "accordingly",
            "argument",
            "demonstrates",
            "establishes",
            "pursuant to",
        ]

        keyword_count = sum(
            content.lower().count(keyword) for keyword in argument_keywords
        )

        # Normalize by document length
        lines = version.line_count or 1
        density = (keyword_count / lines) * 100

        # Normalize to 0-10 scale
        max_density = (
            max(
                (
                    sum(v.content.lower().count(kw) for kw in argument_keywords)
                    / (v.line_count or 1)
                )
                * 100
                for v in self.versions.values()
            )
            or 1
        )

        score = min(density / max_density, 1) * 10

        logger.debug(
            "Arguments score calculated",
            extra={
                "version": version_key,
                "keywords": keyword_count,
                "density": density,
                "score": score,
            },
        )

        return score

    def evaluate_version(self, version_key: str) -> ScoreBreakdown:
        """Score a version on multiple criteria.

        Args:
            version_key: Folder name key

        Returns:
            ScoreBreakdown with individual and total scores
        """
        breakdown = ScoreBreakdown(
            completeness=round(self.score_completeness(version_key), 2),
            recency=round(self.score_recency(version_key), 2),
            structure=round(self.score_structure(version_key), 2),
            citations=round(self.score_citations(version_key), 2),
            arguments=round(self.score_arguments(version_key), 2),
        )

        self.scores[version_key] = breakdown

        logger.info(
            "Version evaluated",
            extra={
                "version": version_key,
                "total_score": breakdown.total,
                "breakdown": breakdown.dict(),
            },
        )

        return breakdown

    def run_tournament(self) -> str:
        """Run tournament evaluation and identify champion.

        Returns:
            Champion folder name

        Raises:
            ValueError: If no versions to evaluate
        """
        if not self.versions:
            logger.error("No versions to evaluate")
            raise ValueError("No versions to evaluate")

        logger.info(
            "Tournament started",
            extra={"document_versions": len(self.versions)},
        )

        # Evaluate all versions
        for version_key in self.versions:
            self.evaluate_version(version_key)

        # Identify champion
        champion = max(self.versions.keys(), key=lambda k: self.scores[k].total)

        logger.info(
            "Tournament complete",
            extra={
                "champion": champion,
                "champion_score": self.scores[champion].total,
            },
        )

        return champion


class TournamentEngine:
    """Main tournament engine for processing multiple document families."""

    def __init__(self, repository: DocumentRepository):
        """Initialize tournament engine.

        Args:
            repository: Document repository for storage operations
        """
        self.repository = repository

    def group_document_versions(
        self, source_folders: List[str]
    ) -> Dict[str, Dict[str, DocumentMetadata]]:
        """Group documents by filename across folders.

        Args:
            source_folders: List of folder names to scan

        Returns:
            Dictionary mapping filename to folder->metadata dict

        Raises:
            FileNotFoundError: If input directory does not exist
        """
        logger.info(
            "Starting version discovery",
            extra={"source_folders": len(source_folders)},
        )

        version_groups: Dict[str, Dict[str, DocumentMetadata]] = defaultdict(dict)

        for folder in source_folders:
            folder_path = settings.input_directory / folder

            if not folder_path.exists():
                logger.warning("Folder not found", extra={"folder": folder})
                continue

            try:
                documents = self.repository.find_documents(folder_path, "*.md")

                for doc in documents:
                    filename = doc.path.name
                    version_groups[filename][folder] = doc

                logger.info(
                    "Folder scanned",
                    extra={"folder": folder, "documents": len(documents)},
                )

            except Exception as e:
                logger.error(
                    "Failed to scan folder",
                    extra={"folder": folder, "error": str(e)},
                )
                continue

        # Filter to only multi-version documents
        multi_version_docs = {
            filename: versions
            for filename, versions in version_groups.items()
            if len(versions) > 1
        }

        logger.info(
            "Version discovery complete",
            extra={
                "multi_version_documents": len(multi_version_docs),
                "total_files": sum(len(v) for v in multi_version_docs.values()),
            },
        )

        return multi_version_docs

    def run_tournaments(
        self, version_groups: Dict[str, Dict[str, DocumentMetadata]]
    ) -> Dict[str, TournamentResult]:
        """Run tournament for each document family.

        Args:
            version_groups: Document version groups from group_document_versions

        Returns:
            Dictionary mapping filename to TournamentResult

        Raises:
            ValueError: If version_groups is empty
        """
        if not version_groups:
            logger.error("No version groups to process")
            raise ValueError("No version groups to process")

        logger.info(
            "Starting tournament execution",
            extra={"document_families": len(version_groups)},
        )

        tournament_results: Dict[str, TournamentResult] = {}

        for filename, versions in sorted(version_groups.items()):
            logger.info(
                "Processing document family",
                extra={"filename": filename, "versions": len(versions)},
            )

            # Run tournament
            tournament = DocumentTournament(versions, self.repository)
            champion_folder = tournament.run_tournament()

            # Calculate runners-up
            runners_up = sorted(
                [
                    (folder, tournament.scores[folder].total)
                    for folder in versions.keys()
                    if folder != champion_folder
                ],
                key=lambda x: x[1],
                reverse=True,
            )

            tournament_results[filename] = TournamentResult(
                filename=filename,
                champion_folder=champion_folder,
                champion_path=versions[champion_folder].path,
                champion_score=tournament.scores[champion_folder].total,
                champion_breakdown=tournament.scores[champion_folder],
                all_scores=tournament.scores,
                version_count=len(versions),
                runners_up=runners_up,
            )

        logger.info(
            "Tournament execution complete",
            extra={"champions_identified": len(tournament_results)},
        )

        return tournament_results

    def execute(self) -> Dict[str, TournamentResult]:
        """Execute full tournament process (discovery + tournaments).

        Returns:
            Dictionary mapping filename to TournamentResult

        Raises:
            ValueError: If no multi-version documents found
        """
        logger.info(
            "Starting tournament-based consolidation",
            extra={
                "input_directory": str(settings.input_directory),
                "source_folders": settings.source_folders,
            },
        )

        # Phase 1: Group versions
        version_groups = self.group_document_versions(settings.source_folders)

        if not version_groups:
            logger.error("No multi-version documents found")
            raise ValueError("No multi-version documents found")

        # Phase 2: Run tournaments
        tournament_results = self.run_tournaments(version_groups)

        logger.info(
            "Tournament-based consolidation complete",
            extra={"champions_identified": len(tournament_results)},
        )

        return tournament_results
