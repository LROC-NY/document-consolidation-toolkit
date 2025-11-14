"""Configuration management for document consolidation toolkit.

Production-ready settings system with:
- Pydantic-based validation
- YAML configuration file support
- Environment variable overrides
- Nested settings structures
- Smart defaults for legal document consolidation
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class TournamentSettings(BaseModel):
    """Tournament scoring configuration.

    Controls the weighting of different scoring criteria in the
    tournament-based document ranking system.
    """

    completeness_weight: float = Field(
        default=10.0,
        ge=0.0,
        le=10.0,
        description="Weight for document completeness (length, sections)",
    )
    recency_weight: float = Field(
        default=10.0,
        ge=0.0,
        le=10.0,
        description="Weight for modification recency",
    )
    structure_weight: float = Field(
        default=10.0,
        ge=0.0,
        le=10.0,
        description="Weight for markdown structure quality",
    )
    citations_weight: float = Field(
        default=10.0,
        ge=0.0,
        le=10.0,
        description="Weight for legal citations density",
    )
    arguments_weight: float = Field(
        default=10.0,
        ge=0.0,
        le=10.0,
        description="Weight for legal argument density",
    )

    @field_validator("*", mode="before")
    @classmethod
    def validate_weight_range(cls, v: Any, info) -> float:
        """Validate weight is in valid range."""
        if not isinstance(v, (int, float)):
            raise ValueError(f"Weight must be numeric, got {type(v)}")

        value = float(v)
        if not 0.0 <= value <= 10.0:
            raise ValueError(
                f"{info.field_name} must be between 0 and 10, got {value}"
            )
        return value

    @property
    def total_weight(self) -> float:
        """Calculate total weight across all criteria."""
        return (
            self.completeness_weight
            + self.recency_weight
            + self.structure_weight
            + self.citations_weight
            + self.arguments_weight
        )


class IntegrationSettings(BaseModel):
    """Content integration configuration.

    Controls how unique content from non-champion versions is
    integrated into the champion document.
    """

    output_dir: Path = Field(
        default=Path("output"),
        description="Output directory for integrated documents",
    )
    add_evolution_metadata: bool = Field(
        default=True,
        description="Add metadata about document evolution",
    )
    preserve_source_attribution: bool = Field(
        default=True,
        description="Preserve source folder attribution for improvements",
    )
    integrate_citations: bool = Field(
        default=True,
        description="Integrate citation enhancements from other versions",
    )
    skip_citation_enhancement: bool = Field(
        default=False,
        description="Skip citation enhancement step",
    )
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Threshold for considering sections similar",
    )
    min_added_lines: int = Field(
        default=3,
        ge=1,
        description="Minimum lines to consider as unique content",
    )

    @field_validator("output_dir", mode="before")
    @classmethod
    def convert_to_path(cls, v: Any) -> Path:
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v).expanduser().resolve()
        return v


class VerificationSettings(BaseModel):
    """Document verification configuration.

    Controls quality checks performed on integrated documents.
    """

    check_markdown_formatting: bool = Field(
        default=True,
        description="Check markdown formatting compliance",
    )
    check_section_numbering: bool = Field(
        default=True,
        description="Check section numbering consistency",
    )
    check_no_duplication: bool = Field(
        default=True,
        description="Check for duplicate sections",
    )
    check_document_navigability: bool = Field(
        default=True,
        description="Check document navigation structure",
    )
    max_consecutive_blank_lines: int = Field(
        default=2,
        ge=1,
        description="Maximum allowed consecutive blank lines",
    )


class Settings(BaseModel):
    """Main application settings.

    Root settings object with nested configuration for all subsystems.
    Supports loading from YAML files and environment variables.
    """

    # Core settings
    input_directory: Path = Field(
        default=Path.cwd(),
        description="Base directory containing source folders",
    )
    source_folders: List[str] = Field(
        default_factory=lambda: ["Markdown Document 2", "Markdown Document 3", "Markdown Document 4"],
        description="Source folders to scan for documents",
    )
    file_pattern: str = Field(
        default="*.md",
        description="File pattern for document discovery",
    )

    # Nested subsystem settings
    tournament: TournamentSettings = Field(
        default_factory=TournamentSettings,
        description="Tournament scoring configuration",
    )
    integration: IntegrationSettings = Field(
        default_factory=IntegrationSettings,
        description="Content integration configuration",
    )
    verification: VerificationSettings = Field(
        default_factory=VerificationSettings,
        description="Document verification configuration",
    )

    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    log_dir: Optional[Path] = Field(
        default=None,
        description="Directory for log files (None = output_dir/logs)",
    )

    @field_validator("input_directory", mode="before")
    @classmethod
    def expand_input_directory(cls, v: Any) -> Path:
        """Expand and resolve input directory path."""
        if isinstance(v, str):
            # Expand ~ and environment variables
            expanded = os.path.expandvars(os.path.expanduser(v))
            return Path(expanded).resolve()
        return Path(v).resolve()

    @field_validator("log_dir", mode="before")
    @classmethod
    def expand_log_dir(cls, v: Any) -> Optional[Path]:
        """Expand and resolve log directory path."""
        if v is None:
            return None
        if isinstance(v, str):
            expanded = os.path.expandvars(os.path.expanduser(v))
            return Path(expanded).resolve()
        return Path(v).resolve()

    @model_validator(mode="after")
    def set_log_dir_default(self) -> "Settings":
        """Set log_dir default based on output_dir if not specified."""
        if self.log_dir is None:
            self.log_dir = self.integration.output_dir / "logs"
        return self

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True
        validate_assignment = True


def load_settings(config_path: Optional[Path] = None) -> Settings:
    """Load settings from YAML file with environment variable overrides.

    Args:
        config_path: Path to YAML configuration file. If None or file doesn't
                    exist, returns settings with defaults.

    Returns:
        Settings object with loaded configuration

    Raises:
        ValueError: If configuration validation fails
        yaml.YAMLError: If YAML parsing fails

    Example:
        >>> settings = load_settings(Path("config.yaml"))
        >>> print(settings.tournament.completeness_weight)
        10.0
    """
    config_data: Dict[str, Any] = {}

    # Load from YAML file if exists
    if config_path and config_path.exists():
        try:
            with open(config_path, "r") as f:
                yaml_data = yaml.safe_load(f)
                if yaml_data:
                    config_data = yaml_data
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML config: {e}") from e

    # Apply environment variable overrides
    config_data = _apply_environment_overrides(config_data)

    # Create and return Settings object
    return Settings(**config_data)


def _apply_environment_overrides(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to config data.

    Environment variables follow the pattern:
    - TOURNAMENT_COMPLETENESS_WEIGHT
    - INTEGRATION_ADD_EVOLUTION_METADATA
    - VERIFICATION_CHECK_MARKDOWN_FORMATTING

    Args:
        config_data: Base configuration dictionary

    Returns:
        Updated configuration dictionary with environment overrides
    """
    # Tournament settings
    if "tournament" not in config_data:
        config_data["tournament"] = {}

    tournament_vars = {
        "TOURNAMENT_COMPLETENESS_WEIGHT": "completeness_weight",
        "TOURNAMENT_RECENCY_WEIGHT": "recency_weight",
        "TOURNAMENT_STRUCTURE_WEIGHT": "structure_weight",
        "TOURNAMENT_CITATIONS_WEIGHT": "citations_weight",
        "TOURNAMENT_ARGUMENTS_WEIGHT": "arguments_weight",
    }

    for env_var, setting_key in tournament_vars.items():
        value = os.getenv(env_var)
        if value is not None:
            config_data["tournament"][setting_key] = float(value)

    # Integration settings
    if "integration" not in config_data:
        config_data["integration"] = {}

    integration_vars = {
        "INTEGRATION_ADD_EVOLUTION_METADATA": "add_evolution_metadata",
        "INTEGRATION_PRESERVE_SOURCE_ATTRIBUTION": "preserve_source_attribution",
        "INTEGRATION_INTEGRATE_CITATIONS": "integrate_citations",
        "INTEGRATION_SKIP_CITATION_ENHANCEMENT": "skip_citation_enhancement",
    }

    for env_var, setting_key in integration_vars.items():
        value = os.getenv(env_var)
        if value is not None:
            config_data["integration"][setting_key] = value.lower() == "true"

    # Verification settings
    if "verification" not in config_data:
        config_data["verification"] = {}

    verification_vars = {
        "VERIFICATION_CHECK_MARKDOWN_FORMATTING": "check_markdown_formatting",
        "VERIFICATION_CHECK_SECTION_NUMBERING": "check_section_numbering",
        "VERIFICATION_CHECK_NO_DUPLICATION": "check_no_duplication",
        "VERIFICATION_CHECK_DOCUMENT_NAVIGABILITY": "check_document_navigability",
        "VERIFICATION_MAX_CONSECUTIVE_BLANK_LINES": "max_consecutive_blank_lines",
    }

    for env_var, setting_key in verification_vars.items():
        value = os.getenv(env_var)
        if value is not None:
            if setting_key == "max_consecutive_blank_lines":
                config_data["verification"][setting_key] = int(value)
            else:
                config_data["verification"][setting_key] = value.lower() == "true"

    # Top-level settings
    if os.getenv("INPUT_DIRECTORY"):
        config_data["input_directory"] = os.getenv("INPUT_DIRECTORY")

    if os.getenv("LOG_LEVEL"):
        config_data["log_level"] = os.getenv("LOG_LEVEL")

    return config_data


# Global settings instance (lazy-loaded)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance.

    Lazy-loads settings on first access. To reload settings,
    call reset_settings() first.

    Returns:
        Global Settings instance
    """
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def reset_settings() -> None:
    """Reset global settings instance.

    Forces reload on next get_settings() call.
    Useful for testing or runtime configuration changes.
    """
    global _settings
    _settings = None


# Convenience alias for backward compatibility
settings = get_settings()
