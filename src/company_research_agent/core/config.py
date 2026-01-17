"""Configuration management for Company Research Agent."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GeminiConfig(BaseSettings):
    """Configuration for Gemini API client.

    Attributes:
        api_key: Google API key for Gemini. Required.
        model: Model name to use. Defaults to gemini-2.5-flash.
        timeout: Timeout in seconds for API calls.
        max_retries: Maximum number of retries for failed requests.
        rpm_limit: Rate limit (requests per minute).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    api_key: str = Field(
        ...,
        alias="GOOGLE_API_KEY",
        description="Google API key for Gemini",
    )
    model: str = Field(
        default="gemini-2.5-flash-preview-05-20",
        description="Model name to use for Gemini API",
    )
    timeout: int = Field(
        default=120,
        description="Timeout in seconds for API calls",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed requests",
    )
    rpm_limit: int = Field(
        default=60,
        description="Rate limit (requests per minute)",
    )


class EDINETConfig(BaseSettings):
    """Configuration for EDINET API client.

    Attributes:
        api_key: EDINET API subscription key. Required.
        base_url: Base URL for EDINET API. Defaults to v2 API.
        timeout_list: Timeout in seconds for document list API calls.
        timeout_download: Timeout in seconds for document download API calls.
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
        description="EDINET API subscription key",
    )
    base_url: str = Field(
        default="https://api.edinet-fsa.go.jp/api/v2",
        description="Base URL for EDINET API",
    )
    timeout_list: int = Field(
        default=30,
        description="Timeout in seconds for document list API calls",
    )
    timeout_download: int = Field(
        default=60,
        description="Timeout in seconds for document download API calls",
    )
