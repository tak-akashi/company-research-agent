"""Type definitions for Company Research Agent."""

from enum import Enum
from typing import Literal


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


# Document download type for EDINET API
# 1: XBRL (ZIP) - 提出本文書及び監査報告書
# 2: PDF - 提出本文書及び監査報告書
# 3: 添付文書 (ZIP)
# 4: 英文ファイル (ZIP)
# 5: CSV (ZIP) - 財務諸表データ
type DocumentDownloadType = Literal[1, 2, 3, 4, 5]

# PDF parsing strategy
# auto: Automatically select the best strategy with fallback chain
#       (pymupdf4llm → yomitoku → gemini)
# pdfplumber: Basic text extraction using pdfplumber
# pymupdf4llm: Markdown conversion with structure preservation
# yomitoku: Japanese OCR for scanned documents and complex layouts
# gemini: LLM-based extraction using Gemini 2.5 Flash (fallback)
type ParseStrategy = Literal["auto", "pdfplumber", "pymupdf4llm", "yomitoku", "gemini"]
