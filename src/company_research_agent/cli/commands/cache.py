"""Cache command implementation."""

from __future__ import annotations

import argparse

from company_research_agent.cli.config import DOC_TYPE_NAMES, get_download_dir
from company_research_agent.cli.output import (
    print_error,
    print_header,
    print_info,
)
from company_research_agent.services.local_cache_service import LocalCacheService


async def cmd_cache(args: argparse.Namespace) -> int:
    """キャッシュ管理コマンド.

    Returns:
        終了コード (0: 成功, 1: エラー)
    """
    print_header("キャッシュ管理")

    cache_service = LocalCacheService(get_download_dir())

    if args.stats:
        # 統計情報
        stats = cache_service.get_cache_stats()
        print(f"総書類数: {stats['total_documents']}")
        print(f"総企業数: {stats['total_companies']}")

        # 詳細統計を計算
        all_docs = cache_service.list_all()
        if all_docs:
            # 企業別集計
            by_company: dict[str, int] = {}
            by_doc_type: dict[str, int] = {}
            for doc in all_docs:
                if doc.sec_code:
                    key = f"{doc.sec_code}_{doc.company_name}"
                else:
                    key = doc.company_name or "unknown"
                by_company[key] = by_company.get(key, 0) + 1
                if doc.doc_type_code:
                    by_doc_type[doc.doc_type_code] = by_doc_type.get(doc.doc_type_code, 0) + 1

            print("\n企業別 (上位10件):")
            for company, count in sorted(by_company.items(), key=lambda x: -x[1])[:10]:
                print(f"  {company}: {count}件")

            print("\n書類種別:")
            for doc_type, count in sorted(by_doc_type.items(), key=lambda x: -x[1]):
                name = DOC_TYPE_NAMES.get(doc_type, doc_type)
                print(f"  {name}: {count}件")

        return 0

    elif args.list:
        # 一覧表示
        docs = cache_service.list_all()
        if not docs:
            print_info("キャッシュは空です")
            return 0

        # フィルタリング
        if args.sec_code:
            docs = [d for d in docs if d.sec_code == args.sec_code]
        if args.doc_type:
            docs = [d for d in docs if d.doc_type_code == args.doc_type]

        print(f"キャッシュ件数: {len(docs)}\n")

        limit = args.limit or 20
        for i, doc in enumerate(docs[:limit], 1):
            doc_type_name = DOC_TYPE_NAMES.get(doc.doc_type_code or "", doc.doc_type_code or "")
            print(f"{i:3}. {doc.doc_id}")
            print(f"     企業: {doc.company_name} ({doc.sec_code})")
            print(f"     種別: {doc_type_name} | 期間: {doc.period}")
            print()

        if len(docs) > limit:
            print(f"... 他 {len(docs) - limit} 件")

        return 0

    elif args.find:
        # 書類ID検索
        info = cache_service.find_by_doc_id(args.find)
        if info:
            print(f"書類ID: {info.doc_id}")
            print(f"ファイルパス: {info.file_path}")
            print(f"企業: {info.company_name} ({info.sec_code})")
            print(f"種別: {DOC_TYPE_NAMES.get(info.doc_type_code or '', info.doc_type_code or '')}")
            print(f"期間: {info.period}")
            return 0
        else:
            print_error(f"書類ID {args.find} が見つかりません")
            return 1

    else:
        print_info("--stats, --list, --find のいずれかを指定してください")
        return 1
