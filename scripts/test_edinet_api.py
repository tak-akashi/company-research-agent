#!/usr/bin/env python3
"""EDINET API動作確認スクリプト.

使用方法:
    # スクリプト実行（.envファイルからAPIキーを自動読み込み）
    uv run python scripts/test_edinet_api.py

    # 特定の日付を指定
    uv run python scripts/test_edinet_api.py --date 2024-06-28

    # PDFダウンロードも実行
    uv run python scripts/test_edinet_api.py --download

    # 有価証券報告書を全件表示
    uv run python scripts/test_edinet_api.py --limit 0

    # 有価証券報告書を10件表示
    uv run python scripts/test_edinet_api.py --limit 10

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
from company_research_agent.schemas.edinet_schemas import DocumentMetadata


async def main(target_date: date, download: bool = False, limit: int = 5) -> None:
    """EDINET APIの動作確認を実行.

    Args:
        target_date: 対象日付
        download: PDFダウンロードを実行するか
        limit: 有価証券報告書の表示件数（0で全件表示）
    """
    print("=== EDINET API 動作確認 ===")
    print(f"対象日付: {target_date}")
    print()

    try:
        config = EDINETConfig()  # type: ignore[call-arg]
        print(f"✓ 設定読み込み完了 (API Key: {config.api_key[:8]}...)")
    except Exception as e:
        print(f"✗ 設定読み込み失敗: {e}")
        print("  EDINET_API_KEY環境変数を設定してください")
        return

    async with EDINETClient(config) as client:
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

        # 主要な書類種別コード
        doc_type_names = {
            "120": "有価証券報告書",
            "130": "訂正有価証券報告書",
            "140": "四半期報告書",
            "150": "訂正四半期報告書",
            "160": "半期報告書",
            "170": "訂正半期報告書",
            "180": "臨時報告書",
            "350": "大量保有報告書",
        }

        for code, count in sorted(doc_types.items()):
            name = doc_type_names.get(code, f"コード{code}")
            print(f"  {name}: {count}件")

        # 4. 有価証券報告書の詳細表示
        if securities_reports:
            print(f"\n--- 4. 有価証券報告書一覧（{len(securities_reports)}件） ---")
            display_count = len(securities_reports) if limit == 0 else limit
            for doc in securities_reports[:display_count]:
                print(f"  [{doc.doc_id}] {doc.filer_name or 'N/A'}")
                print(f"    証券コード: {doc.sec_code or 'なし'}")
                print(f"    期間: {doc.period_start} ~ {doc.period_end}")
                print(
                    f"    XBRL: {'○' if doc.xbrl_flag else '×'} | "
                    f"PDF: {'○' if doc.pdf_flag else '×'} | "
                    f"CSV: {'○' if doc.csv_flag else '×'}"
                )

            if limit > 0 and len(securities_reports) > limit:
                print(f"  ... 他 {len(securities_reports) - limit}件")

        # 5. PDFダウンロード（オプション）
        if download and securities_reports:
            print("\n--- 5. PDFダウンロード ---")
            download_dir = Path("downloads") / str(target_date)
            download_dir.mkdir(parents=True, exist_ok=True)

            # 最初の有価証券報告書をダウンロード
            doc = securities_reports[0]
            if doc.pdf_flag:
                save_path = download_dir / f"{doc.doc_id}.pdf"
                print(f"  ダウンロード中: {doc.filer_name or 'N/A'}")
                try:
                    await client.download_document(doc.doc_id, 2, save_path)
                    print(f"  ✓ 保存完了: {save_path}")
                except EDINETAPIError as e:
                    print(f"  ✗ ダウンロード失敗: {e}")
            else:
                print(f"  スキップ: {doc.filer_name or 'N/A'} (PDFなし)")

    print("\n=== 動作確認完了 ===")


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパース."""
    parser = argparse.ArgumentParser(description="EDINET API動作確認スクリプト")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="対象日付 (YYYY-MM-DD形式)。省略時は直近の営業日を推定",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="最初の有価証券報告書のPDFをダウンロード",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="有価証券報告書の表示件数（0で全件表示、デフォルト: 5）",
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

    if args.date:
        target_date = date.fromisoformat(args.date)
    else:
        target_date = get_recent_business_day()

    asyncio.run(main(target_date, download=args.download, limit=args.limit))
