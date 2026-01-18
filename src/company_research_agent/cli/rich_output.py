"""Rich整形出力ユーティリティ.

クエリ結果や対話モードの出力をRichライブラリで整形する。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from company_research_agent.core.text_utils import extract_text_from_content

if TYPE_CHECKING:
    from company_research_agent.schemas.query_schemas import OrchestratorResult

console = Console()


def print_query_result(result: OrchestratorResult) -> None:
    """クエリ結果をパネル形式で表示.

    Args:
        result: オーケストレーター処理結果
    """
    raw_content = result.result

    if raw_content is None:
        content = "(結果なし)"
    else:
        # リスト形式（マルチモーダル）の場合もテキストを抽出
        content = extract_text_from_content(raw_content)
        if not content:
            content = "(結果なし)"

    # 常にマークダウンとして表示
    md = Markdown(content)
    panel = Panel(
        md,
        title=f"[bold cyan]回答[/bold cyan] ({result.intent})",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)


def print_thinking(message: str) -> None:
    """処理中メッセージを表示（verbose時）.

    Args:
        message: 表示するメッセージ
    """
    console.print(f"[dim]  {message}[/dim]")


def print_tool_call(tool_name: str, args: dict[str, object] | None = None) -> None:
    """ツール呼び出しを表示（verbose時）.

    Args:
        tool_name: ツール名
        args: ツール引数
    """
    args_str = ""
    if args:
        args_str = f" ({', '.join(f'{k}={v}' for k, v in args.items())})"
    console.print(f"[yellow]  -> {tool_name}{args_str}[/yellow]")


def print_tools_summary(tools_used: list[str]) -> None:
    """使用したツールのサマリを表示.

    Args:
        tools_used: 使用したツール名のリスト
    """
    if tools_used:
        tools_str = ", ".join(tools_used)
        console.print(f"[dim]使用ツール: {tools_str}[/dim]")


def print_chat_welcome() -> None:
    """対話モードの開始メッセージを表示."""
    console.print()
    console.print(
        Panel(
            "[bold]企業情報リサーチアシスタント[/bold]\n\n"
            "自然言語で企業情報を問い合わせできます。\n"
            "会話履歴は保持されるため、文脈を踏まえた質問が可能です。\n\n"
            "[dim]コマンド:[/dim]\n"
            "  [cyan]q[/cyan] / [cyan]quit[/cyan] / [cyan]exit[/cyan] - 終了\n"
            "  [cyan]clear[/cyan] - 会話履歴をクリア\n"
            "  [cyan]help[/cyan] - ヘルプ表示",
            title="[bold green]対話モード[/bold green]",
            border_style="green",
        )
    )
    console.print()


def print_chat_prompt() -> str:
    """対話プロンプトを表示して入力を受け取る.

    Returns:
        ユーザー入力
    """
    try:
        return console.input("[bold cyan]質問:[/bold cyan] ")
    except EOFError:
        return "quit"


def print_chat_goodbye() -> None:
    """対話モード終了メッセージを表示."""
    console.print("\n[dim]対話モードを終了しました。[/dim]")


def print_history_cleared() -> None:
    """履歴クリアメッセージを表示."""
    console.print("[yellow]会話履歴をクリアしました。[/yellow]\n")


def print_processing() -> None:
    """処理中表示."""
    console.print("[dim]処理中...[/dim]")
