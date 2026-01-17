#!/usr/bin/env python3
"""EDINET API動作確認スクリプト.

使用方法:
    # スクリプト実行（.envファイルからAPIキーを自動読み込み）
    uv run python scripts/test_edinet_api.py

    # 特定の日付を指定
    uv run python scripts/test_edinet_api.py --date 2024-06-28

    # 期間を指定して検索
    uv run python scripts/test_edinet_api.py --start-date 2024-06-01 --end-date 2024-06-30

    # 証券コードで検索（トヨタ自動車）
    uv run python scripts/test_edinet_api.py --sec-code 72030 --start-date 2024-01-01

    # 会社名で部分一致検索
    uv run python scripts/test_edinet_api.py --company-name ソニー --start-date 2024-06-01

    # EDINETコードで検索
    uv run python scripts/test_edinet_api.py --edinet-code E02144 --start-date 2024-01-01

    # 書類種別を指定（有価証券報告書のみ）
    uv run python scripts/test_edinet_api.py --doc-types 120 --start-date 2024-06-01

    # 複数の書類種別を指定（有価証券報告書と四半期報告書）
    uv run python scripts/test_edinet_api.py --doc-types 120,140 --start-date 2024-06-01

    # PDFダウンロードも実行
    uv run python scripts/test_edinet_api.py --download

    # 表示件数を指定（0で全件表示、デフォルト: 10）
    uv run python scripts/test_edinet_api.py --limit 0

Note:
    EDINET_API_KEYは以下の順序で読み込まれます：
    1. 環境変数（設定されている場合）
    2. プロジェクトルートの .env ファイル
"""

import argparse
import asyncio
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

# プロジェクトルートの .env を読み込み
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from company_research_agent.clients.edinet_client import EDINETClient
from company_research_agent.core.config import EDINETConfig
from company_research_agent.core.exceptions import (
    EDINETAPIError,
    EDINETAuthenticationError,
    EDINETNotFoundError,
)
from company_research_agent.schemas.document_filter import DocumentFilter
from company_research_agent.schemas.edinet_schemas import DocumentMetadata
from company_research_agent.services import EDINETDocumentService

# 主要な書類種別コード
DOC_TYPE_NAMES = {
    "120": "有価証券報告書",
    "130": "訂正有価証券報告書",
    "140": "四半期報告書",
    "150": "訂正四半期報告書",
    "160": "半期報告書",
    "170": "訂正半期報告書",
    "180": "臨時報告書",
    "350": "大量保有報告書",
}


async def main(
    target_date: date | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    sec_code: str | None = None,
    edinet_code: str | None = None,
    company_name: str | None = None,
    doc_type_codes: list[str] | None = None,
    download: bool = False,
    limit: int = 10,
) -> None:
    """EDINET APIの動作確認を実行.

    Args:
        target_date: 単一日付指定（start_date/end_dateより優先）
        start_date: 検索開始日
        end_date: 検索終了日
        sec_code: 証券コードでフィルタ
        edinet_code: EDINETコードでフィルタ
        company_name: 会社名で部分一致フィルタ
        doc_type_codes: 書類種別コードでフィルタ
        download: PDFダウンロードを実行するか
        limit: 書類の表示件数（0で全件表示）
    """
    # 日付の決定
    if target_date:
        search_start = target_date
        search_end = target_date
    else:
        search_end = end_date or date.today()
        search_start = start_date or search_end

    # フィルタ条件の有無を判定
    has_filter = any([sec_code, edinet_code, company_name, doc_type_codes])

    print("=== EDINET API 動作確認 ===")
    print(f"検索期間: {search_start} ~ {search_end}")
    if has_filter:
        print("フィルタ条件:")
        if sec_code:
            print(f"  証券コード: {sec_code}")
        if edinet_code:
            print(f"  EDINETコード: {edinet_code}")
        if company_name:
            print(f"  会社名: {company_name}")
        if doc_type_codes:
            type_names = [DOC_TYPE_NAMES.get(c, c) for c in doc_type_codes]
            print(f"  書類種別: {', '.join(type_names)}")
    print()

    try:
        config = EDINETConfig()  # type: ignore[call-arg]
        print(f"✓ 設定読み込み完了 (API Key: {config.api_key[:8]}...)")
    except Exception as e:
        print(f"✗ 設定読み込み失敗: {e}")
        print("  EDINET_API_KEY環境変数を設定してください")
        return

    async with EDINETClient(config) as client:
        service = EDINETDocumentService(client)

        # フィルタ条件がある場合はサービスを使用
        if has_filter:
            await _search_with_filter(
                service=service,
                client=client,
                start_date=search_start,
                end_date=search_end,
                sec_code=sec_code,
                edinet_code=edinet_code,
                company_name=company_name,
                doc_type_codes=doc_type_codes,
                download=download,
                limit=limit,
            )
        else:
            # フィルタなしの場合は従来の動作（単一日付の一覧取得）
            await _list_documents_for_date(
                client=client,
                target_date=search_start,
                download=download,
                limit=limit,
            )

    print("\n=== 動作確認完了 ===")


async def _search_with_filter(
    service: EDINETDocumentService,
    client: EDINETClient,
    start_date: date,
    end_date: date,
    sec_code: str | None,
    edinet_code: str | None,
    company_name: str | None,
    doc_type_codes: list[str] | None,
    download: bool,
    limit: int,
) -> None:
    """フィルタ条件を使用して書類を検索."""
    print("\n--- フィルタ検索実行 ---")

    doc_filter = DocumentFilter(
        sec_code=sec_code,
        edinet_code=edinet_code,
        company_name=company_name,
        doc_type_codes=doc_type_codes,
        start_date=start_date,
        end_date=end_date,
    )

    try:
        results = await service.search_documents(doc_filter)
        print(f"✓ {len(results)}件の書類が見つかりました")
    except EDINETAuthenticationError as e:
        print(f"✗ 認証エラー: {e.message}")
        print("  APIキーが正しいか確認してください")
        return
    except EDINETAPIError as e:
        print(f"✗ APIエラー: {e}")
        return

    if not results:
        print("  条件に一致する書類がありません。")
        return

    # 書類種別ごとの集計
    print("\n--- 書類種別ごとの集計 ---")
    doc_types: dict[str, int] = {}
    for doc in results:
        doc_type = doc.doc_type_code or "不明"
        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

    for code, count in sorted(doc_types.items()):
        name = DOC_TYPE_NAMES.get(code, f"コード{code}")
        print(f"  {name}: {count}件")

    # 書類一覧表示
    print(f"\n--- 検索結果一覧（{len(results)}件） ---")
    display_count = len(results) if limit == 0 else limit
    for doc in results[:display_count]:
        _print_document_info(doc)

    if limit > 0 and len(results) > limit:
        print(f"  ... 他 {len(results) - limit}件")

    # PDFダウンロード
    if download:
        await _download_first_pdf(client, results)


async def _list_documents_for_date(
    client: EDINETClient,
    target_date: date,
    download: bool,
    limit: int,
) -> None:
    """特定日付の書類一覧を取得（従来の動作）."""
    # 1. メタデータのみ取得（件数確認）
    print("\n--- 1. メタデータ取得（件数確認） ---")
    try:
        metadata_response = await client.get_document_list(target_date, include_details=False)
        count = metadata_response.metadata.resultset.count
        print(f"✓ 書類件数: {count}件")
    except EDINETNotFoundError:
        print(f"✗ 指定日付のデータが見つかりません: {target_date}")
        return
    except EDINETAuthenticationError as e:
        print(f"✗ 認証エラー: {e.message}")
        print("  APIキーが正しいか確認してください")
        return
    except EDINETAPIError as e:
        print(f"✗ APIエラー: {e}")
        return

    if count == 0:
        print("  書類がありません。別の日付を試してください。")
        return

    # 2. 書類一覧取得（詳細情報）
    print("\n--- 2. 書類一覧取得（詳細情報） ---")
    try:
        response = await client.get_document_list(target_date, include_details=True)
        print(f"✓ {len(response.results or [])}件の書類情報を取得")
    except EDINETAPIError as e:
        print(f"✗ APIエラー: {e}")
        return

    # 3. 書類種別ごとの集計
    print("\n--- 3. 書類種別ごとの集計 ---")
    doc_types: dict[str, int] = {}
    securities_reports: list[DocumentMetadata] = []

    for doc in response.results or []:
        doc_type = doc.doc_type_code or "不明"
        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

        # 有価証券報告書（120）を記録
        if doc.doc_type_code == "120":
            securities_reports.append(doc)

    for code, count in sorted(doc_types.items()):
        name = DOC_TYPE_NAMES.get(code, f"コード{code}")
        print(f"  {name}: {count}件")

    # 4. 有価証券報告書の詳細表示
    if securities_reports:
        print(f"\n--- 4. 有価証券報告書一覧（{len(securities_reports)}件） ---")
        display_count = len(securities_reports) if limit == 0 else limit
        for doc in securities_reports[:display_count]:
            _print_document_info(doc)

        if limit > 0 and len(securities_reports) > limit:
            print(f"  ... 他 {len(securities_reports) - limit}件")

    # 5. PDFダウンロード（オプション）
    if download and securities_reports:
        await _download_first_pdf(client, securities_reports)


def _print_document_info(doc: DocumentMetadata) -> None:
    """書類情報を表示."""
    doc_type_name = DOC_TYPE_NAMES.get(doc.doc_type_code or "", doc.doc_type_code or "不明")
    print(f"  [{doc.doc_id}] {doc.filer_name or 'N/A'}")
    print(f"    種別: {doc_type_name}")
    print(f"    証券コード: {doc.sec_code or 'なし'} | EDINETコード: {doc.edinet_code or 'なし'}")
    print(f"    期間: {doc.period_start} ~ {doc.period_end}")
    print(
        f"    XBRL: {'○' if doc.xbrl_flag else '×'} | "
        f"PDF: {'○' if doc.pdf_flag else '×'} | "
        f"CSV: {'○' if doc.csv_flag else '×'}"
    )


async def _download_first_pdf(client: EDINETClient, documents: list[DocumentMetadata]) -> None:
    """最初のPDF対応書類をダウンロード."""
    print("\n--- PDFダウンロード ---")

    # PDF対応の書類を探す
    pdf_doc = next((doc for doc in documents if doc.pdf_flag), None)
    if not pdf_doc:
        print("  PDF対応の書類がありません")
        return

    download_dir = Path("downloads")
    download_dir.mkdir(parents=True, exist_ok=True)

    save_path = download_dir / f"{pdf_doc.doc_id}.pdf"
    print(f"  ダウンロード中: {pdf_doc.filer_name or 'N/A'}")
    try:
        await client.download_document(pdf_doc.doc_id, 2, save_path)
        print(f"  ✓ 保存完了: {save_path}")
    except EDINETAPIError as e:
        print(f"  ✗ ダウンロード失敗: {e}")


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパース."""
    parser = argparse.ArgumentParser(
        description="EDINET API動作確認スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 単一日付の書類一覧
  %(prog)s --date 2024-06-28

  # 期間指定で検索
  %(prog)s --start-date 2024-06-01 --end-date 2024-06-30

  # 証券コードで検索（トヨタ自動車）
  %(prog)s --sec-code 72030 --start-date 2024-01-01

  # 会社名で部分一致検索
  %(prog)s --company-name ソニー --start-date 2024-06-01

  # 書類種別を指定（有価証券報告書のみ）
  %(prog)s --doc-types 120 --start-date 2024-06-01

  # 複数の書類種別を指定
  %(prog)s --doc-types 120,140 --start-date 2024-06-01
        """,
    )

    # 日付関連
    date_group = parser.add_argument_group("日付指定")
    date_group.add_argument(
        "--date",
        type=str,
        default=None,
        help="単一日付 (YYYY-MM-DD形式)。--start-date/--end-dateより優先",
    )
    date_group.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="検索開始日 (YYYY-MM-DD形式)",
    )
    date_group.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="検索終了日 (YYYY-MM-DD形式)",
    )

    # フィルタ条件
    filter_group = parser.add_argument_group("フィルタ条件")
    filter_group.add_argument(
        "--sec-code",
        type=str,
        default=None,
        help="証券コード (例: 72030)",
    )
    filter_group.add_argument(
        "--edinet-code",
        type=str,
        default=None,
        help="EDINETコード (例: E02144)",
    )
    filter_group.add_argument(
        "--company-name",
        type=str,
        default=None,
        help="会社名（部分一致）",
    )
    filter_group.add_argument(
        "--doc-types",
        type=str,
        default=None,
        help="書類種別コード（カンマ区切り）。例: 120,140",
    )

    # その他オプション
    parser.add_argument(
        "--download",
        action="store_true",
        help="最初のPDF対応書類をダウンロード",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="書類の表示件数（0で全件表示、デフォルト: 10）",
    )
    return parser.parse_args()


def get_recent_business_day() -> date:
    """直近の営業日（平日）を推定."""
    today = date.today()
    # 土日を避けて直近の平日を取得
    days_back = 1
    if today.weekday() == 0:  # 月曜日
        days_back = 3  # 金曜日
    elif today.weekday() == 6:  # 日曜日
        days_back = 2  # 金曜日
    return today - timedelta(days=days_back)


if __name__ == "__main__":
    args = parse_args()

    # 日付の処理
    target_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None

    if args.date:
        target_date = date.fromisoformat(args.date)
    else:
        if args.start_date:
            start_date = date.fromisoformat(args.start_date)
        if args.end_date:
            end_date = date.fromisoformat(args.end_date)

        # 日付指定なしかつフィルタ条件もなしの場合は直近営業日
        if (
            not start_date
            and not end_date
            and not any([args.sec_code, args.edinet_code, args.company_name, args.doc_types])
        ):
            target_date = get_recent_business_day()

    # 書類種別の処理
    doc_type_codes: list[str] | None = None
    if args.doc_types:
        doc_type_codes = [code.strip() for code in args.doc_types.split(",")]

    asyncio.run(
        main(
            target_date=target_date,
            start_date=start_date,
            end_date=end_date,
            sec_code=args.sec_code,
            edinet_code=args.edinet_code,
            company_name=args.company_name,
            doc_type_codes=doc_type_codes,
            download=args.download,
            limit=args.limit,
        )
    )
