"""企業検索ツール."""

from __future__ import annotations

import logging
from typing import Annotated

from langchain_core.tools import tool

from company_research_agent.clients.edinet_code_list_client import EDINETCodeListClient
from company_research_agent.schemas.query_schemas import CompanyCandidate

logger = logging.getLogger(__name__)


@tool
async def search_company(
    query: Annotated[str, "検索クエリ（企業名、EDINETコード、証券コード）"],
    limit: Annotated[int, "返却する候補の最大数"] = 10,
) -> list[CompanyCandidate]:
    """企業名で検索し、類似度スコア付き候補リストを返す。

    企業名、カナ名、英語名であいまい検索を行い、類似度スコアが高い順に
    候補を返す。EDINETコードまたは証券コードが指定された場合は
    完全一致で検索する。

    Args:
        query: 検索クエリ（企業名、EDINETコード、証券コード）
        limit: 返却する候補の最大数（デフォルト: 10）

    Returns:
        類似度スコア付きの企業候補リスト

    Example:
        >>> candidates = await search_company("トヨタ")
        >>> for c in candidates:
        ...     print(f"{c.company.company_name} - {c.similarity_score}")
    """
    logger.info(f"Searching companies with query: {query}")

    client = EDINETCodeListClient()
    candidates = await client.search_companies(query, limit)

    logger.info(f"Found {len(candidates)} candidates")
    return candidates
