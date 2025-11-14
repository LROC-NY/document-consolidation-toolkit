"""Logging configuration for document consolidation toolkit.

Production-ready logging with:
- Colored console output
- Rotating file handlers
- Structured logging support
- Configurable log levels
- Suppression of noisy third-party loggers
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

# ANSI color codes for terminal output
COLORS = {
    "DEBUG": "\033[36m",  # Cyan
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",  # Reset
}


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for console."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors based on level.

        Args:
            record: Log record to format

        Returns:
            Formatted log string with ANSI color codes
        """
        # Add color to levelname
        levelname = record.levelname
        if levelname in COLORS:
            record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"

        # Format the message
        formatted = super().format(record)

        # Reset levelname for other handlers
        record.levelname = levelname

        return formatted


def setup_logging(
    log_dir: Optional[Path] = None,
    log_level: str = "INFO",
    console_output: bool = True,
    file_output: bool = True,
) -> None:
    """Setup logging configuration for the application.

    Creates console and file handlers with appropriate formatting.
    Configures log rotation for file handlers.

    Args:
        log_dir: Directory for log files. Created if doesn't exist.
                If None, uses "logs" in current directory.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Enable console logging
        file_output: Enable file logging

    Raises:
        ValueError: If log_level is invalid
        OSError: If log directory cannot be created

    Example:
        >>> from pathlib import Path
        >>> setup_logging(Path("output/logs"), log_level="DEBUG")
    """
    # Validate log level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler with colored output
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        console_format = ColoredFormatter(
            fmt="%(levelname)s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        console_handler.setFormatter(console_format)
        root_logger.addHandler(console_handler)

    # File handler with detailed output
    if file_output:
        # Create log directory
        if log_dir is None:
            log_dir = Path("logs")

        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Main log file with all messages
        main_log_file = log_dir / "consolidation.log"
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)

        file_format = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)

        # Error log file with errors only
        error_log_file = log_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)
        root_logger.addHandler(error_handler)

    # Suppress noisy third-party loggers
    _suppress_noisy_loggers()

    # Log initialization message
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging initialized: level={log_level}, "
        f"console={console_output}, file={file_output}"
    )
    if file_output and log_dir:
        logger.info(f"Log directory: {log_dir.absolute()}")


def _suppress_noisy_loggers() -> None:
    """Suppress overly verbose third-party loggers.

    Sets higher log levels for common noisy libraries to reduce
    log clutter while preserving application logs.
    """
    noisy_loggers = [
        "urllib3",
        "requests",
        "httpx",
        "httpcore",
        "asyncio",
        "chardet",
        "charset_normalizer",
    ]

    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing document")
    """
    return logging.getLogger(name)
