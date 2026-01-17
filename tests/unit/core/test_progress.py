"""Tests for progress display utilities."""

from __future__ import annotations

from io import StringIO

import pytest
from rich.console import Console

from company_research_agent.core.progress import (
    console,
    create_progress,
    print_error,
    print_info,
    print_status,
    print_success,
    print_warning,
    progress_context,
)


class TestPrintFunctions:
    """Tests for print_* functions."""

    def test_print_status_outputs_message(self) -> None:
        """print_status should output message with blue arrow icon."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        from company_research_agent.core import progress

        original_console = progress.console
        progress.console = test_console

        try:
            print_status("検索中")
            result = output.getvalue()
            assert "検索中" in result
            assert "▶" in result  # Blue arrow icon
        finally:
            progress.console = original_console

    def test_print_success_outputs_message(self) -> None:
        """print_success should output message with green checkmark icon."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        from company_research_agent.core import progress

        original_console = progress.console
        progress.console = test_console

        try:
            print_success("ダウンロード完了")
            result = output.getvalue()
            assert "ダウンロード完了" in result
        finally:
            progress.console = original_console

    def test_print_error_outputs_message(self) -> None:
        """print_error should output message with red cross icon."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        from company_research_agent.core import progress

        original_console = progress.console
        progress.console = test_console

        try:
            print_error("ファイルが見つかりません")
            result = output.getvalue()
            assert "ファイルが見つかりません" in result
        finally:
            progress.console = original_console

    def test_print_warning_outputs_message(self) -> None:
        """print_warning should output message with yellow warning icon."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        from company_research_agent.core import progress

        original_console = progress.console
        progress.console = test_console

        try:
            print_warning("キャッシュが古い可能性があります")
            result = output.getvalue()
            assert "キャッシュが古い可能性があります" in result
        finally:
            progress.console = original_console

    def test_print_info_outputs_message(self) -> None:
        """print_info should output message with cyan info icon."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        from company_research_agent.core import progress

        original_console = progress.console
        progress.console = test_console

        try:
            print_info("3件の書類が見つかりました")
            result = output.getvalue()
            assert "3件の書類が見つかりました" in result
        finally:
            progress.console = original_console


class TestCreateProgress:
    """Tests for create_progress function."""

    def test_create_progress_returns_progress_instance(self) -> None:
        """create_progress should return a Progress instance."""
        from rich.progress import Progress

        progress = create_progress()
        assert isinstance(progress, Progress)

    def test_create_progress_has_spinner_column(self) -> None:
        """create_progress should include SpinnerColumn."""
        from rich.progress import SpinnerColumn

        progress = create_progress()
        column_types = [type(col) for col in progress.columns]
        assert SpinnerColumn in column_types

    def test_create_progress_can_be_used_as_context_manager(self) -> None:
        """create_progress should work as a context manager."""
        with create_progress() as progress:
            task_id = progress.add_task("テスト", total=10)
            progress.update(task_id, advance=5)
            assert progress.tasks[0].completed == 5


class TestProgressContext:
    """Tests for progress_context context manager."""

    def test_progress_context_prints_status_and_success_on_completion(self) -> None:
        """progress_context should print status on entry and success on exit."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        from company_research_agent.core import progress

        original_console = progress.console
        progress.console = test_console

        try:
            with progress_context("データ処理中"):
                pass  # Simulate work

            result = output.getvalue()
            assert "データ処理中" in result
            assert "完了" in result
        finally:
            progress.console = original_console

    def test_progress_context_prints_error_on_exception(self) -> None:
        """progress_context should print error message when exception occurs."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        from company_research_agent.core import progress

        original_console = progress.console
        progress.console = test_console

        try:
            with pytest.raises(ValueError):  # noqa: PT011
                with progress_context("データ処理中"):
                    raise ValueError("テストエラー")

            result = output.getvalue()
            assert "データ処理中" in result
            assert "失敗" in result
        finally:
            progress.console = original_console

    def test_progress_context_re_raises_exception(self) -> None:
        """progress_context should re-raise the original exception."""
        with pytest.raises(RuntimeError, match="Original error"):
            with progress_context("処理中"):
                raise RuntimeError("Original error")


class TestConsoleInstance:
    """Tests for module-level console instance."""

    def test_console_is_rich_console_instance(self) -> None:
        """Module-level console should be a Rich Console instance."""
        assert isinstance(console, Console)
