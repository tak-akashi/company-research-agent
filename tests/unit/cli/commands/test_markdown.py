"""Unit tests for markdown command implementation."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from company_research_agent.cli.commands.markdown import cmd_markdown

if TYPE_CHECKING:
    pass


class TestCmdMarkdownWithFile:
    """Tests for cmd_markdown with --file option."""

    @pytest.mark.asyncio
    async def test_file_not_found_returns_error(self, tmp_path: Path) -> None:
        """File not found returns exit code 1."""
        args = argparse.Namespace(
            file=str(tmp_path / "nonexistent.pdf"),
            doc_id=None,
            output=None,
            strategy="auto",
            info_only=False,
            start_page=None,
            end_page=None,
        )

        result = await cmd_markdown(args)

        assert result == 1

    @pytest.mark.asyncio
    async def test_file_exists_calls_parser(self, tmp_path: Path) -> None:
        """Existing file calls PDFParser.to_markdown."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        mock_result = MagicMock()
        mock_result.text = "# Test Markdown"
        mock_result.pages = 5
        mock_result.strategy_used = "pymupdf4llm"

        args = argparse.Namespace(
            file=str(pdf_file),
            doc_id=None,
            output=None,
            strategy="auto",
            info_only=False,
            start_page=None,
            end_page=None,
        )

        with patch("company_research_agent.cli.commands.markdown.PDFParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser.to_markdown.return_value = mock_result
            mock_parser_cls.return_value = mock_parser

            result = await cmd_markdown(args)

            assert result == 0
            mock_parser.to_markdown.assert_called_once_with(
                pdf_file,
                start_page=None,
                end_page=None,
                strategy="auto",
            )

    @pytest.mark.asyncio
    async def test_info_only_calls_get_info(self, tmp_path: Path) -> None:
        """--info-only flag calls PDFParser.get_info."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        mock_info = MagicMock()
        mock_info.file_name = "test.pdf"
        mock_info.total_pages = 10
        mock_info.page_size = {"width": 612, "height": 792}
        mock_info.table_of_contents = ["Chapter 1", "Chapter 2"]

        args = argparse.Namespace(
            file=str(pdf_file),
            doc_id=None,
            output=None,
            strategy="auto",
            info_only=True,
            start_page=None,
            end_page=None,
        )

        with patch("company_research_agent.cli.commands.markdown.PDFParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser.get_info.return_value = mock_info
            mock_parser_cls.return_value = mock_parser

            result = await cmd_markdown(args)

            assert result == 0
            mock_parser.get_info.assert_called_once_with(pdf_file)
            mock_parser.to_markdown.assert_not_called()

    @pytest.mark.asyncio
    async def test_output_writes_to_file(self, tmp_path: Path) -> None:
        """--output option writes result to file."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")
        output_file = tmp_path / "output.md"

        mock_result = MagicMock()
        mock_result.text = "# Test Markdown\n\nContent here."
        mock_result.pages = 3
        mock_result.strategy_used = "pymupdf4llm"

        args = argparse.Namespace(
            file=str(pdf_file),
            doc_id=None,
            output=str(output_file),
            strategy="auto",
            info_only=False,
            start_page=None,
            end_page=None,
        )

        with patch("company_research_agent.cli.commands.markdown.PDFParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser.to_markdown.return_value = mock_result
            mock_parser_cls.return_value = mock_parser

            result = await cmd_markdown(args)

            assert result == 0
            assert output_file.exists()
            assert output_file.read_text(encoding="utf-8") == mock_result.text


class TestCmdMarkdownWithDocId:
    """Tests for cmd_markdown with --doc-id option."""

    @pytest.mark.asyncio
    async def test_doc_id_not_found_returns_error(self) -> None:
        """Doc ID not in cache returns exit code 1."""
        args = argparse.Namespace(
            file=None,
            doc_id="S100XXXX",
            output=None,
            strategy="auto",
            info_only=False,
            start_page=None,
            end_page=None,
        )

        with patch(
            "company_research_agent.cli.commands.markdown.LocalCacheService"
        ) as mock_cache_cls:
            mock_cache = MagicMock()
            mock_cache.find_by_doc_id.return_value = None
            mock_cache_cls.return_value = mock_cache

            result = await cmd_markdown(args)

            assert result == 1
            mock_cache.find_by_doc_id.assert_called_once_with("S100XXXX")

    @pytest.mark.asyncio
    async def test_doc_id_found_calls_parser(self, tmp_path: Path) -> None:
        """Doc ID found in cache calls PDFParser.to_markdown."""
        pdf_file = tmp_path / "S100XXXX.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        mock_cache_info = MagicMock()
        mock_cache_info.file_path = pdf_file

        mock_result = MagicMock()
        mock_result.text = "# Cached Document"
        mock_result.pages = 20
        mock_result.strategy_used = "pymupdf4llm"

        args = argparse.Namespace(
            file=None,
            doc_id="S100XXXX",
            output=None,
            strategy="auto",
            info_only=False,
            start_page=None,
            end_page=None,
        )

        with (
            patch(
                "company_research_agent.cli.commands.markdown.LocalCacheService"
            ) as mock_cache_cls,
            patch("company_research_agent.cli.commands.markdown.PDFParser") as mock_parser_cls,
        ):
            mock_cache = MagicMock()
            mock_cache.find_by_doc_id.return_value = mock_cache_info
            mock_cache_cls.return_value = mock_cache

            mock_parser = MagicMock()
            mock_parser.to_markdown.return_value = mock_result
            mock_parser_cls.return_value = mock_parser

            result = await cmd_markdown(args)

            assert result == 0
            mock_cache.find_by_doc_id.assert_called_once_with("S100XXXX")
            mock_parser.to_markdown.assert_called_once()


class TestCmdMarkdownNoArgs:
    """Tests for cmd_markdown without required arguments."""

    @pytest.mark.asyncio
    async def test_no_file_no_doc_id_returns_error(self) -> None:
        """No --file and no --doc-id returns exit code 1."""
        args = argparse.Namespace(
            file=None,
            doc_id=None,
            output=None,
            strategy="auto",
            info_only=False,
            start_page=None,
            end_page=None,
        )

        result = await cmd_markdown(args)

        assert result == 1


class TestCmdMarkdownErrorHandling:
    """Tests for cmd_markdown error handling."""

    @pytest.mark.asyncio
    async def test_parser_exception_returns_error(self, tmp_path: Path) -> None:
        """PDFParser exception returns exit code 1."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        args = argparse.Namespace(
            file=str(pdf_file),
            doc_id=None,
            output=None,
            strategy="auto",
            info_only=False,
            start_page=None,
            end_page=None,
        )

        with patch("company_research_agent.cli.commands.markdown.PDFParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser.to_markdown.side_effect = RuntimeError("Parse error")
            mock_parser_cls.return_value = mock_parser

            result = await cmd_markdown(args)

            assert result == 1

    @pytest.mark.asyncio
    async def test_info_only_exception_returns_error(self, tmp_path: Path) -> None:
        """PDFParser.get_info exception returns exit code 1."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        args = argparse.Namespace(
            file=str(pdf_file),
            doc_id=None,
            output=None,
            strategy="auto",
            info_only=True,
            start_page=None,
            end_page=None,
        )

        with patch("company_research_agent.cli.commands.markdown.PDFParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser.get_info.side_effect = RuntimeError("Info error")
            mock_parser_cls.return_value = mock_parser

            result = await cmd_markdown(args)

            assert result == 1


class TestCmdMarkdownPageRange:
    """Tests for cmd_markdown page range options."""

    @pytest.mark.asyncio
    async def test_page_range_passed_to_parser(self, tmp_path: Path) -> None:
        """--start-page and --end-page are passed to parser."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        mock_result = MagicMock()
        mock_result.text = "# Page Range"
        mock_result.pages = 5
        mock_result.strategy_used = "pymupdf4llm"

        args = argparse.Namespace(
            file=str(pdf_file),
            doc_id=None,
            output=None,
            strategy="pdfplumber",
            info_only=False,
            start_page=5,
            end_page=10,
        )

        with patch("company_research_agent.cli.commands.markdown.PDFParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser.to_markdown.return_value = mock_result
            mock_parser_cls.return_value = mock_parser

            result = await cmd_markdown(args)

            assert result == 0
            mock_parser.to_markdown.assert_called_once_with(
                pdf_file,
                start_page=5,
                end_page=10,
                strategy="pdfplumber",
            )
