"""Risk extraction node for extracting business risks.

有価証券報告書からリスク情報を抽出するノード。
マークダウンテキストを受け取り、RiskAnalysisを返す。
"""

from __future__ import annotations

import logging
from typing import Any

from company_research_agent.core.config import GeminiConfig
from company_research_agent.prompts.risk_extraction import RISK_EXTRACTION_PROMPT
from company_research_agent.schemas.llm_analysis import RiskAnalysis
from company_research_agent.workflows.nodes.base import LLMAnalysisNode
from company_research_agent.workflows.state import AnalysisState

logger = logging.getLogger(__name__)


class RiskExtractionNode(LLMAnalysisNode[RiskAnalysis]):
    """リスク抽出ノード.

    有価証券報告書のマークダウンテキストから、
    事業等のリスクを抽出し分類する。

    Example:
        node = RiskExtractionNode()
        result = await node(state)
        # result = {"risk_analysis": RiskAnalysis(...), "completed_nodes": ["risk_extraction"]}
    """

    def __init__(
        self,
        config: GeminiConfig | None = None,
    ) -> None:
        """ノードを初期化する.

        Args:
            config: Gemini API設定。Noneの場合は環境変数から読み込む。
        """
        self._config = config
        self._model: Any = None

    @property
    def name(self) -> str:
        """ノード名を返す."""
        return "risk_extraction"

    @property
    def prompt_template(self) -> str:
        """プロンプトテンプレートを返す."""
        return RISK_EXTRACTION_PROMPT

    @property
    def output_schema(self) -> type[RiskAnalysis]:
        """出力スキーマのクラスを返す."""
        return RiskAnalysis

    def _get_config(self) -> GeminiConfig:
        """設定を取得する."""
        if self._config is None:
            # pydantic-settings reads from environment variables
            self._config = GeminiConfig()  # type: ignore[call-arg]
        return self._config

    def _get_model(self) -> Any:
        """LLMモデルを取得する."""
        if self._model is None:
            from langchain_google_genai import ChatGoogleGenerativeAI

            config = self._get_config()
            self._model = ChatGoogleGenerativeAI(
                model=config.model,
                google_api_key=config.api_key,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        return self._model

    async def execute(self, state: AnalysisState) -> RiskAnalysis:
        """リスク情報を抽出する.

        Args:
            state: 現在のワークフロー状態

        Returns:
            抽出されたリスク分析結果

        Raises:
            ValueError: markdown_contentが指定されていない場合
            GeminiAPIError: LLM呼び出しに失敗した場合
        """
        markdown_content = self._get_required_field(state, "markdown_content")
        logger.info(f"Extracting risks from {len(markdown_content)} chars")

        # プロンプトを構築
        prompt = self.prompt_template.format(content=markdown_content)

        # LLMを呼び出し（structured output）
        model = self._get_model()
        structured_model = model.with_structured_output(RiskAnalysis)
        result: RiskAnalysis = await structured_model.ainvoke(prompt)

        logger.info(f"Risks extracted: {len(result.risks)} items")
        return result

    def _update_state(self, state: AnalysisState, result: RiskAnalysis) -> dict[str, Any]:
        """実行結果でStateを更新する.

        Args:
            state: 現在のワークフロー状態
            result: 抽出されたリスク分析結果

        Returns:
            更新するキーと値のdict
        """
        return {"risk_analysis": result}
