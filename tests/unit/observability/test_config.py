"""LangfuseConfigのテスト."""

from __future__ import annotations

import os
from unittest.mock import patch

from company_research_agent.observability.config import LangfuseConfig


class TestLangfuseConfig:
    """LangfuseConfigのテスト."""

    def test_default_disabled(self) -> None:
        """デフォルトでLangfuseが無効であることを確認."""
        with patch.dict(os.environ, {}, clear=True):
            config = LangfuseConfig(_env_file=None)  # type: ignore[call-arg]
            assert config.enabled is False
            assert config.is_configured() is False

    def test_enabled_with_keys(self) -> None:
        """キーが設定されている場合にis_configured()がTrueを返すことを確認."""
        env_vars = {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
            "LANGFUSE_SECRET_KEY": "sk-lf-test",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LangfuseConfig(_env_file=None)  # type: ignore[call-arg]
            assert config.enabled is True
            assert config.is_configured() is True

    def test_enabled_without_public_key(self) -> None:
        """Public Keyが未設定の場合にis_configured()がFalseを返すことを確認."""
        env_vars = {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_SECRET_KEY": "sk-lf-test",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LangfuseConfig(_env_file=None)  # type: ignore[call-arg]
            assert config.enabled is True
            assert config.is_configured() is False

    def test_enabled_without_secret_key(self) -> None:
        """Secret Keyが未設定の場合にis_configured()がFalseを返すことを確認."""
        env_vars = {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LangfuseConfig(_env_file=None)  # type: ignore[call-arg]
            assert config.enabled is True
            assert config.is_configured() is False

    def test_disabled_with_keys(self) -> None:
        """無効な場合にキーがあってもis_configured()がFalseを返すことを確認."""
        env_vars = {
            "LANGFUSE_ENABLED": "false",
            "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
            "LANGFUSE_SECRET_KEY": "sk-lf-test",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LangfuseConfig(_env_file=None)  # type: ignore[call-arg]
            assert config.enabled is False
            assert config.is_configured() is False

    def test_custom_base_url(self) -> None:
        """カスタムベースURLが設定されることを確認."""
        env_vars = {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_BASE_URL": "https://custom.langfuse.com",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LangfuseConfig(_env_file=None)  # type: ignore[call-arg]
            assert config.base_url == "https://custom.langfuse.com"

    def test_default_base_url(self) -> None:
        """デフォルトベースURLが正しいことを確認."""
        with patch.dict(os.environ, {}, clear=True):
            config = LangfuseConfig(_env_file=None)  # type: ignore[call-arg]
            assert config.base_url == "https://cloud.langfuse.com"

    def test_debug_mode(self) -> None:
        """デバッグモードが設定されることを確認."""
        env_vars = {
            "LANGFUSE_DEBUG": "true",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LangfuseConfig(_env_file=None)  # type: ignore[call-arg]
            assert config.debug is True
