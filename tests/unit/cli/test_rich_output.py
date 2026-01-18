"""Tests for cli/rich_output.py - Rich formatted output utilities."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from company_research_agent.cli.rich_output import (
    print_chat_goodbye,
    print_chat_welcome,
    print_history_cleared,
    print_processing,
    print_query_result,
    print_thinking,
    print_tool_call,
    print_tools_summary,
)
from company_research_agent.schemas.query_schemas import OrchestratorResult


class TestPrintQueryResult:
    """print_query_result() のテスト."""

    @pytest.fixture
    def sample_result(self) -> OrchestratorResult:
        """サンプル結果を作成."""
        return OrchestratorResult(
            query="トヨタの有報を探して",
            intent="検索",
            result="トヨタ自動車の有価証券報告書を見つけました。",
            tools_used=["search_company", "search_documents"],
            documents=[],
        )

    def test_prints_panel_with_result(self, sample_result: OrchestratorResult) -> None:
        """結果がパネル形式で出力されること."""
        # Rich consoleの出力をキャプチャ
        with patch("company_research_agent.cli.rich_output.console") as mock_console:
            print_query_result(sample_result)
            mock_console.print.assert_called_once()

    def test_handles_none_result(self) -> None:
        """結果がNoneの場合にも動作すること."""
        result = OrchestratorResult(
            query="test",
            intent="検索",
            result=None,
            tools_used=[],
            documents=[],
        )
        with patch("company_research_agent.cli.rich_output.console") as mock_console:
            print_query_result(result)
            mock_console.print.assert_called_once()

    def test_handles_list_content_multimodal(self) -> None:
        """リスト形式（マルチモーダル）のcontentを正しく処理すること."""
        result = OrchestratorResult(
            query="test",
            intent="検索",
            result=[{"type": "text", "text": "マルチモーダル形式の回答です"}],
            tools_used=[],
            documents=[],
        )
        with patch("company_research_agent.cli.rich_output.console") as mock_console:
            print_query_result(result)
            mock_console.print.assert_called_once()

    def test_handles_multiple_text_blocks(self) -> None:
        """複数のtextブロックを正しく処理すること."""
        result = OrchestratorResult(
            query="test",
            intent="分析",
            result=[
                {"type": "text", "text": "1行目"},
                {"type": "text", "text": "2行目"},
            ],
            tools_used=[],
            documents=[],
        )
        with patch("company_research_agent.cli.rich_output.console") as mock_console:
            print_query_result(result)
            mock_console.print.assert_called_once()

    def test_handles_empty_list_result(self) -> None:
        """空のリストの場合に「結果なし」を表示すること."""
        result = OrchestratorResult(
            query="test",
            intent="検索",
            result=[],
            tools_used=[],
            documents=[],
        )
        with patch("company_research_agent.cli.rich_output.console") as mock_console:
            print_query_result(result)
            mock_console.print.assert_called_once()

    def test_ignores_non_text_blocks_in_list(self) -> None:
        """リスト内のtext以外のブロックは無視すること."""
        result = OrchestratorResult(
            query="test",
            intent="検索",
            result=[
                {"type": "text", "text": "テキスト部分"},
                {"type": "tool_use", "id": "123", "name": "tool"},
            ],
            tools_used=[],
            documents=[],
        )
        with patch("company_research_agent.cli.rich_output.console") as mock_console:
            print_query_result(result)
            mock_console.print.assert_called_once()


class TestPrintThinking:
    """print_thinking() のテスト."""

    def test_prints_dim_message(self) -> None:
        """薄い色でメッセージが出力されること."""
        with patch("company_research_agent.cli.rich_output.console") as mock_console:
            print_thinking("処理中...")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "[dim]" in call_args
            assert "処理中..." in call_args


class TestPrintToolCall:
    """print_tool_call() のテスト."""

    def test_prints_tool_name(self) -> None:
        """ツール名が出力されること."""
        with patch("company_research_agent.cli.rich_output.console") as mock_console:
            print_tool_call("search_company")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "search_company" in call_args

    def test_prints_tool_with_args(self) -> None:
        """引数付きでツールが出力されること."""
        with patch("company_research_agent.cli.rich_output.console") as mock_console:
            print_tool_call("search_company", {"name": "トヨタ"})
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "search_company" in call_args
            assert "name=" in call_args


class TestPrintToolsSummary:
    """print_tools_summary() のテスト."""

    def test_prints_tools_list(self) -> None:
        """ツールリストが出力されること."""
        with patch("company_research_agent.cli.rich_output.console") as mock_console:
            print_tools_summary(["search_company", "search_documents"])
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "search_company" in call_args
            assert "search_documents" in call_args

    def test_no_output_for_empty_list(self) -> None:
        """空リストの場合は出力しないこと."""
        with patch("company_research_agent.cli.rich_output.console") as mock_console:
            print_tools_summary([])
            mock_console.print.assert_not_called()


class TestPrintChatWelcome:
    """print_chat_welcome() のテスト."""

    def test_prints_welcome_panel(self) -> None:
        """ウェルカムパネルが出力されること."""
        with patch("company_research_agent.cli.rich_output.console") as mock_console:
            print_chat_welcome()
            # 複数回printが呼ばれる（空行含む）
            assert mock_console.print.call_count >= 1


class TestPrintChatGoodbye:
    """print_chat_goodbye() のテスト."""

    def test_prints_goodbye_message(self) -> None:
        """終了メッセージが出力されること."""
        with patch("company_research_agent.cli.rich_output.console") as mock_console:
            print_chat_goodbye()
            mock_console.print.assert_called_once()


class TestPrintHistoryCleared:
    """print_history_cleared() のテスト."""

    def test_prints_clear_message(self) -> None:
        """履歴クリアメッセージが出力されること."""
        with patch("company_research_agent.cli.rich_output.console") as mock_console:
            print_history_cleared()
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "クリア" in call_args


class TestPrintProcessing:
    """print_processing() のテスト."""

    def test_prints_processing_message(self) -> None:
        """処理中メッセージが出力されること."""
        with patch("company_research_agent.cli.rich_output.console") as mock_console:
            print_processing()
            mock_console.print.assert_called_once()
