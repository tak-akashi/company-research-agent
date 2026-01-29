"""自然言語クエリオーケストレーター.

自然言語クエリを処理するReActエージェントを提供する。
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from company_research_agent.core.text_utils import extract_text_from_content
from company_research_agent.llm.factory import get_default_provider
from company_research_agent.prompts.orchestrator_system import ORCHESTRATOR_SYSTEM_PROMPT
from company_research_agent.schemas.query_schemas import (
    DocumentResultMetadata,
    OrchestratorResult,
)
from company_research_agent.tools import (
    analyze_document,
    compare_documents,
    download_document,
    search_company,
    search_documents,
    summarize_document,
)
from company_research_agent.tools.ir_tools import (
    explore_ir_page,
    fetch_ir_documents,
    fetch_ir_news,
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
            fetch_ir_documents,
            fetch_ir_news,
            explore_ir_page,
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

    def _get_langfuse_config(self, query: str) -> dict[str, Any]:
        """Langfuse用のconfig設定を取得する.

        Args:
            query: ユーザークエリ

        Returns:
            エージェント実行用のconfig辞書
        """
        from company_research_agent.observability.handler import (
            get_langfuse_handler,
            is_langfuse_enabled,
        )

        if not is_langfuse_enabled():
            return {}

        handler = get_langfuse_handler(
            trace_name="query-orchestrator",
            tags=["orchestrator", f"provider:{self._llm_provider.provider_name}"],
            metadata={
                "query_preview": query[:100] if query else None,
                "model": self._llm_provider.model_name,
            },
        )

        if handler:
            return {"callbacks": [handler]}
        return {}

    async def process(self, query: str) -> OrchestratorResult:
        """クエリを処理し、結果を返す.

        Args:
            query: ユーザーの自然言語クエリ

        Returns:
            処理結果（意図、使用ツール、結果を含む）
        """
        logger.info(f"Processing query: {query}")

        agent = self.get_agent()

        # Langfuse config を取得
        config = self._get_langfuse_config(query)

        # エージェント実行
        result = await agent.ainvoke(
            {"messages": [("user", query)]},
            config=config,  # type: ignore[arg-type]
        )

        # 結果を解析
        return self._parse_result(query, result)

    async def process_with_history(
        self,
        query: str,
        messages: list[Any] | None = None,
    ) -> tuple[OrchestratorResult, list[Any]]:
        """会話履歴を保持してクエリを処理する.

        対話モード用のメソッド。過去のメッセージ履歴を受け取り、
        新しいクエリを追加して処理し、更新された履歴を返す。

        Args:
            query: ユーザーの自然言語クエリ
            messages: 過去のメッセージ履歴（初回はNone）

        Returns:
            (処理結果, 更新されたメッセージ履歴) のタプル

        Example:
            >>> orchestrator = QueryOrchestrator()
            >>> result, history = await orchestrator.process_with_history("トヨタの有報を探して")
            >>> result2, history = await orchestrator.process_with_history("分析して", history)
            >>> # result2は前の文脈を踏まえた回答
        """
        logger.info(f"Processing query with history: {query}")

        if messages is None:
            messages = []

        # 新しいユーザーメッセージを追加
        messages.append(("user", query))

        agent = self.get_agent()
        config = self._get_langfuse_config(query)

        # エージェント実行
        result = await agent.ainvoke(
            {"messages": messages},
            config=config,  # type: ignore[arg-type]
        )

        # 更新されたメッセージ履歴を取得
        updated_messages = result.get("messages", [])

        return self._parse_result(query, result), updated_messages

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
        final_result: str | None = None
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, "content"):
                extracted = extract_text_from_content(last_msg.content)
                final_result = extracted if extracted else None

        # ドキュメントメタデータを抽出
        documents = self._extract_document_metadata(messages)

        return OrchestratorResult(
            query=query,
            intent=intent,
            result=final_result,
            tools_used=tools_used,
            documents=documents,
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
        if "fetch_ir_documents" in tools_used or "explore_ir_page" in tools_used:
            return "IR資料取得"
        if "fetch_ir_news" in tools_used:
            return "IRニュース取得"
        if "search_documents" in tools_used or "search_company" in tools_used:
            return "検索"
        return "その他"

    def _extract_document_metadata(self, messages: list[Any]) -> list[DocumentResultMetadata]:
        """ツールメッセージからドキュメントメタデータを抽出する.

        analyze_document/search_documentsツールの結果からメタデータを抽出し、
        DocumentResultMetadataのリストとして返す。

        Args:
            messages: エージェントのメッセージリスト

        Returns:
            抽出されたドキュメントメタデータのリスト
        """
        documents: list[DocumentResultMetadata] = []
        seen_doc_ids: set[str] = set()  # 重複を防ぐ

        for msg in messages:
            msg_type = type(msg).__name__

            # ToolMessageの場合
            if msg_type == "ToolMessage":
                # artifact属性をチェック（LangChainではツール結果がartifactに格納されることがある）
                if hasattr(msg, "artifact") and msg.artifact is not None:
                    self._extract_from_artifact(msg.artifact, documents, seen_doc_ids)

            # contentをチェック
            if hasattr(msg, "content"):
                content = msg.content

                # contentが文字列の場合、JSONパースを試みる
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except (json.JSONDecodeError, TypeError):
                        continue

                # contentがリストの場合（search_documentsの結果など）
                if isinstance(content, list):
                    self._extract_from_list(content, documents, seen_doc_ids)
                # contentがdictの場合（analyze_documentの結果など）
                elif isinstance(content, dict):
                    self._extract_from_dict(content, documents, seen_doc_ids)

        return documents

    def _extract_from_artifact(
        self,
        artifact: Any,
        documents: list[DocumentResultMetadata],
        seen_doc_ids: set[str],
    ) -> None:
        """artifact属性からメタデータを抽出する."""
        if isinstance(artifact, list):
            self._extract_from_list(artifact, documents, seen_doc_ids)
        elif isinstance(artifact, dict):
            self._extract_from_dict(artifact, documents, seen_doc_ids)

    def _extract_from_list(
        self,
        items: list[Any],
        documents: list[DocumentResultMetadata],
        seen_doc_ids: set[str],
    ) -> None:
        """リストからメタデータを抽出する（search_documentsの結果など）."""
        for item in items:
            doc_id = None
            filer_name = None
            doc_description = None
            period_start = None
            period_end = None

            # Pydanticモデルの場合
            if hasattr(item, "doc_id"):
                doc_id = item.doc_id
                filer_name = getattr(item, "filer_name", None)
                doc_description = getattr(item, "doc_description", None)
                period_start = getattr(item, "period_start", None)
                period_end = getattr(item, "period_end", None)
            # dictの場合
            elif isinstance(item, dict):
                doc_id = item.get("doc_id")
                filer_name = item.get("filer_name")
                doc_description = item.get("doc_description")
                period_start = item.get("period_start")
                period_end = item.get("period_end")

            if doc_id and doc_id not in seen_doc_ids:
                seen_doc_ids.add(doc_id)
                documents.append(
                    DocumentResultMetadata(
                        doc_id=doc_id,
                        filer_name=filer_name,
                        doc_description=doc_description,
                        period_start=period_start,
                        period_end=period_end,
                    )
                )

    def _extract_from_dict(
        self,
        content: dict[str, Any],
        documents: list[DocumentResultMetadata],
        seen_doc_ids: set[str],
    ) -> None:
        """dictからメタデータを抽出する（analyze_documentの結果など）."""
        if "metadata" in content:
            meta = content["metadata"]
            if isinstance(meta, dict):
                doc_id = meta.get("doc_id")
                if doc_id and doc_id not in seen_doc_ids:
                    seen_doc_ids.add(doc_id)
                    documents.append(
                        DocumentResultMetadata(
                            doc_id=doc_id,
                            filer_name=meta.get("filer_name"),
                            doc_description=meta.get("doc_description"),
                            period_start=meta.get("period_start"),
                            period_end=meta.get("period_end"),
                        )
                    )
