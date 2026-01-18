"""ビジョンLLMクライアント（PDF解析用）."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from company_research_agent.core.exceptions import LLMProviderError

if TYPE_CHECKING:
    from company_research_agent.llm.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class VisionLLMClient:
    """PDF解析用のビジョンLLMクライアント.

    任意のLLMプロバイダーを使用してPDFからテキストを抽出する。
    GeminiClientを置換し、複数プロバイダー対応にする。

    Example:
        >>> # 環境変数で自動設定（推奨）
        >>> client = VisionLLMClient()
        >>> markdown = client.extract_pdf_to_markdown(Path("document.pdf"))

        >>> # 明示的にプロバイダーを指定
        >>> from company_research_agent.llm import create_llm_provider, LLMConfig
        >>> config = LLMConfig(vision_provider=LLMProviderType.OPENAI)
        >>> provider = create_llm_provider(config, for_vision=True)
        >>> client = VisionLLMClient(provider=provider)
    """

    # PDF抽出用プロンプト
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

    def __init__(
        self,
        provider: BaseLLMProvider | None = None,
        rpm_limit: int = 60,
    ) -> None:
        """クライアントを初期化する.

        Args:
            provider: LLMプロバイダー。Noneの場合は環境変数から自動設定。
            rpm_limit: レート制限（リクエスト/分）
        """
        self._provider = provider
        self._rpm_limit = rpm_limit
        self._last_request_time: float = 0.0
        self._request_interval: float = 60.0 / rpm_limit

    @property
    def provider(self) -> BaseLLMProvider:
        """LLMプロバイダーを取得する（遅延初期化）."""
        if self._provider is None:
            from company_research_agent.llm.factory import get_vision_provider

            self._provider = get_vision_provider()
        return self._provider

    def _rate_limit(self) -> None:
        """レート制限を適用する."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._request_interval:
            time.sleep(self._request_interval - elapsed)
        self._last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(LLMProviderError),
        reraise=True,
    )
    async def _extract_page_text_async(self, image_path: Path) -> str:
        """ページ画像からテキストを非同期で抽出する.

        Args:
            image_path: ページ画像のパス

        Returns:
            抽出されたマークダウンテキスト

        Raises:
            LLMProviderError: LLM呼び出しに失敗した場合
        """
        self._rate_limit()

        # 画像を読み込み
        with open(image_path, "rb") as f:
            image_data = f.read()

        # ビジョンLLMを呼び出し
        result = await self.provider.ainvoke_vision(
            text_prompt=self.EXTRACTION_PROMPT,
            image_data=image_data,
            mime_type="image/png",
        )

        return result

    def _extract_page_text(self, image_path: Path) -> str:
        """ページ画像からテキストを同期で抽出する.

        Args:
            image_path: ページ画像のパス

        Returns:
            抽出されたマークダウンテキスト

        Raises:
            LLMProviderError: LLM呼び出しに失敗した場合
        """
        return asyncio.get_event_loop().run_until_complete(
            self._extract_page_text_async(image_path)
        )

    def extract_pdf_to_markdown(
        self,
        pdf_path: Path,
        start_page: int | None = None,
        end_page: int | None = None,
    ) -> str:
        """PDFファイルからマークダウンテキストを抽出する.

        PDFの各ページを画像に変換し、ビジョンLLMでテキストを抽出する。

        Args:
            pdf_path: PDFファイルのパス
            start_page: 開始ページ番号（1-based）。Noneで最初から。
            end_page: 終了ページ番号（1-based）。Noneで最後まで。

        Returns:
            抽出されたマークダウンテキスト

        Raises:
            FileNotFoundError: PDFファイルが見つからない場合
            LLMProviderError: テキスト抽出に失敗した場合
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        import tempfile

        import fitz  # type: ignore[import-untyped]  # PyMuPDF

        logger.info(
            f"Extracting PDF to markdown: {pdf_path.name} "
            f"(provider={self.provider.provider_name}, model={self.provider.model_name})"
        )

        try:
            doc = fitz.open(str(pdf_path))
            total_pages = len(doc)

            # ページ範囲を決定
            start_idx = (start_page or 1) - 1
            end_idx = end_page or total_pages

            extracted_texts: list[str] = []

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                for page_num in range(start_idx, min(end_idx, total_pages)):
                    page = doc[page_num]

                    # ページを画像に変換（300 DPI）
                    mat = fitz.Matrix(300 / 72, 300 / 72)
                    pix = page.get_pixmap(matrix=mat)

                    image_path = temp_path / f"page_{page_num + 1}.png"
                    pix.save(str(image_path))

                    # 画像からテキストを抽出
                    logger.debug(f"Extracting page {page_num + 1}/{total_pages}")
                    text = self._extract_page_text(image_path)
                    if text:
                        extracted_texts.append(f"## Page {page_num + 1}\n\n{text}")

            doc.close()

            result = "\n\n---\n\n".join(extracted_texts)
            logger.info(f"Extracted {len(extracted_texts)} pages, {len(result)} chars")
            return result

        except FileNotFoundError:
            raise
        except LLMProviderError:
            raise
        except Exception as e:
            raise LLMProviderError(
                message=f"PDF extraction failed: {e}",
                provider=self.provider.provider_name,
                model=self.provider.model_name,
            ) from e

    async def extract_pdf_to_markdown_async(
        self,
        pdf_path: Path,
        start_page: int | None = None,
        end_page: int | None = None,
    ) -> str:
        """PDFファイルからマークダウンテキストを非同期で抽出する.

        Args:
            pdf_path: PDFファイルのパス
            start_page: 開始ページ番号（1-based）
            end_page: 終了ページ番号（1-based）

        Returns:
            抽出されたマークダウンテキスト
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        import tempfile

        import fitz

        logger.info(
            f"Extracting PDF to markdown (async): {pdf_path.name} "
            f"(provider={self.provider.provider_name}, model={self.provider.model_name})"
        )

        try:
            doc = fitz.open(str(pdf_path))
            total_pages = len(doc)

            start_idx = (start_page or 1) - 1
            end_idx = end_page or total_pages

            extracted_texts: list[str] = []

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                for page_num in range(start_idx, min(end_idx, total_pages)):
                    page = doc[page_num]

                    mat = fitz.Matrix(300 / 72, 300 / 72)
                    pix = page.get_pixmap(matrix=mat)

                    image_path = temp_path / f"page_{page_num + 1}.png"
                    pix.save(str(image_path))

                    logger.debug(f"Extracting page {page_num + 1}/{total_pages}")
                    text = await self._extract_page_text_async(image_path)
                    if text:
                        extracted_texts.append(f"## Page {page_num + 1}\n\n{text}")

            doc.close()

            result = "\n\n---\n\n".join(extracted_texts)
            logger.info(f"Extracted {len(extracted_texts)} pages, {len(result)} chars")
            return result

        except FileNotFoundError:
            raise
        except LLMProviderError:
            raise
        except Exception as e:
            raise LLMProviderError(
                message=f"PDF extraction failed: {e}",
                provider=self.provider.provider_name,
                model=self.provider.model_name,
            ) from e
