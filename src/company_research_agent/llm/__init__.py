"""LLMプロバイダー抽象化レイヤー.

このモジュールは複数のLLMプロバイダー（OpenAI, Google, Anthropic, Ollama）を
統一的に扱うための抽象化レイヤーを提供する。

Example:
    >>> # 環境変数で自動設定（推奨）
    >>> from company_research_agent.llm import get_default_provider
    >>> provider = get_default_provider()
    >>> result = await provider.ainvoke_structured(prompt, BusinessSummary)

    >>> # 明示的に設定
    >>> from company_research_agent.llm import create_llm_provider, LLMConfig, LLMProviderType
    >>> config = LLMConfig(
    ...     provider=LLMProviderType.OPENAI,
    ...     model="gpt-4o",
    ...     openai_api_key="sk-...",
    ... )
    >>> provider = create_llm_provider(config)

環境変数:
    LLM_PROVIDER: プロバイダー種別 (openai/google/anthropic/ollama)
    LLM_MODEL: モデル名（省略時はプロバイダーのデフォルト）
    LLM_VISION_PROVIDER: ビジョン用プロバイダー（省略時はLLM_PROVIDERと同じ）
    LLM_VISION_MODEL: ビジョン用モデル名
    OPENAI_API_KEY: OpenAI APIキー
    GOOGLE_API_KEY: Google APIキー
    ANTHROPIC_API_KEY: Anthropic APIキー
    OLLAMA_BASE_URL: Ollama APIエンドポイント
"""

from __future__ import annotations

from company_research_agent.llm.config import LLMConfig
from company_research_agent.llm.factory import (
    clear_provider_cache,
    create_llm_provider,
    get_default_provider,
    get_vision_provider,
)
from company_research_agent.llm.provider import LLMProvider
from company_research_agent.llm.providers import (
    AnthropicProvider,
    BaseLLMProvider,
    GoogleProvider,
    OllamaProvider,
    OpenAIProvider,
)
from company_research_agent.llm.types import LLMProviderType

__all__ = [
    # 設定
    "LLMConfig",
    "LLMProviderType",
    # プロトコル・基底クラス
    "LLMProvider",
    "BaseLLMProvider",
    # プロバイダー実装
    "OpenAIProvider",
    "GoogleProvider",
    "AnthropicProvider",
    "OllamaProvider",
    # ファクトリー関数
    "create_llm_provider",
    "get_default_provider",
    "get_vision_provider",
    "clear_provider_cache",
]
