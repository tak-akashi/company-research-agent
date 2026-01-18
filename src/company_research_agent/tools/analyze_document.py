"""書類分析ツール."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from langchain_core.tools import tool

from company_research_agent.workflows import AnalysisGraph

logger = logging.getLogger(__name__)


@tool
async def analyze_document(
    doc_id: Annotated[str, "書類ID（S100XXXX形式）"],
    prior_doc_id: Annotated[str | None, "前期書類ID（前期比較を行う場合）"] = None,
    filer_name: Annotated[str | None, "企業名（search_documentsで取得）"] = None,
    doc_description: Annotated[
        str | None, "書類タイトル（例: 有価証券報告書－第45期(2024/04/01－2025/03/31)）"
    ] = None,
    period_start: Annotated[str | None, "対象期間開始日（YYYY-MM-DD形式）"] = None,
    period_end: Annotated[str | None, "対象期間終了日（YYYY-MM-DD形式）"] = None,
) -> dict[str, Any]:
    """書類を分析し、統合レポートを生成する。

    既存のAnalysisGraphを利用して、有価証券報告書の詳細分析を行う。
    事業要約、リスク分析、財務分析、前期比較（オプション）を含む
    統合レポートを生成する。

    **重要**: search_documentsで取得した書類のメタデータ（filer_name, doc_description,
    period_start, period_end）を渡すと、結果に書類のメタ情報が含まれる。

    Args:
        doc_id: 分析対象の書類ID（S100XXXX形式）
        prior_doc_id: 前期書類のID（前期比較を行う場合に指定）
        filer_name: 企業名（search_documentsの結果から取得）
        doc_description: 書類タイトル（search_documentsの結果から取得）
        period_start: 対象期間開始日（search_documentsの結果から取得）
        period_end: 対象期間終了日（search_documentsの結果から取得）

    Returns:
        事業概要、リスク分析、財務分析を含む統合レポートとメタデータ

    Example:
        >>> result = await analyze_document(
        ...     doc_id="S100ABCD",
        ...     filer_name="ソフトバンクグループ株式会社",
        ...     doc_description="有価証券報告書－第45期(2024/04/01－2025/03/31)",
        ... )
        >>> print(result["report"].executive_summary)
        >>> print(result["metadata"]["filer_name"])
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

    return {
        "report": comprehensive_report,
        "metadata": {
            "doc_id": doc_id,
            "filer_name": filer_name,
            "doc_description": doc_description,
            "period_start": period_start,
            "period_end": period_end,
        },
    }
