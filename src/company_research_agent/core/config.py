"""Configuration management for Company Research Agent."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
