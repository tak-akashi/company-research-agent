"""Langfuse configuration."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LangfuseConfig(BaseSettings):
    """Langfuse observability configuration.

    環境変数またはコンストラクタ引数で設定可能。

    環境変数:
        LANGFUSE_ENABLED: Langfuseの有効/無効 (true/false)
        LANGFUSE_PUBLIC_KEY: Langfuse Public Key
        LANGFUSE_SECRET_KEY: Langfuse Secret Key
        LANGFUSE_BASE_URL: Langfuse API Base URL
        LANGFUSE_DEBUG: デバッグモードの有効/無効

    Example:
        >>> config = LangfuseConfig()
        >>> config.is_configured()
        False
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
        description="デバッグモードの有効/無効",
    )

    def is_configured(self) -> bool:
        """Langfuseが正しく設定されているか確認.

        Returns:
            enabledがTrueでpublic_keyとsecret_keyが設定されている場合True
        """
        return bool(self.enabled and self.public_key and self.secret_key)
