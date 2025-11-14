"""Unique content extraction from non-champion versions.

Implements Phase 4.3 of the intelligent cleanup workflow:
- Analyzes differences between champion and non-champion versions
- Identifies unique improvements worth integrating
- Extracts unique sections, enhanced content, and citation improvements
"""

import difflib
import re
from pathlib import Path
from typing import Dict, List, Optional

from document_consolidation.config import get_logger
from document_consolidation.models.document import (
    CitationCounts,
    SectionData,
    TournamentResult,
    UniqueImprovement,
)
from document_consolidation.storage.document_repository import DocumentRepository

logger = get_logger(__name__)


class UniqueContentExtractor:
    """Extract unique content from non-champion versions."""

    # Similarity threshold for detecting enhanced sections
    SIMILARITY_THRESHOLD = 0.8

    # Minimum added lines to consider section significantly enhanced
    MIN_ADDED_LINES = 3

    def __init__(self, repository: DocumentRepository):
        """Initialize extractor.

        Args:
            repository: Document repository for storage operations
        """
        self.repository = repository

    def extract_sections(self, content: str) -> List[SectionData]:
        """Extract markdown sections with their content.

        Args:
            content: Document content

        Returns:
            List of SectionData objects
        """
        sections: List[SectionData] = []
        lines = content.split("\n")
        current_section: Optional[Dict] = None
        current_content: List[str] = []

        for i, line in enumerate(lines):
            # Detect section headers (##, ###, etc.)
            header_match = re.match(r"^(#{2,6})\s+(.+)$", line)

            if header_match:
                # Save previous section
                if current_section:
                    sections.append(
                        SectionData(
                            level=current_section["level"],
                            title=current_section["title"],
                            content="\n".join(current_content),
                            line_start=current_section["line_start"],
                            line_end=i - 1,
                        )
                    )

                # Start new section
                current_section = {
                    "level": len(header_match.group(1)),
                    "title": header_match.group(2).strip(),
                    "line_start": i,
                }
                current_content = [line]
            else:
                if current_content:
                    current_content.append(line)

        # Add final section
        if current_section and current_content:
            sections.append(
                SectionData(
                    level=current_section["level"],
                    title=current_section["title"],
                    content="\n".join(current_content),
                    line_start=current_section["line_start"],
                    line_end=len(lines) - 1,
                )
            )

        logger.debug(
            "Sections extracted",
            extra={"section_count": len(sections)},
        )

        return sections

    def find_unique_sections(
        self, champion_content: str, other_content: str, other_folder: str
    ) -> List[UniqueImprovement]:
        """Find sections in other_content that are unique or significantly different.

        Args:
            champion_content: Champion document content
            other_content: Non-champion document content
            other_folder: Source folder name

        Returns:
            List of UniqueImprovement objects
        """
        champion_sections = self.extract_sections(champion_content)
        other_sections = self.extract_sections(other_content)

        unique_sections: List[UniqueImprovement] = []

        # Create lookup for champion sections by title
        champion_titles = {s.title.lower(): s for s in champion_sections}

        for section in other_sections:
            section_title_lower = section.title.lower()

            # Check if section exists in champion
            if section_title_lower not in champion_titles:
                # Completely new section
                unique_sections.append(
                    UniqueImprovement(
                        type="new_section",
                        title=section.title,
                        level=section.level,
                        content=section.content,
                        lines=f"{section.line_start}-{section.line_end}",
                        source_folder=other_folder,
                        value="high",
                        reason="Section not present in champion version",
                    )
                )

                logger.debug(
                    "Found new section",
                    extra={
                        "title": section.title,
                        "source": other_folder,
                    },
                )

            else:
                # Section exists - check for significant differences
                champion_section = champion_titles[section_title_lower]

                # Calculate similarity ratio
                similarity = difflib.SequenceMatcher(
                    None,
                    champion_section.content,
                    section.content,
                ).ratio()

                # If less than threshold, might have unique content
                if similarity < self.SIMILARITY_THRESHOLD:
                    # Extract the differences
                    diff = list(
                        difflib.unified_diff(
                            champion_section.content.splitlines(),
                            section.content.splitlines(),
                            lineterm="",
                        )
                    )

                    # Count added lines (lines starting with '+' but not '+++')
                    added_lines = [
                        line
                        for line in diff
                        if line.startswith("+") and not line.startswith("+++")
                    ]

                    if len(added_lines) >= self.MIN_ADDED_LINES:
                        value = "medium" if len(added_lines) < 10 else "high"

                        unique_sections.append(
                            UniqueImprovement(
                                type="enhanced_section",
                                title=section.title,
                                level=section.level,
                                content=section.content,
                                lines=f"{section.line_start}-{section.line_end}",
                                source_folder=other_folder,
                                value=value,
                                reason=f"Section has {len(added_lines)} additional lines not in champion",
                                similarity=round(similarity, 2),
                                additions_preview="\n".join(added_lines[:5]),
                            )
                        )

                        logger.debug(
                            "Found enhanced section",
                            extra={
                                "title": section.title,
                                "source": other_folder,
                                "additions": len(added_lines),
                                "similarity": similarity,
                            },
                        )

        return unique_sections

    def analyze_citations(self, content: str) -> CitationCounts:
        """Count legal citations in content.

        Args:
            content: Document content

        Returns:
            CitationCounts object with counts by type
        """
        citation_counts = CitationCounts(
            matter_of=len(re.findall(r"Matter of [A-Z]", content)),
            usc=len(re.findall(r"\d+\s+U\.?S\.?C\.?", content)),
            cfr=len(re.findall(r"\d+\s+C\.?F\.?R\.?", content)),
            ina=len(re.findall(r"INA\s*§\s*\d+", content)),
            form_i=len(re.findall(r"Form I-\d+", content)),
            case_citations=len(re.findall(r"\d+\s+F\.\d+d\s+\d+", content)),
        )

        logger.debug(
            "Citations analyzed",
            extra={"total_citations": citation_counts.total},
        )

        return citation_counts

    def compare_citations(
        self, champion_content: str, other_content: str
    ) -> Optional[Dict[str, Dict[str, int]]]:
        """Check if other version has more or different citations.

        Args:
            champion_content: Champion document content
            other_content: Non-champion document content

        Returns:
            Dictionary of citation improvements, or None if no improvements
        """
        champion_citations = self.analyze_citations(champion_content)
        other_citations = self.analyze_citations(other_content)

        improvements: Dict[str, Dict[str, int]] = {}

        for field_name in CitationCounts.__fields__.keys():
            if field_name == "total":
                continue

            champion_count = getattr(champion_citations, field_name)
            other_count = getattr(other_citations, field_name)

            if other_count > champion_count:
                improvements[field_name] = {
                    "champion": champion_count,
                    "other": other_count,
                    "difference": other_count - champion_count,
                }

        if improvements:
            logger.debug(
                "Citation improvements found",
                extra={"improvement_types": len(improvements)},
            )
            return improvements

        return None

    def extract_for_document(
        self, tournament_result: TournamentResult
    ) -> Optional[Dict[str, any]]:
        """Extract unique content for a single document.

        Args:
            tournament_result: Tournament result for the document

        Returns:
            Dictionary with improvements, or None if no improvements found

        Raises:
            FileNotFoundError: If champion or version files not found
        """
        filename = tournament_result.filename
        champion_folder = tournament_result.champion_folder
        champion_path = tournament_result.champion_path

        logger.info(
            "Analyzing document for unique content",
            extra={"filename": filename, "champion": champion_folder},
        )

        # Load champion content
        try:
            champion_content = self.repository.read_document(champion_path)
        except Exception as e:
            logger.error(
                "Failed to read champion document",
                extra={"path": str(champion_path), "error": str(e)},
            )
            raise

        improvements: List[UniqueImprovement] = []

        # Analyze each non-champion version
        for folder, scores in tournament_result.all_scores.items():
            if folder == champion_folder:
                continue

            # Find path for this version
            other_path = (
                Path(str(champion_path).replace(champion_folder, folder))
            )

            if not self.repository.document_exists(other_path):
                logger.warning(
                    "Version file not found",
                    extra={"folder": folder, "path": str(other_path)},
                )
                continue

            # Load other version content
            try:
                other_content = self.repository.read_document(other_path)
            except Exception as e:
                logger.warning(
                    "Failed to read version",
                    extra={"folder": folder, "error": str(e)},
                )
                continue

            logger.debug(
                "Comparing versions",
                extra={"champion": champion_folder, "other": folder},
            )

            # Find unique sections
            unique_sections = self.find_unique_sections(
                champion_content, other_content, folder
            )

            if unique_sections:
                logger.info(
                    "Found unique sections",
                    extra={"folder": folder, "count": len(unique_sections)},
                )
                improvements.extend(unique_sections)

            # Check for citation improvements
            citation_improvements = self.compare_citations(
                champion_content, other_content
            )

            if citation_improvements:
                logger.info(
                    "Found citation improvements",
                    extra={"folder": folder, "types": len(citation_improvements)},
                )
                improvements.append(
                    UniqueImprovement(
                        type="citation_enhancement",
                        source_folder=folder,
                        citations=citation_improvements,
                        value="high",
                        reason="Contains additional legal citations not in champion",
                    )
                )

        if not improvements:
            logger.info(
                "No unique content found",
                extra={"filename": filename},
            )
            return None

        logger.info(
            "Unique content extraction complete",
            extra={"filename": filename, "improvements": len(improvements)},
        )

        return {
            "champion": champion_folder,
            "champion_path": str(champion_path),
            "champion_score": tournament_result.champion_score,
            "improvements": [imp.dict() for imp in improvements],
            "improvement_count": len(improvements),
        }

    def run_extraction(
        self, tournament_results: Dict[str, TournamentResult]
    ) -> Dict[str, Dict]:
        """Run extraction for all documents.

        Args:
            tournament_results: Tournament results from TournamentEngine

        Returns:
            Dictionary mapping filename to improvement data

        Raises:
            ValueError: If tournament_results is empty
        """
        if not tournament_results:
            logger.error("No tournament results to process")
            raise ValueError("No tournament results to process")

        logger.info(
            "Starting unique content extraction",
            extra={"document_count": len(tournament_results)},
        )

        unique_improvements: Dict[str, Dict] = {}
        total_improvements = 0
        documents_with_improvements = 0

        for filename, result in sorted(tournament_results.items()):
            unique_content = self.extract_for_document(result)

            if unique_content:
                unique_improvements[filename] = unique_content
                total_improvements += unique_content["improvement_count"]
                documents_with_improvements += 1

        logger.info(
            "Unique content extraction complete",
            extra={
                "documents_analyzed": len(tournament_results),
                "documents_with_improvements": documents_with_improvements,
                "total_improvements": total_improvements,
            },
        )

        return unique_improvements
