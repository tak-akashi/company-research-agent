"""IR資料取得コマンド."""

from __future__ import annotations

import argparse
import logging
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from company_research_agent.cli.output import (
    print_error,
    print_info,
    print_success,
    print_warning,
)
from company_research_agent.core.config import get_config

if TYPE_CHECKING:
    from company_research_agent.schemas.ir_schemas import IRDocument

logger = logging.getLogger(__name__)


def _parse_date(date_str: str | None) -> date | None:
    """日付文字列をdateオブジェクトに変換."""
    if date_str is None:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        print_warning(f"Invalid date format: {date_str}, expected YYYY-MM-DD")
        return None


def _format_period(since: date) -> str:
    """期間を人間が読みやすい形式に変換."""
    today = date.today()
    days = (today - since).days

    if days <= 7:
        return f"直近1週間（{since.strftime('%Y/%m/%d')}以降）"
    elif days <= 14:
        return f"直近2週間（{since.strftime('%Y/%m/%d')}以降）"
    elif days <= 31:
        return f"直近1ヶ月（{since.strftime('%Y/%m/%d')}以降）"
    elif days <= 62:
        return f"直近2ヶ月（{since.strftime('%Y/%m/%d')}以降）"
    elif days <= 93:
        return f"直近3ヶ月（{since.strftime('%Y/%m/%d')}以降）"
    elif days <= 186:
        return f"直近6ヶ月（{since.strftime('%Y/%m/%d')}以降）"
    elif days <= 365:
        return f"直近1年（{since.strftime('%Y/%m/%d')}以降）"
    else:
        return f"{since.strftime('%Y/%m/%d')}以降"


async def cmd_ir_fetch(args: argparse.Namespace) -> int:
    """IR資料取得コマンドを実行.

    Args:
        args: コマンドライン引数

    Returns:
        終了コード (0: 成功, 1: エラー)
    """
    from company_research_agent.services.ir_scraper_service import IRScraperService

    # 引数の検証
    if not args.sec_code and not args.url and not args.all:
        print_error("--sec-code, --url, --all のいずれかを指定してください")
        return 1

    # サービスの初期化
    service = IRScraperService()

    # 日付の解析
    since = _parse_date(args.since)
    if since is None and args.since:
        return 1  # 日付パースエラー

    # デフォルトの期間を取得
    config = get_config()
    if since is None:
        since = date.today() - timedelta(days=config.ir_scraper.default_since_days)

    # 期間の表示用文字列を生成
    period_str = _format_period(since)

    # カテゴリのマッピング
    category_map = {
        "earnings": "earnings",
        "news": "news",
        "disclosures": "disclosures",
    }
    category = category_map.get(args.category) if args.category else None

    try:
        if args.all:
            # 全登録企業の処理
            print_info(f"全登録企業の{period_str}のIR資料を取得します...")
            results = await service.fetch_all_registered(
                category=category,
                since=since,
                force=args.force,
            )
            _print_all_results(results, period_str)

        elif args.url:
            # アドホック探索
            print_info(f"{period_str}のIR資料を探索中: {args.url}")
            documents = await service.explore_ir_page(
                url=args.url,
                since=since,
                force=args.force,
                with_summary=True,
            )
            _print_documents(documents, "アドホック探索", period_str)

        else:
            # 指定企業の処理
            print_info(f"{period_str}のIR資料を取得中: {args.sec_code}")
            documents = await service.fetch_ir_documents(
                sec_code=args.sec_code,
                category=category,
                since=since,
                force=args.force,
                with_summary=True,
            )
            _print_documents(documents, args.sec_code, period_str)

        return 0

    except Exception as e:
        logger.exception("IR資料取得中にエラーが発生しました")
        print_error(f"エラー: {e}")
        return 1


def _print_documents(
    documents: list[IRDocument],
    source: str,
    period_str: str = "",
) -> None:
    """取得したドキュメントを表示."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    if not documents:
        print_warning(f"{source}: {period_str}の資料が見つかりませんでした")
        return

    # 統計
    downloaded = sum(1 for d in documents if not d.is_skipped)
    skipped = sum(1 for d in documents if d.is_skipped)

    print_success(f"{source}: {period_str}の資料を{len(documents)}件取得しました")
    if skipped > 0:
        print_info(f"  - 新規ダウンロード: {downloaded}件, スキップ: {skipped}件")

    # テーブル表示
    table = Table(title=f"IR資料一覧 ({source})")
    table.add_column("タイトル", style="cyan", max_width=40)
    table.add_column("カテゴリ", style="green")
    table.add_column("公開日", style="yellow")
    table.add_column("状態", style="magenta")

    category_names = {
        "earnings": "決算",
        "news": "ニュース",
        "disclosures": "開示",
    }

    for doc in documents[:20]:  # 最大20件表示
        # 状態の判定
        if doc.is_skipped:
            status = "スキップ"
        elif doc.file_path is not None:
            status = "ダウンロード済"
        elif doc.summary is not None:
            status = "要約済"  # HTMLページ
        else:
            status = "未処理"
        pub_date = doc.published_date.strftime("%Y-%m-%d") if doc.published_date else "-"
        table.add_row(
            doc.title[:40],
            category_names.get(doc.category, doc.category),
            pub_date,
            status,
        )

    console.print(table)

    # 要約があれば表示
    for doc in documents[:5]:
        if doc.summary and not doc.is_skipped:
            console.print(f"\n[bold]{doc.title}[/bold]")
            console.print(f"  [dim]要約:[/dim] {doc.summary.overview}")
            if doc.summary.impact_points:
                console.print("  [dim]株価影響ポイント:[/dim]")
                for point in doc.summary.impact_points:
                    label_color = {
                        "bullish": "green",
                        "bearish": "red",
                        "warning": "yellow",
                    }.get(point.label, "white")
                    msg = f"    [{label_color}][{point.label}][/{label_color}]"
                    console.print(f"{msg} {point.content}")


def _print_all_results(
    results: dict[str, list[IRDocument]],
    period_str: str = "",
) -> None:
    """全企業の結果を表示."""
    from rich.console import Console

    console = Console()

    total_docs = sum(len(docs) for docs in results.values())
    total_companies = len(results)
    successful = sum(1 for docs in results.values() if docs)

    print_success(f"全{total_companies}社の処理が完了しました（{period_str}）")
    print_info(f"  - 成功: {successful}社, 合計: {total_docs}件の資料")

    for sec_code, documents in results.items():
        if documents:
            console.print(f"\n[bold]証券コード: {sec_code}[/bold]")
            _print_documents(documents, sec_code, period_str)
