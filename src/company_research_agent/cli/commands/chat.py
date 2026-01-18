"""Chat command implementation - interactive mode with conversation history."""

from __future__ import annotations

import argparse
from typing import Any

from company_research_agent.cli.output import print_error
from company_research_agent.cli.rich_output import (
    print_chat_goodbye,
    print_chat_prompt,
    print_chat_welcome,
    print_history_cleared,
    print_processing,
    print_query_result,
    print_thinking,
    print_tools_summary,
)
from company_research_agent.orchestrator.query_orchestrator import QueryOrchestrator


async def cmd_chat(args: argparse.Namespace) -> int:
    """対話モードコマンド（会話履歴保持）.

    インタラクティブに質問を入力し、QueryOrchestratorに問い合わせる。
    セッション中の会話履歴は保持され、文脈を踏まえた回答が可能。

    Returns:
        終了コード (0: 成功, 1: エラー)
    """
    verbose = getattr(args, "verbose", False)

    print_chat_welcome()

    try:
        if verbose:
            print_thinking("QueryOrchestratorを初期化中...")

        orchestrator = QueryOrchestrator()
        messages: list[Any] = []  # 会話履歴

        while True:
            # ユーザー入力を受け取る
            query = print_chat_prompt().strip()

            # 終了コマンド
            if query.lower() in ("q", "quit", "exit"):
                print_chat_goodbye()
                break

            # 履歴クリアコマンド
            if query.lower() == "clear":
                messages = []
                print_history_cleared()
                continue

            # ヘルプコマンド
            if query.lower() == "help":
                _print_help()
                continue

            # 空入力はスキップ
            if not query:
                continue

            try:
                if verbose:
                    print_thinking(f"クエリ実行中: {query}")
                else:
                    print_processing()

                # 会話履歴を保持してクエリ実行
                result, messages = await orchestrator.process_with_history(query, messages)

                if verbose:
                    print_tools_summary(result.tools_used)

                print_query_result(result)
                print()  # 空行

            except Exception as e:
                print_error(f"クエリ実行エラー: {e}")
                # エラーが発生しても対話は継続
                continue

        return 0

    except KeyboardInterrupt:
        print_chat_goodbye()
        return 0
    except Exception as e:
        print_error(f"対話モードエラー: {e}")
        return 1


def _print_help() -> None:
    """ヘルプメッセージを表示."""
    from rich.console import Console

    console = Console()
    console.print()
    console.print("[bold]使用可能なコマンド:[/bold]")
    console.print("  [cyan]q[/cyan] / [cyan]quit[/cyan] / [cyan]exit[/cyan] - 対話モードを終了")
    console.print("  [cyan]clear[/cyan] - 会話履歴をクリアして新しい会話を開始")
    console.print("  [cyan]help[/cyan] - このヘルプを表示")
    console.print()
    console.print("[bold]使用例:[/bold]")
    console.print("  [dim]質問:[/dim] トヨタの有価証券報告書を探して")
    console.print("  [dim]質問:[/dim] 分析して")
    console.print("  [dim]質問:[/dim] ソニーと比較して")
    console.print()
