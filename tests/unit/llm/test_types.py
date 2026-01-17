"""LLMProviderType enumのテスト."""

import pytest

from company_research_agent.llm.types import LLMProviderType


class TestLLMProviderType:
    """LLMProviderType enumのテスト."""

    def test_openai_value(self) -> None:
        """OpenAIプロバイダーの値が正しいことを確認."""
        assert LLMProviderType.OPENAI.value == "openai"

    def test_google_value(self) -> None:
        """Googleプロバイダーの値が正しいことを確認."""
        assert LLMProviderType.GOOGLE.value == "google"

    def test_anthropic_value(self) -> None:
        """Anthropicプロバイダーの値が正しいことを確認."""
        assert LLMProviderType.ANTHROPIC.value == "anthropic"

    def test_ollama_value(self) -> None:
        """Ollamaプロバイダーの値が正しいことを確認."""
        assert LLMProviderType.OLLAMA.value == "ollama"

    def test_str_enum_behavior(self) -> None:
        """strとEnumの両方の性質を持つことを確認."""
        provider = LLMProviderType.GOOGLE
        assert isinstance(provider, str)
        assert provider == "google"

    def test_from_string(self) -> None:
        """文字列からLLMProviderTypeを作成できることを確認."""
        assert LLMProviderType("openai") == LLMProviderType.OPENAI
        assert LLMProviderType("google") == LLMProviderType.GOOGLE
        assert LLMProviderType("anthropic") == LLMProviderType.ANTHROPIC
        assert LLMProviderType("ollama") == LLMProviderType.OLLAMA

    def test_invalid_provider_raises_error(self) -> None:
        """無効なプロバイダー名でValueErrorが発生することを確認."""
        with pytest.raises(ValueError, match="'invalid' is not a valid"):
            LLMProviderType("invalid")

    def test_all_providers_count(self) -> None:
        """4種類のプロバイダーが定義されていることを確認."""
        assert len(LLMProviderType) == 4
