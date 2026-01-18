"""書類比較ツール."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool

from company_research_agent.llm.factory import get_default_provider
from company_research_agent.parsers.pdf_parser import PDFParser
from company_research_agent.prompts.compare_documents import COMPARE_DOCUMENTS_PROMPT
from company_research_agent.schemas.query_schemas import ComparisonReport
from company_research_agent.tools.download_document import download_document

logger = logging.getLogger(__name__)


@tool
async def compare_documents(
    doc_ids: Annotated[list[str], "比較する書類IDのリスト（2つ以上）"],
    aspects: Annotated[
        list[str] | None,
        "比較観点（例: 事業内容、財務状況、リスク）",
    ] = None,
) -> ComparisonReport:
    """複数の書類を比較分析する。

    PDFParserで各書類をマークダウン化し、LLMで比較分析を行う。
    事業内容、財務状況、リスクなどの観点で比較レポートを生成する。

    Args:
        doc_ids: 比較する書類IDのリスト（2つ以上）
        aspects: 比較観点のリスト（省略時は「事業内容、財務状況、リスク」）

    Returns:
        比較分析レポート

    Example:
        >>> report = await compare_documents(
        ...     doc_ids=["S100ABCD", "S100EFGH"],
        ...     aspects=["事業内容", "財務状況"],
        ... )
        >>> print(report.summary)
    """
    logger.info(f"Comparing documents: {doc_ids}")

    if len(doc_ids) < 2:
        raise ValueError("At least 2 document IDs are required for comparison")

    # デフォルトの比較観点
    if aspects is None:
        aspects = ["事業内容", "財務状況", "リスク"]

    # 各書類をダウンロードしてマークダウン化
    parser = PDFParser()
    document_contents: list[str] = []

    for doc_id in doc_ids:
        # ダウンロード
        pdf_path_str = await download_document.ainvoke({"doc_id": doc_id})
        pdf_path = Path(pdf_path_str)

        # マークダウン化
        result = parser.to_markdown(pdf_path)
        document_contents.append(f"## 書類: {doc_id}\n\n{result.text}")

    # プロンプト構築
    documents_text = "\n\n---\n\n".join(document_contents)
    aspects_text = ", ".join(aspects)

    prompt = COMPARE_DOCUMENTS_PROMPT.format(
        documents=documents_text,
        aspects=aspects_text,
    )

    # LLMで比較分析
    llm = get_default_provider()
    report = await llm.ainvoke_structured(prompt, ComparisonReport)

    # doc_idsとaspectsを設定
    report.documents = doc_ids
    report.aspects = aspects

    logger.info("Comparison completed successfully")
    return report
