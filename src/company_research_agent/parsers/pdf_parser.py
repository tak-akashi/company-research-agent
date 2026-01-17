"""PDF parser for extracting text and converting to markdown."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pdfplumber
import pymupdf4llm  # type: ignore[import-untyped]

from company_research_agent.core.exceptions import (
    GeminiAPIError,
    PDFParseError,
    YomitokuError,
)
from company_research_agent.core.types import ParseStrategy

if TYPE_CHECKING:
    from company_research_agent.clients.gemini_client import GeminiClient
    from company_research_agent.core.config import GeminiConfig

    PdfPlumberPDF = Any
    PdfPlumberPage = Any
else:
    PdfPlumberPDF = Any
    PdfPlumberPage = Any

logger = logging.getLogger(__name__)


@dataclass
class PDFInfo:
    """PDF metadata information.

    Attributes:
        file_name: Name of the PDF file.
        file_path: Absolute path to the PDF file.
        total_pages: Total number of pages in the PDF.
        page_size: Width and height of the first page (if available).
        metadata: PDF document metadata (author, title, etc.).
        table_of_contents: Extracted table of contents items.
    """

    file_name: str
    file_path: str
    total_pages: int
    page_size: dict[str, float] | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    table_of_contents: list[str] = field(default_factory=list)


@dataclass
class ParsedPDFContent:
    """Parsed PDF content result.

    Attributes:
        text: Extracted text or markdown content.
        pages: Number of pages processed.
        strategy_used: The parsing strategy that was used.
        metadata: Additional metadata about the parsing.
    """

    text: str
    pages: int
    strategy_used: ParseStrategy
    metadata: dict[str, object] = field(default_factory=dict)


class PDFParser:
    """PDF parser for text extraction and markdown conversion.

    This parser provides methods to:
    - Get PDF metadata (page count, size, table of contents)
    - Extract text from specific page ranges
    - Convert PDF to markdown format

    The parser supports multiple strategies for content extraction:
    - auto: Automatically selects the best strategy with fallback chain
            (pymupdf4llm → yomitoku → gemini)
    - pdfplumber: Basic text extraction
    - pymupdf4llm: Markdown conversion with structure preservation
    - yomitoku: Japanese OCR for scanned documents and complex layouts
    - gemini: LLM-based extraction using Gemini 2.5 Flash (fallback)

    Example:
        parser = PDFParser()

        # Get PDF info
        info = parser.get_info(Path("document.pdf"))
        print(f"Pages: {info.total_pages}")

        # Extract text from specific pages
        text = parser.extract_text(Path("document.pdf"), start_page=1, end_page=10)

        # Convert to markdown (with automatic fallback)
        result = parser.to_markdown(Path("document.pdf"), strategy="auto")
        print(result.text)

        # Use specific strategy
        result = parser.to_markdown(Path("document.pdf"), strategy="yomitoku")
    """

    def __init__(
        self,
        gemini_config: GeminiConfig | None = None,
    ) -> None:
        """Initialize the PDF parser.

        Args:
            gemini_config: Configuration for Gemini API client.
                          Required for "gemini" strategy or "auto" fallback.
        """
        self._gemini_config = gemini_config
        self._gemini_client: GeminiClient | None = None

    def _get_gemini_client(self) -> GeminiClient:
        """Get or create the Gemini client.

        Returns:
            The GeminiClient instance.

        Raises:
            PDFParseError: If Gemini config is not provided.
        """
        if self._gemini_client is None:
            if self._gemini_config is None:
                raise PDFParseError(
                    message="Gemini config is required for gemini strategy",
                    pdf_path="",
                    strategy="gemini",
                )
            from company_research_agent.clients.gemini_client import GeminiClient

            self._gemini_client = GeminiClient(self._gemini_config)
        return self._gemini_client

    def get_info(self, pdf_path: Path) -> PDFInfo:
        """Get PDF metadata and information.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            PDFInfo containing file metadata.

        Raises:
            FileNotFoundError: If the PDF file does not exist.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        with pdfplumber.open(pdf_path) as pdf:
            page_size: dict[str, float] | None = None
            if pdf.pages:
                first_page: PdfPlumberPage = pdf.pages[0]
                page_size = {
                    "width": float(first_page.width),
                    "height": float(first_page.height),
                }

            # Extract metadata, converting values to strings
            raw_metadata = pdf.metadata or {}
            metadata: dict[str, str] = {
                str(k): str(v) for k, v in raw_metadata.items() if v is not None
            }

            # Extract table of contents from text
            toc = self._extract_toc_from_text(pdf)

            return PDFInfo(
                file_name=pdf_path.name,
                file_path=str(pdf_path.absolute()),
                total_pages=len(pdf.pages),
                page_size=page_size,
                metadata=metadata,
                table_of_contents=toc,
            )

    def _extract_toc_from_text(self, pdf: PdfPlumberPDF) -> list[str]:
        """Extract table of contents from the first few pages.

        This method looks for common patterns that indicate TOC entries:
        - Lines starting with numbers (e.g., "1. Introduction")
        - Lines with dot leaders (e.g., "Chapter 1 ..... 5")
        - Lines ending with page numbers

        Args:
            pdf: An open pdfplumber PDF object.

        Returns:
            List of extracted TOC items (up to 30 items).
        """
        toc_items: list[str] = []

        # Search first 5 pages for TOC
        pages_to_search = min(5, len(pdf.pages))
        for page in pdf.pages[:pages_to_search]:
            text = page.extract_text() or ""
            lines = text.split("\n")

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Detect TOC-like lines
                is_numbered = any(line.startswith(f"{n}.") for n in range(1, 20))
                has_dot_leaders = "....." in line
                has_trailing_page_num = len(line) > 5 and line[-1].isdigit() and " " in line

                if is_numbered or has_dot_leaders or has_trailing_page_num:
                    toc_items.append(line)

        return toc_items[:30]

    def extract_text(
        self,
        pdf_path: Path,
        start_page: int = 1,
        end_page: int | None = None,
    ) -> str:
        """Extract text from specified page range.

        Args:
            pdf_path: Path to the PDF file.
            start_page: Starting page number (1-based, inclusive).
            end_page: Ending page number (1-based, inclusive).
                     If None, extracts until the last page.

        Returns:
            Extracted text with page markers.

        Raises:
            FileNotFoundError: If the PDF file does not exist.
            ValueError: If page numbers are invalid.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        if start_page < 1:
            raise ValueError(f"start_page must be >= 1, got {start_page}")

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

            if start_page > total_pages:
                raise ValueError(f"start_page ({start_page}) exceeds total pages ({total_pages})")

            # Convert to 0-based index
            start_idx = start_page - 1
            end_idx = min(total_pages, end_page) if end_page else total_pages

            if end_page is not None and end_page < start_page:
                raise ValueError(f"end_page ({end_page}) must be >= start_page ({start_page})")

            texts: list[str] = []
            for i in range(start_idx, end_idx):
                page: PdfPlumberPage = pdf.pages[i]
                text = page.extract_text() or ""
                texts.append(f"--- Page {i + 1} ---\n{text}")

        return "\n\n".join(texts)

    def to_markdown(
        self,
        pdf_path: Path,
        start_page: int | None = None,
        end_page: int | None = None,
        strategy: ParseStrategy = "auto",
    ) -> ParsedPDFContent:
        """Convert PDF to markdown format.

        Args:
            pdf_path: Path to the PDF file.
            start_page: Starting page number (1-based, inclusive).
                       If None, starts from the first page.
            end_page: Ending page number (1-based, inclusive).
                     If None, processes until the last page.
            strategy: Parsing strategy to use.
                     - "auto": Uses pymupdf4llm with fallback to yomitoku/gemini
                     - "pdfplumber": Basic text extraction
                     - "pymupdf4llm": Markdown with structure
                     - "yomitoku": Japanese OCR
                     - "gemini": LLM-based extraction

        Returns:
            ParsedPDFContent containing the markdown text and metadata.

        Raises:
            FileNotFoundError: If the PDF file does not exist.
            PDFParseError: If parsing fails.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        if strategy == "auto":
            return self._parse_with_auto_fallback(pdf_path, start_page, end_page)

        try:
            if strategy == "pdfplumber":
                return self._parse_with_pdfplumber(pdf_path, start_page, end_page)
            elif strategy == "pymupdf4llm":
                return self._parse_with_pymupdf4llm(pdf_path, start_page, end_page)
            elif strategy == "yomitoku":
                return self._parse_with_yomitoku(pdf_path, start_page, end_page)
            elif strategy == "gemini":
                return self._parse_with_gemini(pdf_path, start_page, end_page)
            else:
                raise PDFParseError(
                    message=f"Unknown strategy: {strategy}",
                    pdf_path=str(pdf_path),
                    strategy=strategy,
                )
        except FileNotFoundError:
            raise
        except PDFParseError:
            raise
        except GeminiAPIError:
            raise
        except YomitokuError:
            raise
        except Exception as e:
            raise PDFParseError(
                message=str(e),
                pdf_path=str(pdf_path),
                strategy=strategy,
            ) from e

    def _parse_with_auto_fallback(
        self,
        pdf_path: Path,
        start_page: int | None,
        end_page: int | None,
    ) -> ParsedPDFContent:
        """Parse PDF with automatic fallback chain.

        Fallback order: pymupdf4llm → yomitoku → gemini

        Args:
            pdf_path: Path to the PDF file.
            start_page: Starting page number (1-based).
            end_page: Ending page number (1-based).

        Returns:
            ParsedPDFContent with extracted text.

        Raises:
            PDFParseError: If all strategies fail.
        """
        errors: list[str] = []

        # Try pymupdf4llm first
        try:
            logger.info(f"Trying pymupdf4llm for {pdf_path}")
            result = self._parse_with_pymupdf4llm(pdf_path, start_page, end_page)
            # Check if result has meaningful content
            if result.text and len(result.text.strip()) > 100:
                return result
            logger.warning(f"pymupdf4llm returned insufficient content for {pdf_path}")
            errors.append("pymupdf4llm: insufficient content")
        except Exception as e:
            logger.warning(f"pymupdf4llm failed for {pdf_path}: {e}")
            errors.append(f"pymupdf4llm: {e}")

        # Try yomitoku if available
        try:
            logger.info(f"Trying yomitoku for {pdf_path}")
            result = self._parse_with_yomitoku(pdf_path, start_page, end_page)
            if result.text and len(result.text.strip()) > 100:
                return result
            logger.warning(f"yomitoku returned insufficient content for {pdf_path}")
            errors.append("yomitoku: insufficient content")
        except YomitokuError as e:
            if "not installed" in str(e):
                logger.info(f"yomitoku not available: {e}")
                errors.append(f"yomitoku: {e}")
            else:
                logger.warning(f"yomitoku failed for {pdf_path}: {e}")
                errors.append(f"yomitoku: {e}")
        except Exception as e:
            logger.warning(f"yomitoku failed for {pdf_path}: {e}")
            errors.append(f"yomitoku: {e}")

        # Try gemini as last resort
        if self._gemini_config is not None:
            try:
                logger.info(f"Trying gemini for {pdf_path}")
                return self._parse_with_gemini(pdf_path, start_page, end_page)
            except GeminiAPIError as e:
                logger.warning(f"gemini failed for {pdf_path}: {e}")
                errors.append(f"gemini: {e}")
            except Exception as e:
                logger.warning(f"gemini failed for {pdf_path}: {e}")
                errors.append(f"gemini: {e}")
        else:
            errors.append("gemini: config not provided")

        # All strategies failed
        raise PDFParseError(
            message=f"All strategies failed: {'; '.join(errors)}",
            pdf_path=str(pdf_path),
            strategy="auto",
        )

    def _parse_with_pdfplumber(
        self,
        pdf_path: Path,
        start_page: int | None,
        end_page: int | None,
    ) -> ParsedPDFContent:
        """Parse PDF using pdfplumber for basic text extraction.

        Args:
            pdf_path: Path to the PDF file.
            start_page: Starting page number (1-based).
            end_page: Ending page number (1-based).

        Returns:
            ParsedPDFContent with extracted text.
        """
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

            # Determine page range
            start_idx = (start_page or 1) - 1
            end_idx = end_page or total_pages

            texts: list[str] = []
            for i in range(start_idx, end_idx):
                if i >= total_pages:
                    break
                page: PdfPlumberPage = pdf.pages[i]
                text = page.extract_text() or ""
                # Format as markdown with page header
                texts.append(f"## Page {i + 1}\n\n{text}")

            pages_processed = min(end_idx, total_pages) - start_idx

        return ParsedPDFContent(
            text="\n\n".join(texts),
            pages=pages_processed,
            strategy_used="pdfplumber",
            metadata={
                "total_pages": total_pages,
                "start_page": start_idx + 1,
                "end_page": min(end_idx, total_pages),
            },
        )

    def _parse_with_pymupdf4llm(
        self,
        pdf_path: Path,
        start_page: int | None,
        end_page: int | None,
    ) -> ParsedPDFContent:
        """Parse PDF using pymupdf4llm for markdown conversion.

        Args:
            pdf_path: Path to the PDF file.
            start_page: Starting page number (1-based).
            end_page: Ending page number (1-based).

        Returns:
            ParsedPDFContent with markdown text.
        """
        # Get total pages first
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

        # Determine page range for pymupdf4llm (0-based indices)
        pages: list[int] | None = None
        if start_page is not None or end_page is not None:
            start_idx = (start_page or 1) - 1
            end_idx = end_page or total_pages
            pages = list(range(start_idx, min(end_idx, total_pages)))

        # Convert to markdown
        md_text: str = pymupdf4llm.to_markdown(str(pdf_path), pages=pages)

        pages_processed = len(pages) if pages is not None else total_pages

        return ParsedPDFContent(
            text=md_text,
            pages=pages_processed,
            strategy_used="pymupdf4llm",
            metadata={
                "total_pages": total_pages,
                "start_page": (start_page or 1),
                "end_page": end_page or total_pages,
            },
        )

    def _parse_with_yomitoku(
        self,
        pdf_path: Path,
        start_page: int | None,
        end_page: int | None,
    ) -> ParsedPDFContent:
        """Parse PDF using yomitoku OCR for Japanese documents.

        Args:
            pdf_path: Path to the PDF file.
            start_page: Starting page number (1-based).
            end_page: Ending page number (1-based).

        Returns:
            ParsedPDFContent with OCR-extracted text.

        Raises:
            YomitokuError: If yomitoku is not installed or OCR fails.
        """
        try:
            from yomitoku import DocumentAnalyzer  # type: ignore[import-not-found]
        except ImportError as e:
            raise YomitokuError(
                message="yomitoku is not installed. Install with: pip install yomitoku",
                pdf_path=str(pdf_path),
            ) from e

        try:
            # Get total pages
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)

            # Determine page range
            start_idx = (start_page or 1) - 1
            end_idx = end_page or total_pages

            # Initialize analyzer
            analyzer = DocumentAnalyzer(configs={"device": "cpu"})

            # Process PDF
            results, _ = analyzer(str(pdf_path), start_page=start_idx, end_page=end_idx)

            # Convert to markdown
            texts: list[str] = []
            for i, result in enumerate(results):
                page_num = start_idx + i + 1
                md_text = result.to_markdown()
                texts.append(f"## Page {page_num}\n\n{md_text}")

            pages_processed = min(end_idx, total_pages) - start_idx

            return ParsedPDFContent(
                text="\n\n".join(texts),
                pages=pages_processed,
                strategy_used="yomitoku",
                metadata={
                    "total_pages": total_pages,
                    "start_page": start_idx + 1,
                    "end_page": min(end_idx, total_pages),
                },
            )

        except ImportError:
            raise
        except Exception as e:
            raise YomitokuError(
                message=f"OCR processing failed: {e}",
                pdf_path=str(pdf_path),
            ) from e

    def _parse_with_gemini(
        self,
        pdf_path: Path,
        start_page: int | None,
        end_page: int | None,
    ) -> ParsedPDFContent:
        """Parse PDF using Gemini API for LLM-based extraction.

        Args:
            pdf_path: Path to the PDF file.
            start_page: Starting page number (1-based).
            end_page: Ending page number (1-based).

        Returns:
            ParsedPDFContent with LLM-extracted text.

        Raises:
            PDFParseError: If Gemini config is not provided.
            GeminiAPIError: If API call fails.
        """
        client = self._get_gemini_client()

        # Get total pages
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

        # Determine page range
        start_idx = (start_page or 1) - 1
        end_idx = end_page or total_pages

        # Extract text using Gemini
        md_text = client.extract_pdf_to_markdown(
            pdf_path,
            start_page=start_idx + 1,
            end_page=min(end_idx, total_pages),
        )

        pages_processed = min(end_idx, total_pages) - start_idx

        return ParsedPDFContent(
            text=md_text,
            pages=pages_processed,
            strategy_used="gemini",
            metadata={
                "total_pages": total_pages,
                "start_page": start_idx + 1,
                "end_page": min(end_idx, total_pages),
            },
        )
