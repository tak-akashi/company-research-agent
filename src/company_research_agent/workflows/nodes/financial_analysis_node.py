"""Financial analysis node for extracting financial information.

有価証券報告書から財務情報を抽出するノード。
マークダウンテキストを受け取り、FinancialAnalysisを返す。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from company_research_agent.prompts.financial_analysis import FINANCIAL_ANALYSIS_PROMPT
from company_research_agent.schemas.llm_analysis import FinancialAnalysis
from company_research_agent.workflows.nodes.base import LLMAnalysisNode
from company_research_agent.workflows.state import AnalysisState

if TYPE_CHECKING:
    from company_research_agent.llm.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class FinancialAnalysisNode(LLMAnalysisNode[FinancialAnalysis]):
    """財務分析ノード.

    有価証券報告書のマークダウンテキストから、
    財務状況、業績分析、キャッシュフロー分析などを抽出する。

    Example:
        # 環境変数で自動設定
        node = FinancialAnalysisNode()
        result = await node(state)

        # 明示的にプロバイダーを指定
        from company_research_agent.llm import create_llm_provider
        provider = create_llm_provider()
        node = FinancialAnalysisNode(llm_provider=provider)
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider | None = None,
    ) -> None:
        """ノードを初期化する.

        Args:
            llm_provider: LLMプロバイダー。Noneの場合は環境変数から自動設定。
        """
        super().__init__(llm_provider)

    @property
    def name(self) -> str:
        """ノード名を返す."""
        return "financial_analysis"

    @property
    def prompt_template(self) -> str:
        """プロンプトテンプレートを返す."""
        return FINANCIAL_ANALYSIS_PROMPT

    @property
    def output_schema(self) -> type[FinancialAnalysis]:
        """出力スキーマのクラスを返す."""
        return FinancialAnalysis

    async def execute(self, state: AnalysisState) -> FinancialAnalysis:
        """財務分析を実行する.

        Args:
            state: 現在のワークフロー状態

        Returns:
            抽出された財務分析結果

        Raises:
            ValueError: markdown_contentが指定されていない場合
            LLMProviderError: LLM呼び出しに失敗した場合
        """
        markdown_content = self._get_required_field(state, "markdown_content")
        logger.info(f"Analyzing financials from {len(markdown_content)} chars")

        # プロンプトを構築
        prompt = self.prompt_template.format(content=markdown_content)

        # LLMを呼び出し
        result = await self._invoke_llm(prompt)

        logger.info(f"Financial analysis completed: {len(result.highlights)} highlights")
        return result

    def _update_state(self, state: AnalysisState, result: FinancialAnalysis) -> dict[str, Any]:
        """実行結果でStateを更新する.

        Args:
            state: 現在のワークフロー状態
            result: 抽出された財務分析結果

        Returns:
            更新するキーと値のdict
        """
        return {"financial_analysis": result}
