"""Markdown command implementation - PDF to Markdown conversion."""

from __future__ import annotations

import argparse
from pathlib import Path

from company_research_agent.cli.config import get_download_dir
from company_research_agent.cli.output import (
    print_error,
    print_header,
    print_info,
    print_success,
)
from company_research_agent.parsers.pdf_parser import PDFParser
from company_research_agent.services.local_cache_service import LocalCacheService


async def cmd_markdown(args: argparse.Namespace) -> int:
    """PDF→マークダウン変換コマンド.

    Returns:
        終了コード (0: 成功, 1: エラー)
    """
    print_header("PDF→マークダウン変換")

    # ファイルパス特定
    pdf_path: Path | None = None

    if args.file:
        pdf_path = Path(args.file)
        if not pdf_path.exists():
            print_error(f"ファイルが見つかりません: {pdf_path}")
            return 1
    elif args.doc_id:
        # キャッシュから検索
        cache_service = LocalCacheService(get_download_dir())
        cache_info = cache_service.find_by_doc_id(args.doc_id)
        if cache_info:
            pdf_path = cache_info.file_path
        else:
            print_error(f"書類ID {args.doc_id} がキャッシュに見つかりません")
            print_info("先に download コマンドでダウンロードしてください")
            return 1
    else:
        print_error("--file または --doc-id を指定してください")
        return 1

    print(f"対象ファイル: {pdf_path}\n")

    try:
        parser = PDFParser()

        # 情報取得
        if args.info_only:
            pdf_info = parser.get_info(pdf_path)
            print(f"ファイル名: {pdf_info.file_name}")
            print(f"総ページ数: {pdf_info.total_pages}")
            if pdf_info.page_size:
                print(f"ページサイズ: {pdf_info.page_size}")
            if pdf_info.table_of_contents:
                print("\n目次:")
                for item in pdf_info.table_of_contents[:20]:  # 最初の20項目
                    print(f"  - {item}")
            return 0

        # マークダウン変換
        print(f"変換戦略: {args.strategy}")
        print("変換中...")

        start_page = args.start_page
        end_page = args.end_page

        result = parser.to_markdown(
            pdf_path,
            start_page=start_page,
            end_page=end_page,
            strategy=args.strategy,
        )

        print_success(f"変換完了 (使用戦略: {result.strategy_used})")
        print(f"抽出ページ数: {result.pages}")

        # 出力
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(result.text, encoding="utf-8")
            print_success(f"保存: {output_path}")
        else:
            print("\n" + "=" * 60)
            print("抽出テキスト (先頭3000文字)")
            print("=" * 60 + "\n")
            print(result.text[:3000])
            if len(result.text) > 3000:
                print(f"\n... (残り {len(result.text) - 3000} 文字)")

        return 0

    except Exception as e:
        print_error(f"変換エラー: {e}")
        return 1
