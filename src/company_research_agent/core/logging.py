"""Logging configuration for Company Research Agent."""

from __future__ import annotations

import logging
import sys
from typing import Literal


def _is_jupyter() -> bool:
    """Detect if running in a Jupyter notebook environment.

    Returns:
        True if running in Jupyter (ZMQInteractiveShell), False otherwise.
    """
    try:
        from IPython import get_ipython  # type: ignore[attr-defined]

        shell = get_ipython()  # type: ignore[no-untyped-call]
        if shell is None:
            return False
        # ZMQInteractiveShell is used in Jupyter notebooks
        return bool(shell.__class__.__name__ == "ZMQInteractiveShell")
    except ImportError:
        return False


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

    # Use stderr for Jupyter to avoid interference with Rich console output
    # Rich console outputs to stdout, so logging to stderr prevents interleaving
    stream = sys.stderr if _is_jupyter() else sys.stdout

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level),
        format=format_str,
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(stream),
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
