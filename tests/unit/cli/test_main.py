"""Tests for cli/main.py - argument parser and entry point."""

from __future__ import annotations

import argparse

import pytest

from company_research_agent.cli.main import create_parser


class TestCreateParser:
    """create_parser() のテスト."""

    @pytest.fixture
    def parser(self) -> argparse.ArgumentParser:
        """パーサーインスタンスを作成."""
        return create_parser()

    def test_parser_prog_name(self, parser: argparse.ArgumentParser) -> None:
        """プログラム名が 'cra' であること."""
        assert parser.prog == "cra"

    def test_parser_has_subcommands(self, parser: argparse.ArgumentParser) -> None:
        """必要なサブコマンドが定義されていること."""
        # サブパーサーのアクションを取得
        subparsers_action = None
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                subparsers_action = action
                break

        assert subparsers_action is not None
        expected_commands = {"search", "list", "download", "markdown", "query", "chat", "cache"}
        assert set(subparsers_action.choices.keys()) == expected_commands


class TestSearchCommand:
    """search サブコマンドのパーサーテスト."""

    @pytest.fixture
    def parser(self) -> argparse.ArgumentParser:
        """パーサーインスタンスを作成."""
        return create_parser()

    def test_search_with_name(self, parser: argparse.ArgumentParser) -> None:
        """--name オプションが正しくパースされること."""
        args = parser.parse_args(["search", "--name", "トヨタ"])
        assert args.command == "search"
        assert args.name == "トヨタ"

    def test_search_with_name_short(self, parser: argparse.ArgumentParser) -> None:
        """-n 短縮オプションが正しくパースされること."""
        args = parser.parse_args(["search", "-n", "ソニー"])
        assert args.name == "ソニー"

    def test_search_with_sec_code(self, parser: argparse.ArgumentParser) -> None:
        """--sec-code オプションが正しくパースされること."""
        args = parser.parse_args(["search", "--sec-code", "72030"])
        assert args.command == "search"
        assert args.sec_code == "72030"

    def test_search_with_edinet_code(self, parser: argparse.ArgumentParser) -> None:
        """--edinet-code オプションが正しくパースされること."""
        args = parser.parse_args(["search", "--edinet-code", "E02144"])
        assert args.command == "search"
        assert args.edinet_code == "E02144"

    def test_search_limit_default(self, parser: argparse.ArgumentParser) -> None:
        """--limit のデフォルト値が 10 であること."""
        args = parser.parse_args(["search", "--name", "test"])
        assert args.limit == 10

    def test_search_limit_custom(self, parser: argparse.ArgumentParser) -> None:
        """--limit オプションが正しくパースされること."""
        args = parser.parse_args(["search", "--name", "test", "--limit", "5"])
        assert args.limit == 5


class TestListCommand:
    """list サブコマンドのパーサーテスト."""

    @pytest.fixture
    def parser(self) -> argparse.ArgumentParser:
        """パーサーインスタンスを作成."""
        return create_parser()

    def test_list_with_sec_code(self, parser: argparse.ArgumentParser) -> None:
        """--sec-code オプションが正しくパースされること."""
        args = parser.parse_args(["list", "--sec-code", "72030"])
        assert args.command == "list"
        assert args.sec_code == "72030"

    def test_list_with_doc_types(self, parser: argparse.ArgumentParser) -> None:
        """--doc-types オプションが正しくパースされること."""
        args = parser.parse_args(["list", "--doc-types", "120,140"])
        assert args.doc_types == "120,140"

    def test_list_with_dates(self, parser: argparse.ArgumentParser) -> None:
        """期間指定オプションが正しくパースされること."""
        args = parser.parse_args(
            [
                "list",
                "--start-date",
                "2024-01-01",
                "--end-date",
                "2024-12-31",
            ]
        )
        assert args.start_date == "2024-01-01"
        assert args.end_date == "2024-12-31"

    def test_list_limit_default(self, parser: argparse.ArgumentParser) -> None:
        """--limit のデフォルト値が 20 であること."""
        args = parser.parse_args(["list"])
        assert args.limit == 20


class TestDownloadCommand:
    """download サブコマンドのパーサーテスト."""

    @pytest.fixture
    def parser(self) -> argparse.ArgumentParser:
        """パーサーインスタンスを作成."""
        return create_parser()

    def test_download_format_default(self, parser: argparse.ArgumentParser) -> None:
        """--format のデフォルト値が 'pdf' であること."""
        args = parser.parse_args(["download", "--sec-code", "72030"])
        assert args.format == "pdf"

    def test_download_format_xbrl(self, parser: argparse.ArgumentParser) -> None:
        """--format xbrl が正しくパースされること."""
        args = parser.parse_args(["download", "--sec-code", "72030", "--format", "xbrl"])
        assert args.format == "xbrl"

    def test_download_force_flag(self, parser: argparse.ArgumentParser) -> None:
        """--force フラグが正しくパースされること."""
        args = parser.parse_args(["download", "--sec-code", "72030", "--force"])
        assert args.force is True

    def test_download_limit_default(self, parser: argparse.ArgumentParser) -> None:
        """--limit のデフォルト値が 5 であること."""
        args = parser.parse_args(["download"])
        assert args.limit == 5


class TestMarkdownCommand:
    """markdown サブコマンドのパーサーテスト."""

    @pytest.fixture
    def parser(self) -> argparse.ArgumentParser:
        """パーサーインスタンスを作成."""
        return create_parser()

    def test_markdown_with_doc_id(self, parser: argparse.ArgumentParser) -> None:
        """--doc-id オプションが正しくパースされること."""
        args = parser.parse_args(["markdown", "--doc-id", "S100XXXX"])
        assert args.command == "markdown"
        assert args.doc_id == "S100XXXX"

    def test_markdown_with_file(self, parser: argparse.ArgumentParser) -> None:
        """--file オプションが正しくパースされること."""
        args = parser.parse_args(["markdown", "--file", "/path/to/doc.pdf"])
        assert args.file == "/path/to/doc.pdf"

    def test_markdown_strategy_default(self, parser: argparse.ArgumentParser) -> None:
        """--strategy のデフォルト値が 'auto' であること."""
        args = parser.parse_args(["markdown", "--doc-id", "S100XXXX"])
        assert args.strategy == "auto"

    def test_markdown_strategy_choices(self, parser: argparse.ArgumentParser) -> None:
        """--strategy の選択肢が正しいこと."""
        strategies = ["auto", "pdfplumber", "pymupdf4llm", "yomitoku", "gemini"]
        for strategy in strategies:
            args = parser.parse_args(["markdown", "--doc-id", "test", "--strategy", strategy])
            assert args.strategy == strategy

    def test_markdown_info_only_flag(self, parser: argparse.ArgumentParser) -> None:
        """--info-only フラグが正しくパースされること."""
        args = parser.parse_args(["markdown", "--doc-id", "test", "--info-only"])
        assert args.info_only is True

    def test_markdown_output_option(self, parser: argparse.ArgumentParser) -> None:
        """--output オプションが正しくパースされること."""
        args = parser.parse_args(["markdown", "--doc-id", "test", "--output", "result.md"])
        assert args.output == "result.md"


class TestQueryCommand:
    """query サブコマンドのパーサーテスト."""

    @pytest.fixture
    def parser(self) -> argparse.ArgumentParser:
        """パーサーインスタンスを作成."""
        return create_parser()

    def test_query_with_text(self, parser: argparse.ArgumentParser) -> None:
        """位置引数 query が正しくパースされること."""
        args = parser.parse_args(["query", "トヨタの有報を探して"])
        assert args.command == "query"
        assert args.query == "トヨタの有報を探して"

    def test_query_verbose_flag(self, parser: argparse.ArgumentParser) -> None:
        """--verbose フラグが正しくパースされること."""
        args = parser.parse_args(["query", "test", "--verbose"])
        assert args.verbose is True

    def test_query_verbose_short(self, parser: argparse.ArgumentParser) -> None:
        """-v 短縮フラグが正しくパースされること."""
        args = parser.parse_args(["query", "test", "-v"])
        assert args.verbose is True

    def test_query_verbose_default(self, parser: argparse.ArgumentParser) -> None:
        """--verbose のデフォルト値が False であること."""
        args = parser.parse_args(["query", "test"])
        assert args.verbose is False


class TestChatCommand:
    """chat サブコマンドのパーサーテスト."""

    @pytest.fixture
    def parser(self) -> argparse.ArgumentParser:
        """パーサーインスタンスを作成."""
        return create_parser()

    def test_chat_command(self, parser: argparse.ArgumentParser) -> None:
        """chat コマンドが正しくパースされること."""
        args = parser.parse_args(["chat"])
        assert args.command == "chat"

    def test_chat_verbose_flag(self, parser: argparse.ArgumentParser) -> None:
        """--verbose フラグが正しくパースされること."""
        args = parser.parse_args(["chat", "--verbose"])
        assert args.verbose is True

    def test_chat_verbose_short(self, parser: argparse.ArgumentParser) -> None:
        """-v 短縮フラグが正しくパースされること."""
        args = parser.parse_args(["chat", "-v"])
        assert args.verbose is True

    def test_chat_verbose_default(self, parser: argparse.ArgumentParser) -> None:
        """--verbose のデフォルト値が False であること."""
        args = parser.parse_args(["chat"])
        assert args.verbose is False


class TestCacheCommand:
    """cache サブコマンドのパーサーテスト."""

    @pytest.fixture
    def parser(self) -> argparse.ArgumentParser:
        """パーサーインスタンスを作成."""
        return create_parser()

    def test_cache_stats_flag(self, parser: argparse.ArgumentParser) -> None:
        """--stats フラグが正しくパースされること."""
        args = parser.parse_args(["cache", "--stats"])
        assert args.command == "cache"
        assert args.stats is True

    def test_cache_list_flag(self, parser: argparse.ArgumentParser) -> None:
        """--list フラグが正しくパースされること."""
        args = parser.parse_args(["cache", "--list"])
        assert args.list is True

    def test_cache_find_option(self, parser: argparse.ArgumentParser) -> None:
        """--find オプションが正しくパースされること."""
        args = parser.parse_args(["cache", "--find", "S100XXXX"])
        assert args.find == "S100XXXX"

    def test_cache_filter_options(self, parser: argparse.ArgumentParser) -> None:
        """フィルタオプションが正しくパースされること."""
        args = parser.parse_args(
            [
                "cache",
                "--list",
                "--sec-code",
                "72030",
                "--doc-type",
                "120",
                "--limit",
                "50",
            ]
        )
        assert args.sec_code == "72030"
        assert args.doc_type == "120"
        assert args.limit == 50
