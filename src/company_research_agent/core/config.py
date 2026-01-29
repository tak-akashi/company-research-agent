"""Configuration management for Company Research Agent.

全設定を一元管理するモジュール。環境変数で上書き可能。

Example:
    >>> from company_research_agent.core.config import get_config
    >>> config = get_config()
    >>> config.ir_scraper.default_since_days
    30
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from company_research_agent.core.types import LLMProviderType


class LoggingConfig(BaseSettings):
    """ログ設定.

    Environment Variables:
        LOG_LEVEL: ログレベル (DEBUG/INFO/WARNING/ERROR)
        LOG_FORMAT: ログフォーマット (simple/detailed)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="ログレベル",
    )
    format_style: Literal["simple", "detailed"] = Field(
        default="simple",
        alias="LOG_FORMAT",
        description="ログフォーマット",
    )


class EDINETConfig(BaseSettings):
    """EDINET API設定.

    Environment Variables:
        EDINET_API_KEY: EDINET APIキー（必須）
        EDINET_BASE_URL: EDINET APIベースURL
        EDINET_TIMEOUT_LIST: 一覧取得タイムアウト（秒）
        EDINET_TIMEOUT_DOWNLOAD: ダウンロードタイムアウト（秒）
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    api_key: str = Field(
        ...,
        alias="EDINET_API_KEY",
        description="EDINET APIキー",
    )
    base_url: str = Field(
        default="https://api.edinet-fsa.go.jp/api/v2",
        alias="EDINET_BASE_URL",
        description="EDINET APIベースURL",
    )
    timeout_list: int = Field(
        default=30,
        alias="EDINET_TIMEOUT_LIST",
        description="一覧取得タイムアウト（秒）",
    )
    timeout_download: int = Field(
        default=60,
        alias="EDINET_TIMEOUT_DOWNLOAD",
        description="ダウンロードタイムアウト（秒）",
    )


class LLMConfig(BaseSettings):
    """LLM設定.

    Environment Variables:
        LLM_PROVIDER: プロバイダー (openai/google/anthropic/ollama)
        LLM_MODEL: モデル名
        LLM_VISION_PROVIDER: ビジョン用プロバイダー
        LLM_VISION_MODEL: ビジョン用モデル名
        LLM_TIMEOUT: タイムアウト（秒）
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
        description="LLMプロバイダー",
    )
    model: str | None = Field(
        default=None,
        alias="LLM_MODEL",
        description="モデル名",
    )

    # ビジョン用
    vision_provider: LLMProviderType | None = Field(
        default=None,
        alias="LLM_VISION_PROVIDER",
        description="ビジョン用プロバイダー",
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
        description="タイムアウト（秒）",
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

    # プロバイダー固有
    openai_api_key: str | None = Field(
        default=None,
        alias="OPENAI_API_KEY",
        description="OpenAI APIキー",
    )
    google_api_key: str | None = Field(
        default=None,
        alias="GOOGLE_API_KEY",
        description="Google APIキー",
    )
    anthropic_api_key: str | None = Field(
        default=None,
        alias="ANTHROPIC_API_KEY",
        description="Anthropic APIキー",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
        description="Ollama APIエンドポイント",
    )

    def get_effective_provider(self, for_vision: bool = False) -> LLMProviderType:
        """有効なプロバイダーを取得."""
        if for_vision and self.vision_provider is not None:
            return self.vision_provider
        return self.provider

    def get_effective_model(self, for_vision: bool = False) -> str | None:
        """有効なモデル名を取得."""
        if for_vision and self.vision_model is not None:
            return self.vision_model
        if for_vision and self.vision_provider is not None:
            return None
        return self.model


class LangfuseConfig(BaseSettings):
    """Langfuse observability設定.

    Environment Variables:
        LANGFUSE_ENABLED: 有効/無効
        LANGFUSE_PUBLIC_KEY: Public Key
        LANGFUSE_SECRET_KEY: Secret Key
        LANGFUSE_BASE_URL: API Base URL
        LANGFUSE_DEBUG: デバッグモード
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enabled: bool = Field(
        default=False,
        alias="LANGFUSE_ENABLED",
        description="Langfuseの有効/無効",
    )
    public_key: str | None = Field(
        default=None,
        alias="LANGFUSE_PUBLIC_KEY",
        description="Langfuse Public Key",
    )
    secret_key: str | None = Field(
        default=None,
        alias="LANGFUSE_SECRET_KEY",
        description="Langfuse Secret Key",
    )
    base_url: str = Field(
        default="https://cloud.langfuse.com",
        alias="LANGFUSE_BASE_URL",
        description="Langfuse API Base URL",
    )
    debug: bool = Field(
        default=False,
        alias="LANGFUSE_DEBUG",
        description="デバッグモード",
    )

    def is_configured(self) -> bool:
        """Langfuseが正しく設定されているか確認."""
        return bool(self.enabled and self.public_key and self.secret_key)


class IRScraperConfig(BaseSettings):
    """IRスクレイパー設定.

    Environment Variables:
        IR_DEFAULT_SINCE_DAYS: デフォルト検索期間（日数）
        IR_RATE_LIMIT_SECONDS: リクエスト間隔（秒）
        IR_TIMEOUT_MS: タイムアウト（ミリ秒）
        IR_HEADLESS: ヘッドレスモード
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    default_since_days: int = Field(
        default=30,
        alias="IR_DEFAULT_SINCE_DAYS",
        description="デフォルト検索期間（日数）",
    )
    rate_limit_seconds: float = Field(
        default=1.0,
        alias="IR_RATE_LIMIT_SECONDS",
        description="リクエスト間隔（秒）",
    )
    timeout_ms: int = Field(
        default=30000,
        alias="IR_TIMEOUT_MS",
        description="タイムアウト（ミリ秒）",
    )
    headless: bool = Field(
        default=True,
        alias="IR_HEADLESS",
        description="ヘッドレスモード",
    )


class DownloadConfig(BaseSettings):
    """ダウンロード設定.

    Environment Variables:
        DOWNLOAD_DIR: ダウンロードディレクトリ
        DOWNLOAD_DEFAULT_LIMIT: デフォルトダウンロード件数
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    download_dir: Path = Field(
        default=Path("downloads"),
        alias="DOWNLOAD_DIR",
        description="ダウンロードディレクトリ",
    )
    default_limit: int = Field(
        default=5,
        alias="DOWNLOAD_DEFAULT_LIMIT",
        description="デフォルトダウンロード件数",
    )


class AppConfig(BaseSettings):
    """アプリケーション全体の設定.

    全ての設定を一元管理する。各サブ設定は環境変数で上書き可能。

    Example:
        >>> config = AppConfig()
        >>> config.ir_scraper.default_since_days
        30
        >>> config.download.download_dir
        PosixPath('downloads')
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    langfuse: LangfuseConfig = Field(default_factory=LangfuseConfig)
    ir_scraper: IRScraperConfig = Field(default_factory=IRScraperConfig)
    download: DownloadConfig = Field(default_factory=DownloadConfig)

    # EDINETConfigは必須フィールドがあるため遅延初期化
    _edinet: EDINETConfig | None = None

    @property
    def edinet(self) -> EDINETConfig:
        """EDINET設定を取得（遅延初期化）."""
        if self._edinet is None:
            # pydantic-settingsが環境変数から値を読み込むため、引数は不要
            self._edinet = EDINETConfig()  # type: ignore[call-arg]
        return self._edinet


# シングルトンインスタンス
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """アプリケーション設定を取得.

    Returns:
        AppConfigインスタンス（シングルトン）
    """
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reset_config() -> None:
    """設定をリセット（テスト用）."""
    global _config
    _config = None


# 後方互換性のためのエイリアス
GeminiConfig = LLMConfig  # 非推奨: LLMConfigを使用してください
