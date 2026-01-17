"""Ollama LLMプロバイダー."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from company_research_agent.llm.providers.base import BaseLLMProvider

if TYPE_CHECKING:
    from company_research_agent.llm.config import LLMConfig


class OllamaProvider(BaseLLMProvider):
    """Ollama ローカルLLMプロバイダー.

    llama3.2, gpt-oss-20b, llava等のローカルモデルに対応。
    ビジョン機能はllava系モデルのみ対応。

    Example:
        >>> config = LLMConfig(
        ...     provider=LLMProviderType.OLLAMA,
        ...     model="gpt-oss-20b",
        ...     ollama_base_url="http://localhost:11434",
        ... )
        >>> provider = OllamaProvider(config)
        >>> result = await provider.ainvoke_structured(prompt, BusinessSummary)
    """

    DEFAULT_MODEL = "llama3.2"
    """デフォルトのテキスト用モデル名."""

    DEFAULT_VISION_MODEL = "llava"
    """デフォルトのビジョン用モデル名."""

    # ビジョン対応モデルのプレフィックス
    VISION_CAPABLE_PREFIXES = ("llava", "bakllava", "moondream")
    """ビジョン対応モデルのプレフィックス."""

    def __init__(self, config: LLMConfig) -> None:
        """プロバイダーを初期化する.

        Args:
            config: LLM設定
        """
        super().__init__(config)

    @property
    def model_name(self) -> str:
        """使用中のモデル名を返す."""
        return self._config.get_effective_model() or self.DEFAULT_MODEL

    @property
    def provider_name(self) -> str:
        """プロバイダー名を返す."""
        return "ollama"

    @property
    def supports_vision(self) -> bool:
        """ビジョン機能をサポートするかどうかを返す.

        llava, bakllava, moondream等のマルチモーダルモデルのみ対応。
        """
        model_lower = self.model_name.lower()
        return any(model_lower.startswith(prefix) for prefix in self.VISION_CAPABLE_PREFIXES)

    def _create_model(self) -> Any:
        """Ollama ChatModelを作成する."""
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=self.model_name,
            base_url=self._config.ollama_base_url,
            # ChatOllamaはtimeoutパラメータを直接サポートしないため省略
        )
