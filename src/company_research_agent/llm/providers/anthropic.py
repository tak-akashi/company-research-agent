"""Anthropic Claude LLMプロバイダー."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from company_research_agent.llm.providers.base import BaseLLMProvider

if TYPE_CHECKING:
    from company_research_agent.llm.config import LLMConfig


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude APIプロバイダー.

    Claude Sonnet, Opus等のモデルに対応。
    Claude 3以降でビジョン機能が利用可能。

    Example:
        >>> config = LLMConfig(provider=LLMProviderType.ANTHROPIC, anthropic_api_key="sk-ant-...")
        >>> provider = AnthropicProvider(config)
        >>> result = await provider.ainvoke_structured(prompt, BusinessSummary)
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    """デフォルトのモデル名."""

    def __init__(self, config: LLMConfig) -> None:
        """プロバイダーを初期化する.

        Args:
            config: LLM設定（anthropic_api_keyが必須）
        """
        super().__init__(config)

    @property
    def model_name(self) -> str:
        """使用中のモデル名を返す."""
        return self._config.get_effective_model() or self.DEFAULT_MODEL

    @property
    def provider_name(self) -> str:
        """プロバイダー名を返す."""
        return "anthropic"

    def _create_model(self) -> Any:
        """Anthropic Claude ChatModelを作成する."""
        from langchain_anthropic import ChatAnthropic
        from pydantic import SecretStr

        from company_research_agent.core.exceptions import LLMProviderError

        api_key = self._config.anthropic_api_key
        if not api_key:
            raise LLMProviderError(
                message="Anthropic API key is required",
                provider=self.provider_name,
                model=self.model_name,
            )
        return ChatAnthropic(
            model_name=self.model_name,
            api_key=SecretStr(api_key),
            timeout=float(self._config.timeout),
            max_retries=self._config.max_retries,
        )  # type: ignore[call-arg]
