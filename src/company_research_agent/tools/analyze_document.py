"""書類分析ツール."""

from __future__ import annotations

import logging
from typing import Annotated

from langchain_core.tools import tool

from company_research_agent.schemas.llm_analysis import ComprehensiveReport
from company_research_agent.workflows import AnalysisGraph

logger = logging.getLogger(__name__)


@tool
async def analyze_document(
    doc_id: Annotated[str, "書類ID（S100XXXX形式）"],
    prior_doc_id: Annotated[str | None, "前期書類ID（前期比較を行う場合）"] = None,
) -> ComprehensiveReport:
    """書類を分析し、統合レポートを生成する。

    既存のAnalysisGraphを利用して、有価証券報告書の詳細分析を行う。
    事業要約、リスク分析、財務分析、前期比較（オプション）を含む
    統合レポートを生成する。

    Args:
        doc_id: 分析対象の書類ID（S100XXXX形式）
        prior_doc_id: 前期書類のID（前期比較を行う場合に指定）

    Returns:
        事業概要、リスク分析、財務分析を含む統合レポート

    Example:
        >>> report = await analyze_document("S100ABCD")
        >>> print(report.executive_summary)
    """
    logger.info(f"Analyzing document: {doc_id}, prior: {prior_doc_id}")

    graph = AnalysisGraph()
    result = await graph.run_full_analysis(doc_id, prior_doc_id)

    comprehensive_report = result.get("comprehensive_report")
    if comprehensive_report is None:
        errors = result.get("errors", [])
        error_msg = "; ".join(errors) if errors else "Unknown error"
        raise ValueError(f"Analysis failed: {error_msg}")

    logger.info("Analysis completed successfully")
    return comprehensive_report
