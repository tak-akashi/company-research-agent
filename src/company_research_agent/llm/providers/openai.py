"""OpenAI LLMプロバイダー."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from company_research_agent.llm.providers.base import BaseLLMProvider

if TYPE_CHECKING:
    from company_research_agent.llm.config import LLMConfig


class OpenAIProvider(BaseLLMProvider):
    """OpenAI APIプロバイダー.

    GPT-4o, GPT-5-mini等のモデルに対応。
    ビジョン機能はGPT-4o等のマルチモーダルモデルで利用可能。

    Example:
        >>> config = LLMConfig(provider=LLMProviderType.OPENAI, openai_api_key="sk-...")
        >>> provider = OpenAIProvider(config)
        >>> result = await provider.ainvoke_structured(prompt, BusinessSummary)
    """

    DEFAULT_MODEL = "gpt-4o"
    """デフォルトのモデル名."""

    DEFAULT_VISION_MODEL = "gpt-4o"
    """デフォルトのビジョン用モデル名."""

    def __init__(self, config: LLMConfig) -> None:
        """プロバイダーを初期化する.

        Args:
            config: LLM設定（openai_api_keyが必須）
        """
        super().__init__(config)

    @property
    def model_name(self) -> str:
        """使用中のモデル名を返す."""
        return self._config.get_effective_model() or self.DEFAULT_MODEL

    @property
    def provider_name(self) -> str:
        """プロバイダー名を返す."""
        return "openai"

    def _create_model(self) -> Any:
        """OpenAI ChatModelを作成する."""
        from langchain_openai import ChatOpenAI
        from pydantic import SecretStr

        from company_research_agent.core.exceptions import LLMProviderError

        api_key = self._config.openai_api_key
        if not api_key:
            raise LLMProviderError(
                message="OpenAI API key is required",
                provider=self.provider_name,
                model=self.model_name,
            )
        return ChatOpenAI(
            model=self.model_name,
            api_key=SecretStr(api_key),
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
        )
