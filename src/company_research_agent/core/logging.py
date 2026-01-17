"""Logging configuration for Company Research Agent."""

from __future__ import annotations

import logging
import sys
from typing import Literal


def setup_logging(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO",
    format_style: Literal["simple", "detailed"] = "simple",
) -> None:
    """Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
        format_style: Format style - 'simple' for basic output, 'detailed' for debug.

    Example:
        >>> setup_logging(level="DEBUG", format_style="detailed")
    """
    # Define formats
    simple_format = "%(asctime)s [%(levelname)s] %(message)s"
    detailed_format = "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"

    format_str = simple_format if format_style == "simple" else detailed_format

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level),
        format=format_str,
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,  # Override any existing configuration
    )

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name, typically __name__.

    Returns:
        Configured logger instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    return logging.getLogger(name)
