"""Intelligent document integration with citation support.

Implements Phase 4.4 of the intelligent cleanup workflow:
- Merges unique improvements from non-champion versions into champions
- Integrates citations and enhanced content
- Adds source attribution and evolution metadata
- Creates comprehensive master documents
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from document_consolidation.config import get_logger, settings
from document_consolidation.models.document import (
    IntegrationResult,
    UniqueImprovement,
)
from document_consolidation.storage.document_repository import DocumentRepository

logger = get_logger(__name__)


class DocumentIntegrator:
    """Intelligently integrate improvements into champion documents."""

    def __init__(self, repository: DocumentRepository):
        """Initialize integrator.

        Args:
            repository: Document repository for storage operations
        """
        self.repository = repository

    def find_insertion_point(
        self, champion_content: str, improvement: UniqueImprovement
    ) -> int:
        """Find optimal insertion point for improvement.

        Args:
            champion_content: Champion document content
            improvement: Improvement to insert

        Returns:
            Line index for insertion
        """
        lines = champion_content.split("\n")

        # Strategy 1: If it's a new section, append before the final metadata/footer
        if improvement.type == "new_section":
            # Look for common footer patterns
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].startswith("---") or lines[i].startswith(
                    "**Document Evolution"
                ):
                    logger.debug(
                        "Found footer for new section insertion",
                        extra={"line": i},
                    )
                    return i

            # No footer found - append to end
            logger.debug("No footer found, appending to end")
            return len(lines)

        # Strategy 2: If it's an enhanced section, find the related section
        if improvement.type == "enhanced_section" and improvement.title:
            section_title = improvement.title.lower()

            # Find the section in champion
            for i, line in enumerate(lines):
                if line.startswith("##") and section_title in line.lower():
                    # Find the end of this section
                    for j in range(i + 1, len(lines)):
                        # Next section header
                        if lines[j].startswith("##"):
                            logger.debug(
                                "Found section end for enhanced section",
                                extra={"line": j},
                            )
                            return j
                    # No next section - append at end
                    logger.debug("No next section, appending to end")
                    return len(lines)

        # Default: append at end
        logger.debug("Using default insertion point (end)")
        return len(lines)

    def format_improvement(
        self, improvement: UniqueImprovement, source_folder: str
    ) -> str:
        """Format improvement for insertion.

        Args:
            improvement: Improvement to format
            source_folder: Source folder name

        Returns:
            Formatted improvement text
        """
        if improvement.type == "citation_enhancement":
            # Skip citation enhancements if disabled
            if settings.integration.skip_citation_enhancement:
                logger.debug("Skipping citation enhancement (disabled in settings)")
                return ""
            return ""  # Will be handled by integrate_citations

        formatted = []

        formatted.append("")  # Blank line before
        formatted.append(f"## {improvement.title}")

        # Add source attribution if enabled
        if settings.integration.preserve_source_attribution:
            formatted.append(f"*[Integrated from {source_folder}]*")
            formatted.append("")

        # Add content (skip the header line from original)
        if improvement.content:
            content_lines = improvement.content.split("\n")[
                1:
            ]  # Skip first line (header)
            formatted.extend(content_lines)

        formatted.append("")  # Blank line after

        return "\n".join(formatted)

    def extract_citations_from_improvement(
        self, improvement: UniqueImprovement, other_content: str
    ) -> List[str]:
        """Extract specific citation text from improvement.

        Args:
            improvement: Citation enhancement improvement
            other_content: Full content of the non-champion version

        Returns:
            List of citation strings to integrate
        """
        if improvement.type != "citation_enhancement" or not improvement.citations:
            return []

        citations_found: List[str] = []

        # Citation patterns to extract
        patterns = {
            "matter_of": r"Matter of [A-Z][^.]*\.",
            "usc": r"\d+\s+U\.?S\.?C\.?\s*§?\s*\d+[^.]*\.",
            "cfr": r"\d+\s+C\.?F\.?R\.?\s*§?\s*\d+[^.]*\.",
            "ina": r"INA\s*§\s*\d+[^.]*\.",
            "form_i": r"Form I-\d+[^.]*\.",
            "case_citations": r"\d+\s+F\.\d+d\s+\d+[^.]*\.",
        }

        for citation_type, citation_data in improvement.citations.items():
            if citation_type in patterns:
                pattern = patterns[citation_type]
                matches = re.findall(pattern, other_content)

                # Take up to the difference count
                difference = citation_data.get("difference", 0)
                citations_found.extend(matches[:difference])

                logger.debug(
                    "Extracted citations",
                    extra={
                        "type": citation_type,
                        "count": len(matches[:difference]),
                    },
                )

        return citations_found

    def integrate_citations(
        self,
        champion_content: str,
        citations: List[str],
        source_folder: str,
    ) -> str:
        """Integrate citations into champion document.

        Args:
            champion_content: Champion document content
            citations: List of citation strings to integrate
            source_folder: Source folder name

        Returns:
            Updated content with integrated citations
        """
        if not citations or not settings.integration.integrate_citations:
            return champion_content

        # Create citations section
        citation_section = [
            "",
            "## Additional Legal Citations",
        ]

        if settings.integration.preserve_source_attribution:
            citation_section.append(f"*[Integrated from {source_folder}]*")

        citation_section.append("")

        for citation in citations:
            citation_section.append(f"- {citation.strip()}")

        citation_section.append("")

        # Find insertion point (before footer/metadata)
        lines = champion_content.split("\n")
        insertion_point = len(lines)

        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith("---") or lines[i].startswith(
                "**Document Evolution"
            ):
                insertion_point = i
                break

        # Insert citations
        lines.insert(insertion_point, "\n".join(citation_section))
        updated_content = "\n".join(lines)

        logger.info(
            "Citations integrated",
            extra={"count": len(citations), "source": source_folder},
        )

        return updated_content

    def add_evolution_metadata(
        self,
        original_content: str,
        integrated_content: str,
        filename: str,
        improvements: List[UniqueImprovement],
    ) -> str:
        """Add evolution metadata to document.

        Args:
            original_content: Original champion content
            integrated_content: Content with improvements integrated
            filename: Document filename
            improvements: List of improvements integrated

        Returns:
            Content with metadata appended
        """
        if not settings.integration.add_evolution_metadata:
            return integrated_content

        original_lines = original_content.count("\n") + 1
        integrated_lines = integrated_content.count("\n") + 1
        added_lines = integrated_lines - original_lines

        # Collect source folders
        source_folders: Set[str] = set()
        for imp in improvements:
            source_folders.add(imp.source_folder)

        metadata = [
            "",
            "---",
            "",
            "## Document Evolution",
            "",
            f"**Original Champion Lines**: {original_lines}",
            f"**Integrated Lines**: {integrated_lines} (+{added_lines} lines)",
            f"**Improvements Integrated**: {len(improvements)}",
            "",
            "**Sources**:",
        ]

        for folder in sorted(source_folders):
            count = len([imp for imp in improvements if imp.source_folder == folder])
            metadata.append(f"- {folder}: {count} improvements")

        metadata.extend(
            [
                "",
                f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}",
                "**Status**: COMPREHENSIVE MASTER DOCUMENT",
                "",
            ]
        )

        return integrated_content + "\n".join(metadata)

    def integrate_document(
        self, filename: str, improvement_data: Dict
    ) -> Optional[IntegrationResult]:
        """Integrate all improvements for a single document.

        Args:
            filename: Document filename
            improvement_data: Improvement data from extractor

        Returns:
            IntegrationResult, or None if no improvements integrated

        Raises:
            FileNotFoundError: If champion document not found
        """
        logger.info("Starting document integration", extra={"filename": filename})

        champion_path = Path(improvement_data["champion_path"])
        improvements_raw = improvement_data["improvements"]

        # Convert raw dicts to UniqueImprovement objects
        improvements = [UniqueImprovement(**imp) for imp in improvements_raw]

        # Load champion document
        try:
            champion_content = self.repository.read_document(champion_path)
            original_lines = champion_content.count("\n") + 1
            logger.debug(
                "Champion loaded",
                extra={"path": str(champion_path), "lines": original_lines},
            )
        except Exception as e:
            logger.error(
                "Failed to load champion",
                extra={"path": str(champion_path), "error": str(e)},
            )
            raise

        # Sort improvements by type (enhanced sections first, then new sections)
        sorted_improvements = sorted(
            improvements, key=lambda x: 0 if x.type == "enhanced_section" else 1
        )

        integrated_content = champion_content
        integration_count = 0
        citation_improvements: List[UniqueImprovement] = []

        # First pass: Integrate sections
        for improvement in sorted_improvements:
            # Save citation enhancements for later
            if improvement.type == "citation_enhancement":
                citation_improvements.append(improvement)
                continue

            # Find insertion point
            insertion_point = self.find_insertion_point(
                integrated_content, improvement
            )

            # Format improvement
            formatted_improvement = self.format_improvement(
                improvement, improvement.source_folder
            )

            if not formatted_improvement:
                continue

            # Insert into document
            lines = integrated_content.split("\n")
            lines.insert(insertion_point, formatted_improvement)
            integrated_content = "\n".join(lines)

            integration_count += 1
            logger.info(
                "Improvement integrated",
                extra={
                    "title": improvement.title,
                    "source": improvement.source_folder,
                    "type": improvement.type,
                },
            )

        # Second pass: Integrate citations
        for citation_improvement in citation_improvements:
            if settings.integration.skip_citation_enhancement:
                logger.debug("Skipping citation enhancement (disabled)")
                continue

            # For citation integration, we need to read the source document
            # to extract the actual citation text
            source_folder = citation_improvement.source_folder
            source_path = Path(str(champion_path).replace(
                improvement_data["champion"], source_folder
            ))

            try:
                source_content = self.repository.read_document(source_path)
                citations = self.extract_citations_from_improvement(
                    citation_improvement, source_content
                )

                if citations:
                    integrated_content = self.integrate_citations(
                        integrated_content, citations, source_folder
                    )
                    integration_count += 1

            except Exception as e:
                logger.warning(
                    "Failed to integrate citations",
                    extra={"source": source_folder, "error": str(e)},
                )
                continue

        if integration_count == 0:
            logger.info("No improvements integrated", extra={"filename": filename})
            return None

        # Add evolution metadata
        integrated_content = self.add_evolution_metadata(
            champion_content, integrated_content, filename, improvements
        )

        # Create result
        integrated_lines = integrated_content.count("\n") + 1
        source_folders = list(set(imp.source_folder for imp in improvements))

        result = IntegrationResult(
            filename=filename,
            champion_folder=improvement_data["champion"],
            champion_path=champion_path,
            original_line_count=original_lines,
            integrated_line_count=integrated_lines,
            added_lines=integrated_lines - original_lines,
            improvements_integrated=integration_count,
            source_folders=source_folders,
            integrated_content=integrated_content,
        )

        logger.info(
            "Document integration complete",
            extra={
                "filename": filename,
                "original_lines": original_lines,
                "integrated_lines": integrated_lines,
                "added_lines": result.added_lines,
                "growth": f"{result.growth_percentage:.1f}%",
            },
        )

        return result

    def save_integrated_document(
        self, result: IntegrationResult
    ) -> Optional[Path]:
        """Save integrated document to output directory.

        Args:
            result: Integration result

        Returns:
            Output path, or None if save failed
        """
        # Ensure output directory exists
        output_dir = settings.input_directory / settings.integration.output_dir
        self.repository.create_directory(output_dir)

        # Create filename with COMPREHENSIVE_ prefix
        output_filename = f"COMPREHENSIVE_{result.filename}"
        output_path = output_dir / output_filename

        try:
            self.repository.write_document(output_path, result.integrated_content)

            logger.info(
                "Integrated document saved",
                extra={"path": str(output_path), "size": len(result.integrated_content)},
            )

            return output_path

        except Exception as e:
            logger.error(
                "Failed to save integrated document",
                extra={"path": str(output_path), "error": str(e)},
            )
            return None

    def run_integration(
        self, unique_improvements: Dict[str, Dict]
    ) -> List[IntegrationResult]:
        """Run integration for all documents.

        Args:
            unique_improvements: Unique improvements from extractor

        Returns:
            List of IntegrationResult objects

        Raises:
            ValueError: If unique_improvements is empty
        """
        if not unique_improvements:
            logger.error("No improvements to integrate")
            raise ValueError("No improvements to integrate")

        logger.info(
            "Starting intelligent integration",
            extra={
                "document_count": len(unique_improvements),
                "output_dir": str(settings.integration.output_dir),
            },
        )

        integration_results: List[IntegrationResult] = []
        successful_integrations = 0

        for filename, improvement_data in sorted(unique_improvements.items()):
            result = self.integrate_document(filename, improvement_data)

            if result:
                output_path = self.save_integrated_document(result)
                if output_path:
                    integration_results.append(result)
                    successful_integrations += 1

        logger.info(
            "Intelligent integration complete",
            extra={
                "documents_processed": len(unique_improvements),
                "successful_integrations": successful_integrations,
            },
        )

        return integration_results
