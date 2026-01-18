"""Period comparison node for comparing current and prior period reports.

当期と前期の有価証券報告書を比較するノード。
2つのマークダウンテキストを受け取り、PeriodComparisonを返す。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from company_research_agent.prompts.period_comparison import (
    PERIOD_COMPARISON_PROMPT,
    PERIOD_COMPARISON_SINGLE_PROMPT,
)
from company_research_agent.schemas.llm_analysis import PeriodComparison
from company_research_agent.workflows.nodes.base import LLMAnalysisNode
from company_research_agent.workflows.state import AnalysisState

if TYPE_CHECKING:
    from company_research_agent.llm.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class PeriodComparisonNode(LLMAnalysisNode[PeriodComparison]):
    """前期比較ノード.

    当期と前期の有価証券報告書を比較し、
    重要な変化点を抽出する。

    前期の書類がない場合は、当期書類内の前期比較記述から変化点を抽出。

    Example:
        # 環境変数で自動設定
        node = PeriodComparisonNode()
        result = await node(state)

        # 明示的にプロバイダーを指定
        from company_research_agent.llm import create_llm_provider
        provider = create_llm_provider()
        node = PeriodComparisonNode(llm_provider=provider)
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
        return "period_comparison"

    @property
    def prompt_template(self) -> str:
        """プロンプトテンプレートを返す（2文書比較用）."""
        return PERIOD_COMPARISON_PROMPT

    @property
    def output_schema(self) -> type[PeriodComparison]:
        """出力スキーマのクラスを返す."""
        return PeriodComparison

    async def execute(self, state: AnalysisState) -> PeriodComparison:
        """前期比較を実行する.

        Args:
            state: 現在のワークフロー状態

        Returns:
            抽出された前期比較結果

        Raises:
            ValueError: markdown_contentが指定されていない場合
            LLMProviderError: LLM呼び出しに失敗した場合
        """
        markdown_content = self._get_required_field(state, "markdown_content")
        prior_markdown_content = state.get("prior_markdown_content")

        if prior_markdown_content:
            # 2文書比較
            logger.info(
                f"Comparing periods: current={len(markdown_content)} chars, "
                f"prior={len(prior_markdown_content)} chars"
            )
            prompt = self.prompt_template.format(
                current_content=markdown_content,
                prior_content=prior_markdown_content,
            )
        else:
            # 単一文書から前期比較情報を抽出
            logger.info(
                f"Extracting period changes from single document: {len(markdown_content)} chars"
            )
            prompt = PERIOD_COMPARISON_SINGLE_PROMPT.format(content=markdown_content)

        # LLMを呼び出し
        result = await self._invoke_llm(prompt)

        logger.info(f"Period comparison completed: {len(result.change_points)} changes")
        return result

    def _update_state(self, state: AnalysisState, result: PeriodComparison) -> dict[str, Any]:
        """実行結果でStateを更新する.

        Args:
            state: 現在のワークフロー状態
            result: 抽出された前期比較結果

        Returns:
            更新するキーと値のdict
        """
        return {"period_comparison": result}
