"""LangGraph workflow state definition.

LLM分析ワークフローの状態（State）を定義する。
各ノードはこのStateを受け取り、更新された部分のdictを返す。
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from company_research_agent.schemas.llm_analysis import (
    BusinessSummary,
    ComprehensiveReport,
    FinancialAnalysis,
    PeriodComparison,
    RiskAnalysis,
)


def _merge_lists(left: list[str], right: list[str]) -> list[str]:
    """リストをマージする（重複を避けて追加）."""
    result = left.copy()
    for item in right:
        if item not in result:
            result.append(item)
    return result


class AnalysisState(TypedDict, total=False):
    """LLM分析ワークフローの状態.

    LangGraphのStateとして使用される。各ノードはこのStateを受け取り、
    更新したいキーのみを含むdictを返す。

    Attributes:
        doc_id: 分析対象のEDINET書類ID（必須）
        prior_doc_id: 前期書類のEDINET書類ID（前期比較時のみ）
        pdf_path: ダウンロードしたPDFファイルのパス
        prior_pdf_path: 前期PDFファイルのパス
        markdown_content: PDFから抽出したマークダウンテキスト
        prior_markdown_content: 前期PDFから抽出したマークダウンテキスト
        business_summary: 事業要約の分析結果
        risk_analysis: リスク分析の結果
        financial_analysis: 財務分析の結果
        period_comparison: 前期比較の結果
        comprehensive_report: 統合レポート
        errors: 発生したエラーのリスト
        completed_nodes: 完了したノードのリスト
    """

    # 入力
    doc_id: str
    prior_doc_id: str | None

    # 中間結果（PDFパス）
    pdf_path: str | None
    prior_pdf_path: str | None

    # 中間結果（マークダウン）
    markdown_content: str | None
    prior_markdown_content: str | None

    # 個別出力（各ノードの結果）
    business_summary: BusinessSummary | None
    risk_analysis: RiskAnalysis | None
    financial_analysis: FinancialAnalysis | None
    period_comparison: PeriodComparison | None

    # 統合出力
    comprehensive_report: ComprehensiveReport | None

    # メタデータ（Annotatedでreducerを指定）
    errors: Annotated[list[str], _merge_lists]
    completed_nodes: Annotated[list[str], _merge_lists]


def create_initial_state(
    doc_id: str,
    prior_doc_id: str | None = None,
) -> AnalysisState:
    """初期状態を作成する.

    Args:
        doc_id: 分析対象のEDINET書類ID
        prior_doc_id: 前期書類のEDINET書類ID（オプション）

    Returns:
        初期化されたAnalysisState
    """
    return AnalysisState(
        doc_id=doc_id,
        prior_doc_id=prior_doc_id,
        pdf_path=None,
        prior_pdf_path=None,
        markdown_content=None,
        prior_markdown_content=None,
        business_summary=None,
        risk_analysis=None,
        financial_analysis=None,
        period_comparison=None,
        comprehensive_report=None,
        errors=[],
        completed_nodes=[],
    )
