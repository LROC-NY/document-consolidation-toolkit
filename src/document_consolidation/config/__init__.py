"""Configuration system for document consolidation toolkit.

Provides:
- Settings management with YAML support
- Logging configuration
- Environment variable overrides
- Global settings access

Example:
    >>> from document_consolidation.config import settings, get_logger, setup_logging
    >>>
    >>> # Setup logging
    >>> setup_logging(settings.log_dir, settings.log_level)
    >>>
    >>> # Get logger for module
    >>> logger = get_logger(__name__)
    >>> logger.info("Starting consolidation")
    >>>
    >>> # Access settings
    >>> print(settings.tournament.completeness_weight)
"""

from document_consolidation.config.logging_config import get_logger, setup_logging
from document_consolidation.config.settings import (
    IntegrationSettings,
    Settings,
    TournamentSettings,
    VerificationSettings,
    get_settings,
    load_settings,
    reset_settings,
    settings,
)

__all__ = [
    # Settings classes
    "Settings",
    "TournamentSettings",
    "IntegrationSettings",
    "VerificationSettings",
    # Settings functions
    "load_settings",
    "get_settings",
    "reset_settings",
    "settings",
    # Logging functions
    "setup_logging",
    "get_logger",
]
