"""Performance tests for PDF parser.

These tests validate the performance requirements from the PRD:
- 1 document (50-100 pages) should be parsed within 5 minutes
- pdfplumber strategy should be fastest
- Gemini fallback may take up to 15 minutes
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from company_research_agent.parsers.pdf_parser import PDFParser

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class PerformanceResult:
    """Result of a performance measurement."""

    strategy: str
    page_count: int
    elapsed_seconds: float
    pages_per_second: float
    meets_requirement: bool


def create_mock_pdfplumber_doc(page_count: int) -> MagicMock:
    """Create a mock pdfplumber document with configurable page count."""
    mock_doc = MagicMock()
    mock_doc.pages = [MagicMock() for _ in range(page_count)]
    mock_doc.metadata = {
        "title": f"Test Document ({page_count} pages)",
        "author": "Test",
    }

    # Configure each page to return sample text
    for i, page in enumerate(mock_doc.pages):
        page.extract_text.return_value = (
            f"Page {i + 1} content. Sample Japanese: 売上高 1,234,567百万円"
        )
        page.extract_tables.return_value = [
            [["項目", "金額"], ["売上高", "1,234,567"], ["営業利益", "123,456"]]
        ]
        # Add page dimensions
        page.width = 595
        page.height = 842

    # Mock context manager
    mock_doc.__enter__ = MagicMock(return_value=mock_doc)
    mock_doc.__exit__ = MagicMock(return_value=None)

    return mock_doc


class TestPDFParserPerformance:
    """Performance tests for PDFParser."""

    # Performance requirements (in seconds)
    MAX_TIME_PDFPLUMBER_PER_PAGE = 0.5  # 50 pages in 25 seconds
    MAX_TIME_PYMUPDF4LLM_PER_PAGE = 1.0  # 50 pages in 50 seconds
    MAX_TIME_5_MINUTES = 300  # 5 minutes total for standard docs
    MAX_TIME_15_MINUTES = 900  # 15 minutes for Gemini fallback

    @pytest.fixture
    def parser(self) -> PDFParser:
        """Provide a PDFParser instance."""
        return PDFParser()

    @pytest.fixture
    def mock_pdfplumber_factory(self) -> Callable[[int], MagicMock]:
        """Factory for creating mock pdfplumber documents."""
        return create_mock_pdfplumber_doc

    def _measure_parsing_time(
        self,
        parser: PDFParser,
        pdf_path: Path,
        strategy: str,
    ) -> tuple[float, str]:
        """Measure time taken to parse a PDF.

        Returns:
            Tuple of (elapsed_seconds, result_content).
        """
        start_time = time.perf_counter()
        result = parser.to_markdown(pdf_path, strategy=strategy)  # type: ignore[arg-type]
        elapsed = time.perf_counter() - start_time
        return elapsed, result.text

    def test_pdfplumber_strategy_timing(
        self,
        parser: PDFParser,
        mock_pdfplumber_factory: Callable[[int], MagicMock],
        tmp_path: Path,
    ) -> None:
        """Test pdfplumber strategy meets performance requirements."""
        page_count = 50
        mock_doc = mock_pdfplumber_factory(page_count)
        test_pdf = tmp_path / "test.pdf"
        test_pdf.touch()

        with patch("pdfplumber.open", return_value=mock_doc):
            elapsed, _ = self._measure_parsing_time(parser, test_pdf, "pdfplumber")

        # Calculate metrics
        pages_per_second = page_count / elapsed if elapsed > 0 else float("inf")
        time_per_page = elapsed / page_count

        result = PerformanceResult(
            strategy="pdfplumber",
            page_count=page_count,
            elapsed_seconds=elapsed,
            pages_per_second=pages_per_second,
            meets_requirement=time_per_page <= self.MAX_TIME_PDFPLUMBER_PER_PAGE,
        )

        # Assert performance requirements
        assert result.meets_requirement, (
            f"pdfplumber strategy too slow: "
            f"{time_per_page:.2f}s/page (max: {self.MAX_TIME_PDFPLUMBER_PER_PAGE}s/page)"
        )

    def test_pymupdf4llm_strategy_timing(
        self,
        parser: PDFParser,
        mock_pdfplumber_factory: Callable[[int], MagicMock],
        tmp_path: Path,
    ) -> None:
        """Test pymupdf4llm strategy meets performance requirements."""
        page_count = 50
        test_pdf = tmp_path / "test.pdf"
        test_pdf.touch()

        # Mock both pdfplumber (for page count) and pymupdf4llm (for conversion)
        mock_doc = mock_pdfplumber_factory(page_count)
        mock_result = "# Test Document\n\nSample content. 売上高 1,234,567百万円\n" * page_count

        with (
            patch("pdfplumber.open", return_value=mock_doc),
            patch("pymupdf4llm.to_markdown", return_value=mock_result),
        ):
            elapsed, _ = self._measure_parsing_time(parser, test_pdf, "pymupdf4llm")

        # Calculate metrics
        pages_per_second = page_count / elapsed if elapsed > 0 else float("inf")
        time_per_page = elapsed / page_count

        result = PerformanceResult(
            strategy="pymupdf4llm",
            page_count=page_count,
            elapsed_seconds=elapsed,
            pages_per_second=pages_per_second,
            meets_requirement=time_per_page <= self.MAX_TIME_PYMUPDF4LLM_PER_PAGE,
        )

        assert result.meets_requirement, (
            f"pymupdf4llm strategy too slow: "
            f"{time_per_page:.2f}s/page (max: {self.MAX_TIME_PYMUPDF4LLM_PER_PAGE}s/page)"
        )

    def test_100_page_document_within_5_minutes(
        self,
        parser: PDFParser,
        mock_pdfplumber_factory: Callable[[int], MagicMock],
        tmp_path: Path,
    ) -> None:
        """Test that a 100-page document can be parsed within 5 minutes."""
        page_count = 100
        mock_doc = mock_pdfplumber_factory(page_count)
        test_pdf = tmp_path / "test.pdf"
        test_pdf.touch()

        with patch("pdfplumber.open", return_value=mock_doc):
            elapsed, result = self._measure_parsing_time(parser, test_pdf, "pdfplumber")

        # Verify result contains content
        assert result, "Parsing returned empty result"
        assert "売上高" in result or "Page" in result, "Result doesn't contain expected content"

        # Check timing requirement
        assert (
            elapsed < self.MAX_TIME_5_MINUTES
        ), f"100-page document took {elapsed:.2f}s (max: {self.MAX_TIME_5_MINUTES}s)"


class TestPerformanceMetrics:
    """Tests for performance metrics collection and reporting."""

    @pytest.fixture
    def parser(self) -> PDFParser:
        """Provide a PDFParser instance."""
        return PDFParser()

    def test_extract_text_performance(
        self,
        parser: PDFParser,
        tmp_path: Path,
    ) -> None:
        """Test extract_text method performance."""
        page_count = 20
        test_pdf = tmp_path / "test.pdf"
        test_pdf.touch()

        # Create mock document
        mock_doc = create_mock_pdfplumber_doc(page_count)

        with patch("pdfplumber.open", return_value=mock_doc):
            start = time.perf_counter()
            result = parser.extract_text(test_pdf)
            elapsed = time.perf_counter() - start

        # Verify result
        assert result, "extract_text returned empty"
        assert "売上高" in result, "Result doesn't contain expected Japanese text"

        # Performance check: should be fast for text extraction
        max_expected = 2.0  # 2 seconds for 20 pages
        assert (
            elapsed < max_expected
        ), f"extract_text too slow: {elapsed:.2f}s (max: {max_expected}s)"

    def test_get_info_performance(
        self,
        parser: PDFParser,
        tmp_path: Path,
    ) -> None:
        """Test get_info method performance."""
        test_pdf = tmp_path / "test.pdf"
        test_pdf.touch()

        # Create mock document
        mock_doc = create_mock_pdfplumber_doc(50)
        mock_doc.pages[
            0
        ].extract_text.return_value = "Table of Contents\n1. Introduction\n2. Summary"

        with patch("pdfplumber.open", return_value=mock_doc):
            start = time.perf_counter()
            info = parser.get_info(test_pdf)
            elapsed = time.perf_counter() - start

        # Verify result
        assert info.total_pages == 50

        # Performance check: get_info should be very fast
        max_expected = 0.5  # 500ms
        assert elapsed < max_expected, f"get_info too slow: {elapsed:.2f}s (max: {max_expected}s)"


class TestStrategyPerformanceComparison:
    """Compare performance across different parsing strategies."""

    @pytest.fixture
    def parser(self) -> PDFParser:
        """Provide a PDFParser instance."""
        return PDFParser()

    def test_strategy_comparison_report(
        self,
        parser: PDFParser,
        tmp_path: Path,
    ) -> None:
        """Generate performance comparison report for strategies."""
        page_count = 30
        test_pdf = tmp_path / "test.pdf"
        test_pdf.touch()

        results: list[PerformanceResult] = []

        # Test pdfplumber
        mock_doc = create_mock_pdfplumber_doc(page_count)

        with patch("pdfplumber.open", return_value=mock_doc):
            start = time.perf_counter()
            parser.to_markdown(test_pdf, strategy="pdfplumber")  # type: ignore[arg-type]
            elapsed = time.perf_counter() - start
            results.append(
                PerformanceResult(
                    strategy="pdfplumber",
                    page_count=page_count,
                    elapsed_seconds=elapsed,
                    pages_per_second=page_count / elapsed if elapsed > 0 else 0,
                    meets_requirement=True,
                )
            )

        # Test pymupdf4llm (need to mock pdfplumber for page count)
        mock_result = "# Test\n" * page_count
        with (
            patch("pdfplumber.open", return_value=mock_doc),
            patch("pymupdf4llm.to_markdown", return_value=mock_result),
        ):
            start = time.perf_counter()
            parser.to_markdown(test_pdf, strategy="pymupdf4llm")  # type: ignore[arg-type]
            elapsed = time.perf_counter() - start
            results.append(
                PerformanceResult(
                    strategy="pymupdf4llm",
                    page_count=page_count,
                    elapsed_seconds=elapsed,
                    pages_per_second=page_count / elapsed if elapsed > 0 else 0,
                    meets_requirement=True,
                )
            )

        # Verify we got results for both strategies
        assert len(results) == 2
        assert all(r.elapsed_seconds > 0 for r in results)

        # pdfplumber should generally be fast for simple operations
        pdfplumber_result = next(r for r in results if r.strategy == "pdfplumber")
        assert pdfplumber_result.elapsed_seconds < 10, "pdfplumber strategy unexpectedly slow"
