"""CLI main entry point."""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import TYPE_CHECKING, Literal

from company_research_agent.cli.commands.cache import cmd_cache
from company_research_agent.cli.commands.chat import cmd_chat
from company_research_agent.cli.commands.download import cmd_download
from company_research_agent.cli.commands.list import cmd_list
from company_research_agent.cli.commands.markdown import cmd_markdown
from company_research_agent.cli.commands.query import cmd_query
from company_research_agent.cli.commands.search import cmd_search

if TYPE_CHECKING:
    pass


def create_parser() -> argparse.ArgumentParser:
    """ArgumentParserを作成."""
    parser = argparse.ArgumentParser(
        prog="cra",
        description="企業有価証券の検索・ダウンロード・分析CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  企業検索:
    cra search --name "トヨタ"
    cra search --sec-code 72030

  書類一覧:
    cra list --sec-code 72030 --doc-types 120,140

  ダウンロード:
    cra download --sec-code 72030 --doc-types 120 --limit 3

  マークダウン変換:
    cra markdown --doc-id S100XXXX
    cra markdown --file path/to/document.pdf --output result.md

  自然言語クエリ:
    cra query "トヨタの有報を分析して"

  対話モード:
    cra chat

  キャッシュ確認:
    cra cache --stats
    cra cache --list --sec-code 72030

  デバッグモード:
    cra -v list --sec-code 72030
    LOG_LEVEL=DEBUG cra list --sec-code 72030
""",
    )

    # グローバルオプション
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="詳細ログを表示 (DEBUG レベル)"
    )

    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    _create_search_parser(subparsers)
    _create_list_parser(subparsers)
    _create_download_parser(subparsers)
    _create_markdown_parser(subparsers)
    _create_query_parser(subparsers)
    _create_chat_parser(subparsers)
    _create_cache_parser(subparsers)

    return parser


def _create_search_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """searchサブコマンドを定義."""
    search_parser = subparsers.add_parser("search", help="企業検索")
    search_group = search_parser.add_mutually_exclusive_group()
    search_group.add_argument("--name", "-n", type=str, help="企業名 (あいまい検索)")
    search_group.add_argument("--sec-code", "-s", type=str, help="証券コード")
    search_group.add_argument("--edinet-code", "-e", type=str, help="EDINETコード")
    search_parser.add_argument("--limit", "-l", type=int, default=10, help="最大件数 (default: 10)")


def _create_list_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """listサブコマンドを定義."""
    list_parser = subparsers.add_parser("list", help="書類一覧")
    list_parser.add_argument("--sec-code", "-s", type=str, help="証券コード")
    list_parser.add_argument("--edinet-code", "-e", type=str, help="EDINETコード")
    list_parser.add_argument("--company-name", "-c", type=str, help="企業名 (部分一致)")
    list_parser.add_argument(
        "--doc-types", "-t", type=str, help="書類種別コード (カンマ区切り, default: 120,140)"
    )
    list_parser.add_argument("--start-date", type=str, help="開始日 (YYYY-MM-DD)")
    list_parser.add_argument("--end-date", type=str, help="終了日 (YYYY-MM-DD)")
    list_parser.add_argument("--limit", "-l", type=int, default=20, help="最大件数 (default: 20)")


def _create_download_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """downloadサブコマンドを定義."""
    dl_parser = subparsers.add_parser("download", help="書類ダウンロード")
    dl_parser.add_argument("--sec-code", "-s", type=str, help="証券コード")
    dl_parser.add_argument("--edinet-code", "-e", type=str, help="EDINETコード")
    dl_parser.add_argument("--company-name", "-c", type=str, help="企業名 (部分一致)")
    dl_parser.add_argument(
        "--doc-types", "-t", type=str, help="書類種別コード (カンマ区切り, default: 120)"
    )
    dl_parser.add_argument("--start-date", type=str, help="開始日 (YYYY-MM-DD)")
    dl_parser.add_argument("--end-date", type=str, help="終了日 (YYYY-MM-DD)")
    dl_parser.add_argument("--limit", "-l", type=int, default=5, help="最大件数 (default: 5)")
    dl_parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=["pdf", "xbrl"],
        default="pdf",
        help="形式 (default: pdf)",
    )
    dl_parser.add_argument("--force", action="store_true", help="既存ファイルを上書き")


def _create_markdown_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """markdownサブコマンドを定義."""
    md_parser = subparsers.add_parser("markdown", help="PDF→マークダウン変換")
    md_source = md_parser.add_mutually_exclusive_group()
    md_source.add_argument("--doc-id", "-d", type=str, help="書類ID (キャッシュから検索)")
    md_source.add_argument("--file", "-f", type=str, help="PDFファイルパス")
    md_parser.add_argument("--output", "-o", type=str, help="出力ファイルパス")
    md_parser.add_argument("--start-page", type=int, help="開始ページ")
    md_parser.add_argument("--end-page", type=int, help="終了ページ")
    md_parser.add_argument(
        "--strategy",
        type=str,
        choices=["auto", "pdfplumber", "pymupdf4llm", "yomitoku", "gemini"],
        default="auto",
        help="変換戦略 (default: auto)",
    )
    md_parser.add_argument("--info-only", action="store_true", help="PDF情報のみ表示")


def _create_query_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """queryサブコマンドを定義."""
    query_parser = subparsers.add_parser(
        "query",
        help="自然言語クエリ実行",
        description="自然言語で企業情報を問い合わせます",
    )
    query_parser.add_argument("query", type=str, help="質問文")
    query_parser.add_argument("-v", "--verbose", action="store_true", help="詳細表示モード")


def _create_chat_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """chatサブコマンドを定義."""
    chat_parser = subparsers.add_parser(
        "chat",
        help="対話モード",
        description="対話形式で企業情報を問い合わせます（会話履歴保持）",
    )
    chat_parser.add_argument("-v", "--verbose", action="store_true", help="詳細表示モード")


def _create_cache_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """cacheサブコマンドを定義."""
    cache_parser = subparsers.add_parser("cache", help="キャッシュ管理")
    cache_parser.add_argument("--stats", action="store_true", help="統計情報を表示")
    cache_parser.add_argument("--list", action="store_true", help="キャッシュ一覧を表示")
    cache_parser.add_argument("--find", type=str, help="書類IDで検索")
    cache_parser.add_argument("--sec-code", "-s", type=str, help="証券コードでフィルタ")
    cache_parser.add_argument("--doc-type", "-t", type=str, help="書類種別でフィルタ")
    cache_parser.add_argument("--limit", "-l", type=int, help="表示件数")


async def run(args: argparse.Namespace) -> int:
    """コマンドをディスパッチして実行.

    Returns:
        終了コード (0: 成功, 1: エラー)
    """
    if args.command == "search":
        return await cmd_search(args)
    elif args.command == "list":
        return await cmd_list(args)
    elif args.command == "download":
        return await cmd_download(args)
    elif args.command == "markdown":
        return await cmd_markdown(args)
    elif args.command == "query":
        return await cmd_query(args)
    elif args.command == "chat":
        return await cmd_chat(args)
    elif args.command == "cache":
        return await cmd_cache(args)
    else:
        print("使用方法: cra <command> [options]")
        print("  commands: search, list, download, markdown, query, chat, cache")
        print("  詳細は --help を参照してください")
        return 1


def _setup_logging(verbose: bool = False) -> None:
    """CLIのログ設定を初期化.

    Args:
        verbose: True の場合は DEBUG レベル。

    環境変数 LOG_LEVEL でも制御可能 (DEBUG, INFO, WARNING, ERROR)。
    優先順位: -v オプション > 環境変数 > デフォルト(WARNING)
    """
    from company_research_agent.core.config import LoggingConfig
    from company_research_agent.core.logging import setup_logging

    LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    try:
        config = LoggingConfig()
        level: LogLevel
        if verbose:
            level = "DEBUG"
        elif config.level != "INFO":
            # 環境変数で明示的に設定された場合
            level = config.level
        else:
            # CLIデフォルトはWARNING (静かに動作)
            level = "WARNING"
        setup_logging(level=level, format_style=config.format_style)
    except Exception:
        # 設定読み込み失敗時はデフォルト設定
        level_fallback: LogLevel = "DEBUG" if verbose else "WARNING"
        setup_logging(level=level_fallback, format_style="simple")


def main() -> None:
    """CLIエントリーポイント."""
    parser = create_parser()
    args = parser.parse_args()
    _setup_logging(verbose=getattr(args, "verbose", False))
    exit_code = asyncio.run(run(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
