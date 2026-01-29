"""Gemini API client for PDF text extraction using vision capabilities."""

from __future__ import annotations

import base64
import time
from pathlib import Path
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from company_research_agent.core.config import GeminiConfig
from company_research_agent.core.exceptions import GeminiAPIError


class GeminiClient:
    """Client for Gemini API with PDF text extraction capabilities.

    This client uses Gemini's vision model via LangChain to extract text
    from PDF pages, handling rate limiting and retries automatically.

    Example:
        config = GeminiConfig()
        client = GeminiClient(config)
        markdown_text = client.extract_pdf_to_markdown(Path("document.pdf"))
    """

    # Prompt for PDF text extraction
    EXTRACTION_PROMPT = """
あなたはPDFからテキストと表を抽出する専門家です。
このPDFページの内容をマークダウン形式で正確に抽出してください。

ルール:
1. テキストは段落ごとに抽出し、見出しは適切なレベルの#を付ける
2. 表はマークダウンテーブル形式（| col1 | col2 |）で抽出する
3. 図やグラフがある場合は [図: 説明] の形式で記述する
4. ページ番号やヘッダー/フッターは除外する
5. 日本語の固有名詞や数値は正確に抽出する
6. 会計用語や財務諸表の項目名は正確に抽出する

出力はマークダウン形式のテキストのみを返してください。説明や前置きは不要です。
""".strip()

    def __init__(self, config: GeminiConfig) -> None:
        """Initialize the Gemini client.

        Args:
            config: Configuration containing API key and settings.
        """
        self._config = config
        self._model: Any = None
        self._last_request_time: float = 0.0
        self._request_interval: float = 60.0 / config.rpm_limit

    def _get_model(self) -> Any:
        """Get or create the Gemini model via LangChain.

        Returns:
            The configured ChatGoogleGenerativeAI instance.
        """
        if self._model is None:
            from langchain_google_genai import ChatGoogleGenerativeAI

            self._model = ChatGoogleGenerativeAI(
                model=self._config.model,
                google_api_key=self._config.google_api_key,
                timeout=self._config.timeout,
                max_retries=self._config.max_retries,
            )
        return self._model

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._request_interval:
            time.sleep(self._request_interval - elapsed)
        self._last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(GeminiAPIError),
        reraise=True,
    )
    def _extract_page_text(self, image_path: Path) -> str:
        """Extract text from a single page image.

        Args:
            image_path: Path to the page image file.

        Returns:
            Extracted text in markdown format.

        Raises:
            GeminiAPIError: If the API call fails.
        """
        from langchain_core.messages import HumanMessage

        self._rate_limit()

        try:
            model = self._get_model()

            # Read image and encode to base64
            with open(image_path, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")

            # Create multimodal message with image
            message = HumanMessage(
                content=[
                    {"type": "text", "text": self.EXTRACTION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"},
                    },
                ]
            )

            response = model.invoke([message])

            if response.content:
                return str(response.content).strip()
            return ""

        except Exception as e:
            error_message = str(e)
            # Check for rate limit errors
            if "429" in error_message or "quota" in error_message.lower():
                raise GeminiAPIError(
                    message=f"Rate limit exceeded: {error_message}",
                    model=self._config.model,
                ) from e
            raise GeminiAPIError(
                message=f"API call failed: {error_message}",
                model=self._config.model,
            ) from e

    def extract_pdf_to_markdown(
        self,
        pdf_path: Path,
        start_page: int | None = None,
        end_page: int | None = None,
    ) -> str:
        """Extract text from a PDF file and convert to markdown.

        This method converts each page of the PDF to an image and uses
        Gemini's vision capabilities to extract text.

        Args:
            pdf_path: Path to the PDF file.
            start_page: Starting page number (1-based). None for first page.
            end_page: Ending page number (1-based). None for last page.

        Returns:
            Extracted text in markdown format.

        Raises:
            FileNotFoundError: If the PDF file does not exist.
            GeminiAPIError: If text extraction fails.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        import tempfile

        import fitz  # type: ignore[import-untyped]  # PyMuPDF

        try:
            doc = fitz.open(str(pdf_path))
            total_pages = len(doc)

            # Determine page range
            start_idx = (start_page or 1) - 1
            end_idx = end_page or total_pages

            extracted_texts: list[str] = []

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                for page_num in range(start_idx, min(end_idx, total_pages)):
                    page = doc[page_num]

                    # Convert page to image (300 DPI for good quality)
                    mat = fitz.Matrix(300 / 72, 300 / 72)
                    pix = page.get_pixmap(matrix=mat)

                    image_path = temp_path / f"page_{page_num + 1}.png"
                    pix.save(str(image_path))

                    # Extract text from image
                    text = self._extract_page_text(image_path)
                    if text:
                        extracted_texts.append(f"## Page {page_num + 1}\n\n{text}")

            doc.close()

            return "\n\n---\n\n".join(extracted_texts)

        except FileNotFoundError:
            raise
        except GeminiAPIError:
            raise
        except Exception as e:
            raise GeminiAPIError(
                message=f"PDF extraction failed: {e}",
                model=self._config.model,
            ) from e
