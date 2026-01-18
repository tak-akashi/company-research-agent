"""書類要約ツール."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool

from company_research_agent.llm.factory import get_default_provider
from company_research_agent.parsers.pdf_parser import PDFParser
from company_research_agent.prompts.summarize_document import SUMMARIZE_DOCUMENT_PROMPT
from company_research_agent.schemas.query_schemas import Summary
from company_research_agent.tools.download_document import download_document

logger = logging.getLogger(__name__)


@tool
async def summarize_document(
    doc_id: Annotated[str, "書類ID（S100XXXX形式）"],
    focus: Annotated[
        str | None,
        "要約の焦点（例: 事業概要、リスク、財務）",
    ] = None,
    sec_code: Annotated[str | None, "証券コード（5桁）"] = None,
    filer_name: Annotated[str | None, "企業名"] = None,
    doc_type_code: Annotated[str | None, "書類種別コード（120=有報等）"] = None,
    period_end: Annotated[str | None, "決算期末日（YYYY-MM-DD形式）"] = None,
) -> Summary:
    """書類を要約する。

    PDFParserで書類をマークダウン化し、LLMで要約を行う。
    焦点を指定することで、特定の観点に重点を置いた要約を生成する。

    Args:
        doc_id: 書類ID（S100XXXX形式）
        focus: 要約の焦点（省略時は「全体」）
        sec_code: 証券コード（5桁、例: "72030"）
        filer_name: 企業名（例: "トヨタ自動車株式会社"）
        doc_type_code: 書類種別コード（例: "120" = 有価証券報告書）
        period_end: 決算期末日（YYYY-MM-DD形式）

    Returns:
        要約レポート

    Example:
        >>> summary = await summarize_document(
        ...     doc_id="S100ABCD",
        ...     focus="事業リスク",
        ...     sec_code="72030",
        ...     filer_name="トヨタ自動車株式会社",
        ...     doc_type_code="120",
        ...     period_end="2025-03-31",
        ... )
        >>> print(summary.summary_text)
    """
    logger.info(f"Summarizing document: {doc_id}, focus: {focus}")

    # ダウンロード（メタデータ付き）
    pdf_path_str = await download_document.ainvoke(
        {
            "doc_id": doc_id,
            "sec_code": sec_code,
            "filer_name": filer_name,
            "doc_type_code": doc_type_code,
            "period_end": period_end,
        }
    )
    pdf_path = Path(pdf_path_str)

    # マークダウン化
    parser = PDFParser()
    result = parser.to_markdown(pdf_path)

    # プロンプト構築
    prompt = SUMMARIZE_DOCUMENT_PROMPT.format(
        content=result.text,
        focus=focus or "全体",
    )

    # LLMで要約
    llm = get_default_provider()
    summary = await llm.ainvoke_structured(prompt, Summary)

    # doc_idとfocusを設定
    summary.doc_id = doc_id
    summary.focus = focus

    logger.info("Summary completed successfully")
    return summary
