"""書類検索ツール."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Annotated, Any

from langchain_core.tools import tool

from company_research_agent.clients.edinet_client import EDINETClient
from company_research_agent.core.config import EDINETConfig
from company_research_agent.core.progress import print_info, print_status, print_success
from company_research_agent.schemas.document_filter import DocumentFilter, SearchOrder
from company_research_agent.services.edinet_document_service import EDINETDocumentService

logger = logging.getLogger(__name__)


def _parse_date(date_str: str | None) -> date | None:
    """日付文字列をdateオブジェクトに変換.

    Args:
        date_str: 日付文字列（YYYY-MM-DD形式）またはNone

    Returns:
        dateオブジェクトまたはNone
    """
    if date_str is None:
        return None

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        logger.warning(f"Invalid date format: {date_str}, expected YYYY-MM-DD")
        return None


@tool
async def search_documents(
    edinet_code: Annotated[str, "企業のEDINETコード（例: E02144）"],
    doc_type_codes: Annotated[
        list[str] | None,
        "書類種別コード（120=有価証券報告書, 140=四半期報告書, 160=臨時報告書等）",
    ] = None,
    start_date: Annotated[
        str | None,
        "検索開始日（YYYY-MM-DD形式）",
    ] = None,
    end_date: Annotated[
        str | None,
        "検索終了日（YYYY-MM-DD形式）",
    ] = None,
    search_order: Annotated[
        str,
        "検索順序（newest_first=新しい順, oldest_first=古い順）",
    ] = "newest_first",
    max_documents: Annotated[
        int | None,
        "取得する書類の最大数（指定すると早期終了する）",
    ] = None,
) -> list[dict[str, Any]]:
    """EDINET書類を検索する。

    指定された企業のEDINETコードに基づいて書類を検索し、
    書類種別や日付範囲でフィルタリングする。

    Args:
        edinet_code: 企業のEDINETコード（例: E02144）
        doc_type_codes: 書類種別コードのリスト（省略時は全種別）
            - 120: 有価証券報告書
            - 140: 四半期報告書
            - 160: 臨時報告書
        start_date: 検索開始日（YYYY-MM-DD形式、省略時は終了日と同じ）
        end_date: 検索終了日（YYYY-MM-DD形式、省略時は今日）
        search_order: 検索順序
            - "newest_first": 最新の書類から検索（デフォルト）
            - "oldest_first": 古い書類から検索
        max_documents: 取得する書類の最大数（省略時は全件取得）

    Returns:
        書類メタデータのリスト（submit_date_timeの降順でソート済み）

    Example:
        >>> # 最新の有報を1件だけ取得
        >>> docs = await search_documents(
        ...     edinet_code="E02144",
        ...     doc_type_codes=["120"],
        ...     start_date="2020-01-01",
        ...     search_order="newest_first",
        ...     max_documents=1,
        ... )
    """
    # Parse search_order string to enum
    order = SearchOrder.NEWEST_FIRST if search_order == "newest_first" else SearchOrder.OLDEST_FIRST

    print_status(f"EDINET書類を検索中: {edinet_code} ({search_order})")
    logger.info(
        f"Searching documents for {edinet_code}, "
        f"doc_types={doc_type_codes}, start={start_date}, end={end_date}, "
        f"search_order={search_order}, max_documents={max_documents}"
    )

    doc_filter = DocumentFilter(
        edinet_code=edinet_code,
        doc_type_codes=doc_type_codes,
        start_date=_parse_date(start_date),
        end_date=_parse_date(end_date),
        search_order=order,
        max_documents=max_documents,
    )

    config = EDINETConfig()  # type: ignore[call-arg]
    async with EDINETClient(config) as client:
        service = EDINETDocumentService(client)
        documents = await service.search_documents(doc_filter)

    print_success(f"検索完了: {len(documents)}件の書類が見つかりました")
    if documents:
        print_info(f"最新の書類: {documents[0].doc_description or documents[0].doc_id}")
    logger.info(f"Found {len(documents)} documents")

    # Pydanticモデルを辞書にシリアライズ（LangChainのToolMessageでJSON化できるように）
    return [doc.model_dump() for doc in documents]
