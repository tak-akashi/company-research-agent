"""Download command implementation."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from typing import Literal

from company_research_agent.cli.config import (
    DEFAULT_DOWNLOAD_DOC_TYPES,
    DOC_TYPE_NAMES,
    get_download_dir,
)
from company_research_agent.cli.output import (
    print_error,
    print_header,
    print_info,
    print_success,
)
from company_research_agent.clients.edinet_client import EDINETClient
from company_research_agent.core.config import EDINETConfig
from company_research_agent.core.exceptions import (
    EDINETAPIError,
    EDINETAuthenticationError,
    EDINETNotFoundError,
)
from company_research_agent.schemas.document_filter import DocumentFilter, SearchOrder
from company_research_agent.services import EDINETDocumentService


def sanitize_filename(name: str) -> str:
    """ファイル名に使用できない文字を除去."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "")
    return name[:50]  # 長すぎる場合は切り詰め


async def cmd_download(args: argparse.Namespace) -> int:
    """ダウンロードコマンド.

    Returns:
        終了コード (0: 成功, 1: エラー)
    """
    print_header("書類ダウンロード")

    try:
        config = EDINETConfig()  # type: ignore[call-arg]
    except Exception as e:
        print_error(f"設定読み込み失敗: {e}")
        return 1

    # 期間設定
    end_date = date.today() if not args.end_date else date.fromisoformat(args.end_date)
    start_date = (
        end_date - timedelta(days=365)
        if not args.start_date
        else date.fromisoformat(args.start_date)
    )

    # フィルタ作成
    doc_types = args.doc_types.split(",") if args.doc_types else DEFAULT_DOWNLOAD_DOC_TYPES

    filter_obj = DocumentFilter(
        sec_code=args.sec_code,
        edinet_code=args.edinet_code,
        company_name=args.company_name,
        doc_type_codes=doc_types,
        start_date=start_date,
        end_date=end_date,
        search_order=SearchOrder.NEWEST_FIRST,
        max_documents=args.limit,
    )

    download_dir = get_download_dir()
    success_count = 0
    error_count = 0

    async with EDINETClient(config) as client:
        service = EDINETDocumentService(client)

        try:
            documents = await service.search_documents(filter_obj)

            if not documents:
                print_info("該当する書類がありません")
                return 0

            print(f"ダウンロード対象: {len(documents)}件\n")

            for i, doc in enumerate(documents, 1):
                doc_type_code = doc.doc_type_code or "000"
                doc_type_name = DOC_TYPE_NAMES.get(doc_type_code, doc_type_code)

                # 保存パス作成
                sec_code = doc.sec_code or "unknown"
                filer_name = doc.filer_name or "unknown"
                company_name = sanitize_filename(filer_name)
                # period_end は文字列 (YYYY-MM-DD 形式)
                period = doc.period_end[:7].replace("-", "") if doc.period_end else "unknown"

                save_dir = (
                    download_dir
                    / f"{sec_code}_{company_name}"
                    / f"{doc_type_code}_{doc_type_name}"
                    / period
                )
                save_dir.mkdir(parents=True, exist_ok=True)

                # ダウンロードタイプ決定
                download_type: Literal[1, 2, 3, 4, 5]
                if args.format == "xbrl":
                    download_type = 1
                    ext = ".zip"
                else:
                    download_type = 2
                    ext = ".pdf"

                save_path = save_dir / f"{doc.doc_id}{ext}"

                if save_path.exists() and not args.force:
                    print(f"[{i}/{len(documents)}] SKIP (既存): {doc.doc_id}")
                    continue

                print(f"[{i}/{len(documents)}] ダウンロード中: {doc.doc_id} ({doc_type_name})")

                try:
                    await client.download_document(doc.doc_id, download_type, save_path)
                    print_success(f"保存: {save_path}")
                    success_count += 1
                except EDINETNotFoundError:
                    print_error(f"書類が見つかりません: {doc.doc_id}")
                    error_count += 1
                except EDINETAPIError as e:
                    print_error(f"ダウンロード失敗: {e}")
                    error_count += 1

            print(f"\n完了: {success_count}件成功, {error_count}件失敗")
            return 0 if error_count == 0 else 1

        except EDINETAuthenticationError:
            print_error("認証エラー: APIキーを確認してください")
            return 1
        except EDINETAPIError as e:
            print_error(f"APIエラー: {e}")
            return 1
