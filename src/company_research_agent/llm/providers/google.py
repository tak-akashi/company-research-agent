"""Google Gemini LLMプロバイダー."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from company_research_agent.llm.providers.base import BaseLLMProvider

if TYPE_CHECKING:
    from company_research_agent.llm.config import LLMConfig


class GoogleProvider(BaseLLMProvider):
    """Google Gemini APIプロバイダー.

    Gemini 2.5 Flash, Pro等のモデルに対応。
    全モデルでビジョン機能が利用可能。

    Example:
        >>> config = LLMConfig(provider=LLMProviderType.GOOGLE, google_api_key="AIza...")
        >>> provider = GoogleProvider(config)
        >>> result = await provider.ainvoke_structured(prompt, BusinessSummary)
    """

    DEFAULT_MODEL = "gemini-2.5-flash"
    """デフォルトのモデル名."""

    def __init__(self, config: LLMConfig) -> None:
        """プロバイダーを初期化する.

        Args:
            config: LLM設定（google_api_keyが必須）
        """
        super().__init__(config)

    @property
    def model_name(self) -> str:
        """使用中のモデル名を返す."""
        return self._config.get_effective_model() or self.DEFAULT_MODEL

    @property
    def provider_name(self) -> str:
        """プロバイダー名を返す."""
        return "google"

    def _create_model(self) -> Any:
        """Google Gemini ChatModelを作成する."""
        from langchain_google_genai import ChatGoogleGenerativeAI

        from company_research_agent.core.exceptions import LLMProviderError

        api_key = self._config.google_api_key
        if not api_key:
            raise LLMProviderError(
                message="Google API key is required",
                provider=self.provider_name,
                model=self.model_name,
            )
        return ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=api_key,
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
        )
