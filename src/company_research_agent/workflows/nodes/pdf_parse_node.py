"""PDF parse node for extracting text and converting to markdown.

PDFを解析してマークダウン形式に変換するノード。
pdf_pathを受け取り、マークダウンテキストを返す。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from company_research_agent.core.config import GeminiConfig
from company_research_agent.core.types import ParseStrategy
from company_research_agent.parsers.pdf_parser import PDFParser
from company_research_agent.workflows.nodes.base import AnalysisNode
from company_research_agent.workflows.state import AnalysisState

logger = logging.getLogger(__name__)


class PDFParseNode(AnalysisNode[str]):
    """PDF解析ノード.

    PDFファイルをマークダウン形式に変換する。
    段階的な解析戦略（pymupdf4llm → yomitoku → gemini）を使用。

    Example:
        node = PDFParseNode()
        result = await node(state)
        # result = {"markdown_content": "# Page 1\n...", "completed_nodes": ["pdf_parse"]}
    """

    def __init__(
        self,
        strategy: ParseStrategy = "auto",
        gemini_config: GeminiConfig | None = None,
    ) -> None:
        """ノードを初期化する.

        Args:
            strategy: 解析戦略。"auto"で段階的フォールバック。
            gemini_config: Gemini API設定。"gemini"戦略使用時に必要。
        """
        self._strategy = strategy
        self._gemini_config = gemini_config

    @property
    def name(self) -> str:
        """ノード名を返す."""
        return "pdf_parse"

    def _get_gemini_config(self) -> GeminiConfig | None:
        """Gemini設定を取得する."""
        if self._gemini_config is None:
            try:
                # pydantic-settings reads from environment variables
                self._gemini_config = GeminiConfig()  # type: ignore[call-arg]
            except Exception:
                pass
        return self._gemini_config

    async def execute(self, state: AnalysisState) -> str:
        """PDFをマークダウンに変換する.

        Args:
            state: 現在のワークフロー状態

        Returns:
            マークダウン形式のテキスト

        Raises:
            ValueError: pdf_pathが指定されていない場合
            FileNotFoundError: PDFファイルが存在しない場合
            PDFParseError: 解析に失敗した場合
        """
        pdf_path_str = self._get_required_field(state, "pdf_path")
        pdf_path = Path(pdf_path_str)

        logger.info(f"Parsing PDF: {pdf_path}")

        # PDFパーサーを初期化
        parser = PDFParser(gemini_config=self._get_gemini_config())

        # マークダウンに変換
        result = parser.to_markdown(pdf_path, strategy=self._strategy)

        logger.info(f"PDF parsed: {result.pages} pages, strategy={result.strategy_used}")

        return result.text

    def _update_state(self, state: AnalysisState, result: str) -> dict[str, Any]:
        """実行結果でStateを更新する.

        Args:
            state: 現在のワークフロー状態
            result: マークダウンテキスト

        Returns:
            更新するキーと値のdict
        """
        return {"markdown_content": result}
