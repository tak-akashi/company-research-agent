"""Integration tests for PDF parser with real data.

These tests are designed to run with real EDINET PDF documents.
They are marked with 'integration' and 'slow' markers and are skipped by default.

To run integration tests:
    uv run pytest tests/integration -v -m integration

To run with a specific PDF file:
    TEST_PDF_PATH=/path/to/document.pdf uv run pytest tests/integration -v
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from company_research_agent.parsers.accuracy_benchmark import AccuracyBenchmark
from company_research_agent.parsers.pdf_parser import PDFParser

if TYPE_CHECKING:
    pass


# Markers for integration tests
pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
]


@pytest.fixture
def pdf_parser() -> PDFParser:
    """Provide a real PDFParser instance."""
    return PDFParser()


@pytest.fixture
def accuracy_benchmark() -> AccuracyBenchmark:
    """Provide an AccuracyBenchmark instance."""
    return AccuracyBenchmark(tolerance_percent=1.0)


@pytest.fixture
def test_pdf_path() -> Path | None:
    """Get test PDF path from environment variable.

    Set TEST_PDF_PATH environment variable to a real PDF file path.
    """
    pdf_path = os.environ.get("TEST_PDF_PATH")
    if pdf_path:
        return Path(pdf_path)
    return None


class TestPDFParserRealData:
    """Integration tests with real PDF documents.

    These tests are skipped if TEST_PDF_PATH is not set.
    """

    def test_parse_real_pdf_with_pdfplumber(
        self,
        pdf_parser: PDFParser,
        test_pdf_path: Path | None,
    ) -> None:
        """Test parsing real PDF with pdfplumber strategy."""
        if test_pdf_path is None:
            pytest.skip("TEST_PDF_PATH not set")

        if not test_pdf_path.exists():
            pytest.skip(f"PDF file not found: {test_pdf_path}")

        result = pdf_parser.to_markdown(test_pdf_path, strategy="pdfplumber")

        assert result.text, "Should extract text from PDF"
        assert result.pages > 0, "Should process at least one page"
        assert result.strategy_used == "pdfplumber"

    def test_parse_real_pdf_with_pymupdf4llm(
        self,
        pdf_parser: PDFParser,
        test_pdf_path: Path | None,
    ) -> None:
        """Test parsing real PDF with pymupdf4llm strategy."""
        if test_pdf_path is None:
            pytest.skip("TEST_PDF_PATH not set")

        if not test_pdf_path.exists():
            pytest.skip(f"PDF file not found: {test_pdf_path}")

        result = pdf_parser.to_markdown(test_pdf_path, strategy="pymupdf4llm")

        assert result.text, "Should extract text from PDF"
        assert result.pages > 0, "Should process at least one page"
        assert result.strategy_used == "pymupdf4llm"

    def test_get_info_from_real_pdf(
        self,
        pdf_parser: PDFParser,
        test_pdf_path: Path | None,
    ) -> None:
        """Test getting info from real PDF."""
        if test_pdf_path is None:
            pytest.skip("TEST_PDF_PATH not set")

        if not test_pdf_path.exists():
            pytest.skip(f"PDF file not found: {test_pdf_path}")

        info = pdf_parser.get_info(test_pdf_path)

        assert info.total_pages > 0
        assert info.file_name
        assert info.file_path


class TestAccuracyBenchmarkIntegration:
    """Integration tests for accuracy benchmark with real data."""

    def test_benchmark_with_real_extracted_text(
        self,
        accuracy_benchmark: AccuracyBenchmark,
    ) -> None:
        """Test benchmark framework with sample extracted text.

        This test simulates what would happen with real PDF extraction.
        """
        # Sample extracted text that might come from a real PDF
        extracted_text = """
        株式会社テスト

        第1四半期決算短信

        売上高: 1,234,567百万円
        営業利益: 123,456百万円
        経常利益: 120,000百万円
        当期純利益: 80,000百万円
        """

        # Expected values from earnings summary
        expected_items = {
            "売上高": "1,234,567",
            "営業利益": "123,456",
            "経常利益": "120,000",
            "当期純利益": "80,000",
        }

        result = accuracy_benchmark.compare_financial_items(
            expected_items=expected_items,
            extracted_text=extracted_text,
            company_name="株式会社テスト",
            document_id="S100TEST",
            fiscal_year=2024,
        )

        assert result.accuracy == 100.0, "All items should match exactly"
        assert result.matched_count == 4
        assert result.total_count == 4

    def test_benchmark_with_tolerance(
        self,
        accuracy_benchmark: AccuracyBenchmark,
    ) -> None:
        """Test benchmark tolerance for slight variations."""
        extracted_text = """
        売上高: 1,234,580百万円
        営業利益: 123,400百万円
        """

        # Expected values with slight differences (within 1% tolerance)
        expected_items = {
            "売上高": "1,234,567",  # 0.001% difference
            "営業利益": "123,456",  # 0.05% difference
        }

        result = accuracy_benchmark.compare_financial_items(
            expected_items=expected_items,
            extracted_text=extracted_text,
            company_name="株式会社テスト",
            document_id="S100TEST",
            fiscal_year=2024,
        )

        # With 1% tolerance, slight variations should still match
        assert result.accuracy == 100.0
        assert result.matched_count == 2

    def test_benchmark_report_generation(
        self,
        accuracy_benchmark: AccuracyBenchmark,
    ) -> None:
        """Test benchmark report generation."""
        extracted_text = "売上高: 1,000,000\n営業利益: 50,000"
        expected_items = {"売上高": "1,000,000", "営業利益": "50,000"}

        result = accuracy_benchmark.compare_financial_items(
            expected_items=expected_items,
            extracted_text=extracted_text,
            company_name="テスト株式会社",
            document_id="S100ABC1",
            fiscal_year=2024,
        )

        report = accuracy_benchmark.generate_report([result])

        assert "# PDF解析精度測定レポート" in report
        assert "テスト株式会社" in report
        assert "売上高" in report
        assert "営業利益" in report


class TestPDFParserAutoFallback:
    """Integration tests for auto-fallback strategy."""

    def test_auto_strategy_fallback_chain(
        self,
        pdf_parser: PDFParser,
        test_pdf_path: Path | None,
    ) -> None:
        """Test auto strategy fallback chain with real PDF."""
        if test_pdf_path is None:
            pytest.skip("TEST_PDF_PATH not set")

        if not test_pdf_path.exists():
            pytest.skip(f"PDF file not found: {test_pdf_path}")

        result = pdf_parser.to_markdown(test_pdf_path, strategy="auto")

        assert result.text, "Auto strategy should produce output"
        assert result.strategy_used in ["pymupdf4llm", "yomitoku", "gemini"]


class TestAccuracyValidation:
    """Integration tests for Japanese text extraction accuracy validation.

    These tests validate the 95% accuracy requirement from PRD.
    Set TEST_PDF_PATH and EXPECTED_VALUES environment variables to run.

    Environment variables:
        TEST_PDF_PATH: Path to EDINET PDF file
        EXPECTED_SALES: Expected sales value (e.g., "1234567")
        EXPECTED_OPERATING_PROFIT: Expected operating profit
        EXPECTED_ORDINARY_PROFIT: Expected ordinary profit
        EXPECTED_NET_INCOME: Expected net income
        COMPANY_NAME: Company name for reporting
        DOCUMENT_ID: EDINET document ID
        FISCAL_YEAR: Fiscal year (e.g., "2024")
    """

    @pytest.fixture
    def expected_values(self) -> dict[str, str] | None:
        """Get expected values from environment variables."""
        values = {}

        mapping = {
            "EXPECTED_SALES": "売上高",
            "EXPECTED_OPERATING_PROFIT": "営業利益",
            "EXPECTED_ORDINARY_PROFIT": "経常利益",
            "EXPECTED_NET_INCOME": "当期純利益",
            "EXPECTED_TOTAL_ASSETS": "総資産",
            "EXPECTED_NET_ASSETS": "純資産",
        }

        for env_var, item_name in mapping.items():
            value = os.environ.get(env_var)
            if value:
                values[item_name] = value

        return values if values else None

    @pytest.fixture
    def document_info(self) -> dict[str, str | int]:
        """Get document info from environment variables."""
        return {
            "company_name": os.environ.get("COMPANY_NAME", "テスト企業"),
            "document_id": os.environ.get("DOCUMENT_ID", "S100TEST"),
            "fiscal_year": int(os.environ.get("FISCAL_YEAR", "2024")),
        }

    def test_extraction_accuracy_with_real_pdf(
        self,
        pdf_parser: PDFParser,
        accuracy_benchmark: AccuracyBenchmark,
        test_pdf_path: Path | None,
        expected_values: dict[str, str] | None,
        document_info: dict[str, str | int],
    ) -> None:
        """Test extraction accuracy against known values from real PDF.

        This test validates the PRD requirement:
        - 285 items out of 300 (95%) must match within 1% tolerance.
        """
        if test_pdf_path is None:
            pytest.skip("TEST_PDF_PATH not set")

        if not test_pdf_path.exists():
            pytest.skip(f"PDF file not found: {test_pdf_path}")

        if expected_values is None:
            pytest.skip("No EXPECTED_* environment variables set")

        # Extract text from PDF
        result = pdf_parser.to_markdown(test_pdf_path, strategy="auto")
        assert result.text, "Should extract text from PDF"

        # Compare with expected values
        benchmark_result = accuracy_benchmark.compare_financial_items(
            expected_items=expected_values,
            extracted_text=result.text,
            company_name=str(document_info["company_name"]),
            document_id=str(document_info["document_id"]),
            fiscal_year=int(document_info["fiscal_year"]),
        )

        # Generate report for debugging
        report = accuracy_benchmark.generate_report([benchmark_result])
        print("\n" + report)

        # Assert 95% accuracy (PRD requirement)
        assert benchmark_result.accuracy >= 95.0, (
            f"Accuracy {benchmark_result.accuracy:.1f}% is below 95% threshold. "
            f"Matched: {benchmark_result.matched_count}/{benchmark_result.total_count}"
        )

    def test_table_extraction_accuracy(
        self,
        pdf_parser: PDFParser,
        test_pdf_path: Path | None,
    ) -> None:
        """Test that tables are extracted in markdown format."""
        if test_pdf_path is None:
            pytest.skip("TEST_PDF_PATH not set")

        if not test_pdf_path.exists():
            pytest.skip(f"PDF file not found: {test_pdf_path}")

        # Use pymupdf4llm for table extraction
        result = pdf_parser.to_markdown(test_pdf_path, strategy="pymupdf4llm")

        # Check for markdown table indicators
        has_table = "|" in result.text or "---" in result.text

        # Financial PDFs should contain table-like structures
        assert has_table or len(result.text) > 1000, (
            "PDF should contain tables or substantial text content"
        )


class TestGeminiIntegration:
    """Integration tests for Gemini API.

    Set GOOGLE_API_KEY environment variable to run these tests.
    """

    @pytest.fixture
    def gemini_available(self) -> bool:
        """Check if Gemini API is available."""
        return os.environ.get("GOOGLE_API_KEY") is not None

    def test_gemini_strategy_with_real_pdf(
        self,
        pdf_parser: PDFParser,
        test_pdf_path: Path | None,
        gemini_available: bool,
    ) -> None:
        """Test Gemini strategy with real PDF."""
        if not gemini_available:
            pytest.skip("GOOGLE_API_KEY not set")

        if test_pdf_path is None:
            pytest.skip("TEST_PDF_PATH not set")

        if not test_pdf_path.exists():
            pytest.skip(f"PDF file not found: {test_pdf_path}")

        # Test with only first 2 pages to limit API calls
        result = pdf_parser.to_markdown(
            test_pdf_path,
            start_page=1,
            end_page=2,
            strategy="gemini",
        )

        assert result.text, "Gemini should extract text from PDF"
        assert result.strategy_used == "gemini"
        assert len(result.text) > 100, "Should extract substantial text"

    def test_gemini_japanese_accuracy(
        self,
        accuracy_benchmark: AccuracyBenchmark,
        gemini_available: bool,
    ) -> None:
        """Test Gemini's Japanese number handling through benchmark.

        This test verifies the benchmark can handle Gemini's output format.
        """
        if not gemini_available:
            pytest.skip("GOOGLE_API_KEY not set")

        # Simulate Gemini output format
        extracted_text = """
## Page 1

# 連結財務諸表

## 連結損益計算書

| 項目 | 当期 | 前期 |
|------|------|------|
| 売上高 | 10,000,000 | 9,500,000 |
| 営業利益 | 800,000 | 750,000 |
| 経常利益 | 850,000 | 780,000 |
| 当期純利益 | 600,000 | 550,000 |
        """

        expected_items = {
            "売上高": "10,000,000",
            "営業利益": "800,000",
            "経常利益": "850,000",
            "当期純利益": "600,000",
        }

        result = accuracy_benchmark.compare_financial_items(
            expected_items=expected_items,
            extracted_text=extracted_text,
            company_name="テスト企業",
            document_id="S100TEST",
            fiscal_year=2024,
        )

        assert result.accuracy == 100.0, "All items should match exactly"


class TestYomitokuIntegration:
    """Integration tests for YOMITOKU OCR.

    These tests require yomitoku package to be installed.
    """

    @pytest.fixture
    def yomitoku_available(self) -> bool:
        """Check if yomitoku is available."""
        try:
            import yomitoku  # noqa: F401

            return True
        except ImportError:
            return False

    def test_yomitoku_strategy_with_real_pdf(
        self,
        pdf_parser: PDFParser,
        test_pdf_path: Path | None,
        yomitoku_available: bool,
    ) -> None:
        """Test YOMITOKU strategy with real PDF."""
        if not yomitoku_available:
            pytest.skip("yomitoku not installed")

        if test_pdf_path is None:
            pytest.skip("TEST_PDF_PATH not set")

        if not test_pdf_path.exists():
            pytest.skip(f"PDF file not found: {test_pdf_path}")

        # Test with only first page to limit processing time
        result = pdf_parser.to_markdown(
            test_pdf_path,
            start_page=1,
            end_page=1,
            strategy="yomitoku",
        )

        assert result.text, "YOMITOKU should extract text from PDF"
        assert result.strategy_used == "yomitoku"
