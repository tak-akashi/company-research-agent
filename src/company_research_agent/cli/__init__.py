"""CLI module for Company Research Agent."""

# Suppress pymupdf recommendation messages before any pymupdf4llm import
import logging
import os

logging.getLogger("pymupdf").setLevel(logging.ERROR)
os.environ.setdefault("PYMUPDF_SUGGEST_LAYOUT_ANALYZER", "0")

from company_research_agent.cli.main import main  # noqa: E402

__all__ = ["main"]
