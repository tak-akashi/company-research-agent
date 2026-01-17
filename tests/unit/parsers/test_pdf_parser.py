"""Tests for PDF parser."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from company_research_agent.core.exceptions import (
    LLMProviderError,
    PDFParseError,
    YomitokuError,
)
from company_research_agent.parsers.pdf_parser import (
    ParsedPDFContent,
    PDFInfo,
    PDFParser,
)


class TestPDFParserGetInfo:
    """Tests for PDFParser.get_info method."""

    def test_get_info_success(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """get_info should return PDFInfo with correct metadata."""
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_pdfplumber_pdf

            parser = PDFParser()
            info = parser.get_info(mock_pdf_path)

        assert isinstance(info, PDFInfo)
        assert info.file_name == "test.pdf"
        assert info.total_pages == 3
        assert info.page_size is not None
        assert info.page_size["width"] == 612.0
        assert info.page_size["height"] == 792.0
        assert info.metadata["Author"] == "Test Author"
        assert info.metadata["Title"] == "Test Document"
        # TOC items should be extracted from first page
        assert len(info.table_of_contents) > 0

    def test_get_info_file_not_found(self, tmp_path: Path) -> None:
        """get_info should raise FileNotFoundError for non-existent file."""
        non_existent_path = tmp_path / "non_existent.pdf"

        parser = PDFParser()
        with pytest.raises(FileNotFoundError) as exc_info:
            parser.get_info(non_existent_path)

        assert "PDF not found" in str(exc_info.value)

    def test_get_info_empty_metadata(
        self,
        mock_pdf_path: Path,
    ) -> None:
        """get_info should handle PDF with no metadata."""
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.width = 612.0
        mock_page.height = 792.0
        mock_page.extract_text.return_value = "Simple content"
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = None

        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_pdf

            parser = PDFParser()
            info = parser.get_info(mock_pdf_path)

        assert info.metadata == {}


class TestPDFParserExtractText:
    """Tests for PDFParser.extract_text method."""

    def test_extract_text_success(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """extract_text should return text from all pages."""
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_pdfplumber_pdf

            parser = PDFParser()
            text = parser.extract_text(mock_pdf_path)

        assert "--- Page 1 ---" in text
        assert "--- Page 2 ---" in text
        assert "--- Page 3 ---" in text
        assert "Page 1 content" in text
        assert "Page 2 content" in text
        assert "Page 3 content" in text

    def test_extract_text_with_page_range(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """extract_text should respect start_page and end_page parameters."""
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_pdfplumber_pdf

            parser = PDFParser()
            text = parser.extract_text(mock_pdf_path, start_page=2, end_page=2)

        assert "--- Page 2 ---" in text
        assert "--- Page 1 ---" not in text
        assert "--- Page 3 ---" not in text

    def test_extract_text_file_not_found(self, tmp_path: Path) -> None:
        """extract_text should raise FileNotFoundError for non-existent file."""
        non_existent_path = tmp_path / "non_existent.pdf"

        parser = PDFParser()
        with pytest.raises(FileNotFoundError) as exc_info:
            parser.extract_text(non_existent_path)

        assert "PDF not found" in str(exc_info.value)

    def test_extract_text_invalid_start_page(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """extract_text should raise ValueError for invalid start_page."""
        with patch("pdfplumber.open"):
            parser = PDFParser()
            with pytest.raises(ValueError) as exc_info:
                parser.extract_text(mock_pdf_path, start_page=0)

        assert "start_page must be >= 1" in str(exc_info.value)

    def test_extract_text_start_page_exceeds_total(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """extract_text should raise ValueError when start_page exceeds total pages."""
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_pdfplumber_pdf

            parser = PDFParser()
            with pytest.raises(ValueError) as exc_info:
                parser.extract_text(mock_pdf_path, start_page=10)

        assert "exceeds total pages" in str(exc_info.value)

    def test_extract_text_invalid_page_range(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """extract_text should raise ValueError when end_page < start_page."""
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_pdfplumber_pdf

            parser = PDFParser()
            with pytest.raises(ValueError) as exc_info:
                parser.extract_text(mock_pdf_path, start_page=3, end_page=1)

        assert "must be >= start_page" in str(exc_info.value)


class TestPDFParserToMarkdown:
    """Tests for PDFParser.to_markdown method."""

    def test_to_markdown_auto_strategy(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """to_markdown with auto strategy should use pymupdf4llm first."""
        with (
            patch("pdfplumber.open") as mock_pdfplumber,
            patch("pymupdf4llm.to_markdown") as mock_pymupdf,
        ):
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdfplumber_pdf
            # Return enough content to pass the 100 char threshold
            mock_pymupdf.return_value = "# Markdown Content\n\n" + "Some text. " * 20

            parser = PDFParser()
            result = parser.to_markdown(mock_pdf_path, strategy="auto")

        assert isinstance(result, ParsedPDFContent)
        assert result.strategy_used == "pymupdf4llm"
        assert "# Markdown Content" in result.text
        mock_pymupdf.assert_called_once()

    def test_to_markdown_pdfplumber_strategy(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """to_markdown with pdfplumber strategy should use pdfplumber."""
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_pdfplumber_pdf

            parser = PDFParser()
            result = parser.to_markdown(mock_pdf_path, strategy="pdfplumber")

        assert isinstance(result, ParsedPDFContent)
        assert result.strategy_used == "pdfplumber"
        assert result.pages == 3
        assert "## Page 1" in result.text
        assert "Page 1 content" in result.text

    def test_to_markdown_pymupdf4llm_strategy(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """to_markdown with pymupdf4llm strategy should use pymupdf4llm."""
        with (
            patch("pdfplumber.open") as mock_pdfplumber,
            patch("pymupdf4llm.to_markdown") as mock_pymupdf,
        ):
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdfplumber_pdf
            mock_pymupdf.return_value = "# Document\n\n## Section 1\n\nContent here."

            parser = PDFParser()
            result = parser.to_markdown(mock_pdf_path, strategy="pymupdf4llm")

        assert isinstance(result, ParsedPDFContent)
        assert result.strategy_used == "pymupdf4llm"
        assert "# Document" in result.text
        mock_pymupdf.assert_called_once()

    def test_to_markdown_with_page_range(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """to_markdown should respect page range parameters."""
        with (
            patch("pdfplumber.open") as mock_pdfplumber,
            patch("pymupdf4llm.to_markdown") as mock_pymupdf,
        ):
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdfplumber_pdf
            mock_pymupdf.return_value = "Page 2 markdown content"

            parser = PDFParser()
            result = parser.to_markdown(
                mock_pdf_path, start_page=2, end_page=2, strategy="pymupdf4llm"
            )

        assert result.pages == 1
        # Check that pages parameter was passed to pymupdf4llm
        call_args = mock_pymupdf.call_args
        assert call_args[1]["pages"] == [1]  # 0-based index for page 2

    def test_to_markdown_file_not_found(self, tmp_path: Path) -> None:
        """to_markdown should raise FileNotFoundError for non-existent file."""
        non_existent_path = tmp_path / "non_existent.pdf"

        parser = PDFParser()
        with pytest.raises(FileNotFoundError) as exc_info:
            parser.to_markdown(non_existent_path)

        assert "PDF not found" in str(exc_info.value)

    def test_to_markdown_parse_error(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """to_markdown should raise PDFParseError on parsing failure."""
        with (
            patch("pdfplumber.open") as mock_pdfplumber,
            patch("pymupdf4llm.to_markdown") as mock_pymupdf,
        ):
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdfplumber_pdf
            mock_pymupdf.side_effect = RuntimeError("PDF is corrupted")

            parser = PDFParser()
            with pytest.raises(PDFParseError) as exc_info:
                parser.to_markdown(mock_pdf_path, strategy="pymupdf4llm")

        assert "PDF is corrupted" in str(exc_info.value)
        assert exc_info.value.strategy == "pymupdf4llm"


class TestPDFParserYomitokuStrategy:
    """Tests for PDFParser yomitoku strategy."""

    def test_to_markdown_yomitoku_not_installed(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """to_markdown with yomitoku should raise YomitokuError if not installed."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "yomitoku" or name.startswith("yomitoku."):
                raise ModuleNotFoundError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)  # type: ignore[arg-type]

        with (
            patch("pdfplumber.open") as mock_pdfplumber,
            patch.object(builtins, "__import__", side_effect=mock_import),
        ):
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdfplumber_pdf

            parser = PDFParser()
            with pytest.raises(YomitokuError) as exc_info:
                parser.to_markdown(mock_pdf_path, strategy="yomitoku")

        assert "not installed" in str(exc_info.value)


class TestPDFParserGeminiStrategy:
    """Tests for PDFParser gemini strategy."""

    def test_to_markdown_gemini_no_config(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """to_markdown with gemini should raise PDFParseError if no config."""
        with patch("pdfplumber.open") as mock_pdfplumber:
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdfplumber_pdf

            parser = PDFParser()  # No vision_provider
            with pytest.raises(PDFParseError) as exc_info:
                parser.to_markdown(mock_pdf_path, strategy="gemini")

        # Should fail due to missing API key
        assert "GOOGLE_API_KEY" in str(exc_info.value) or "API key" in str(exc_info.value)

    def test_to_markdown_gemini_success(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """to_markdown with gemini should work with proper config."""
        mock_provider = MagicMock()
        mock_provider.provider_name = "google"
        mock_provider.model_name = "gemini-2.5-flash"

        mock_client_instance = MagicMock()
        mock_client_instance.extract_pdf_to_markdown.return_value = "## Page 1\n\nGemini extracted."

        with patch("pdfplumber.open") as mock_pdfplumber:
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdfplumber_pdf

            parser = PDFParser(vision_provider=mock_provider)
            # Directly inject the mock client
            parser._vision_client = mock_client_instance
            result = parser.to_markdown(mock_pdf_path, strategy="gemini")

        assert isinstance(result, ParsedPDFContent)
        assert result.strategy_used == "gemini"
        assert "Gemini extracted" in result.text

    def test_to_markdown_gemini_api_error(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """to_markdown with gemini should raise LLMProviderError on API failure."""
        mock_provider = MagicMock()
        mock_provider.provider_name = "google"
        mock_provider.model_name = "gemini-2.5-flash"

        mock_client_instance = MagicMock()
        mock_client_instance.extract_pdf_to_markdown.side_effect = LLMProviderError(
            message="Rate limit exceeded",
            provider="google",
            model="gemini-2.5-flash",
        )

        with patch("pdfplumber.open") as mock_pdfplumber:
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdfplumber_pdf

            parser = PDFParser(vision_provider=mock_provider)
            # Directly inject the mock client
            parser._vision_client = mock_client_instance
            with pytest.raises(LLMProviderError) as exc_info:
                parser.to_markdown(mock_pdf_path, strategy="gemini")

        assert "Rate limit exceeded" in str(exc_info.value)


class TestPDFParserAutoFallback:
    """Tests for PDFParser auto fallback strategy."""

    def test_auto_fallback_pymupdf_succeeds(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """auto strategy should use pymupdf4llm if it succeeds."""
        with (
            patch("pdfplumber.open") as mock_pdfplumber,
            patch("pymupdf4llm.to_markdown") as mock_pymupdf,
        ):
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdfplumber_pdf
            mock_pymupdf.return_value = "# Good content\n\n" + "Text content " * 20

            parser = PDFParser()
            result = parser.to_markdown(mock_pdf_path, strategy="auto")

        assert result.strategy_used == "pymupdf4llm"

    def test_auto_fallback_all_fail(
        self,
        mock_pdf_path: Path,
        mock_pdfplumber_pdf: MagicMock,
    ) -> None:
        """auto strategy should raise PDFParseError if all strategies fail."""
        with (
            patch("pdfplumber.open") as mock_pdfplumber,
            patch("pymupdf4llm.to_markdown") as mock_pymupdf,
        ):
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdfplumber_pdf
            # Return insufficient content
            mock_pymupdf.return_value = "Short"

            parser = PDFParser()  # No gemini config
            with pytest.raises(PDFParseError) as exc_info:
                parser.to_markdown(mock_pdf_path, strategy="auto")

        assert "All strategies failed" in str(exc_info.value)
        assert exc_info.value.strategy == "auto"


class TestPDFParserTocExtraction:
    """Tests for TOC extraction logic."""

    def test_extract_toc_with_numbered_items(
        self,
        mock_pdf_path: Path,
    ) -> None:
        """TOC extraction should find numbered items."""
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.width = 612.0
        mock_page.height = 792.0
        mock_page.extract_text.return_value = (
            "Table of Contents\n1. Introduction\n2. Background\n3. Methods\n"
        )
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {}

        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_pdf

            parser = PDFParser()
            info = parser.get_info(mock_pdf_path)

        assert "1. Introduction" in info.table_of_contents
        assert "2. Background" in info.table_of_contents
        assert "3. Methods" in info.table_of_contents

    def test_extract_toc_with_dot_leaders(
        self,
        mock_pdf_path: Path,
    ) -> None:
        """TOC extraction should find items with dot leaders."""
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.width = 612.0
        mock_page.height = 792.0
        mock_page.extract_text.return_value = (
            "Table of Contents\nIntroduction ..... 1\nBackground ..... 5\nConclusion ..... 10\n"
        )
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {}

        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_pdf

            parser = PDFParser()
            info = parser.get_info(mock_pdf_path)

        assert "Introduction ..... 1" in info.table_of_contents
        assert "Background ..... 5" in info.table_of_contents


class TestPDFParserTableExtraction:
    """Tests for table extraction functionality.

    Note: pdfplumber strategy extracts raw text only.
    pymupdf4llm strategy preserves markdown table format.
    """

    def test_pdfplumber_extracts_text_content(
        self,
        mock_pdf_path: Path,
    ) -> None:
        """pdfplumber strategy should extract text content from pages."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        # Text that would appear in a PDF with table data (as plain text)
        mock_page.extract_text.return_value = "項目 金額\n売上高 1,234,567\n営業利益 123,456"
        mock_doc.pages = [mock_page]
        mock_doc.metadata = {}
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=None)

        with patch("pdfplumber.open", return_value=mock_doc):
            parser = PDFParser()
            result = parser.to_markdown(mock_pdf_path, strategy="pdfplumber")

        # Verify text content is extracted
        assert "項目" in result.text
        assert "売上高" in result.text
        assert "1,234,567" in result.text

    def test_pdfplumber_extracts_financial_text_structure(
        self,
        mock_pdf_path: Path,
    ) -> None:
        """pdfplumber strategy should extract financial data as text."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        # Financial data as it might appear in extracted text
        mock_page.extract_text.return_value = """財務諸表
勘定科目 前期 当期 増減
売上高 10,000,000 12,000,000 2,000,000
売上原価 7,000,000 8,000,000 1,000,000
営業利益 1,000,000 1,500,000 500,000"""
        mock_doc.pages = [mock_page]
        mock_doc.metadata = {}
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=None)

        with patch("pdfplumber.open", return_value=mock_doc):
            parser = PDFParser()
            result = parser.to_markdown(mock_pdf_path, strategy="pdfplumber")

        # Verify financial data is extracted
        text = result.text
        assert "勘定科目" in text
        assert "前期" in text
        assert "売上高" in text
        assert "営業利益" in text

    def test_pdfplumber_handles_empty_page_text(
        self,
        mock_pdf_path: Path,
    ) -> None:
        """pdfplumber strategy should handle pages with empty or minimal text."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_doc.pages = [mock_page]
        mock_doc.metadata = {}
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=None)

        with patch("pdfplumber.open", return_value=mock_doc):
            parser = PDFParser()
            # Should not raise an error
            result = parser.to_markdown(mock_pdf_path, strategy="pdfplumber")

        assert result is not None
        assert result.pages == 1

    def test_pdfplumber_handles_plain_text(
        self,
        mock_pdf_path: Path,
    ) -> None:
        """pdfplumber strategy should handle pages with plain text."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "This is plain text without any tables."
        mock_doc.pages = [mock_page]
        mock_doc.metadata = {}
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=None)

        with patch("pdfplumber.open", return_value=mock_doc):
            parser = PDFParser()
            result = parser.to_markdown(mock_pdf_path, strategy="pdfplumber")

        assert result.text, "Should return non-empty result"
        assert "plain text" in result.text

    def test_pdfplumber_handles_multi_page(
        self,
        mock_pdf_path: Path,
    ) -> None:
        """pdfplumber strategy should extract text from multiple pages."""
        mock_doc = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content: 売上高 1,000"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content: 営業利益 500"
        mock_doc.pages = [mock_page1, mock_page2]
        mock_doc.metadata = {}
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=None)

        with patch("pdfplumber.open", return_value=mock_doc):
            parser = PDFParser()
            result = parser.to_markdown(mock_pdf_path, strategy="pdfplumber")

        # Should contain text from both pages
        text = result.text
        assert "売上高" in text
        assert "営業利益" in text
        assert result.pages == 2

    def test_pymupdf4llm_preserves_table_markdown(
        self,
        mock_pdf_path: Path,
    ) -> None:
        """pymupdf4llm strategy should preserve markdown table format."""
        mock_doc = MagicMock()
        mock_doc.pages = [MagicMock()]
        mock_doc.metadata = {}
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=None)

        # pymupdf4llm returns markdown with tables
        markdown_with_table = """# 財務諸表

| 項目 | 前期 | 当期 |
|------|------|------|
| 売上高 | 10,000 | 12,000 |
| 営業利益 | 1,000 | 1,500 |

注記事項については...
"""
        with (
            patch("pdfplumber.open", return_value=mock_doc),
            patch("pymupdf4llm.to_markdown", return_value=markdown_with_table),
        ):
            parser = PDFParser()
            result = parser.to_markdown(mock_pdf_path, strategy="pymupdf4llm")

        # Verify table structure is preserved
        text = result.text
        assert "| 項目 |" in text
        assert "|------|" in text
        assert "| 売上高 |" in text

    def test_pymupdf4llm_extracts_complex_table(
        self,
        mock_pdf_path: Path,
    ) -> None:
        """pymupdf4llm strategy should extract complex multi-column tables."""
        mock_doc = MagicMock()
        mock_doc.pages = [MagicMock()]
        mock_doc.metadata = {}
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=None)

        # Complex financial table with multiple columns
        markdown_with_table = """# 連結損益計算書

| 勘定科目 | 前連結会計年度 | 当連結会計年度 | 増減 | 増減率 |
|----------|----------------|----------------|------|--------|
| 売上高 | 10,000,000 | 12,000,000 | 2,000,000 | 20.0% |
| 売上原価 | 7,000,000 | 8,000,000 | 1,000,000 | 14.3% |
| 売上総利益 | 3,000,000 | 4,000,000 | 1,000,000 | 33.3% |
| 営業利益 | 1,000,000 | 1,500,000 | 500,000 | 50.0% |
| 経常利益 | 900,000 | 1,400,000 | 500,000 | 55.6% |
"""
        with (
            patch("pdfplumber.open", return_value=mock_doc),
            patch("pymupdf4llm.to_markdown", return_value=markdown_with_table),
        ):
            parser = PDFParser()
            result = parser.to_markdown(mock_pdf_path, strategy="pymupdf4llm")

        # Verify complex table structure
        text = result.text
        assert "| 勘定科目 |" in text
        assert "前連結会計年度" in text
        assert "| 売上高 |" in text
        assert "20.0%" in text

    def test_pymupdf4llm_handles_negative_numbers_in_table(
        self,
        mock_pdf_path: Path,
    ) -> None:
        """pymupdf4llm should preserve Japanese negative number indicators in tables."""
        mock_doc = MagicMock()
        mock_doc.pages = [MagicMock()]
        mock_doc.metadata = {}
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=None)

        # Table with Japanese negative indicators
        markdown_with_table = """# キャッシュ・フロー計算書

| 項目 | 金額（百万円） |
|------|----------------|
| 営業活動CF | 1,234 |
| 投資活動CF | △567 |
| 財務活動CF | ▲890 |
"""
        with (
            patch("pdfplumber.open", return_value=mock_doc),
            patch("pymupdf4llm.to_markdown", return_value=markdown_with_table),
        ):
            parser = PDFParser()
            result = parser.to_markdown(mock_pdf_path, strategy="pymupdf4llm")

        # Verify negative indicators are preserved
        text = result.text
        assert "△567" in text or "△" in text
        assert "▲890" in text or "▲" in text

    def test_pdfplumber_extracts_japanese_numbers_in_text(
        self,
        mock_pdf_path: Path,
    ) -> None:
        """pdfplumber should extract Japanese number formats in text."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = """財務データ
科目 金額
売上高 １２，３４５百万円
営業利益 △1,234百万円
経常利益 ▲567百万円"""
        mock_doc.pages = [mock_page]
        mock_doc.metadata = {}
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=None)

        with patch("pdfplumber.open", return_value=mock_doc):
            parser = PDFParser()
            result = parser.to_markdown(mock_pdf_path, strategy="pdfplumber")

        # Verify Japanese number formats are preserved in text
        text = result.text
        assert "１２，３４５" in text
        assert "△1,234" in text
        assert "▲567" in text
