"""LangGraph workflows for LLM analysis.

有価証券報告書のLLM分析機能をLangGraphワークフローとして提供する。

Example:
    from company_research_agent.workflows import AnalysisGraph

    graph = AnalysisGraph()

    # 全ワークフロー実行
    result = await graph.run_full_analysis(doc_id="S100...")

    # 個別ノード実行
    summary = await graph.run_node("business_summary", doc_id="S100...")
"""

from company_research_agent.workflows.graph import AnalysisGraph, build_analysis_graph
from company_research_agent.workflows.state import AnalysisState, create_initial_state

__all__ = [
    "AnalysisGraph",
    "AnalysisState",
    "build_analysis_graph",
    "create_initial_state",
]
