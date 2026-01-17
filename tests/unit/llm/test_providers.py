"""各LLMプロバイダーのテスト."""

# mypy: disable-error-code="call-arg"

import os
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from company_research_agent.core.exceptions import LLMProviderError
from company_research_agent.llm.config import LLMConfig
from company_research_agent.llm.providers.anthropic import AnthropicProvider
from company_research_agent.llm.providers.google import GoogleProvider
from company_research_agent.llm.providers.ollama import OllamaProvider
from company_research_agent.llm.providers.openai import OpenAIProvider


@pytest.fixture(autouse=True)
def clean_env() -> Generator[None, None, None]:
    """テスト前に環境変数をクリア."""
    with patch.dict(os.environ, {}, clear=True):
        yield


class SampleOutput(BaseModel):
    """テスト用の出力スキーマ."""

    content: str


# =============================================================================
# GoogleProvider Tests
# =============================================================================


class TestGoogleProvider:
    """GoogleProviderのテスト."""

    def test_provider_name(self) -> None:
        """プロバイダー名が正しいことを確認."""
        env_vars = {"LLM_PROVIDER": "google", "GOOGLE_API_KEY": "test-key"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = GoogleProvider(config)
            assert provider.provider_name == "google"

    def test_default_model_name(self) -> None:
        """デフォルトモデル名が正しいことを確認."""
        env_vars = {"LLM_PROVIDER": "google", "GOOGLE_API_KEY": "test-key"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = GoogleProvider(config)
            assert provider.model_name == GoogleProvider.DEFAULT_MODEL

    def test_custom_model_name(self) -> None:
        """カスタムモデル名が正しく設定されることを確認."""
        env_vars = {
            "LLM_PROVIDER": "google",
            "GOOGLE_API_KEY": "test-key",
            "LLM_MODEL": "gemini-1.5-pro",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = GoogleProvider(config)
            assert provider.model_name == "gemini-1.5-pro"

    def test_supports_vision(self) -> None:
        """ビジョンサポートがTrueであることを確認."""
        env_vars = {"LLM_PROVIDER": "google", "GOOGLE_API_KEY": "test-key"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = GoogleProvider(config)
            assert provider.supports_vision is True

    def test_create_model_without_api_key_raises_error(self) -> None:
        """APIキーなしでモデル作成時にエラーが発生することを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "google"}, clear=True):
            config = LLMConfig(_env_file=None)
            provider = GoogleProvider(config)
            with pytest.raises(LLMProviderError, match="Google API key is required"):
                provider.get_model()

    def test_create_model_with_api_key(self) -> None:
        """APIキーありでモデルが作成されることを確認."""
        env_vars = {"LLM_PROVIDER": "google", "GOOGLE_API_KEY": "test-key"}
        with patch.dict(os.environ, env_vars, clear=True):
            with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_chat:
                mock_chat.return_value = MagicMock()
                config = LLMConfig(_env_file=None)
                provider = GoogleProvider(config)
                model = provider.get_model()
                assert model is not None
                mock_chat.assert_called_once()


# =============================================================================
# OpenAIProvider Tests
# =============================================================================


class TestOpenAIProvider:
    """OpenAIProviderのテスト."""

    def test_provider_name(self) -> None:
        """プロバイダー名が正しいことを確認."""
        env_vars = {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OpenAIProvider(config)
            assert provider.provider_name == "openai"

    def test_default_model_name(self) -> None:
        """デフォルトモデル名が正しいことを確認."""
        env_vars = {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OpenAIProvider(config)
            assert provider.model_name == OpenAIProvider.DEFAULT_MODEL

    def test_custom_model_name(self) -> None:
        """カスタムモデル名が正しく設定されることを確認."""
        env_vars = {
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "sk-test",
            "LLM_MODEL": "gpt-4o-mini",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OpenAIProvider(config)
            assert provider.model_name == "gpt-4o-mini"

    def test_supports_vision(self) -> None:
        """ビジョンサポートがTrueであることを確認."""
        env_vars = {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OpenAIProvider(config)
            assert provider.supports_vision is True

    def test_create_model_without_api_key_raises_error(self) -> None:
        """APIキーなしでモデル作成時にエラーが発生することを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai"}, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OpenAIProvider(config)
            with pytest.raises(LLMProviderError, match="OpenAI API key is required"):
                provider.get_model()

    def test_create_model_with_api_key(self) -> None:
        """APIキーありでモデルが作成されることを確認."""
        env_vars = {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}
        with patch.dict(os.environ, env_vars, clear=True):
            with patch("langchain_openai.ChatOpenAI") as mock_chat:
                mock_chat.return_value = MagicMock()
                config = LLMConfig(_env_file=None)
                provider = OpenAIProvider(config)
                model = provider.get_model()
                assert model is not None
                mock_chat.assert_called_once()


# =============================================================================
# AnthropicProvider Tests
# =============================================================================


class TestAnthropicProvider:
    """AnthropicProviderのテスト."""

    def test_provider_name(self) -> None:
        """プロバイダー名が正しいことを確認."""
        env_vars = {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-ant-test"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = AnthropicProvider(config)
            assert provider.provider_name == "anthropic"

    def test_default_model_name(self) -> None:
        """デフォルトモデル名が正しいことを確認."""
        env_vars = {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-ant-test"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = AnthropicProvider(config)
            assert provider.model_name == AnthropicProvider.DEFAULT_MODEL

    def test_custom_model_name(self) -> None:
        """カスタムモデル名が正しく設定されることを確認."""
        env_vars = {
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "sk-ant-test",
            "LLM_MODEL": "claude-3-haiku-20240307",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = AnthropicProvider(config)
            assert provider.model_name == "claude-3-haiku-20240307"

    def test_supports_vision(self) -> None:
        """ビジョンサポートがTrueであることを確認."""
        env_vars = {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-ant-test"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = AnthropicProvider(config)
            assert provider.supports_vision is True

    def test_create_model_without_api_key_raises_error(self) -> None:
        """APIキーなしでモデル作成時にエラーが発生することを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic"}, clear=True):
            config = LLMConfig(_env_file=None)
            provider = AnthropicProvider(config)
            with pytest.raises(LLMProviderError, match="Anthropic API key is required"):
                provider.get_model()

    def test_create_model_with_api_key(self) -> None:
        """APIキーありでモデルが作成されることを確認."""
        env_vars = {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-ant-test"}
        with patch.dict(os.environ, env_vars, clear=True):
            with patch("langchain_anthropic.ChatAnthropic") as mock_chat:
                mock_chat.return_value = MagicMock()
                config = LLMConfig(_env_file=None)
                provider = AnthropicProvider(config)
                model = provider.get_model()
                assert model is not None
                mock_chat.assert_called_once()


# =============================================================================
# OllamaProvider Tests
# =============================================================================


class TestOllamaProvider:
    """OllamaProviderのテスト."""

    def test_provider_name(self) -> None:
        """プロバイダー名が正しいことを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OllamaProvider(config)
            assert provider.provider_name == "ollama"

    def test_default_model_name(self) -> None:
        """デフォルトモデル名が正しいことを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OllamaProvider(config)
            assert provider.model_name == OllamaProvider.DEFAULT_MODEL

    def test_custom_model_name(self) -> None:
        """カスタムモデル名が正しく設定されることを確認."""
        env_vars = {"LLM_PROVIDER": "ollama", "LLM_MODEL": "gpt-oss-20b"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OllamaProvider(config)
            assert provider.model_name == "gpt-oss-20b"

    def test_no_api_key_required(self) -> None:
        """APIキーなしでプロバイダーが作成できることを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OllamaProvider(config)
            assert provider is not None

    @pytest.mark.parametrize(
        "model_name,expected_vision",
        [
            ("llama3.2", False),
            ("gpt-oss-20b", False),
            ("mistral", False),
            ("llava", True),
            ("llava:13b", True),
            ("llava-phi3", True),
            ("bakllava", True),
            ("bakllava:7b", True),
            ("moondream", True),
            ("moondream2", True),
        ],
    )
    def test_supports_vision_based_on_model(self, model_name: str, expected_vision: bool) -> None:
        """モデル名に基づいてビジョンサポートが判定されることを確認."""
        env_vars = {"LLM_PROVIDER": "ollama", "LLM_MODEL": model_name}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OllamaProvider(config)
            assert provider.supports_vision is expected_vision

    def test_create_model(self) -> None:
        """モデルが作成されることを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=True):
            with patch("langchain_ollama.ChatOllama") as mock_chat:
                mock_chat.return_value = MagicMock()
                config = LLMConfig(_env_file=None)
                provider = OllamaProvider(config)
                model = provider.get_model()
                assert model is not None
                mock_chat.assert_called_once()

    def test_custom_base_url(self) -> None:
        """カスタムベースURLが設定されることを確認."""
        env_vars = {
            "LLM_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://custom-server:11434",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OllamaProvider(config)
            assert provider._config.ollama_base_url == "http://custom-server:11434"


# =============================================================================
# BaseLLMProvider Tests (via concrete implementations)
# =============================================================================


class TestBaseLLMProviderMethods:
    """BaseLLMProviderの共通メソッドテスト."""

    def test_lazy_model_initialization(self) -> None:
        """モデルが遅延初期化されることを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OllamaProvider(config)
            # 内部モデルはNone
            assert provider._model is None

    def test_model_cached_after_first_call(self) -> None:
        """get_model()が2回目以降はキャッシュを使用することを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=True):
            with patch("langchain_ollama.ChatOllama") as mock_chat:
                mock_chat.return_value = MagicMock()
                config = LLMConfig(_env_file=None)
                provider = OllamaProvider(config)

                model1 = provider.get_model()
                model2 = provider.get_model()

                assert model1 is model2
                mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_ainvoke_structured_success(self) -> None:
        """ainvoke_structured()が正常に動作することを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OllamaProvider(config)

            mock_model = MagicMock()
            mock_structured = MagicMock()
            mock_structured.ainvoke = AsyncMock(return_value=SampleOutput(content="test"))
            mock_model.with_structured_output.return_value = mock_structured

            with patch.object(provider, "get_model", return_value=mock_model):
                result = await provider.ainvoke_structured("test prompt", SampleOutput)

            assert result.content == "test"
            mock_model.with_structured_output.assert_called_once_with(SampleOutput)

    @pytest.mark.asyncio
    async def test_ainvoke_structured_error_handling(self) -> None:
        """ainvoke_structured()のエラーがLLMProviderErrorでラップされることを確認."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OllamaProvider(config)

            mock_model = MagicMock()
            mock_structured = MagicMock()
            mock_structured.ainvoke = AsyncMock(side_effect=Exception("API error"))
            mock_model.with_structured_output.return_value = mock_structured

            with patch.object(provider, "get_model", return_value=mock_model):
                with pytest.raises(LLMProviderError) as exc_info:
                    await provider.ainvoke_structured("test prompt", SampleOutput)

            assert exc_info.value.provider == "ollama"
            assert "API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_ainvoke_vision_not_supported(self) -> None:
        """ビジョン非対応モデルでainvoke_vision()がエラーを発生させることを確認."""
        env_vars = {"LLM_PROVIDER": "ollama", "LLM_MODEL": "llama3.2"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OllamaProvider(config)

            with pytest.raises(LLMProviderError, match="Vision not supported"):
                await provider.ainvoke_vision("describe image", b"fake_image_data")

    @pytest.mark.asyncio
    async def test_ainvoke_vision_success(self) -> None:
        """ainvoke_vision()が正常に動作することを確認."""
        env_vars = {"LLM_PROVIDER": "ollama", "LLM_MODEL": "llava"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = OllamaProvider(config)

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.content = "Image description"
            mock_model.ainvoke = AsyncMock(return_value=mock_response)

            with patch.object(provider, "get_model", return_value=mock_model):
                result = await provider.ainvoke_vision("describe image", b"fake_image_data")

            assert result == "Image description"


# =============================================================================
# Cross-Provider Tests
# =============================================================================


class TestAllProvidersCommonBehavior:
    """全プロバイダーで共通の動作テスト."""

    @pytest.mark.parametrize(
        "provider_class,env_vars",
        [
            (GoogleProvider, {"LLM_PROVIDER": "google", "GOOGLE_API_KEY": "test"}),
            (OpenAIProvider, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}),
            (AnthropicProvider, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-ant-test"}),
            (OllamaProvider, {"LLM_PROVIDER": "ollama"}),
        ],
    )
    def test_all_providers_have_provider_name(
        self, provider_class: type, env_vars: dict[str, str]
    ) -> None:
        """全プロバイダーがprovider_nameを持つことを確認."""
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = provider_class(config)
            assert provider.provider_name is not None
            assert isinstance(provider.provider_name, str)

    @pytest.mark.parametrize(
        "provider_class,env_vars",
        [
            (GoogleProvider, {"LLM_PROVIDER": "google", "GOOGLE_API_KEY": "test"}),
            (OpenAIProvider, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}),
            (AnthropicProvider, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-ant-test"}),
            (OllamaProvider, {"LLM_PROVIDER": "ollama"}),
        ],
    )
    def test_all_providers_have_model_name(
        self, provider_class: type, env_vars: dict[str, str]
    ) -> None:
        """全プロバイダーがmodel_nameを持つことを確認."""
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = provider_class(config)
            assert provider.model_name is not None
            assert isinstance(provider.model_name, str)

    @pytest.mark.parametrize(
        "provider_class,env_vars",
        [
            (GoogleProvider, {"LLM_PROVIDER": "google", "GOOGLE_API_KEY": "test"}),
            (OpenAIProvider, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}),
            (AnthropicProvider, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-ant-test"}),
            (OllamaProvider, {"LLM_PROVIDER": "ollama"}),
        ],
    )
    def test_all_providers_have_supports_vision(
        self, provider_class: type, env_vars: dict[str, str]
    ) -> None:
        """全プロバイダーがsupports_visionを持つことを確認."""
        with patch.dict(os.environ, env_vars, clear=True):
            config = LLMConfig(_env_file=None)
            provider = provider_class(config)
            assert isinstance(provider.supports_vision, bool)
