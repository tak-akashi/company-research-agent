"""Progress display utilities using rich library."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

if TYPE_CHECKING:
    from collections.abc import Iterator


def _is_jupyter() -> bool:
    """Detect if running in a Jupyter notebook environment.

    Returns:
        True if running in Jupyter (ZMQInteractiveShell), False otherwise.
    """
    try:
        from IPython import get_ipython  # type: ignore[attr-defined]

        shell = get_ipython()  # type: ignore[no-untyped-call]
        if shell is None:
            return False
        # ZMQInteractiveShell is used in Jupyter notebooks
        return bool(shell.__class__.__name__ == "ZMQInteractiveShell")
    except ImportError:
        return False


def _create_console() -> Console:
    """Create a Console instance configured for the current environment.

    In Jupyter environments, we disable the terminal features to avoid
    output interleaving issues with logging.

    Returns:
        Configured Console instance.
    """
    if _is_jupyter():
        # In Jupyter, use force_terminal=False to avoid ANSI escape sequences
        # and set force_jupyter=True to use Jupyter-specific rendering
        return Console(force_terminal=False, force_jupyter=True)
    return Console()


# Global console instance (configured for the current environment)
console = _create_console()


def print_status(message: str) -> None:
    """Print a status message (blue, with arrow icon).

    Args:
        message: Status message to display.

    Example:
        >>> print_status("検索中...")
    """
    console.print(f"[bold blue]▶[/bold blue] {message}")


def print_success(message: str) -> None:
    """Print a success message (green, with checkmark icon).

    Args:
        message: Success message to display.

    Example:
        >>> print_success("ダウンロード完了")
    """
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str) -> None:
    """Print an error message (red, with cross icon).

    Args:
        message: Error message to display.

    Example:
        >>> print_error("ファイルが見つかりません")
    """
    console.print(f"[bold red]✗[/bold red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message (yellow, with warning icon).

    Args:
        message: Warning message to display.

    Example:
        >>> print_warning("キャッシュが古い可能性があります")
    """
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message (cyan, with info icon).

    Args:
        message: Info message to display.

    Example:
        >>> print_info("3件の書類が見つかりました")
    """
    console.print(f"[bold cyan]ℹ[/bold cyan] {message}")


def print_node_start(node_name: str) -> None:
    """Print a graph node start message (dimmed arrow, indented).

    Args:
        node_name: Name of the graph node starting execution.

    Example:
        >>> print_node_start("edinet")
        # Output: "  ▷ ノード: edinet を実行中..."
    """
    console.print(f"  [dim]▷[/dim] ノード: {node_name} を実行中...")


def print_node_complete(node_name: str, success: bool = True) -> None:
    """Print a graph node completion message (indented).

    Args:
        node_name: Name of the graph node that completed.
        success: Whether the node completed successfully.

    Example:
        >>> print_node_complete("edinet", success=True)
        # Output: "  ✓ ノード: edinet 完了"
        >>> print_node_complete("edinet", success=False)
        # Output: "  ✗ ノード: edinet 失敗"
    """
    if success:
        console.print(f"  [green]✓[/green] ノード: {node_name} 完了")
    else:
        console.print(f"  [red]✗[/red] ノード: {node_name} 失敗")


def create_progress() -> Progress:
    """Create a progress bar with spinner.

    Returns:
        Progress instance for tracking long-running tasks.

    Example:
        >>> with create_progress() as progress:
        ...     task = progress.add_task("ダウンロード中...", total=100)
        ...     progress.update(task, advance=10)
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )


# For contextmanager type hint compatibility
try:
    from contextlib import contextmanager as _contextmanager

    @_contextmanager
    def progress_context(description: str) -> Iterator[None]:
        """Context manager for showing progress during an operation.

        Args:
            description: Description of the ongoing operation.

        Yields:
            None

        Example:
            >>> with progress_context("データ処理中..."):
            ...     do_something()
        """
        print_status(description)
        try:
            yield
        except Exception:
            print_error(f"{description} - 失敗")
            raise
        else:
            print_success(f"{description} - 完了")

except ImportError:
    pass
