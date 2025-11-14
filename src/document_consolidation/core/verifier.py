"""Document verification and quality assurance.

Implements Phase 4.5 of the intelligent cleanup workflow:
- Verifies integrated documents meet quality standards
- Checks markdown formatting, section numbering, duplication
- Ensures document navigability and metadata presence
- Generates verification reports
"""

import re
from pathlib import Path
from typing import List

from document_consolidation.config import get_logger, settings
from document_consolidation.models.document import (
    IntegrationResult,
    VerificationIssue,
    VerificationResult,
)
from document_consolidation.storage.document_repository import DocumentRepository

logger = get_logger(__name__)


class DocumentVerifier:
    """Verify integrated documents meet quality standards."""

    def __init__(self, repository: DocumentRepository):
        """Initialize verifier.

        Args:
            repository: Document repository for storage operations
        """
        self.repository = repository

    def verify_markdown_formatting(
        self, filepath: Path, content: str
    ) -> List[VerificationIssue]:
        """Check markdown formatting is correct.

        Args:
            filepath: Path to document
            content: Document content

        Returns:
            List of VerificationIssue objects
        """
        if not settings.verification.check_markdown_formatting:
            return []

        issues: List[VerificationIssue] = []
        lines = content.split("\n")

        # Check: Headers are properly formatted
        for i, line in enumerate(lines, 1):
            if line.startswith("#"):
                if not re.match(r"^#{1,6}\s+.+$", line):
                    issues.append(
                        VerificationIssue(
                            type="formatting",
                            severity="medium",
                            message=f"Malformed header: {line[:50]}",
                            line_number=i,
                        )
                    )

        # Check: No consecutive blank lines (more than max)
        blank_count = 0
        max_blanks = settings.verification.max_consecutive_blank_lines

        for i, line in enumerate(lines, 1):
            if line.strip() == "":
                blank_count += 1
                if blank_count > max_blanks:
                    issues.append(
                        VerificationIssue(
                            type="formatting",
                            severity="low",
                            message=f"Excessive blank lines ({blank_count} consecutive)",
                            line_number=i,
                        )
                    )
            else:
                blank_count = 0

        # Check: Document Evolution section exists (if metadata enabled)
        if settings.integration.add_evolution_metadata:
            if "## Document Evolution" not in content:
                issues.append(
                    VerificationIssue(
                        type="formatting",
                        severity="medium",
                        message="Missing Document Evolution metadata section",
                    )
                )

        if issues:
            logger.warning(
                "Formatting issues found",
                extra={"path": str(filepath), "issue_count": len(issues)},
            )
        else:
            logger.debug("Formatting verification passed", extra={"path": str(filepath)})

        return issues

    def verify_section_numbering(self, content: str) -> List[VerificationIssue]:
        """Check section numbering is correct.

        Args:
            content: Document content

        Returns:
            List of VerificationIssue objects
        """
        if not settings.verification.check_section_numbering:
            return []

        issues: List[VerificationIssue] = []
        lines = content.split("\n")
        sections: List[tuple[int, int, str]] = []

        for i, line in enumerate(lines, 1):
            header_match = re.match(r"^(#{2,6})\s+(.+)$", line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2)
                sections.append((i, level, title))

        # Check for proper hierarchy
        prev_level = 1
        for line_num, level, title in sections:
            if level > prev_level + 1:
                issues.append(
                    VerificationIssue(
                        type="numbering",
                        severity="low",
                        message=f"Section level jump from {prev_level} to {level}",
                        line_number=line_num,
                    )
                )
            prev_level = level

        if issues:
            logger.warning(
                "Section numbering issues found",
                extra={"issue_count": len(issues)},
            )
        else:
            logger.debug("Section numbering verification passed")

        return issues

    def verify_no_duplication(self, content: str) -> List[VerificationIssue]:
        """Check for obvious content duplication.

        Args:
            content: Document content

        Returns:
            List of VerificationIssue objects
        """
        if not settings.verification.check_no_duplication:
            return []

        issues: List[VerificationIssue] = []
        lines = content.split("\n")

        # Check for duplicate sections
        section_titles: List[str] = []
        for i, line in enumerate(lines, 1):
            if line.startswith("##"):
                title = line[2:].strip()
                if title in section_titles:
                    issues.append(
                        VerificationIssue(
                            type="duplication",
                            severity="high",
                            message=f"Duplicate section title: {title}",
                            line_number=i,
                        )
                    )
                section_titles.append(title)

        if issues:
            logger.warning(
                "Duplication issues found",
                extra={"issue_count": len(issues)},
            )
        else:
            logger.debug("Duplication verification passed")

        return issues

    def verify_document_navigability(self, content: str) -> List[VerificationIssue]:
        """Check document is navigable.

        Args:
            content: Document content

        Returns:
            List of VerificationIssue objects
        """
        if not settings.verification.check_document_navigability:
            return []

        issues: List[VerificationIssue] = []

        # Check: Document has sections
        has_sections = "## " in content

        if not has_sections:
            issues.append(
                VerificationIssue(
                    type="navigation",
                    severity="medium",
                    message="Document may not be navigable (no clear sections)",
                )
            )

        if issues:
            logger.warning(
                "Navigation issues found",
                extra={"issue_count": len(issues)},
            )
        else:
            logger.debug("Navigation verification passed")

        return issues

    def verify_document(
        self, filename: str, filepath: Path
    ) -> VerificationResult:
        """Verify a single integrated document.

        Args:
            filename: Document filename
            filepath: Path to document file

        Returns:
            VerificationResult object

        Raises:
            FileNotFoundError: If document not found
        """
        logger.info("Starting document verification", extra={"filename": filename})

        if not self.repository.document_exists(filepath):
            logger.error("Document not found", extra={"path": str(filepath)})
            raise FileNotFoundError(f"Document not found: {filepath}")

        # Load document
        try:
            content = self.repository.read_document(filepath)
            line_count = content.count("\n") + 1
            logger.debug(
                "Document loaded for verification",
                extra={"path": str(filepath), "lines": line_count},
            )
        except Exception as e:
            logger.error(
                "Failed to load document",
                extra={"path": str(filepath), "error": str(e)},
            )
            raise

        all_issues: List[VerificationIssue] = []

        # Run verifications
        logger.debug("Running verification checks")

        # 1. Markdown formatting
        formatting_issues = self.verify_markdown_formatting(filepath, content)
        all_issues.extend(formatting_issues)

        # 2. Section numbering
        numbering_issues = self.verify_section_numbering(content)
        all_issues.extend(numbering_issues)

        # 3. No duplication
        duplication_issues = self.verify_no_duplication(content)
        all_issues.extend(duplication_issues)

        # 4. Document navigability
        navigation_issues = self.verify_document_navigability(content)
        all_issues.extend(navigation_issues)

        # Create result
        passed = len(all_issues) == 0

        result = VerificationResult(
            filename=filename,
            filepath=filepath,
            line_count=line_count,
            issues=all_issues,
            passed=passed,
        )

        if passed:
            logger.info(
                "Document verification passed",
                extra={"filename": filename},
            )
        else:
            logger.warning(
                "Document verification failed",
                extra={"filename": filename, "issues": len(all_issues)},
            )

        return result

    def run_verification(
        self, integration_results: List[IntegrationResult]
    ) -> List[VerificationResult]:
        """Run verification for all integrated documents.

        Args:
            integration_results: Integration results from integrator

        Returns:
            List of VerificationResult objects

        Raises:
            ValueError: If integration_results is empty
        """
        if not integration_results:
            logger.error("No integration results to verify")
            raise ValueError("No integration results to verify")

        logger.info(
            "Starting verification process",
            extra={"document_count": len(integration_results)},
        )

        verification_results: List[VerificationResult] = []
        output_dir = settings.input_directory / settings.integration.output_dir

        for result in integration_results:
            output_filename = f"COMPREHENSIVE_{result.filename}"
            filepath = output_dir / output_filename

            try:
                verification_result = self.verify_document(
                    result.filename, filepath
                )
                verification_results.append(verification_result)

            except Exception as e:
                logger.error(
                    "Verification failed for document",
                    extra={"filename": result.filename, "error": str(e)},
                )
                continue

        # Summary
        passed = sum(1 for r in verification_results if r.passed)
        total = len(verification_results)

        logger.info(
            "Verification process complete",
            extra={
                "total_documents": total,
                "passed": passed,
                "failed": total - passed,
            },
        )

        return verification_results


class ReportGenerator:
    """Generate comprehensive reports for the consolidation process."""

    @staticmethod
    def generate_integration_report(
        tournament_results: dict,
        integration_results: List[IntegrationResult],
    ) -> str:
        """Generate comprehensive integration report.

        Args:
            tournament_results: Tournament results dictionary
            integration_results: List of integration results

        Returns:
            Markdown report content
        """
        from datetime import datetime

        report = []

        report.append("# Phase 4: Tournament-Based Document Consolidation")
        report.append(
            f"\n**Completion Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report.append("**Status**: COMPLETE")
        report.append("\n---\n")

        report.append("## Executive Summary")
        report.append(
            f"\nSuccessfully consolidated **{len(tournament_results)} document families** "
            f"across {len(settings.source_folders)} source folders using tournament-based ranking system."
        )
        report.append("\n**Integration Results**:")
        report.append(f"- Documents with improvements: {len(integration_results)}")
        report.append(
            f"- Documents already comprehensive: {len(tournament_results) - len(integration_results)}"
        )

        total_original = sum(r.original_line_count for r in integration_results)
        total_integrated = sum(r.integrated_line_count for r in integration_results)
        total_added = sum(r.added_lines for r in integration_results)

        report.append(f"- Total lines added: {total_added:,}")
        if total_original > 0:
            report.append(
                f"- Average growth: {(total_added / total_original * 100):.1f}%"
            )
        report.append("\n---\n")

        report.append("## Tournament Methodology")
        report.append("\n### Evaluation Criteria (0-50 points total)")
        report.append(
            "1. **Completeness** (0-10): Document length, section count, subsection depth"
        )
        report.append("2. **Recency** (0-10): Modification timestamps")
        report.append(
            "3. **Structure** (0-10): Markdown hierarchy, headers, lists, code blocks"
        )
        report.append("4. **Citations** (0-10): Legal citations, case law references")
        report.append(
            "5. **Arguments** (0-10): Legal reasoning density and quality"
        )
        report.append("\n---\n")

        report.append("## Integration Results by Document")

        for result in sorted(
            integration_results, key=lambda x: x.added_lines, reverse=True
        ):
            report.append(f"\n### {result.filename}")
            report.append(f"- **Champion**: {result.champion_folder}")
            report.append(f"- **Original Lines**: {result.original_line_count:,}")
            report.append(f"- **Integrated Lines**: {result.integrated_line_count:,}")
            report.append(
                f"- **Added Lines**: +{result.added_lines:,} (+{result.growth_percentage:.1f}%)"
            )
            report.append(
                f"- **Improvements Integrated**: {result.improvements_integrated}"
            )
            report.append(f"- **Source Folders**: {', '.join(result.source_folders)}")

        report.append("\n---\n")
        report.append("\n**Status**: COMPREHENSIVE MASTER DOCUMENTS READY FOR USE")

        return "\n".join(report)

    @staticmethod
    def generate_verification_report(
        verification_results: List[VerificationResult],
    ) -> str:
        """Generate verification report.

        Args:
            verification_results: List of verification results

        Returns:
            Markdown report content
        """
        from datetime import datetime

        report = []

        report.append("# Document Verification Report")
        report.append(
            f"\n**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report.append("\n---\n")

        passed = sum(1 for r in verification_results if r.passed)
        total = len(verification_results)

        report.append("## Summary")
        report.append(f"\n- **Documents Verified**: {total}")
        report.append(f"- **Passed**: {passed}")
        report.append(f"- **Failed**: {total - passed}")
        report.append("\n---\n")

        # Documents with issues
        failed_results = [r for r in verification_results if not r.passed]

        if failed_results:
            report.append("## Documents with Issues")

            for result in failed_results:
                report.append(f"\n### {result.filename}")
                report.append(f"- **Issues**: {result.issue_count}")

                # Group issues by type
                issue_types = {}
                for issue in result.issues:
                    if issue.type not in issue_types:
                        issue_types[issue.type] = []
                    issue_types[issue.type].append(issue)

                for issue_type, issues in issue_types.items():
                    report.append(f"\n**{issue_type.title()} Issues ({len(issues)})**:")
                    for issue in issues[:5]:  # Limit to first 5 per type
                        line_info = f" (Line {issue.line_number})" if issue.line_number else ""
                        report.append(f"- {issue.message}{line_info}")
                    if len(issues) > 5:
                        report.append(f"- ... and {len(issues) - 5} more")

        else:
            report.append("## All Documents Passed Verification")

        report.append("\n---\n")
        report.append(
            f"\n**Overall Status**: {'PASSED' if passed == total else 'ISSUES FOUND'}"
        )

        return "\n".join(report)
