"""Query command implementation - single natural language query execution."""

from __future__ import annotations

import argparse

from company_research_agent.cli.output import print_error
from company_research_agent.cli.rich_output import (
    print_query_result,
    print_thinking,
    print_tools_summary,
)
from company_research_agent.orchestrator.query_orchestrator import QueryOrchestrator


async def cmd_query(args: argparse.Namespace) -> int:
    """単発自然言語クエリコマンド.

    自然言語でQueryOrchestratorに問い合わせを行い、結果を表示する。

    Returns:
        終了コード (0: 成功, 1: エラー)
    """
    query = args.query
    verbose = getattr(args, "verbose", False)

    if not query or not query.strip():
        print_error("クエリを指定してください")
        return 1

    try:
        if verbose:
            print_thinking("QueryOrchestratorを初期化中...")

        orchestrator = QueryOrchestrator()

        if verbose:
            print_thinking(f"クエリ実行中: {query}")

        result = await orchestrator.process(query)

        if verbose:
            print_tools_summary(result.tools_used)

        print_query_result(result)
        return 0

    except Exception as e:
        print_error(f"クエリ実行エラー: {e}")
        return 1
