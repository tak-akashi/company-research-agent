"""LLMプロバイダーのプロトコル定義."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from typing import Any

T = TypeVar("T", bound=BaseModel)


class LLMProvider(Protocol):
    """LLMプロバイダーのプロトコル.

    各プロバイダー（OpenAI, Google, Anthropic, Ollama）はこのプロトコルを実装する。
    LangChainのChatModelをラップし、統一されたインターフェースを提供する。

    Example:
        >>> provider: LLMProvider = GoogleProvider(config)
        >>> result = await provider.ainvoke_structured(prompt, BusinessSummary)
    """

    @property
    def model_name(self) -> str:
        """使用中のモデル名を返す.

        Returns:
            モデル名（例: "gpt-4o", "gemini-2.5-flash-preview-05-20"）
        """
        ...

    @property
    def provider_name(self) -> str:
        """プロバイダー名を返す.

        Returns:
            プロバイダー名（"openai", "google", "anthropic", "ollama"のいずれか）
        """
        ...

    @property
    def supports_vision(self) -> bool:
        """ビジョン機能をサポートするかどうかを返す.

        Returns:
            ビジョン機能をサポートする場合True
        """
        ...

    def get_model(self) -> Any:
        """LangChain ChatModelインスタンスを返す.

        Returns:
            BaseChatModel互換のインスタンス
        """
        ...

    async def ainvoke_structured(
        self,
        prompt: str,
        output_schema: type[T],
    ) -> T:
        """構造化出力でLLMを非同期呼び出しする.

        LangChainのwith_structured_output()を使用してPydanticスキーマに
        従った出力を取得する。

        Args:
            prompt: LLMに送信するプロンプト
            output_schema: 出力のPydanticスキーマクラス

        Returns:
            スキーマに従った構造化出力

        Raises:
            LLMProviderError: LLM呼び出しに失敗した場合
        """
        ...

    async def ainvoke_vision(
        self,
        text_prompt: str,
        image_data: bytes,
        mime_type: str = "image/png",
    ) -> str:
        """ビジョン入力でLLMを非同期呼び出しする.

        画像とテキストを組み合わせたマルチモーダル入力でLLMを呼び出す。
        PDF解析（ページ画像からのテキスト抽出）に使用される。

        Args:
            text_prompt: テキストプロンプト
            image_data: 画像のバイナリデータ
            mime_type: 画像のMIMEタイプ（デフォルト: "image/png"）

        Returns:
            LLMからの応答テキスト

        Raises:
            LLMProviderError: ビジョン機能が非対応、またはLLM呼び出しに失敗した場合
        """
        ...
