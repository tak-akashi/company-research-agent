"""LLMプロバイダーファクトリー."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

from company_research_agent.llm.config import LLMConfig
from company_research_agent.llm.types import LLMProviderType

if TYPE_CHECKING:
    from company_research_agent.llm.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


def create_llm_provider(
    config: LLMConfig | None = None,
    for_vision: bool = False,
) -> BaseLLMProvider:
    """設定に基づいてLLMプロバイダーを作成する.

    Args:
        config: LLM設定。Noneの場合は環境変数から読み込む。
        for_vision: ビジョン用プロバイダーを作成する場合True。
                   Trueの場合、vision_provider/vision_modelが優先される。

    Returns:
        設定されたプロバイダーのインスタンス

    Raises:
        ValueError: 未サポートのプロバイダーが指定された場合
        ValueError: 必要なAPIキーが設定されていない場合

    Example:
        >>> # 環境変数から自動設定
        >>> provider = create_llm_provider()

        >>> # 明示的に設定
        >>> config = LLMConfig(provider=LLMProviderType.OPENAI, openai_api_key="sk-...")
        >>> provider = create_llm_provider(config)

        >>> # ビジョン用プロバイダー
        >>> vision_provider = create_llm_provider(for_vision=True)
    """
    if config is None:
        config = LLMConfig()

    # 有効なプロバイダータイプを取得
    provider_type = config.get_effective_provider(for_vision=for_vision)

    # ビジョン用の場合、vision_modelを適用した新しいconfigを作成
    effective_config = config
    if for_vision:
        effective_model = config.get_effective_model(for_vision=True)
        if effective_model is not None and effective_model != config.model:
            # vision_modelが指定されている場合、modelをオーバーライド
            effective_config = config.model_copy(update={"model": effective_model})

    logger.info(
        f"Creating LLM provider: {provider_type.value}"
        f" (model={effective_config.model or 'default'}, for_vision={for_vision})"
    )

    match provider_type:
        case LLMProviderType.OPENAI:
            from company_research_agent.llm.providers.openai import OpenAIProvider

            if not config.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY is required for OpenAI provider. "
                    "Set the environment variable or pass openai_api_key in config."
                )
            return OpenAIProvider(effective_config)

        case LLMProviderType.GOOGLE:
            from company_research_agent.llm.providers.google import GoogleProvider

            if not config.google_api_key:
                raise ValueError(
                    "GOOGLE_API_KEY is required for Google provider. "
                    "Set the environment variable or pass google_api_key in config."
                )
            return GoogleProvider(effective_config)

        case LLMProviderType.ANTHROPIC:
            from company_research_agent.llm.providers.anthropic import AnthropicProvider

            if not config.anthropic_api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY is required for Anthropic provider. "
                    "Set the environment variable or pass anthropic_api_key in config."
                )
            return AnthropicProvider(effective_config)

        case LLMProviderType.OLLAMA:
            from company_research_agent.llm.providers.ollama import OllamaProvider

            # OllamaはローカルなのでAPIキー不要
            return OllamaProvider(effective_config)

        case _:
            raise ValueError(f"Unsupported LLM provider: {provider_type}")


@lru_cache(maxsize=1)
def get_default_provider() -> BaseLLMProvider:
    """デフォルトのLLMプロバイダーを取得する（シングルトン）.

    環境変数で設定されたプロバイダーのインスタンスを返す。
    初回呼び出し時にインスタンスが作成され、以降はキャッシュされる。

    Returns:
        環境変数で設定されたプロバイダーのインスタンス

    Example:
        >>> provider = get_default_provider()
        >>> result = await provider.ainvoke_structured(prompt, schema)
    """
    return create_llm_provider()


@lru_cache(maxsize=1)
def get_vision_provider() -> BaseLLMProvider:
    """ビジョン用のLLMプロバイダーを取得する（シングルトン）.

    環境変数で設定されたビジョン用プロバイダーのインスタンスを返す。
    LLM_VISION_PROVIDER/LLM_VISION_MODELが設定されていればそれを使用し、
    未設定の場合はLLM_PROVIDER/LLM_MODELを使用する。

    Returns:
        ビジョン用プロバイダーのインスタンス

    Example:
        >>> provider = get_vision_provider()
        >>> result = await provider.ainvoke_vision(prompt, image_data)
    """
    return create_llm_provider(for_vision=True)


def clear_provider_cache() -> None:
    """プロバイダーキャッシュをクリアする.

    テスト時や設定変更後にキャッシュをクリアする場合に使用。
    """
    get_default_provider.cache_clear()
    get_vision_provider.cache_clear()
    logger.debug("Provider cache cleared")
