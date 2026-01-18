"""Base class for analysis nodes.

LangGraphワークフローで使用する分析ノードの基底クラスを定義する。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, cast

from company_research_agent.workflows.state import AnalysisState

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AnalysisNode(ABC, Generic[T]):
    """分析ノードの基底クラス.

    LangGraphのノードとして使用される。各サブクラスは
    execute()メソッドを実装して分析ロジックを提供する。

    Example:
        class BusinessSummaryNode(AnalysisNode[BusinessSummary]):
            @property
            def name(self) -> str:
                return "business_summary"

            async def execute(self, state: AnalysisState) -> BusinessSummary:
                # 分析ロジック
                return BusinessSummary(...)

            def _update_state(self, state: AnalysisState, result: BusinessSummary) -> dict:
                return {
                    "business_summary": result,
                    "completed_nodes": [self.name],
                }
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """ノード名を返す.

        Returns:
            ノードの識別名（例: 'business_summary', 'risk_extraction'）
        """
        ...

    @abstractmethod
    async def execute(self, state: AnalysisState) -> T:
        """ノードを実行する.

        Args:
            state: 現在のワークフロー状態

        Returns:
            分析結果（型Tのインスタンス）

        Raises:
            AnalysisError: 分析処理に失敗した場合
        """
        ...

    @abstractmethod
    def _update_state(self, state: AnalysisState, result: T) -> dict[str, Any]:
        """実行結果でStateを更新する.

        Args:
            state: 現在のワークフロー状態
            result: execute()の戻り値

        Returns:
            更新するキーと値のdict
        """
        ...

    async def __call__(self, state: AnalysisState) -> dict[str, Any]:
        """LangGraphから呼び出されるエントリーポイント.

        execute()を呼び出し、結果でStateを更新する。
        エラーが発生した場合はエラー情報をStateに追加する。

        Args:
            state: 現在のワークフロー状態

        Returns:
            更新するキーと値のdict
        """
        from company_research_agent.core.progress import (
            print_node_complete,
            print_node_start,
        )

        print_node_start(self.name)
        logger.info(f"Starting node: {self.name}")
        try:
            result = await self.execute(state)
            update = self._update_state(state, result)
            # completed_nodesにノード名を追加
            update.setdefault("completed_nodes", []).append(self.name)
            logger.info(f"Completed node: {self.name}")
            print_node_complete(self.name, success=True)
            return update
        except Exception as e:
            logger.exception(f"Error in node {self.name}: {e}")
            print_node_complete(self.name, success=False)
            return self._handle_error(state, e)

    def _handle_error(self, state: AnalysisState, error: Exception) -> dict[str, Any]:
        """エラーハンドリング.

        Args:
            state: 現在のワークフロー状態
            error: 発生した例外

        Returns:
            エラー情報を含むdict
        """
        error_message = f"{self.name}: {type(error).__name__}: {str(error)}"
        return {"errors": [error_message]}

    def _get_required_field(
        self, state: AnalysisState, field: str, field_name: str | None = None
    ) -> Any:
        """必須フィールドを取得する.

        Args:
            state: 現在のワークフロー状態
            field: フィールドのキー名
            field_name: エラーメッセージ用のフィールド名（省略時はfieldを使用）

        Returns:
            フィールドの値

        Raises:
            ValueError: フィールドがNoneまたは空の場合
        """
        value = state.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            display_name = field_name or field
            raise ValueError(f"Required field is missing or empty: {display_name}")
        return value


class LLMAnalysisNode(AnalysisNode[T]):
    """LLM呼び出しを行う分析ノードの基底クラス.

    LLMProviderを使用してLLMを呼び出す共通処理を提供する。
    プロバイダーは環境変数で切り替え可能（OpenAI, Google, Anthropic, Ollama）。

    Example:
        class BusinessSummaryNode(LLMAnalysisNode[BusinessSummary]):
            @property
            def prompt_template(self) -> str:
                return BUSINESS_SUMMARY_PROMPT

            @property
            def output_schema(self) -> type[BusinessSummary]:
                return BusinessSummary

            async def execute(self, state: AnalysisState) -> BusinessSummary:
                prompt = self._build_prompt(state)
                return await self._invoke_llm(prompt)
    """

    def __init__(self, llm_provider: Any = None) -> None:
        """ノードを初期化する.

        Args:
            llm_provider: LLMプロバイダー。Noneの場合は環境変数から自動設定。
        """
        self._llm_provider = llm_provider

    @property
    def llm_provider(self) -> Any:
        """LLMプロバイダーを取得する（遅延初期化）.

        Returns:
            BaseLLMProviderインスタンス
        """
        if self._llm_provider is None:
            from company_research_agent.llm.factory import get_default_provider

            self._llm_provider = get_default_provider()
        return self._llm_provider

    @property
    @abstractmethod
    def prompt_template(self) -> str:
        """プロンプトテンプレートを返す.

        Returns:
            LLM呼び出し用のプロンプトテンプレート
        """
        ...

    @property
    @abstractmethod
    def output_schema(self) -> type[T]:
        """出力スキーマのクラスを返す.

        Returns:
            Pydanticモデルのクラス
        """
        ...

    def _build_prompt(self, state: AnalysisState) -> str:
        """プロンプトを構築する.

        サブクラスでオーバーライドして、stateから必要な情報を
        プロンプトに埋め込む。

        Args:
            state: 現在のワークフロー状態

        Returns:
            LLM呼び出し用のプロンプト
        """
        markdown_content = self._get_required_field(state, "markdown_content")
        return self.prompt_template.format(content=markdown_content)

    async def _invoke_llm(self, prompt: str) -> T:
        """LLMを呼び出して構造化出力を取得する.

        Args:
            prompt: LLMに送信するプロンプト

        Returns:
            スキーマに従った構造化出力

        Raises:
            LLMProviderError: LLM呼び出しに失敗した場合
        """
        logger.debug(
            f"Invoking LLM: provider={self.llm_provider.provider_name}, "
            f"model={self.llm_provider.model_name}, schema={self.output_schema.__name__}"
        )
        result = await self.llm_provider.ainvoke_structured(
            prompt=prompt,
            output_schema=self.output_schema,
        )
        return cast(T, result)
