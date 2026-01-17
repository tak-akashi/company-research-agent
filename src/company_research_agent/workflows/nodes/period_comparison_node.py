"""Period comparison node for comparing current and prior period reports.

当期と前期の有価証券報告書を比較するノード。
2つのマークダウンテキストを受け取り、PeriodComparisonを返す。
"""

from __future__ import annotations

import logging
from typing import Any

from company_research_agent.core.config import GeminiConfig
from company_research_agent.prompts.period_comparison import (
    PERIOD_COMPARISON_PROMPT,
    PERIOD_COMPARISON_SINGLE_PROMPT,
)
from company_research_agent.schemas.llm_analysis import PeriodComparison
from company_research_agent.workflows.nodes.base import LLMAnalysisNode
from company_research_agent.workflows.state import AnalysisState

logger = logging.getLogger(__name__)


class PeriodComparisonNode(LLMAnalysisNode[PeriodComparison]):
    """前期比較ノード.

    当期と前期の有価証券報告書を比較し、
    重要な変化点を抽出する。

    前期の書類がない場合は、当期書類内の前期比較記述から変化点を抽出。

    Example:
        node = PeriodComparisonNode()
        result = await node(state)
        # result = {"period_comparison": PeriodComparison(...), ...}
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
        return "period_comparison"

    @property
    def prompt_template(self) -> str:
        """プロンプトテンプレートを返す（2文書比較用）."""
        return PERIOD_COMPARISON_PROMPT

    @property
    def output_schema(self) -> type[PeriodComparison]:
        """出力スキーマのクラスを返す."""
        return PeriodComparison

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

    async def execute(self, state: AnalysisState) -> PeriodComparison:
        """前期比較を実行する.

        Args:
            state: 現在のワークフロー状態

        Returns:
            抽出された前期比較結果

        Raises:
            ValueError: markdown_contentが指定されていない場合
            GeminiAPIError: LLM呼び出しに失敗した場合
        """
        markdown_content = self._get_required_field(state, "markdown_content")
        prior_markdown_content = state.get("prior_markdown_content")

        model = self._get_model()
        structured_model = model.with_structured_output(PeriodComparison)

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
        result: PeriodComparison = await structured_model.ainvoke(prompt)

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
