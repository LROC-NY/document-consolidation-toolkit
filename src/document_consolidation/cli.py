"""Command-line interface for document consolidation toolkit.

Production-ready CLI with:
- Click framework for robust argument parsing
- Progress bars using tqdm
- Colorful console output
- Integration with configuration system
- Comprehensive error handling
"""

import sys
from pathlib import Path
from typing import Optional

import click
from tqdm import tqdm

from document_consolidation.config import (
    Settings,
    get_logger,
    load_settings,
    setup_logging,
)
from document_consolidation.core.tournament import TournamentEngine
from document_consolidation.core.extractor import UniqueContentExtractor
from document_consolidation.core.integrator import DocumentIntegrator
from document_consolidation.core.verifier import DocumentVerifier
from document_consolidation.storage.filesystem_repository import FileSystemRepository


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to YAML configuration file",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging (DEBUG level)",
)
@click.option(
    "--quiet",
    is_flag=True,
    help="Suppress console output (WARNING level only)",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    help="Override output directory for integrated documents",
)
@click.pass_context
def cli(
    ctx: click.Context,
    config: Optional[Path],
    verbose: bool,
    quiet: bool,
    output_dir: Optional[Path],
) -> None:
    """Document Consolidation Toolkit - Production-ready legal document merging.

    Consolidates multiple versions of legal documents using tournament-based
    ranking, unique content extraction, and intelligent integration.

    \b
    Example:
        consolidate full --config config.yaml
        consolidate tournament --verbose
        consolidate integrate --output-dir ./output
    """
    try:
        # Load settings from config file or defaults
        settings = load_settings(config)

        # Apply CLI overrides
        if output_dir:
            settings.integration.output_dir = output_dir.expanduser().resolve()

        if verbose and quiet:
            click.secho(
                "Error: Cannot specify both --verbose and --quiet",
                fg="red",
                err=True,
            )
            ctx.exit(1)

        if verbose:
            settings.log_level = "DEBUG"
        elif quiet:
            settings.log_level = "WARNING"

        # Setup logging
        setup_logging(
            settings.log_dir,
            settings.log_level,
            console_output=not quiet,
            file_output=True,
        )

        # Store settings in context for subcommands
        ctx.obj = settings

        logger = get_logger(__name__)
        logger.info(f"Initialized with config: {config or 'defaults'}")
        logger.debug(f"Settings: {settings.model_dump()}")

    except Exception as e:
        click.secho(f"Error initializing CLI: {e}", fg="red", err=True)
        ctx.exit(1)


@cli.command()
@click.pass_obj
def full(settings: Settings) -> None:
    """Run complete consolidation pipeline.

    Executes all four phases:
    1. Tournament-based document ranking
    2. Extract unique content from non-champions
    3. Integrate improvements into champions
    4. Verify integrated document quality
    """
    logger = get_logger(__name__)

    click.secho("\n=== Document Consolidation Toolkit ===\n", fg="cyan", bold=True)
    click.secho(f"Input Directory: {settings.input_directory}", fg="cyan")
    click.secho(f"Output Directory: {settings.integration.output_dir}\n", fg="cyan")

    try:
        # Initialize repository
        repository = FileSystemRepository()

        # Phase 1: Tournament
        click.secho("Phase 1: Tournament-based ranking", fg="green", bold=True)
        logger.info("Starting tournament phase")

        engine = TournamentEngine(repository)
        tournament_results = engine.execute()

        click.secho(f"  ✓ Identified {len(tournament_results)} champions\n", fg="green")

        # Phase 2: Extract unique content
        click.secho("Phase 2: Extract unique content", fg="green", bold=True)
        logger.info("Starting extraction phase")

        extractor = UniqueContentExtractor(repository)
        extraction_results = extractor.run_extraction(tournament_results)

        improvements_count = sum(
            r["improvement_count"] for r in extraction_results.values() if r
        )
        click.secho(
            f"  ✓ Found {improvements_count} improvements across {len(extraction_results)} documents\n",
            fg="green",
        )

        # Phase 3: Integrate improvements
        click.secho("Phase 3: Integrate improvements", fg="green", bold=True)
        logger.info("Starting integration phase")

        integrator = DocumentIntegrator(repository)
        integration_results = integrator.run_integration(extraction_results)

        total_added_lines = sum(r.added_lines for r in integration_results)
        click.secho(
            f"  ✓ Integrated {len(integration_results)} documents (+{total_added_lines:,} lines)\n",
            fg="green",
        )

        # Phase 4: Verify quality
        click.secho("Phase 4: Verify document quality", fg="green", bold=True)
        logger.info("Starting verification phase")

        verifier = DocumentVerifier(repository)
        verification_results = verifier.run_verification(
            integration_results, tournament_results
        )

        total_issues = sum(len(r.issues) for r in verification_results)
        click.secho(
            f"  ✓ Verified {len(verification_results)} documents ({total_issues} issues found)\n",
            fg="green" if total_issues == 0 else "yellow",
        )

        # Summary
        click.secho("=" * 50, fg="cyan")
        click.secho("✓ Consolidation complete!", fg="green", bold=True)
        click.secho(f"Output directory: {settings.integration.output_dir}", fg="cyan")
        logger.info("Full consolidation pipeline completed successfully")

    except KeyboardInterrupt:
        click.secho("\n\nOperation cancelled by user", fg="yellow", err=True)
        logger.warning("User cancelled operation")
        sys.exit(130)

    except Exception as e:
        click.secho(f"\nError during consolidation: {e}", fg="red", err=True)
        logger.error(f"Consolidation failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.pass_obj
def tournament(settings: Settings) -> None:
    """Run tournament-based document ranking.

    Analyzes documents using weighted scoring criteria:
    - Completeness (length, sections)
    - Recency (modification time)
    - Structure (markdown quality)
    - Citations (legal citation density)
    - Arguments (legal argument density)
    """
    logger = get_logger(__name__)

    click.secho("\n=== Tournament-based Document Ranking ===\n", fg="cyan", bold=True)

    try:
        repository = FileSystemRepository()
        engine = TournamentEngine(repository)

        logger.info("Starting tournament ranking")
        tournament_results = engine.execute()

        click.secho(f"\n✓ Identified {len(tournament_results)} champions!", fg="green", bold=True)
        click.secho(f"Output directory: {settings.integration.output_dir}", fg="cyan")
        logger.info(f"Tournament ranking completed - {len(tournament_results)} champions identified")

    except Exception as e:
        click.secho(f"\nError during tournament: {e}", fg="red", err=True)
        logger.error(f"Tournament failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.pass_obj
def extract(settings: Settings) -> None:
    """Extract unique content from non-champion documents.

    Identifies content in non-champion versions that is not present
    in the champion document. Uses semantic similarity analysis to
    detect truly unique sections.
    """
    logger = get_logger(__name__)

    click.secho("\n=== Extract Unique Content ===\n", fg="cyan", bold=True)

    try:
        repository = FileSystemRepository()

        # Run tournament first
        logger.info("Running tournament phase (required for extraction)")
        engine = TournamentEngine(repository)
        tournament_results = engine.execute()

        # Now run extraction
        logger.info("Starting content extraction")
        extractor = UniqueContentExtractor(repository)
        extraction_results = extractor.run_extraction(tournament_results)

        improvements_count = sum(
            r["improvement_count"] for r in extraction_results.values() if r
        )
        click.secho(
            f"\n✓ Found {improvements_count} improvements across {len(extraction_results)} documents!",
            fg="green",
            bold=True,
        )
        logger.info("Content extraction completed successfully")

    except Exception as e:
        click.secho(f"\nError during extraction: {e}", fg="red", err=True)
        logger.error(f"Extraction failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.pass_obj
def integrate(settings: Settings) -> None:
    """Integrate unique content into champion documents.

    Merges unique content from non-champions into the champion document
    while preserving source attribution and adding evolution metadata.
    """
    logger = get_logger(__name__)

    click.secho("\n=== Integrate Improvements ===\n", fg="cyan", bold=True)

    try:
        repository = FileSystemRepository()

        # Run tournament and extraction first
        logger.info("Running tournament phase (required for integration)")
        engine = TournamentEngine(repository)
        tournament_results = engine.execute()

        logger.info("Running extraction phase (required for integration)")
        extractor = UniqueContentExtractor(repository)
        extraction_results = extractor.run_extraction(tournament_results)

        # Now run integration
        logger.info("Starting content integration")
        integrator = DocumentIntegrator(repository)
        integration_results = integrator.run_integration(extraction_results)

        total_added_lines = sum(r.added_lines for r in integration_results)
        click.secho(
            f"\n✓ Integrated {len(integration_results)} documents (+{total_added_lines:,} lines)!",
            fg="green",
            bold=True,
        )
        click.secho(
            f"Output directory: {settings.integration.output_dir}", fg="cyan"
        )
        logger.info("Content integration completed successfully")

    except Exception as e:
        click.secho(f"\nError during integration: {e}", fg="red", err=True)
        logger.error(f"Integration failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.pass_obj
def verify(settings: Settings) -> None:
    """Verify integrated documents for quality.

    Performs quality checks on integrated documents:
    - Markdown formatting compliance
    - Section numbering consistency
    - Duplicate section detection
    - Document navigation structure
    """
    logger = get_logger(__name__)

    click.secho("\n=== Verify Document Quality ===\n", fg="cyan", bold=True)

    try:
        repository = FileSystemRepository()

        # Run all previous phases
        logger.info("Running tournament phase (required for verification)")
        engine = TournamentEngine(repository)
        tournament_results = engine.execute()

        logger.info("Running extraction phase (required for verification)")
        extractor = UniqueContentExtractor(repository)
        extraction_results = extractor.run_extraction(tournament_results)

        logger.info("Running integration phase (required for verification)")
        integrator = DocumentIntegrator(repository)
        integration_results = integrator.run_integration(extraction_results)

        # Now run verification
        logger.info("Starting document verification")
        verifier = DocumentVerifier(repository)
        verification_results = verifier.run_verification(
            integration_results, tournament_results
        )

        total_issues = sum(len(r.issues) for r in verification_results)
        click.secho(
            f"\n✓ Verified {len(verification_results)} documents ({total_issues} issues found)!",
            fg="green" if total_issues == 0 else "yellow",
            bold=True,
        )
        logger.info("Document verification completed successfully")

    except Exception as e:
        click.secho(f"\nError during verification: {e}", fg="red", err=True)
        logger.error(f"Verification failed: {e}", exc_info=True)
        sys.exit(1)


def main() -> None:
    """Entry point for CLI.

    Invokes the Click command group with proper exception handling.
    """
    try:
        cli()
    except Exception as e:
        click.secho(f"Fatal error: {e}", fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
