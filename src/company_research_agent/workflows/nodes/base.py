"""Base class for analysis nodes.

LangGraphワークフローで使用する分析ノードの基底クラスを定義する。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

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
        logger.info(f"Starting node: {self.name}")
        try:
            result = await self.execute(state)
            update = self._update_state(state, result)
            # completed_nodesにノード名を追加
            update.setdefault("completed_nodes", []).append(self.name)
            logger.info(f"Completed node: {self.name}")
            return update
        except Exception as e:
            logger.exception(f"Error in node {self.name}: {e}")
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

    GeminiClientを使用してLLMを呼び出す共通処理を提供する。
    """

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
