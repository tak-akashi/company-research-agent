"""List command implementation."""

from __future__ import annotations

import argparse
from datetime import date, timedelta

from company_research_agent.cli.config import DEFAULT_DOC_TYPES, DOC_TYPE_NAMES
from company_research_agent.cli.output import (
    print_documents_table,
    print_error,
    print_header,
    print_info,
)
from company_research_agent.clients.edinet_client import EDINETClient
from company_research_agent.core.config import EDINETConfig
from company_research_agent.core.exceptions import (
    EDINETAPIError,
    EDINETAuthenticationError,
)
from company_research_agent.schemas.document_filter import DocumentFilter, SearchOrder
from company_research_agent.services import EDINETDocumentService


async def cmd_list(args: argparse.Namespace) -> int:
    """書類一覧コマンド.

    Returns:
        終了コード (0: 成功, 1: エラー)
    """
    print_header("書類一覧")

    try:
        config = EDINETConfig()  # type: ignore[call-arg]
    except Exception as e:
        print_error(f"設定読み込み失敗: {e}")
        print_info("EDINET_API_KEY を .env に設定してください")
        return 1

    # 期間設定
    end_date = date.today() if not args.end_date else date.fromisoformat(args.end_date)
    start_date = (
        end_date - timedelta(days=365)
        if not args.start_date
        else date.fromisoformat(args.start_date)
    )

    # フィルタ作成
    doc_types = args.doc_types.split(",") if args.doc_types else DEFAULT_DOC_TYPES

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

    print(f"検索期間: {start_date} 〜 {end_date}")
    print(f"書類種別: {', '.join(DOC_TYPE_NAMES.get(c, c) for c in doc_types)}")
    if args.sec_code:
        print(f"証券コード: {args.sec_code}")
    if args.edinet_code:
        print(f"EDINETコード: {args.edinet_code}")
    if args.company_name:
        print(f"企業名: {args.company_name}")
    print()

    async with EDINETClient(config) as client:
        service = EDINETDocumentService(client)

        try:
            documents = await service.search_documents(filter_obj)

            if not documents:
                print_info("該当する書類がありません")
                return 0

            print(f"取得件数: {len(documents)}件\n")
            print_documents_table(documents)
            return 0

        except EDINETAuthenticationError:
            print_error("認証エラー: APIキーを確認してください")
            return 1
        except EDINETAPIError as e:
            print_error(f"APIエラー: {e}")
            return 1
