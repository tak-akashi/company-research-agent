"""LLMプロバイダーの型定義."""

from __future__ import annotations

from enum import Enum


class LLMProviderType(str, Enum):
    """LLMプロバイダーの種類.

    環境変数 LLM_PROVIDER で指定可能な値。

    Example:
        >>> provider_type = LLMProviderType.GOOGLE
        >>> provider_type.value
        'google'
    """

    OPENAI = "openai"
    """OpenAI API (GPT-4o, GPT-5-mini等)."""

    GOOGLE = "google"
    """Google Gemini API (Gemini 2.5 Flash, Pro等)."""

    ANTHROPIC = "anthropic"
    """Anthropic Claude API (Claude Sonnet, Opus等)."""

    OLLAMA = "ollama"
    """Ollama ローカルLLM (llama3.2, gpt-oss-20b, llava等)."""
