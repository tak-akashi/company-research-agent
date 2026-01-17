"""Aggregator node for combining all analysis results.

全ての分析結果を統合して総合レポートを生成するノード。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from company_research_agent.core.config import GeminiConfig
from company_research_agent.schemas.llm_analysis import (
    BusinessSummary,
    ComprehensiveReport,
    FinancialAnalysis,
    PeriodComparison,
    RiskAnalysis,
)
from company_research_agent.workflows.nodes.base import AnalysisNode
from company_research_agent.workflows.state import AnalysisState

logger = logging.getLogger(__name__)


AGGREGATOR_PROMPT = """
あなたは企業分析の専門家です。
以下の分析結果を統合し、投資家向けの総合レポートを作成してください。

# 事業要約

{business_summary}

# リスク分析

{risk_analysis}

# 財務分析

{financial_analysis}

# 前期比較

{period_comparison}

# 指示

上記の分析結果を踏まえ、以下を作成してください。日本語で回答してください。

1. **エグゼクティブサマリー** (executive_summary): 300-500字の総括
   - 企業の現状と強み
   - 主要なリスク
   - 財務状況のポイント
   - 投資判断に重要な要素

2. **投資ハイライト** (investment_highlights): ポジティブな要因（3-7件）
   - 競争優位性、成長機会、財務の強さなど

3. **懸念事項** (concerns): ネガティブな要因（3-7件）
   - リスク、課題、不確実性など

# 注意事項

- 客観的な分析を心がけてください
- 推測は避け、分析結果に基づいて記述してください
- 投資判断の参考になる情報を優先してください
""".strip()


class AggregatorNode(AnalysisNode[ComprehensiveReport]):
    """結果統合ノード.

    BusinessSummary、RiskAnalysis、FinancialAnalysis、PeriodComparisonを
    統合してComprehensiveReportを生成する。

    Example:
        node = AggregatorNode()
        result = await node(state)
        # result = {"comprehensive_report": ComprehensiveReport(...), ...}
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
        return "aggregator"

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

    def _format_analysis(self, analysis: Any, title: str) -> str:
        """分析結果を文字列にフォーマットする."""
        if analysis is None:
            return f"{title}: なし"

        if hasattr(analysis, "model_dump"):
            import json

            return json.dumps(analysis.model_dump(), ensure_ascii=False, indent=2)
        return str(analysis)

    async def execute(self, state: AnalysisState) -> ComprehensiveReport:
        """分析結果を統合する.

        Args:
            state: 現在のワークフロー状態

        Returns:
            統合されたComprehensiveReport

        Raises:
            ValueError: 必要な分析結果が揃っていない場合
            GeminiAPIError: LLM呼び出しに失敗した場合
        """
        business_summary: BusinessSummary | None = state.get("business_summary")
        risk_analysis: RiskAnalysis | None = state.get("risk_analysis")
        financial_analysis: FinancialAnalysis | None = state.get("financial_analysis")
        period_comparison: PeriodComparison | None = state.get("period_comparison")

        # 少なくとも1つの分析結果が必要
        if not any([business_summary, risk_analysis, financial_analysis]):
            raise ValueError("At least one analysis result is required")

        logger.info("Aggregating analysis results")

        # プロンプトを構築
        prompt = AGGREGATOR_PROMPT.format(
            business_summary=self._format_analysis(business_summary, "事業要約"),
            risk_analysis=self._format_analysis(risk_analysis, "リスク分析"),
            financial_analysis=self._format_analysis(financial_analysis, "財務分析"),
            period_comparison=self._format_analysis(period_comparison, "前期比較"),
        )

        # LLMを呼び出してサマリーと投資ハイライトを生成
        from pydantic import BaseModel, Field

        class AggregatorOutput(BaseModel):
            """Aggregatorの出力."""

            executive_summary: str = Field(..., description="エグゼクティブサマリー")
            investment_highlights: list[str] = Field(..., description="投資ハイライト")
            concerns: list[str] = Field(..., description="懸念事項")

        model = self._get_model()
        structured_model = model.with_structured_output(AggregatorOutput)
        llm_result = await structured_model.ainvoke(prompt)

        # ComprehensiveReportを構築
        # 分析結果がない場合のデフォルト値を設定
        from company_research_agent.schemas.llm_analysis import (
            BusinessSummary as BS,
        )
        from company_research_agent.schemas.llm_analysis import (
            FinancialAnalysis as FA,
        )
        from company_research_agent.schemas.llm_analysis import (
            RiskAnalysis as RA,
        )

        default_business_summary = BS(
            company_name="不明",
            fiscal_year="不明",
            business_description="分析結果なし",
            main_products_services=[],
            business_segments=[],
            competitive_advantages=[],
            growth_strategy="分析結果なし",
            key_initiatives=[],
        )

        default_risk_analysis = RA(
            risks=[],
            new_risks=[],
            risk_summary="分析結果なし",
        )

        default_financial_analysis = FA(
            revenue_analysis="分析結果なし",
            profit_analysis="分析結果なし",
            cash_flow_analysis="分析結果なし",
            financial_position="分析結果なし",
            highlights=[],
            outlook="分析結果なし",
        )

        result = ComprehensiveReport(
            executive_summary=llm_result.executive_summary,
            business_summary=business_summary or default_business_summary,
            risk_analysis=risk_analysis or default_risk_analysis,
            financial_analysis=financial_analysis or default_financial_analysis,
            period_comparison=period_comparison,
            investment_highlights=llm_result.investment_highlights,
            concerns=llm_result.concerns,
            generated_at=datetime.now(),
        )

        logger.info("Comprehensive report generated")
        return result

    def _update_state(self, state: AnalysisState, result: ComprehensiveReport) -> dict[str, Any]:
        """実行結果でStateを更新する.

        Args:
            state: 現在のワークフロー状態
            result: 生成された統合レポート

        Returns:
            更新するキーと値のdict
        """
        return {"comprehensive_report": result}
