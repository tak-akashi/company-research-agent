"""LLMプロバイダーの基底クラス."""

from __future__ import annotations

import base64
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel

from company_research_agent.core.exceptions import LLMProviderError

if TYPE_CHECKING:
    from langchain_core.callbacks import BaseCallbackHandler

    from company_research_agent.llm.config import LLMConfig

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """LLMプロバイダーの基底クラス.

    共通処理（モデル初期化、エラーハンドリング、ロギング）を提供する。
    各プロバイダーは_create_model()をオーバーライドして固有のモデルを作成する。

    Example:
        >>> class MyProvider(BaseLLMProvider):
        ...     def _create_model(self) -> Any:
        ...         return SomeChatModel(...)
    """

    def __init__(self, config: LLMConfig) -> None:
        """プロバイダーを初期化する.

        Args:
            config: LLM設定
        """
        self._config = config
        self._model: Any = None

    @property
    @abstractmethod
    def model_name(self) -> str:
        """使用中のモデル名を返す."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """プロバイダー名を返す."""
        ...

    @property
    def supports_vision(self) -> bool:
        """ビジョン機能をサポートするかどうかを返す.

        デフォルトはTrue。非対応のプロバイダー/モデルはオーバーライドする。
        """
        return True

    @abstractmethod
    def _create_model(self) -> Any:
        """LangChain ChatModelを作成する.

        サブクラスでオーバーライドして、各プロバイダー固有のモデルを作成する。

        Returns:
            BaseChatModel互換のインスタンス
        """
        ...

    def get_model(self) -> Any:
        """LangChain ChatModelインスタンスを返す（遅延初期化）.

        Returns:
            BaseChatModel互換のインスタンス
        """
        if self._model is None:
            self._model = self._create_model()
            logger.info(f"Created {self.provider_name} model: {self.model_name}")
        return self._model

    def _get_callbacks(
        self,
        callbacks: list[BaseCallbackHandler] | None = None,
    ) -> list[Any]:
        """コールバックリストを構築する.

        明示的なcallbacksが渡されない場合、Langfuseハンドラーを自動取得する。

        Args:
            callbacks: 明示的なコールバックリスト

        Returns:
            使用するコールバックのリスト
        """
        if callbacks is not None:
            return list(callbacks)

        from company_research_agent.observability.handler import (
            create_trace_handler,
            is_langfuse_enabled,
        )

        if is_langfuse_enabled():
            handler = create_trace_handler(
                operation="llm-call",
                provider=self.provider_name,
                model=self.model_name,
            )
            if handler:
                return [handler]

        return []

    async def ainvoke_structured(
        self,
        prompt: str,
        output_schema: type[T],
        callbacks: list[BaseCallbackHandler] | None = None,
    ) -> T:
        """構造化出力でLLMを非同期呼び出しする.

        Args:
            prompt: LLMに送信するプロンプト
            output_schema: 出力のPydanticスキーマクラス
            callbacks: コールバックハンドラーリスト（オプション）

        Returns:
            スキーマに従った構造化出力

        Raises:
            LLMProviderError: LLM呼び出しに失敗した場合
        """
        try:
            model = self.get_model()
            structured_model = model.with_structured_output(output_schema)

            effective_callbacks = self._get_callbacks(callbacks)
            config = {"callbacks": effective_callbacks} if effective_callbacks else {}

            result: T = await structured_model.ainvoke(prompt, config=config)
            logger.debug(f"{self.provider_name} structured output: {type(result).__name__}")
            return result
        except Exception as e:
            logger.exception(f"LLM invocation failed: {self.provider_name}")
            raise LLMProviderError(
                message=str(e),
                provider=self.provider_name,
                model=self.model_name,
            ) from e

    async def ainvoke_vision(
        self,
        text_prompt: str,
        image_data: bytes,
        mime_type: str = "image/png",
        callbacks: list[BaseCallbackHandler] | None = None,
    ) -> str:
        """ビジョン入力でLLMを非同期呼び出しする.

        Args:
            text_prompt: テキストプロンプト
            image_data: 画像のバイナリデータ
            mime_type: 画像のMIMEタイプ
            callbacks: コールバックハンドラーリスト（オプション）

        Returns:
            LLMからの応答テキスト

        Raises:
            LLMProviderError: ビジョン機能が非対応、またはLLM呼び出しに失敗した場合
        """
        if not self.supports_vision:
            raise LLMProviderError(
                message=f"Vision not supported by model: {self.model_name}",
                provider=self.provider_name,
                model=self.model_name,
            )

        try:
            from langchain_core.messages import HumanMessage

            model = self.get_model()

            # Base64エンコード
            b64_data = base64.standard_b64encode(image_data).decode("utf-8")

            # マルチモーダルメッセージを作成
            message = HumanMessage(
                content=[
                    {"type": "text", "text": text_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{b64_data}"},
                    },
                ]
            )

            effective_callbacks = self._get_callbacks(callbacks)
            config = {"callbacks": effective_callbacks} if effective_callbacks else {}

            response = await model.ainvoke([message], config=config)
            result = str(response.content).strip()
            logger.debug(f"{self.provider_name} vision output: {len(result)} chars")
            return result

        except LLMProviderError:
            raise
        except Exception as e:
            logger.exception(f"Vision invocation failed: {self.provider_name}")
            raise LLMProviderError(
                message=str(e),
                provider=self.provider_name,
                model=self.model_name,
            ) from e
