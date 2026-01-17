"""Tests for analyze_document tool."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from company_research_agent.schemas.llm_analysis import (
    BusinessSegment,
    BusinessSummary,
    ComprehensiveReport,
    FinancialAnalysis,
    FinancialHighlight,
    RiskAnalysis,
    RiskCategory,
    RiskItem,
    Severity,
)
from company_research_agent.tools.analyze_document import analyze_document


@pytest.fixture
def sample_comprehensive_report() -> ComprehensiveReport:
    """Sample comprehensive report fixture."""
    return ComprehensiveReport(
        executive_summary="トヨタ自動車は自動車製造業のグローバルリーダーであり、安定した財務基盤を持つ。",
        business_summary=BusinessSummary(
            company_name="トヨタ自動車株式会社",
            fiscal_year="2024年3月期",
            business_description="世界最大級の自動車メーカーで、トヨタ、レクサスブランドで自動車を製造販売している。",
            main_products_services=["乗用車", "商用車", "レクサス車"],
            business_segments=[
                BusinessSegment(
                    name="自動車事業",
                    description="自動車の製造・販売",
                    revenue_share="90%",
                    key_products=["カローラ", "プリウス"],
                ),
            ],
            competitive_advantages=["生産効率", "ブランド力"],
            growth_strategy="電動化と自動運転への投資を加速",
            key_initiatives=["EV開発", "水素自動車開発"],
        ),
        risk_analysis=RiskAnalysis(
            risks=[
                RiskItem(
                    category=RiskCategory.MARKET,
                    title="為替変動リスク",
                    description="為替変動により収益に影響を受ける可能性がある",
                    severity=Severity.HIGH,
                    mitigation="ヘッジ取引による軽減",
                ),
            ],
            new_risks=[],
            risk_summary="主に為替と半導体供給リスクに注意が必要",
        ),
        financial_analysis=FinancialAnalysis(
            revenue_analysis="売上高は前期比10%増の45兆円となった",
            profit_analysis="営業利益は前期比15%増と好調",
            cash_flow_analysis="営業キャッシュフローは2兆円を維持",
            financial_position="自己資本比率は40%で安定",
            highlights=[
                FinancialHighlight(
                    metric_name="売上高",
                    current_value="45兆円",
                    prior_value="40兆円",
                    change_rate="+12.5%",
                    comment="増収",
                ),
            ],
            outlook="来期も増収増益を見込む",
        ),
        period_comparison=None,
        investment_highlights=["EVへの投資加速", "収益性改善"],
        concerns=["半導体不足リスク"],
        generated_at=datetime.now(),
    )


class TestAnalyzeDocument:
    """Tests for analyze_document tool."""

    @pytest.mark.asyncio
    async def test_analyze_document_returns_report(
        self, sample_comprehensive_report: ComprehensiveReport
    ) -> None:
        """analyze_document should return comprehensive report."""
        mock_graph = MagicMock()
        mock_graph.run_full_analysis = AsyncMock(
            return_value={"comprehensive_report": sample_comprehensive_report}
        )

        with patch(
            "company_research_agent.tools.analyze_document.AnalysisGraph"
        ) as mock_graph_class:
            mock_graph_class.return_value = mock_graph

            result = await analyze_document.ainvoke({"doc_id": "S100ABCD"})

            assert isinstance(result, ComprehensiveReport)
            assert "トヨタ自動車" in result.executive_summary
            mock_graph.run_full_analysis.assert_called_once_with("S100ABCD", None)

    @pytest.mark.asyncio
    async def test_analyze_document_with_prior_doc(
        self, sample_comprehensive_report: ComprehensiveReport
    ) -> None:
        """analyze_document should pass prior_doc_id to AnalysisGraph."""
        mock_graph = MagicMock()
        mock_graph.run_full_analysis = AsyncMock(
            return_value={"comprehensive_report": sample_comprehensive_report}
        )

        with patch(
            "company_research_agent.tools.analyze_document.AnalysisGraph"
        ) as mock_graph_class:
            mock_graph_class.return_value = mock_graph

            await analyze_document.ainvoke({"doc_id": "S100ABCD", "prior_doc_id": "S100WXYZ"})

            mock_graph.run_full_analysis.assert_called_once_with("S100ABCD", "S100WXYZ")

    @pytest.mark.asyncio
    async def test_analyze_document_raises_on_failure(self) -> None:
        """analyze_document should raise error when analysis fails."""
        mock_graph = MagicMock()
        mock_graph.run_full_analysis = AsyncMock(
            return_value={"comprehensive_report": None, "errors": ["PDF解析エラー"]}
        )

        with patch(
            "company_research_agent.tools.analyze_document.AnalysisGraph"
        ) as mock_graph_class:
            mock_graph_class.return_value = mock_graph

            with pytest.raises(ValueError, match="Analysis failed"):
                await analyze_document.ainvoke({"doc_id": "S100ABCD"})

    @pytest.mark.asyncio
    async def test_analyze_document_raises_on_unknown_error(self) -> None:
        """analyze_document should handle unknown errors."""
        mock_graph = MagicMock()
        mock_graph.run_full_analysis = AsyncMock(
            return_value={"comprehensive_report": None}  # No errors list
        )

        with patch(
            "company_research_agent.tools.analyze_document.AnalysisGraph"
        ) as mock_graph_class:
            mock_graph_class.return_value = mock_graph

            with pytest.raises(ValueError, match="Unknown error"):
                await analyze_document.ainvoke({"doc_id": "S100ABCD"})

    @pytest.mark.asyncio
    async def test_analyze_document_creates_analysis_graph(
        self, sample_comprehensive_report: ComprehensiveReport
    ) -> None:
        """analyze_document should create AnalysisGraph instance."""
        mock_graph = MagicMock()
        mock_graph.run_full_analysis = AsyncMock(
            return_value={"comprehensive_report": sample_comprehensive_report}
        )

        with patch(
            "company_research_agent.tools.analyze_document.AnalysisGraph"
        ) as mock_graph_class:
            mock_graph_class.return_value = mock_graph

            await analyze_document.ainvoke({"doc_id": "S100ABCD"})

            mock_graph_class.assert_called_once()
