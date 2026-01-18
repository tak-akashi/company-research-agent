"""Orchestrator module - Natural language query processing.

自然言語クエリを処理するオーケストレーターを提供する。

Example:
    from company_research_agent.orchestrator import QueryOrchestrator

    orchestrator = QueryOrchestrator()

    # 検索のみ
    result = await orchestrator.process("トヨタの有報を探して")

    # 分析まで
    result = await orchestrator.process("トヨタの有報を分析して")

    # 比較
    result = await orchestrator.process("トヨタとホンダの有報を比較して")
"""

from company_research_agent.orchestrator.query_orchestrator import QueryOrchestrator

__all__ = ["QueryOrchestrator"]
