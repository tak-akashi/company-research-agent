"""IR資料取得ツール."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Annotated, Any

from langchain_core.tools import tool

from company_research_agent.core.config import get_config
from company_research_agent.core.progress import print_status, print_success

logger = logging.getLogger(__name__)

# 設定からデフォルト値を取得
_config = get_config()
_DEFAULT_SINCE_DAYS = _config.ir_scraper.default_since_days


def _format_period_days(days: int) -> str:
    """日数を人間が読みやすい期間表現に変換."""
    if days <= 7:
        return "直近1週間"
    elif days <= 14:
        return "直近2週間"
    elif days <= 31:
        return "直近1ヶ月"
    elif days <= 62:
        return "直近2ヶ月"
    elif days <= 93:
        return "直近3ヶ月"
    elif days <= 186:
        return "直近6ヶ月"
    elif days <= 365:
        return "直近1年"
    else:
        return f"過去{days}日間"


@tool
async def fetch_ir_documents(
    sec_code: Annotated[str, "証券コード（5桁）"],
    category: Annotated[
        str | None,
        "カテゴリ（earnings=決算関連, news=事業ニュース, disclosures=適時開示）",
    ] = None,
    since_days: Annotated[int, "過去何日分を取得するか"] = _DEFAULT_SINCE_DAYS,
    with_summary: Annotated[
        bool,
        "要約を生成するか（True=要約あり、False=ダウンロードのみ）",
    ] = False,
) -> dict[str, Any]:
    """登録企業のIR資料をダウンロードする。

    企業のIRページから決算説明会資料、適時開示、事業ニュースを取得する。
    with_summary=Trueの場合は、LLMで要約して株価影響ポイントも抽出する。

    Args:
        sec_code: 証券コード（5桁、例: "72030"）
        category: 取得するカテゴリ
            - "earnings": 決算関連（決算説明会資料など）
            - "news": 事業ニュース（新製品発表、大型受注など）
            - "disclosures": 適時開示（業績修正、M&Aなど）
        since_days: 過去何日分を取得するか（デフォルト: 設定値）
        with_summary: 要約を生成するか（デフォルト: False = ダウンロードのみ）

    Returns:
        IR資料情報の辞書:
        - period: 期間の表示文字列（例: "直近1ヶ月"）
        - since_date: 検索開始日（YYYY-MM-DD形式）
        - count: 取得件数
        - documents: IR資料情報のリスト（with_summary=Trueの場合は要約を含む）

    Example:
        >>> # トヨタの決算関連資料をダウンロードのみ
        >>> docs = await fetch_ir_documents(
        ...     sec_code="72030",
        ...     category="earnings",
        ... )
        >>> # トヨタの決算関連資料をダウンロード＋要約
        >>> docs = await fetch_ir_documents(
        ...     sec_code="72030",
        ...     category="earnings",
        ...     with_summary=True,
        ... )
    """
    from company_research_agent.services.ir_scraper_service import IRScraperService

    # 期間の表示用文字列を生成
    period_str = _format_period_days(since_days)

    action = "取得・要約中" if with_summary else "取得中"
    print_status(f"{period_str}のIR資料を{action}: {sec_code}")
    logger.info(
        f"Fetching IR documents for {sec_code}, "
        f"category={category}, since_days={since_days}, with_summary={with_summary}"
    )

    since = date.today() - timedelta(days=since_days)

    service = IRScraperService()
    documents = await service.fetch_ir_documents(
        sec_code=sec_code,
        category=category,
        since=since,
        force=False,
        with_summary=with_summary,
    )

    print_success(f"{period_str}のIR資料を{len(documents)}件取得しました")
    logger.info(f"Fetched {len(documents)} IR documents for {sec_code}")

    # 辞書形式に変換
    results = []
    for doc in documents:
        result: dict[str, Any] = {
            "title": doc.title,
            "url": doc.url,
            "category": doc.category,
            "published_date": doc.published_date.isoformat() if doc.published_date else None,
            "is_skipped": doc.is_skipped,
            "file_path": str(doc.file_path) if doc.file_path else None,
            "is_downloaded": doc.file_path is not None,
        }

        if doc.summary:
            result["summary"] = {
                "overview": doc.summary.overview,
                "impact_points": [
                    {"label": p.label, "content": p.content} for p in doc.summary.impact_points
                ],
            }

        results.append(result)

    # メタ情報を先頭に追加
    return {
        "period": period_str,
        "since_date": since.isoformat(),
        "count": len(results),
        "documents": results,
    }


@tool
async def fetch_ir_news(
    sec_code: Annotated[str, "証券コード（5桁）"],
    limit: Annotated[int, "取得件数"] = 10,
    since_days: Annotated[int, "過去何日分を取得するか"] = _DEFAULT_SINCE_DAYS,
) -> list[dict[str, Any]]:
    """登録企業のIRニュース一覧を取得する。

    企業のIRページから事業ニュース（新製品発表、大型受注、経営陣異動など）を
    取得する。要約は含まない（一覧取得のみ）。

    Args:
        sec_code: 証券コード（5桁、例: "72030"）
        limit: 取得する最大件数（デフォルト: 10件）
        since_days: 過去何日分を取得するか（デフォルト: 設定値）

    Returns:
        ニュース情報のリスト（タイトル、URL、公開日を含む）

    Example:
        >>> # ソニーの最新ニュースを5件取得
        >>> news = await fetch_ir_news(
        ...     sec_code="67580",
        ...     limit=5,
        ...     since_days=30,
        ... )
    """
    from company_research_agent.services.ir_scraper_service import IRScraperService

    print_status(f"IRニュースを取得中: {sec_code}")
    logger.info(f"Fetching IR news for {sec_code}, limit={limit}, since_days={since_days}")

    since = date.today() - timedelta(days=since_days)

    service = IRScraperService()
    documents = await service.fetch_ir_documents(
        sec_code=sec_code,
        category="news",
        since=since,
        force=False,
        with_summary=False,  # ニュース一覧なので要約は不要
    )

    # limitで制限
    documents = documents[:limit]

    print_success(f"IRニュースを{len(documents)}件取得しました")
    logger.info(f"Fetched {len(documents)} IR news items for {sec_code}")

    return [
        {
            "title": doc.title,
            "url": doc.url,
            "published_date": doc.published_date.isoformat() if doc.published_date else None,
        }
        for doc in documents
    ]


@tool
async def explore_ir_page(
    url: Annotated[str, "IRページのURL"],
    since_days: Annotated[int, "過去何日分を取得するか"] = _DEFAULT_SINCE_DAYS,
) -> list[dict[str, Any]]:
    """未登録企業のIRページを解析してIR資料を探す。

    LLMを使用してIRページの構造を動的に解析し、
    PDF資料へのリンクを抽出する。テンプレートが登録されていない
    企業のIR情報を取得する際に使用する。

    Args:
        url: IRページのURL（例: "https://example.com/ir/"）
        since_days: 過去何日分を取得するか（デフォルト: 設定値）

    Returns:
        IR資料情報のリスト（タイトル、URL、カテゴリ、要約を含む）

    Example:
        >>> # 未登録企業のIRページを探索
        >>> docs = await explore_ir_page(
        ...     url="https://example.com/ir/",
        ...     since_days=60,
        ... )
    """
    from company_research_agent.services.ir_scraper_service import IRScraperService

    print_status(f"IRページを探索中: {url}")
    logger.info(f"Exploring IR page: {url}, since_days={since_days}")

    since = date.today() - timedelta(days=since_days)

    service = IRScraperService()
    documents = await service.explore_ir_page(
        url=url,
        since=since,
        force=False,
        with_summary=True,
    )

    print_success(f"IR資料を{len(documents)}件発見しました")
    logger.info(f"Discovered {len(documents)} IR documents from {url}")

    results = []
    for doc in documents:
        result: dict[str, Any] = {
            "title": doc.title,
            "url": doc.url,
            "category": doc.category,
            "published_date": doc.published_date.isoformat() if doc.published_date else None,
            "file_path": str(doc.file_path) if doc.file_path else None,
            "is_downloaded": doc.file_path is not None,
        }

        if doc.summary:
            result["summary"] = {
                "overview": doc.summary.overview,
                "impact_points": [
                    {"label": p.label, "content": p.content} for p in doc.summary.impact_points
                ],
            }

        results.append(result)

    return results
