"""Search command implementation."""

from __future__ import annotations

import argparse

from company_research_agent.cli.output import (
    print_company_info,
    print_error,
    print_header,
)
from company_research_agent.clients.edinet_code_list_client import EDINETCodeListClient


async def cmd_search(args: argparse.Namespace) -> int:
    """企業検索コマンド.

    Returns:
        終了コード (0: 成功, 1: エラー)
    """
    print_header("企業検索")

    client = EDINETCodeListClient()

    try:
        if args.sec_code:
            # 証券コードで検索
            company = await client.get_by_sec_code(args.sec_code)
            if company:
                print_company_info(company)
                return 0
            else:
                print_error(f"証券コード {args.sec_code} の企業が見つかりません")
                return 1

        elif args.edinet_code:
            # EDINETコードで検索
            company = await client.get_by_edinet_code(args.edinet_code)
            if company:
                print_company_info(company)
                return 0
            else:
                print_error(f"EDINETコード {args.edinet_code} の企業が見つかりません")
                return 1

        elif args.name:
            # 企業名で検索
            candidates = await client.search_companies(args.name, limit=args.limit)
            if candidates:
                print(f"検索結果: {len(candidates)}件\n")
                for i, candidate in enumerate(candidates, 1):
                    c = candidate.company  # CompanyCandidate.company -> CompanyInfo
                    print(f"{i:2}. {c.company_name}")
                    print(f"    EDINETコード: {c.edinet_code}")
                    print(f"    証券コード: {c.sec_code or '(未上場)'}")
                    print(f"    類似度: {candidate.similarity_score:.1f}%")
                    print()
                return 0
            else:
                print_error(f"「{args.name}」に一致する企業が見つかりません")
                return 1
        else:
            print_error("--name, --sec-code, --edinet-code のいずれかを指定してください")
            return 1

    except Exception as e:
        print_error(f"検索エラー: {e}")
        return 1
