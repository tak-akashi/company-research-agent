"""LLMプロバイダーの設定."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from company_research_agent.llm.types import LLMProviderType


class LLMConfig(BaseSettings):
    """LLM統合設定.

    環境変数またはコンストラクタ引数で設定可能。

    Example:
        >>> # 環境変数から読み込み
        >>> config = LLMConfig()

        >>> # 明示的に指定
        >>> config = LLMConfig(
        ...     provider=LLMProviderType.OPENAI,
        ...     model="gpt-4o",
        ...     openai_api_key="sk-...",
        ... )

    環境変数:
        LLM_PROVIDER: プロバイダー種別 (openai/google/anthropic/ollama)
        LLM_MODEL: モデル名（省略時はプロバイダーのデフォルト）
        LLM_VISION_PROVIDER: ビジョン用プロバイダー（省略時はLLM_PROVIDERと同じ）
        LLM_VISION_MODEL: ビジョン用モデル名
        LLM_TIMEOUT: タイムアウト秒数
        LLM_MAX_RETRIES: 最大リトライ回数
        LLM_RPM_LIMIT: レート制限（リクエスト/分）
        OPENAI_API_KEY: OpenAI APIキー
        GOOGLE_API_KEY: Google APIキー
        ANTHROPIC_API_KEY: Anthropic APIキー
        OLLAMA_BASE_URL: Ollama APIエンドポイント
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # テキスト分析用
    provider: LLMProviderType = Field(
        default=LLMProviderType.GOOGLE,
        alias="LLM_PROVIDER",
        description="LLMプロバイダー種別",
    )
    model: str | None = Field(
        default=None,
        alias="LLM_MODEL",
        description="モデル名（省略時はプロバイダーのデフォルト）",
    )

    # ビジョン用（省略時はprovider/modelと同じ）
    vision_provider: LLMProviderType | None = Field(
        default=None,
        alias="LLM_VISION_PROVIDER",
        description="ビジョン用プロバイダー（省略時はLLM_PROVIDERと同じ）",
    )
    vision_model: str | None = Field(
        default=None,
        alias="LLM_VISION_MODEL",
        description="ビジョン用モデル名",
    )

    # 共通設定
    timeout: int = Field(
        default=120,
        alias="LLM_TIMEOUT",
        description="タイムアウト秒数",
    )
    max_retries: int = Field(
        default=3,
        alias="LLM_MAX_RETRIES",
        description="最大リトライ回数",
    )
    rpm_limit: int = Field(
        default=60,
        alias="LLM_RPM_LIMIT",
        description="レート制限（リクエスト/分）",
    )

    # OpenAI固有
    openai_api_key: str | None = Field(
        default=None,
        alias="OPENAI_API_KEY",
        description="OpenAI APIキー",
    )

    # Google固有
    google_api_key: str | None = Field(
        default=None,
        alias="GOOGLE_API_KEY",
        description="Google APIキー",
    )

    # Anthropic固有
    anthropic_api_key: str | None = Field(
        default=None,
        alias="ANTHROPIC_API_KEY",
        description="Anthropic APIキー",
    )

    # Ollama固有
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
        description="Ollama APIエンドポイント",
    )

    def get_effective_provider(self, for_vision: bool = False) -> LLMProviderType:
        """有効なプロバイダータイプを取得する.

        Args:
            for_vision: ビジョン用プロバイダーを取得する場合True

        Returns:
            有効なプロバイダータイプ
        """
        if for_vision and self.vision_provider is not None:
            return self.vision_provider
        return self.provider

    def get_effective_model(self, for_vision: bool = False) -> str | None:
        """有効なモデル名を取得する.

        Args:
            for_vision: ビジョン用モデルを取得する場合True

        Returns:
            モデル名（未指定の場合はNone）
        """
        if for_vision and self.vision_model is not None:
            return self.vision_model
        if for_vision and self.vision_provider is not None:
            # ビジョンプロバイダーが指定されているがモデルは未指定
            return None
        return self.model
