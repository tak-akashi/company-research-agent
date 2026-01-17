"""自然言語クエリオーケストレーター.

自然言語クエリを処理するReActエージェントを提供する。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from company_research_agent.llm.factory import get_default_provider
from company_research_agent.prompts.orchestrator_system import ORCHESTRATOR_SYSTEM_PROMPT
from company_research_agent.schemas.query_schemas import OrchestratorResult
from company_research_agent.tools import (
    analyze_document,
    compare_documents,
    download_document,
    search_company,
    search_documents,
    summarize_document,
)

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph

    from company_research_agent.llm.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class QueryOrchestrator:
    """自然言語クエリを処理するReActエージェント.

    ユーザーの自然言語クエリを解釈し、適切なツールを選択・実行して
    結果を返す。

    Example:
        >>> orchestrator = QueryOrchestrator()
        >>> result = await orchestrator.process("トヨタの有報を探して")
        >>> print(result.intent)  # "検索"
        >>> print(result.tools_used)  # ["search_company", "search_documents"]
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider | None = None,
        tools: list[BaseTool] | None = None,
    ) -> None:
        """オーケストレーターを初期化する.

        Args:
            llm_provider: LLMプロバイダー。Noneの場合は環境変数から自動設定。
            tools: 使用するツールのリスト。Noneの場合はデフォルトツールを使用。
        """
        self._llm_provider = llm_provider or get_default_provider()
        self._tools = tools or self._default_tools()
        self._agent: CompiledStateGraph[Any] | None = None

    def _default_tools(self) -> list[BaseTool]:
        """デフォルトのツールリストを返す.

        Returns:
            検索系・分析系ツールのリスト
        """
        return [
            search_company,
            search_documents,
            download_document,
            analyze_document,
            compare_documents,
            summarize_document,
        ]

    def _build_agent(self) -> CompiledStateGraph[Any]:
        """ReActエージェントを構築する.

        Returns:
            コンパイル済みのStateGraph
        """
        model = self._llm_provider.get_model()
        return create_react_agent(
            model=model,
            tools=self._tools,
            prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        )

    def get_agent(self) -> CompiledStateGraph[Any]:
        """エージェントを取得する（遅延初期化）.

        Returns:
            コンパイル済みのStateGraph
        """
        if self._agent is None:
            self._agent = self._build_agent()
            logger.info("QueryOrchestrator agent initialized")
        return self._agent

    async def process(self, query: str) -> OrchestratorResult:
        """クエリを処理し、結果を返す.

        Args:
            query: ユーザーの自然言語クエリ

        Returns:
            処理結果（意図、使用ツール、結果を含む）
        """
        logger.info(f"Processing query: {query}")

        agent = self.get_agent()

        # エージェント実行
        result = await agent.ainvoke({"messages": [("user", query)]})

        # 結果を解析
        return self._parse_result(query, result)

    def _parse_result(self, query: str, result: dict[str, Any]) -> OrchestratorResult:
        """エージェント結果を解析してOrchestratorResultに変換する.

        Args:
            query: 元のクエリ
            result: エージェントの実行結果

        Returns:
            OrchestratorResult
        """
        messages = result.get("messages", [])

        # 使用したツールを抽出
        tools_used: list[str] = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get("name", "")
                    if tool_name and tool_name not in tools_used:
                        tools_used.append(tool_name)

        # 意図を推定
        intent = self._infer_intent(tools_used)

        # 最終メッセージを取得
        final_result: Any = None
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, "content"):
                final_result = last_msg.content

        return OrchestratorResult(
            query=query,
            intent=intent,
            result=final_result,
            tools_used=tools_used,
        )

    def _infer_intent(self, tools_used: list[str]) -> str:
        """使用ツールから意図を推定する.

        Args:
            tools_used: 使用されたツールのリスト

        Returns:
            推定された意図
        """
        if "analyze_document" in tools_used:
            return "分析"
        if "compare_documents" in tools_used:
            return "比較"
        if "summarize_document" in tools_used:
            return "要約"
        if "download_document" in tools_used:
            return "取得"
        if "search_documents" in tools_used or "search_company" in tools_used:
            return "検索"
        return "その他"
