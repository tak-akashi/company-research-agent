"""LLMConfigのテスト."""

# mypy: disable-error-code="call-arg"

import os
from unittest.mock import patch

import pytest

from company_research_agent.llm.config import LLMConfig
from company_research_agent.llm.types import LLMProviderType


class TestLLMConfigDefaults:
    """LLMConfigのデフォルト値テスト."""

    def test_default_provider_is_google(self) -> None:
        """デフォルトプロバイダーがGoogleであることを確認."""
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.provider == LLMProviderType.GOOGLE

    def test_default_model_is_none(self) -> None:
        """デフォルトモデルがNoneであることを確認."""
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.model is None

    def test_default_vision_provider_is_none(self) -> None:
        """デフォルトのビジョンプロバイダーがNoneであることを確認."""
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.vision_provider is None

    def test_default_timeout(self) -> None:
        """デフォルトタイムアウトが120秒であることを確認."""
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.timeout == 120

    def test_default_max_retries(self) -> None:
        """デフォルトリトライ回数が3であることを確認."""
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.max_retries == 3

    def test_default_rpm_limit(self) -> None:
        """デフォルトRPM制限が60であることを確認."""
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.rpm_limit == 60

    def test_default_ollama_base_url(self) -> None:
        """デフォルトのOllama URLがlocalhost:11434であることを確認."""
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.ollama_base_url == "http://localhost:11434"


class TestLLMConfigFromEnvironment:
    """環境変数からの設定読み込みテスト."""

    def test_provider_from_env(self) -> None:
        """環境変数LLM_PROVIDERからプロバイダーを読み込めることを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai"}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.provider == LLMProviderType.OPENAI

    def test_model_from_env(self) -> None:
        """環境変数LLM_MODELからモデルを読み込めることを確認."""
        with patch.dict(os.environ, {"LLM_MODEL": "gpt-4o-mini"}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.model == "gpt-4o-mini"

    def test_vision_provider_from_env(self) -> None:
        """環境変数LLM_VISION_PROVIDERからビジョンプロバイダーを読み込めることを確認."""
        with patch.dict(os.environ, {"LLM_VISION_PROVIDER": "anthropic"}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.vision_provider == LLMProviderType.ANTHROPIC

    def test_vision_model_from_env(self) -> None:
        """環境変数LLM_VISION_MODELからビジョンモデルを読み込めることを確認."""
        with patch.dict(os.environ, {"LLM_VISION_MODEL": "claude-sonnet-4-20250514"}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.vision_model == "claude-sonnet-4-20250514"

    def test_timeout_from_env(self) -> None:
        """環境変数LLM_TIMEOUTからタイムアウトを読み込めることを確認."""
        with patch.dict(os.environ, {"LLM_TIMEOUT": "300"}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.timeout == 300

    def test_api_keys_from_env(self) -> None:
        """各プロバイダーのAPIキーを環境変数から読み込めることを確認."""
        env_vars = {
            "OPENAI_API_KEY": "sk-test-openai",
            "GOOGLE_API_KEY": "AIza-test-google",
            "ANTHROPIC_API_KEY": "sk-ant-test-anthropic",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.openai_api_key == "sk-test-openai"
            assert config.google_api_key == "AIza-test-google"
            assert config.anthropic_api_key == "sk-ant-test-anthropic"


class TestLLMConfigExplicit:
    """明示的なコンストラクタ引数テスト."""

    def test_explicit_provider(self) -> None:
        """プロバイダーを環境変数で指定できることを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic"}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.provider == LLMProviderType.ANTHROPIC

    def test_explicit_model(self) -> None:
        """モデルを環境変数で指定できることを確認."""
        with patch.dict(os.environ, {"LLM_MODEL": "gpt-4o"}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.model == "gpt-4o"

    def test_explicit_api_keys(self) -> None:
        """APIキーを環境変数で指定できることを確認."""
        env_vars = {
            "OPENAI_API_KEY": "sk-explicit",
            "GOOGLE_API_KEY": "AIza-explicit",
            "ANTHROPIC_API_KEY": "sk-ant-explicit",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.openai_api_key == "sk-explicit"
            assert config.google_api_key == "AIza-explicit"
            assert config.anthropic_api_key == "sk-ant-explicit"


class TestGetEffectiveProvider:
    """get_effective_provider()メソッドのテスト."""

    def test_returns_provider_for_non_vision(self) -> None:
        """for_vision=Falseで通常のプロバイダーを返すことを確認."""
        env_vars = {
            "LLM_PROVIDER": "openai",
            "LLM_VISION_PROVIDER": "anthropic",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.get_effective_provider(for_vision=False) == LLMProviderType.OPENAI

    def test_returns_vision_provider_when_set(self) -> None:
        """for_vision=Trueでビジョンプロバイダーを返すことを確認."""
        env_vars = {
            "LLM_PROVIDER": "openai",
            "LLM_VISION_PROVIDER": "anthropic",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.get_effective_provider(for_vision=True) == LLMProviderType.ANTHROPIC

    def test_returns_provider_when_vision_not_set(self) -> None:
        """ビジョンプロバイダー未設定時は通常のプロバイダーを返すことを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "google"}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.get_effective_provider(for_vision=True) == LLMProviderType.GOOGLE


class TestGetEffectiveModel:
    """get_effective_model()メソッドのテスト."""

    def test_returns_model_for_non_vision(self) -> None:
        """for_vision=Falseで通常のモデルを返すことを確認."""
        env_vars = {"LLM_MODEL": "gpt-4o", "LLM_VISION_MODEL": "gpt-4o-vision"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.get_effective_model(for_vision=False) == "gpt-4o"

    def test_returns_vision_model_when_set(self) -> None:
        """for_vision=Trueでビジョンモデルを返すことを確認."""
        env_vars = {"LLM_MODEL": "gpt-4o", "LLM_VISION_MODEL": "gpt-4o-vision"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.get_effective_model(for_vision=True) == "gpt-4o-vision"

    def test_returns_none_when_vision_provider_set_but_model_not(self) -> None:
        """ビジョンプロバイダーのみ設定時はNoneを返すことを確認."""
        env_vars = {"LLM_MODEL": "gpt-4o", "LLM_VISION_PROVIDER": "anthropic"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.get_effective_model(for_vision=True) is None

    def test_returns_model_when_vision_not_set(self) -> None:
        """ビジョン設定が未設定時は通常のモデルを返すことを確認."""
        with patch.dict(os.environ, {"LLM_MODEL": "gpt-4o"}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.get_effective_model(for_vision=True) == "gpt-4o"


class TestLLMConfigAllProviders:
    """全プロバイダーの設定テスト."""

    @pytest.mark.parametrize(
        "provider_str,expected",
        [
            ("openai", LLMProviderType.OPENAI),
            ("google", LLMProviderType.GOOGLE),
            ("anthropic", LLMProviderType.ANTHROPIC),
            ("ollama", LLMProviderType.OLLAMA),
        ],
    )
    def test_all_providers_from_env(self, provider_str: str, expected: LLMProviderType) -> None:
        """全プロバイダーを環境変数から読み込めることを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": provider_str}, clear=True):
            config = LLMConfig(_env_file=None)
            assert config.provider == expected
