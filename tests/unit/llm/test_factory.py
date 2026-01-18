"""LLMプロバイダーファクトリーのテスト."""

# mypy: disable-error-code="call-arg"

import os
from collections.abc import Generator
from unittest.mock import patch

import pytest

from company_research_agent.llm.config import LLMConfig
from company_research_agent.llm.factory import (
    clear_provider_cache,
    create_llm_provider,
    get_default_provider,
    get_vision_provider,
)
from company_research_agent.llm.providers.anthropic import AnthropicProvider
from company_research_agent.llm.providers.google import GoogleProvider
from company_research_agent.llm.providers.ollama import OllamaProvider
from company_research_agent.llm.providers.openai import OpenAIProvider


@pytest.fixture(autouse=True)
def clean_env() -> Generator[None, None, None]:
    """テスト前に環境変数をクリアし、キャッシュをリセット."""
    with patch.dict(os.environ, {}, clear=True):
        clear_provider_cache()
        yield


class TestCreateLLMProvider:
    """create_llm_provider()のテスト."""

    def test_create_google_provider(self) -> None:
        """GoogleProviderを作成できることを確認."""
        env_vars = {"LLM_PROVIDER": "google", "GOOGLE_API_KEY": "test-key"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = create_llm_provider(config)
            assert isinstance(provider, GoogleProvider)
            assert provider.provider_name == "google"

    def test_create_openai_provider(self) -> None:
        """OpenAIProviderを作成できることを確認."""
        env_vars = {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test-key"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = create_llm_provider(config)
            assert isinstance(provider, OpenAIProvider)
            assert provider.provider_name == "openai"

    def test_create_anthropic_provider(self) -> None:
        """AnthropicProviderを作成できることを確認."""
        env_vars = {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-ant-test"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = create_llm_provider(config)
            assert isinstance(provider, AnthropicProvider)
            assert provider.provider_name == "anthropic"

    def test_create_ollama_provider(self) -> None:
        """OllamaProviderを作成できることを確認（APIキー不要）."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=True):
            config = LLMConfig(_env_file=None)
            provider = create_llm_provider(config)
            assert isinstance(provider, OllamaProvider)
            assert provider.provider_name == "ollama"


class TestCreateLLMProviderErrors:
    """APIキー未設定時のエラーテスト."""

    def test_google_without_api_key_raises_error(self) -> None:
        """GoogleプロバイダーでAPIキー未設定時にエラーが発生することを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "google"}, clear=True):
            config = LLMConfig(_env_file=None)
            with pytest.raises(ValueError, match="GOOGLE_API_KEY is required"):
                create_llm_provider(config)

    def test_openai_without_api_key_raises_error(self) -> None:
        """OpenAIプロバイダーでAPIキー未設定時にエラーが発生することを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai"}, clear=True):
            config = LLMConfig(_env_file=None)
            with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
                create_llm_provider(config)

    def test_anthropic_without_api_key_raises_error(self) -> None:
        """AnthropicプロバイダーでAPIキー未設定時にエラーが発生することを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic"}, clear=True):
            config = LLMConfig(_env_file=None)
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
                create_llm_provider(config)

    def test_ollama_without_api_key_succeeds(self) -> None:
        """OllamaプロバイダーはAPIキー不要で作成できることを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=True):
            config = LLMConfig(_env_file=None)
            provider = create_llm_provider(config)
            assert isinstance(provider, OllamaProvider)


class TestCreateLLMProviderVision:
    """ビジョン用プロバイダー作成テスト."""

    def test_vision_provider_uses_vision_settings(self) -> None:
        """for_vision=Trueでビジョン設定が使用されることを確認."""
        env_vars = {
            "LLM_PROVIDER": "google",
            "GOOGLE_API_KEY": "test-key",
            "LLM_VISION_PROVIDER": "google",
            "LLM_VISION_MODEL": "gemini-1.5-pro-vision",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = create_llm_provider(config, for_vision=True)
            assert provider.model_name == "gemini-1.5-pro-vision"

    def test_vision_provider_different_from_text(self) -> None:
        """テキストとビジョンで異なるプロバイダーを使用できることを確認."""
        env_vars = {
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "sk-test",
            "LLM_VISION_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "sk-ant-test",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            text_provider = create_llm_provider(config, for_vision=False)
            vision_provider = create_llm_provider(config, for_vision=True)

            assert isinstance(text_provider, OpenAIProvider)
            assert isinstance(vision_provider, AnthropicProvider)


class TestGetDefaultProvider:
    """get_default_provider()のテスト."""

    def teardown_method(self) -> None:
        """各テスト後にキャッシュをクリア."""
        clear_provider_cache()

    def test_returns_singleton(self) -> None:
        """同一インスタンスが返されることを確認."""
        env_vars = {"LLM_PROVIDER": "ollama"}
        with patch.dict(os.environ, env_vars, clear=True):
            clear_provider_cache()
            provider1 = get_default_provider()
            provider2 = get_default_provider()
            assert provider1 is provider2

    def test_uses_environment_config(self) -> None:
        """環境変数からの設定が使用されることを確認."""
        env_vars = {"LLM_PROVIDER": "ollama"}
        with patch.dict(os.environ, env_vars, clear=True):
            clear_provider_cache()
            provider = get_default_provider()
            assert isinstance(provider, OllamaProvider)


class TestGetVisionProvider:
    """get_vision_provider()のテスト."""

    def teardown_method(self) -> None:
        """各テスト後にキャッシュをクリア."""
        clear_provider_cache()

    def test_returns_singleton(self) -> None:
        """同一インスタンスが返されることを確認."""
        env_vars = {"LLM_PROVIDER": "ollama"}
        with patch.dict(os.environ, env_vars, clear=True):
            clear_provider_cache()
            provider1 = get_vision_provider()
            provider2 = get_vision_provider()
            assert provider1 is provider2

    def test_uses_vision_settings(self) -> None:
        """ビジョン用設定が使用されることを確認."""
        env_vars = {
            "LLM_PROVIDER": "ollama",
            "LLM_VISION_MODEL": "llava:13b",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            clear_provider_cache()
            provider = get_vision_provider()
            assert provider.model_name == "llava:13b"


class TestClearProviderCache:
    """clear_provider_cache()のテスト."""

    def test_clears_cache(self) -> None:
        """キャッシュがクリアされることを確認."""
        env_vars = {"LLM_PROVIDER": "ollama"}
        with patch.dict(os.environ, env_vars, clear=True):
            clear_provider_cache()
            provider1 = get_default_provider()
            clear_provider_cache()
            provider2 = get_default_provider()
            # キャッシュクリア後は新しいインスタンスが作成される
            assert provider1 is not provider2


class TestCreateLLMProviderFromEnv:
    """環境変数からのプロバイダー作成テスト."""

    def test_create_from_env_without_config(self) -> None:
        """config=Noneで環境変数から設定を読み込めることを確認."""
        env_vars = {"LLM_PROVIDER": "ollama"}
        with patch.dict(os.environ, env_vars, clear=True):
            provider = create_llm_provider()
            assert isinstance(provider, OllamaProvider)

    @pytest.mark.parametrize(
        "provider_type,api_key_var,api_key_value,expected_class",
        [
            ("google", "GOOGLE_API_KEY", "test-google", GoogleProvider),
            ("openai", "OPENAI_API_KEY", "sk-test", OpenAIProvider),
            ("anthropic", "ANTHROPIC_API_KEY", "sk-ant-test", AnthropicProvider),
        ],
    )
    def test_create_all_providers_from_env(
        self,
        provider_type: str,
        api_key_var: str,
        api_key_value: str,
        expected_class: type,
    ) -> None:
        """全プロバイダーを環境変数から作成できることを確認."""
        env_vars = {
            "LLM_PROVIDER": provider_type,
            api_key_var: api_key_value,
        }
        with patch.dict(os.environ, env_vars, clear=True):
            provider = create_llm_provider()
            assert isinstance(provider, expected_class)
