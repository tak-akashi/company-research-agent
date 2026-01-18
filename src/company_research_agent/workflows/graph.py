"""LangGraph analysis workflow graph.

有価証券報告書のLLM分析ワークフローを構築・実行する。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from company_research_agent.workflows.state import AnalysisState, create_initial_state

if TYPE_CHECKING:
    from company_research_agent.llm.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class AnalysisGraph:
    """LLM分析ワークフローのグラフ.

    有価証券報告書のLLM分析を実行するLangGraphワークフロー。
    各ノードを順次または並列に実行し、分析結果を統合する。

    Example:
        # 環境変数で自動設定
        graph = AnalysisGraph()
        result = await graph.run_full_analysis(doc_id="S100...")

        # 明示的にプロバイダーを指定
        from company_research_agent.llm import create_llm_provider
        provider = create_llm_provider()
        graph = AnalysisGraph(llm_provider=provider)
        result = await graph.run_full_analysis(doc_id="S100...")

        # 個別ノード実行（事業要約のみ）
        summary = await graph.run_node("business_summary", doc_id="S100...")
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider | None = None,
    ) -> None:
        """グラフを初期化する.

        Args:
            llm_provider: LLMプロバイダー。Noneの場合は環境変数から自動設定。
        """
        self._llm_provider = llm_provider
        self._full_graph: CompiledStateGraph[Any] | None = None
        self._node_graphs: dict[str, CompiledStateGraph[Any]] = {}

    def _build_full_graph(self) -> CompiledStateGraph[Any]:
        """全ワークフローのグラフを構築する.

        Returns:
            コンパイル済みのStateGraph
        """
        from company_research_agent.workflows.nodes.aggregator_node import (
            AggregatorNode,
        )
        from company_research_agent.workflows.nodes.business_summary_node import (
            BusinessSummaryNode,
        )
        from company_research_agent.workflows.nodes.edinet_node import EDINETNode
        from company_research_agent.workflows.nodes.financial_analysis_node import (
            FinancialAnalysisNode,
        )
        from company_research_agent.workflows.nodes.pdf_parse_node import PDFParseNode
        from company_research_agent.workflows.nodes.period_comparison_node import (
            PeriodComparisonNode,
        )
        from company_research_agent.workflows.nodes.risk_extraction_node import (
            RiskExtractionNode,
        )

        graph = StateGraph(AnalysisState)

        # ノードインスタンス作成（LLM分析ノードにはllm_providerを注入）
        edinet_node = EDINETNode()
        pdf_parse_node = PDFParseNode()
        business_summary_node = BusinessSummaryNode(llm_provider=self._llm_provider)
        risk_extraction_node = RiskExtractionNode(llm_provider=self._llm_provider)
        financial_analysis_node = FinancialAnalysisNode(llm_provider=self._llm_provider)
        period_comparison_node = PeriodComparisonNode(llm_provider=self._llm_provider)
        aggregator_node = AggregatorNode(llm_provider=self._llm_provider)

        # ノード追加（各ノードは __call__ メソッドで callable）
        graph.add_node("edinet", edinet_node)
        graph.add_node("pdf_parse", pdf_parse_node)
        graph.add_node("business_summary", business_summary_node)
        graph.add_node("risk_extraction", risk_extraction_node)
        graph.add_node("financial_analysis", financial_analysis_node)
        graph.add_node("period_comparison", period_comparison_node)
        graph.add_node("aggregator", aggregator_node)

        # エッジ追加（順次処理）
        graph.add_edge("edinet", "pdf_parse")

        # 並列処理の分岐（pdf_parse後に3つのノードへ）
        graph.add_edge("pdf_parse", "business_summary")
        graph.add_edge("pdf_parse", "risk_extraction")
        graph.add_edge("pdf_parse", "financial_analysis")

        # 並列処理の合流（3つのノードからperiod_comparisonへ）
        graph.add_edge("business_summary", "period_comparison")
        graph.add_edge("risk_extraction", "period_comparison")
        graph.add_edge("financial_analysis", "period_comparison")

        # 最終処理
        graph.add_edge("period_comparison", "aggregator")
        graph.add_edge("aggregator", END)

        # エントリーポイント
        graph.set_entry_point("edinet")

        return graph.compile()

    def _build_node_graph(self, node_name: str) -> CompiledStateGraph[Any]:
        """特定ノードまでのグラフを構築する.

        Args:
            node_name: 実行するノード名

        Returns:
            コンパイル済みのStateGraph
        """
        from company_research_agent.workflows.nodes.business_summary_node import (
            BusinessSummaryNode,
        )
        from company_research_agent.workflows.nodes.edinet_node import EDINETNode
        from company_research_agent.workflows.nodes.financial_analysis_node import (
            FinancialAnalysisNode,
        )
        from company_research_agent.workflows.nodes.pdf_parse_node import PDFParseNode
        from company_research_agent.workflows.nodes.risk_extraction_node import (
            RiskExtractionNode,
        )

        graph = StateGraph(AnalysisState)

        # 共通の前処理ノード
        edinet_node = EDINETNode()
        pdf_parse_node = PDFParseNode()

        graph.add_node("edinet", edinet_node)
        graph.add_node("pdf_parse", pdf_parse_node)
        graph.add_edge("edinet", "pdf_parse")

        # ターゲットノードを追加（LLM分析ノードにはllm_providerを注入）
        target_nodes = {
            "business_summary": BusinessSummaryNode,
            "risk_extraction": RiskExtractionNode,
            "financial_analysis": FinancialAnalysisNode,
        }

        if node_name in target_nodes:
            target_node = target_nodes[node_name](llm_provider=self._llm_provider)
            graph.add_node(node_name, target_node)  # type: ignore[call-overload]
            graph.add_edge("pdf_parse", node_name)
            graph.add_edge(node_name, END)
        elif node_name == "pdf_parse":
            graph.add_edge("pdf_parse", END)
        elif node_name == "edinet":
            graph.add_edge("edinet", END)
            graph.set_entry_point("edinet")
            return graph.compile()
        else:
            raise ValueError(f"Unknown node name: {node_name}")

        graph.set_entry_point("edinet")
        return graph.compile()

    def get_full_graph(self) -> CompiledStateGraph[Any]:
        """全ワークフローのグラフを取得する.

        Returns:
            コンパイル済みのStateGraph
        """
        if self._full_graph is None:
            self._full_graph = self._build_full_graph()
        return self._full_graph

    def get_node_graph(self, node_name: str) -> CompiledStateGraph[Any]:
        """特定ノードまでのグラフを取得する.

        Args:
            node_name: 実行するノード名

        Returns:
            コンパイル済みのStateGraph
        """
        if node_name not in self._node_graphs:
            self._node_graphs[node_name] = self._build_node_graph(node_name)
        return self._node_graphs[node_name]

    async def run_full_analysis(
        self,
        doc_id: str,
        prior_doc_id: str | None = None,
    ) -> AnalysisState:
        """全ワークフローを実行する.

        Args:
            doc_id: 分析対象のEDINET書類ID
            prior_doc_id: 前期書類のEDINET書類ID（オプション）

        Returns:
            最終状態（全ての分析結果を含む）
        """
        logger.info(f"Starting full analysis for doc_id={doc_id}")
        graph = self.get_full_graph()
        initial_state = create_initial_state(doc_id, prior_doc_id)

        result = await graph.ainvoke(initial_state)

        if result.get("errors"):
            logger.warning(f"Analysis completed with errors: {result['errors']}")
        else:
            logger.info("Analysis completed successfully")

        return cast(AnalysisState, result)

    async def run_node(
        self,
        node_name: str,
        doc_id: str,
        prior_doc_id: str | None = None,
    ) -> Any:
        """特定のノードまで実行する.

        Args:
            node_name: 実行するノード名
            doc_id: 分析対象のEDINET書類ID
            prior_doc_id: 前期書類のEDINET書類ID（オプション）

        Returns:
            ノードの出力（ノードに応じた型）
        """
        logger.info(f"Running node '{node_name}' for doc_id={doc_id}")
        graph = self.get_node_graph(node_name)
        initial_state = create_initial_state(doc_id, prior_doc_id)

        result = await graph.ainvoke(initial_state)

        if result.get("errors"):
            logger.warning(f"Node execution completed with errors: {result['errors']}")

        # ノード名に対応する結果を返す
        node_to_field = {
            "edinet": "pdf_path",
            "pdf_parse": "markdown_content",
            "business_summary": "business_summary",
            "risk_extraction": "risk_analysis",
            "financial_analysis": "financial_analysis",
        }

        field = node_to_field.get(node_name)
        if field:
            return result.get(field)
        return result


def build_analysis_graph() -> CompiledStateGraph[Any]:
    """分析ワークフローのグラフを構築する.

    Returns:
        コンパイル済みのStateGraph
    """
    graph = AnalysisGraph()
    return graph.get_full_graph()
