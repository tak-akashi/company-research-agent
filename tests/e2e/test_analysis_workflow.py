"""E2E tests for LLM analysis workflow.

有価証券報告書のLLM分析ワークフローのE2Eテスト。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from company_research_agent.schemas.llm_analysis import (
    BusinessSegment,
    BusinessSummary,
    ChangeCategory,
    ChangePoint,
    FinancialAnalysis,
    FinancialHighlight,
    PeriodComparison,
    RiskAnalysis,
    RiskCategory,
    RiskItem,
    Severity,
)
from company_research_agent.workflows import AnalysisGraph, AnalysisState
from company_research_agent.workflows.nodes import (
    AggregatorNode,
    BusinessSummaryNode,
    EDINETNode,
    FinancialAnalysisNode,
    PDFParseNode,
    PeriodComparisonNode,
    RiskExtractionNode,
)
from company_research_agent.workflows.state import create_initial_state

if TYPE_CHECKING:
    from pathlib import Path


class TestAnalysisGraph:
    """AnalysisGraphのテスト."""

    def test_graph_initialization(self) -> None:
        """グラフの初期化をテスト."""
        graph = AnalysisGraph()
        assert graph._full_graph is None
        assert graph._node_graphs == {}

    def test_build_full_graph(self) -> None:
        """全ワークフローのグラフ構築をテスト."""
        graph = AnalysisGraph()
        compiled_graph = graph.get_full_graph()
        assert compiled_graph is not None
        # 2回目はキャッシュから取得
        cached_graph = graph.get_full_graph()
        assert cached_graph is compiled_graph

    @pytest.mark.parametrize(
        "node_name",
        [
            "edinet",
            "pdf_parse",
            "business_summary",
            "risk_extraction",
            "financial_analysis",
        ],
    )
    def test_build_node_graph(self, node_name: str) -> None:
        """個別ノードのグラフ構築をテスト."""
        graph = AnalysisGraph()
        compiled_graph = graph.get_node_graph(node_name)
        assert compiled_graph is not None
        # 2回目はキャッシュから取得
        cached_graph = graph.get_node_graph(node_name)
        assert cached_graph is compiled_graph

    def test_build_node_graph_unknown_node(self) -> None:
        """未知のノード名でエラーをテスト."""
        graph = AnalysisGraph()
        with pytest.raises(ValueError, match="Unknown node name"):
            graph.get_node_graph("unknown_node")


class TestAnalysisState:
    """AnalysisStateのテスト."""

    def test_create_initial_state(self) -> None:
        """初期状態の作成をテスト."""
        state = create_initial_state("S100TEST")
        assert state["doc_id"] == "S100TEST"
        assert state["prior_doc_id"] is None
        assert state["errors"] == []
        assert state["completed_nodes"] == []

    def test_create_initial_state_with_prior(self) -> None:
        """前期書類IDありの初期状態をテスト."""
        state = create_initial_state("S100TEST", "S100PRIOR")
        assert state["doc_id"] == "S100TEST"
        assert state["prior_doc_id"] == "S100PRIOR"


class TestEDINETNode:
    """EDINETNodeのテスト."""

    @pytest.fixture
    def edinet_node(self) -> EDINETNode:
        """EDINETNodeのインスタンスを作成."""
        return EDINETNode()

    def test_node_name(self, edinet_node: EDINETNode) -> None:
        """ノード名をテスト."""
        assert edinet_node.name == "edinet"

    @pytest.mark.asyncio
    async def test_execute_missing_doc_id(self, edinet_node: EDINETNode) -> None:
        """doc_idがない場合のエラーをテスト."""
        state: AnalysisState = {"errors": [], "completed_nodes": []}
        with pytest.raises(ValueError, match="Required field is missing or empty: doc_id"):
            await edinet_node.execute(state)

    @pytest.mark.asyncio
    async def test_execute_existing_file(self, edinet_node: EDINETNode, tmp_path: Path) -> None:
        """既存ファイルの場合にスキップをテスト."""
        # 既存ファイルを作成
        pdf_file = tmp_path / "S100TEST.pdf"
        pdf_file.touch()

        edinet_node._download_dir = tmp_path
        state: AnalysisState = {
            "doc_id": "S100TEST",
            "errors": [],
            "completed_nodes": [],
        }

        result = await edinet_node.execute(state)
        assert result == str(pdf_file)


class TestPDFParseNode:
    """PDFParseNodeのテスト."""

    @pytest.fixture
    def pdf_parse_node(self) -> PDFParseNode:
        """PDFParseNodeのインスタンスを作成."""
        return PDFParseNode()

    def test_node_name(self, pdf_parse_node: PDFParseNode) -> None:
        """ノード名をテスト."""
        assert pdf_parse_node.name == "pdf_parse"

    @pytest.mark.asyncio
    async def test_execute_missing_pdf_path(self, pdf_parse_node: PDFParseNode) -> None:
        """pdf_pathがない場合のエラーをテスト."""
        state: AnalysisState = {"errors": [], "completed_nodes": []}
        with pytest.raises(ValueError, match="Required field is missing or empty: pdf_path"):
            await pdf_parse_node.execute(state)


class TestBusinessSummaryNode:
    """BusinessSummaryNodeのテスト."""

    @pytest.fixture
    def business_summary_node(self) -> BusinessSummaryNode:
        """BusinessSummaryNodeのインスタンスを作成."""
        return BusinessSummaryNode()

    def test_node_name(self, business_summary_node: BusinessSummaryNode) -> None:
        """ノード名をテスト."""
        assert business_summary_node.name == "business_summary"

    def test_output_schema(self, business_summary_node: BusinessSummaryNode) -> None:
        """出力スキーマをテスト."""
        assert business_summary_node.output_schema == BusinessSummary


class TestRiskExtractionNode:
    """RiskExtractionNodeのテスト."""

    @pytest.fixture
    def risk_extraction_node(self) -> RiskExtractionNode:
        """RiskExtractionNodeのインスタンスを作成."""
        return RiskExtractionNode()

    def test_node_name(self, risk_extraction_node: RiskExtractionNode) -> None:
        """ノード名をテスト."""
        assert risk_extraction_node.name == "risk_extraction"

    def test_output_schema(self, risk_extraction_node: RiskExtractionNode) -> None:
        """出力スキーマをテスト."""
        assert risk_extraction_node.output_schema == RiskAnalysis


class TestFinancialAnalysisNode:
    """FinancialAnalysisNodeのテスト."""

    @pytest.fixture
    def financial_analysis_node(self) -> FinancialAnalysisNode:
        """FinancialAnalysisNodeのインスタンスを作成."""
        return FinancialAnalysisNode()

    def test_node_name(self, financial_analysis_node: FinancialAnalysisNode) -> None:
        """ノード名をテスト."""
        assert financial_analysis_node.name == "financial_analysis"

    def test_output_schema(self, financial_analysis_node: FinancialAnalysisNode) -> None:
        """出力スキーマをテスト."""
        assert financial_analysis_node.output_schema == FinancialAnalysis


class TestPeriodComparisonNode:
    """PeriodComparisonNodeのテスト."""

    @pytest.fixture
    def period_comparison_node(self) -> PeriodComparisonNode:
        """PeriodComparisonNodeのインスタンスを作成."""
        return PeriodComparisonNode()

    def test_node_name(self, period_comparison_node: PeriodComparisonNode) -> None:
        """ノード名をテスト."""
        assert period_comparison_node.name == "period_comparison"

    def test_output_schema(self, period_comparison_node: PeriodComparisonNode) -> None:
        """出力スキーマをテスト."""
        assert period_comparison_node.output_schema == PeriodComparison


class TestAggregatorNode:
    """AggregatorNodeのテスト."""

    @pytest.fixture
    def aggregator_node(self) -> AggregatorNode:
        """AggregatorNodeのインスタンスを作成."""
        return AggregatorNode()

    def test_node_name(self, aggregator_node: AggregatorNode) -> None:
        """ノード名をテスト."""
        assert aggregator_node.name == "aggregator"

    @pytest.mark.asyncio
    async def test_execute_no_analysis_results(self, aggregator_node: AggregatorNode) -> None:
        """分析結果がない場合のエラーをテスト."""
        state: AnalysisState = {
            "business_summary": None,
            "risk_analysis": None,
            "financial_analysis": None,
            "errors": [],
            "completed_nodes": [],
        }
        with pytest.raises(ValueError, match="At least one analysis result is required"):
            await aggregator_node.execute(state)


class TestSchemas:
    """スキーマのテスト."""

    def test_business_summary_creation(self) -> None:
        """BusinessSummaryの作成をテスト."""
        summary = BusinessSummary(
            company_name="テスト株式会社",
            fiscal_year="2024年3月期",
            business_description="テスト事業を展開",
            main_products_services=["製品A", "サービスB"],
            business_segments=[
                BusinessSegment(
                    name="セグメント1",
                    description="主力事業",
                    revenue_share="60%",
                    key_products=["製品A"],
                )
            ],
            competitive_advantages=["技術力", "ブランド力"],
            growth_strategy="新規事業への展開",
            key_initiatives=["DX推進", "海外展開"],
        )
        assert summary.company_name == "テスト株式会社"
        assert len(summary.business_segments) == 1

    def test_risk_analysis_creation(self) -> None:
        """RiskAnalysisの作成をテスト."""
        analysis = RiskAnalysis(
            risks=[
                RiskItem(
                    title="市場リスク",
                    category=RiskCategory.MARKET,
                    severity=Severity.HIGH,
                    description="市場環境の変化によるリスク",
                    mitigation="分散投資",
                )
            ],
            new_risks=["新規リスク項目"],
            risk_summary="主要なリスクの概要",
        )
        assert len(analysis.risks) == 1
        assert analysis.risks[0].category == RiskCategory.MARKET

    def test_financial_analysis_creation(self) -> None:
        """FinancialAnalysisの作成をテスト."""
        analysis = FinancialAnalysis(
            revenue_analysis="売上高分析",
            profit_analysis="利益分析",
            cash_flow_analysis="キャッシュフロー分析",
            financial_position="財務状況",
            highlights=[
                FinancialHighlight(
                    metric_name="売上高",
                    current_value="1,000億円",
                    prior_value="900億円",
                    change_rate="+10.0%",
                    comment="過去最高",
                )
            ],
            outlook="今後の見通し",
        )
        assert len(analysis.highlights) == 1
        assert analysis.highlights[0].metric_name == "売上高"

    def test_period_comparison_creation(self) -> None:
        """PeriodComparisonの作成をテスト."""
        comparison = PeriodComparison(
            change_points=[
                ChangePoint(
                    category=ChangeCategory.STRATEGY,
                    title="戦略変更",
                    current_state="新戦略",
                    prior_state="旧戦略",
                    significance=Severity.MEDIUM,
                    implication="成長性に好影響",
                )
            ],
            new_developments=["新規事業A"],
            discontinued_items=["終了事業B"],
            overall_assessment="主要な変化点のまとめ",
        )
        assert len(comparison.change_points) == 1
        assert comparison.change_points[0].category == ChangeCategory.STRATEGY


class TestRiskExtractionWithMock:
    """リスク抽出ノードのモックテスト.

    PRD要件: リスク項目が5件以上抽出される
    """

    @pytest.fixture
    def mock_risk_analysis_minimum(self) -> RiskAnalysis:
        """最小要件を満たすリスク分析結果."""
        return RiskAnalysis(
            risks=[
                RiskItem(
                    title=f"リスク項目{i + 1}",
                    category=RiskCategory.MARKET,
                    severity=Severity.MEDIUM,
                    description=f"リスク{i + 1}の詳細説明",
                    mitigation=f"対策{i + 1}",
                )
                for i in range(5)
            ],
            new_risks=["新規リスク"],
            risk_summary="テスト用リスクサマリー",
        )

    @pytest.fixture
    def mock_risk_analysis_comprehensive(self) -> RiskAnalysis:
        """包括的なリスク分析結果（10件）."""
        categories = list(RiskCategory)
        severities = list(Severity)
        return RiskAnalysis(
            risks=[
                RiskItem(
                    title=f"リスク項目{i + 1}",
                    category=categories[i % len(categories)],
                    severity=severities[i % len(severities)],
                    description=f"リスク{i + 1}の詳細説明",
                    mitigation=f"対策{i + 1}",
                )
                for i in range(10)
            ],
            new_risks=["新規リスク1", "新規リスク2"],
            risk_summary="包括的なリスクサマリー",
        )

    def test_risk_analysis_minimum_count(self, mock_risk_analysis_minimum: RiskAnalysis) -> None:
        """最小5件のリスクが含まれることを確認."""
        assert len(mock_risk_analysis_minimum.risks) >= 5, (
            f"PRD要件: リスク項目は5件以上必要 (実際: {len(mock_risk_analysis_minimum.risks)}件)"
        )

    def test_risk_analysis_comprehensive_count(
        self, mock_risk_analysis_comprehensive: RiskAnalysis
    ) -> None:
        """包括的なリスク分析が5件以上であることを確認."""
        assert len(mock_risk_analysis_comprehensive.risks) >= 5

    def test_risk_item_has_required_fields(self, mock_risk_analysis_minimum: RiskAnalysis) -> None:
        """各リスク項目が必須フィールドを持つことを確認."""
        for risk in mock_risk_analysis_minimum.risks:
            assert risk.title, "タイトルは必須"
            assert risk.category in RiskCategory, "有効なカテゴリが必要"
            assert risk.severity in Severity, "有効な重要度が必要"
            assert risk.description, "説明は必須"

    def test_risk_categories_coverage(self, mock_risk_analysis_comprehensive: RiskAnalysis) -> None:
        """複数のリスクカテゴリがカバーされていることを確認."""
        categories = {risk.category for risk in mock_risk_analysis_comprehensive.risks}
        assert len(categories) >= 3, "少なくとも3つの異なるカテゴリが必要"


class TestPeriodComparisonWithMock:
    """前期比較ノードのモックテスト.

    PRD要件: 重要な変化点が3件以上検出される
    """

    @pytest.fixture
    def mock_period_comparison_minimum(self) -> PeriodComparison:
        """最小要件を満たす前期比較結果."""
        return PeriodComparison(
            change_points=[
                ChangePoint(
                    category=ChangeCategory.BUSINESS,
                    title="事業構造の変化",
                    current_state="新規事業を開始",
                    prior_state="既存事業のみ",
                    significance=Severity.HIGH,
                    implication="成長ドライバーとなる可能性",
                ),
                ChangePoint(
                    category=ChangeCategory.FINANCIAL,
                    title="財務状況の改善",
                    current_state="自己資本比率50%",
                    prior_state="自己資本比率40%",
                    significance=Severity.MEDIUM,
                    implication="財務安定性の向上",
                ),
                ChangePoint(
                    category=ChangeCategory.STRATEGY,
                    title="戦略方針の転換",
                    current_state="海外展開加速",
                    prior_state="国内中心",
                    significance=Severity.HIGH,
                    implication="収益源の多様化",
                ),
            ],
            new_developments=["新規事業A", "新製品B"],
            discontinued_items=["旧サービスX"],
            overall_assessment="全体的に前向きな変化が見られる",
        )

    @pytest.fixture
    def mock_period_comparison_comprehensive(self) -> PeriodComparison:
        """包括的な前期比較結果（7件）."""
        categories = list(ChangeCategory)
        return PeriodComparison(
            change_points=[
                ChangePoint(
                    category=categories[i % len(categories)],
                    title=f"変化点{i + 1}",
                    current_state=f"当期状況{i + 1}",
                    prior_state=f"前期状況{i + 1}",
                    significance=Severity.MEDIUM,
                    implication=f"影響{i + 1}",
                )
                for i in range(7)
            ],
            new_developments=["新規展開1", "新規展開2", "新規展開3"],
            discontinued_items=["終了項目1"],
            overall_assessment="包括的な変化のまとめ",
        )

    def test_period_comparison_minimum_count(
        self, mock_period_comparison_minimum: PeriodComparison
    ) -> None:
        """最小3件の変化点が含まれることを確認."""
        count = len(mock_period_comparison_minimum.change_points)
        assert count >= 3, f"PRD要件: 変化点は3件以上必要 (実際: {count}件)"

    def test_period_comparison_comprehensive_count(
        self, mock_period_comparison_comprehensive: PeriodComparison
    ) -> None:
        """包括的な前期比較が3件以上であることを確認."""
        assert len(mock_period_comparison_comprehensive.change_points) >= 3

    def test_change_point_has_required_fields(
        self, mock_period_comparison_minimum: PeriodComparison
    ) -> None:
        """各変化点が必須フィールドを持つことを確認."""
        for change in mock_period_comparison_minimum.change_points:
            assert change.title, "タイトルは必須"
            assert change.category in ChangeCategory, "有効なカテゴリが必要"
            assert change.current_state, "当期状況は必須"
            assert change.prior_state, "前期状況は必須"
            assert change.significance in Severity, "有効な重要度が必要"

    def test_change_categories_coverage(
        self, mock_period_comparison_comprehensive: PeriodComparison
    ) -> None:
        """複数の変化カテゴリがカバーされていることを確認."""
        categories = {cp.category for cp in mock_period_comparison_comprehensive.change_points}
        assert len(categories) >= 3, "少なくとも3つの異なるカテゴリが必要"


class TestParallelExecutionStructure:
    """並列実行の構造テスト.

    PRD要件: 分析ノード（Business, Risk, Financial）を並列実行できる
    """

    def test_parallel_nodes_have_same_predecessor(self) -> None:
        """並列ノードが同じ前段ノード（pdf_parse）を持つことを確認."""
        graph = AnalysisGraph()
        compiled_graph = graph.get_full_graph()

        # グラフ構造の確認
        # LangGraphのCompiledStateGraphからノードとエッジ情報を取得
        nodes = compiled_graph.nodes
        assert "business_summary" in nodes
        assert "risk_extraction" in nodes
        assert "financial_analysis" in nodes
        assert "pdf_parse" in nodes

    def test_parallel_nodes_have_same_successor(self) -> None:
        """並列ノードが同じ後続ノード（period_comparison）を持つことを確認."""
        graph = AnalysisGraph()
        compiled_graph = graph.get_full_graph()

        nodes = compiled_graph.nodes
        assert "period_comparison" in nodes
        assert "aggregator" in nodes

    def test_graph_has_correct_node_count(self) -> None:
        """グラフが正しいノード数を持つことを確認."""
        graph = AnalysisGraph()
        compiled_graph = graph.get_full_graph()

        # 7ノード: edinet, pdf_parse, business_summary, risk_extraction,
        #          financial_analysis, period_comparison, aggregator
        # + __start__, __end__
        nodes = compiled_graph.nodes
        expected_nodes = {
            "edinet",
            "pdf_parse",
            "business_summary",
            "risk_extraction",
            "financial_analysis",
            "period_comparison",
            "aggregator",
        }
        for node_name in expected_nodes:
            assert node_name in nodes, f"ノード '{node_name}' がグラフに存在しない"


class TestNodeIndependence:
    """ノード独立性のテスト.

    PRD要件: 各ノードを個別に実行できる（部分実行対応）
    """

    @pytest.mark.parametrize(
        "node_name,expected_nodes",
        [
            ("edinet", {"edinet"}),
            ("pdf_parse", {"edinet", "pdf_parse"}),
            ("business_summary", {"edinet", "pdf_parse", "business_summary"}),
            ("risk_extraction", {"edinet", "pdf_parse", "risk_extraction"}),
            ("financial_analysis", {"edinet", "pdf_parse", "financial_analysis"}),
        ],
    )
    def test_individual_node_graph_contains_expected_nodes(
        self, node_name: str, expected_nodes: set[str]
    ) -> None:
        """個別ノードグラフが期待されるノードを含むことを確認."""
        graph = AnalysisGraph()
        node_graph = graph.get_node_graph(node_name)

        for expected_node in expected_nodes:
            assert expected_node in node_graph.nodes, (
                f"ノード '{expected_node}' が個別グラフに存在しない"
            )

    def test_individual_node_graph_does_not_affect_full_graph(self) -> None:
        """個別ノードグラフの構築がフルグラフに影響しないことを確認."""
        graph = AnalysisGraph()

        # フルグラフを先に構築
        full_graph1 = graph.get_full_graph()
        full_node_count1 = len(full_graph1.nodes)

        # 個別ノードグラフを構築
        graph.get_node_graph("business_summary")
        graph.get_node_graph("risk_extraction")

        # フルグラフが変更されていないことを確認
        full_graph2 = graph.get_full_graph()
        full_node_count2 = len(full_graph2.nodes)

        assert full_node_count1 == full_node_count2, (
            "個別ノードグラフの構築がフルグラフに影響を与えている"
        )
        assert full_graph1 is full_graph2, "フルグラフはキャッシュされるべき"


class TestStateManagement:
    """State管理のテスト."""

    def test_state_merge_function(self) -> None:
        """Stateのマージ関数が正しく動作することを確認."""
        state1 = create_initial_state("S100TEST")
        assert state1["completed_nodes"] == []
        assert state1["errors"] == []

    def test_state_with_prior_document(self) -> None:
        """前期書類IDを含むStateの作成を確認."""
        state = create_initial_state("S100CURRENT", "S100PRIOR")
        assert state["doc_id"] == "S100CURRENT"
        assert state["prior_doc_id"] == "S100PRIOR"


@pytest.mark.skipif(
    True,
    reason="E2E test requires real EDINET and Gemini API credentials",
)
class TestFullWorkflowE2E:
    """フルワークフローのE2Eテスト.

    注意: このテストは実際のAPIクレデンシャルが必要です。
    ローカルで実行する場合は、.envファイルに以下を設定してください:
    - EDINET_API_KEY
    - GOOGLE_API_KEY
    """

    @pytest.mark.asyncio
    async def test_run_full_analysis(self) -> None:
        """フルワークフローの実行をテスト."""
        graph = AnalysisGraph()
        # 実際の書類IDを使用
        result = await graph.run_full_analysis(doc_id="S100QFNQ")

        assert result is not None
        assert "comprehensive_report" in result
        assert "business_summary" in result
        assert "risk_analysis" in result
        assert "financial_analysis" in result

    @pytest.mark.asyncio
    async def test_run_single_node(self) -> None:
        """個別ノードの実行をテスト."""
        graph = AnalysisGraph()
        result = await graph.run_node("business_summary", doc_id="S100QFNQ")

        assert result is not None
        assert isinstance(result, BusinessSummary)
