# 設計書

## アーキテクチャ概要

LLMプロバイダーを抽象化し、ファクトリーパターンで切り替え可能にする。

```
┌─────────────────────────────────────────────────────────────────┐
│   ワークフローレイヤー (workflows/)                              │
│   └─ AnalysisGraph: LLMProviderを注入                           │
│   └─ nodes/: 各分析ノードがLLMProviderを使用                     │
├─────────────────────────────────────────────────────────────────┤
│   LLM抽象化レイヤー (llm/)  ← 今回の実装対象                     │
│   ├─ config.py: LLMConfig（環境変数からの設定読み込み）          │
│   ├─ provider.py: LLMProviderプロトコル + BaseLLMProvider        │
│   ├─ factory.py: create_llm_provider()                          │
│   └─ providers/: 各プロバイダー実装                              │
│       ├─ openai.py: OpenAIProvider                              │
│       ├─ google.py: GoogleProvider                              │
│       ├─ anthropic.py: AnthropicProvider                        │
│       └─ ollama.py: OllamaProvider                              │
├─────────────────────────────────────────────────────────────────┤
│   クライアントレイヤー (clients/)                                │
│   └─ vision_client.py: VisionLLMClient（GeminiClient置換）      │
├─────────────────────────────────────────────────────────────────┤
│   既存レイヤー                                                   │
│   └─ parsers/pdf_parser.py: VisionLLMClientを使用               │
│   └─ schemas/llm_analysis.py: 出力スキーマ                      │
│   └─ prompts/: プロンプトテンプレート                           │
└─────────────────────────────────────────────────────────────────┘
```

## クラス設計

### 1. LLMProviderType（llm/types.py）

```python
from enum import Enum

class LLMProviderType(str, Enum):
    """LLMプロバイダーの種類."""
    OPENAI = "openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
```

### 2. LLMConfig（llm/config.py）

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class LLMConfig(BaseSettings):
    """LLM統合設定."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # テキスト分析用
    provider: LLMProviderType = Field(
        default=LLMProviderType.GOOGLE,
        alias="LLM_PROVIDER",
    )
    model: str | None = Field(default=None, alias="LLM_MODEL")

    # ビジョン用
    vision_provider: LLMProviderType | None = Field(
        default=None,
        alias="LLM_VISION_PROVIDER",
    )
    vision_model: str | None = Field(default=None, alias="LLM_VISION_MODEL")

    # 共通設定
    timeout: int = Field(default=120, alias="LLM_TIMEOUT")
    max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")
    rpm_limit: int = Field(default=60, alias="LLM_RPM_LIMIT")

    # APIキー
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
    )
```

### 3. LLMProviderプロトコル（llm/provider.py）

```python
from typing import Protocol, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class LLMProvider(Protocol):
    """LLMプロバイダーのプロトコル."""

    @property
    def model_name(self) -> str: ...

    @property
    def provider_name(self) -> str: ...

    @property
    def supports_vision(self) -> bool: ...

    async def ainvoke_structured(
        self,
        prompt: str,
        output_schema: type[T],
    ) -> T:
        """構造化出力でLLM呼び出し."""
        ...

    async def ainvoke_vision(
        self,
        text_prompt: str,
        image_data: bytes,
        mime_type: str = "image/png",
    ) -> str:
        """ビジョン入力でLLM呼び出し."""
        ...
```

### 4. BaseLLMProvider（llm/providers/base.py）

```python
from abc import ABC, abstractmethod
from typing import Any, TypeVar
from pydantic import BaseModel
from company_research_agent.llm.config import LLMConfig
from company_research_agent.core.exceptions import LLMProviderError

T = TypeVar("T", bound=BaseModel)

class BaseLLMProvider(ABC):
    """LLMプロバイダーの基底クラス."""

    def __init__(self, config: LLMConfig) -> None:
        self._config = config
        self._model: Any = None

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    def supports_vision(self) -> bool:
        return True  # デフォルトはTrue、非対応はオーバーライド

    @abstractmethod
    def _create_model(self) -> Any:
        """LangChain ChatModelを作成."""
        ...

    def get_model(self) -> Any:
        """モデルを取得（遅延初期化）."""
        if self._model is None:
            self._model = self._create_model()
        return self._model

    async def ainvoke_structured(
        self,
        prompt: str,
        output_schema: type[T],
    ) -> T:
        """構造化出力でLLM呼び出し."""
        try:
            model = self.get_model()
            structured = model.with_structured_output(output_schema)
            return await structured.ainvoke(prompt)
        except Exception as e:
            raise LLMProviderError(
                message=str(e),
                provider=self.provider_name,
                model=self.model_name,
            ) from e

    async def ainvoke_vision(
        self,
        text_prompt: str,
        image_data: bytes,
        mime_type: str = "image/png",
    ) -> str:
        """ビジョン入力でLLM呼び出し."""
        if not self.supports_vision:
            raise LLMProviderError(
                message="Vision not supported",
                provider=self.provider_name,
                model=self.model_name,
            )
        # 各プロバイダーでオーバーライド
        raise NotImplementedError
```

### 5. 各プロバイダー実装

#### OpenAIProvider（llm/providers/openai.py）

```python
class OpenAIProvider(BaseLLMProvider):
    DEFAULT_MODEL = "gpt-4o"
    DEFAULT_VISION_MODEL = "gpt-4o"

    @property
    def model_name(self) -> str:
        return self._config.model or self.DEFAULT_MODEL

    @property
    def provider_name(self) -> str:
        return "openai"

    def _create_model(self) -> Any:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=self.model_name,
            api_key=self._config.openai_api_key,
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
        )

    async def ainvoke_vision(
        self,
        text_prompt: str,
        image_data: bytes,
        mime_type: str = "image/png",
    ) -> str:
        import base64
        from langchain_core.messages import HumanMessage

        b64_data = base64.standard_b64encode(image_data).decode("utf-8")
        message = HumanMessage(
            content=[
                {"type": "text", "text": text_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{b64_data}"},
                },
            ]
        )
        response = await self.get_model().ainvoke([message])
        return str(response.content).strip()
```

#### GoogleProvider（llm/providers/google.py）

```python
class GoogleProvider(BaseLLMProvider):
    DEFAULT_MODEL = "gemini-2.5-flash-preview-05-20"

    @property
    def model_name(self) -> str:
        return self._config.model or self.DEFAULT_MODEL

    @property
    def provider_name(self) -> str:
        return "google"

    def _create_model(self) -> Any:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self._config.google_api_key,
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
        )
```

#### AnthropicProvider（llm/providers/anthropic.py）

```python
class AnthropicProvider(BaseLLMProvider):
    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    @property
    def model_name(self) -> str:
        return self._config.model or self.DEFAULT_MODEL

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def _create_model(self) -> Any:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=self.model_name,
            api_key=self._config.anthropic_api_key,
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
        )
```

#### OllamaProvider（llm/providers/ollama.py）

```python
class OllamaProvider(BaseLLMProvider):
    DEFAULT_MODEL = "llama3.2"
    DEFAULT_VISION_MODEL = "llava"

    @property
    def model_name(self) -> str:
        return self._config.model or self.DEFAULT_MODEL

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def supports_vision(self) -> bool:
        # llava系モデルのみビジョン対応
        return "llava" in self.model_name.lower()

    def _create_model(self) -> Any:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=self.model_name,
            base_url=self._config.ollama_base_url,
            timeout=self._config.timeout,
        )
```

### 6. ファクトリー（llm/factory.py）

```python
from functools import lru_cache
from company_research_agent.llm.config import LLMConfig
from company_research_agent.llm.types import LLMProviderType
from company_research_agent.llm.providers.base import BaseLLMProvider

def create_llm_provider(
    config: LLMConfig | None = None,
    for_vision: bool = False,
) -> BaseLLMProvider:
    """LLMプロバイダーを作成."""
    if config is None:
        config = LLMConfig()

    # ビジョン用の場合、vision_providerを優先
    provider_type = config.provider
    if for_vision and config.vision_provider:
        provider_type = config.vision_provider
        # ビジョン用モデルを設定
        if config.vision_model:
            config = config.model_copy(update={"model": config.vision_model})

    match provider_type:
        case LLMProviderType.OPENAI:
            from company_research_agent.llm.providers.openai import OpenAIProvider
            if not config.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required")
            return OpenAIProvider(config)

        case LLMProviderType.GOOGLE:
            from company_research_agent.llm.providers.google import GoogleProvider
            if not config.google_api_key:
                raise ValueError("GOOGLE_API_KEY is required")
            return GoogleProvider(config)

        case LLMProviderType.ANTHROPIC:
            from company_research_agent.llm.providers.anthropic import AnthropicProvider
            if not config.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is required")
            return AnthropicProvider(config)

        case LLMProviderType.OLLAMA:
            from company_research_agent.llm.providers.ollama import OllamaProvider
            return OllamaProvider(config)

@lru_cache(maxsize=1)
def get_default_provider() -> BaseLLMProvider:
    """デフォルトプロバイダーを取得（シングルトン）."""
    return create_llm_provider()

@lru_cache(maxsize=1)
def get_vision_provider() -> BaseLLMProvider:
    """ビジョン用プロバイダーを取得（シングルトン）."""
    return create_llm_provider(for_vision=True)
```

### 7. VisionLLMClient（clients/vision_client.py）

GeminiClientを置換し、任意のプロバイダーでPDF解析を行う。

```python
class VisionLLMClient:
    """PDF解析用のビジョンLLMクライアント."""

    EXTRACTION_PROMPT = """..."""  # 既存のプロンプトを継承

    def __init__(
        self,
        provider: BaseLLMProvider | None = None,
        rpm_limit: int = 60,
    ) -> None:
        self._provider = provider
        self._rpm_limit = rpm_limit
        self._last_request_time: float = 0.0

    @property
    def provider(self) -> BaseLLMProvider:
        if self._provider is None:
            from company_research_agent.llm.factory import get_vision_provider
            self._provider = get_vision_provider()
        return self._provider

    def extract_pdf_to_markdown(self, pdf_path: Path) -> str:
        """PDFからマークダウンを抽出."""
        # 既存のGeminiClientロジックを移植
        # self.provider.ainvoke_vision()を使用
```

### 8. LLMAnalysisNode修正（workflows/nodes/base.py）

```python
class LLMAnalysisNode(AnalysisNode[T]):
    def __init__(self, llm_provider: BaseLLMProvider | None = None) -> None:
        self._llm_provider = llm_provider

    @property
    def llm_provider(self) -> BaseLLMProvider:
        if self._llm_provider is None:
            from company_research_agent.llm.factory import get_default_provider
            self._llm_provider = get_default_provider()
        return self._llm_provider

    async def _invoke_llm(self, prompt: str) -> T:
        return await self.llm_provider.ainvoke_structured(
            prompt=prompt,
            output_schema=self.output_schema,
        )
```

## ディレクトリ構造

```
src/company_research_agent/
├── llm/                           # 新規
│   ├── __init__.py
│   ├── types.py                   # LLMProviderType
│   ├── config.py                  # LLMConfig
│   ├── provider.py                # LLMProvider Protocol
│   ├── factory.py                 # create_llm_provider
│   └── providers/
│       ├── __init__.py
│       ├── base.py                # BaseLLMProvider
│       ├── openai.py              # OpenAIProvider
│       ├── google.py              # GoogleProvider
│       ├── anthropic.py           # AnthropicProvider
│       └── ollama.py              # OllamaProvider
├── clients/
│   ├── vision_client.py           # 新規（GeminiClient置換）
│   └── gemini_client.py           # 削除予定
├── workflows/
│   ├── graph.py                   # 修正
│   └── nodes/
│       ├── base.py                # 修正
│       └── *.py                   # 各ノード修正
└── core/
    ├── config.py                  # GeminiConfig削除
    └── exceptions.py              # LLMProviderError追加
```

## データフロー

```
環境変数
    │
    ▼
LLMConfig（設定読み込み）
    │
    ▼
LLMProviderFactory
    │
    ├─► OpenAIProvider ──► ChatOpenAI
    ├─► GoogleProvider ──► ChatGoogleGenerativeAI
    ├─► AnthropicProvider ──► ChatAnthropic
    └─► OllamaProvider ──► ChatOllama
           │
           ▼
    LLMAnalysisNode / VisionLLMClient
           │
           ▼
    ainvoke_structured() / ainvoke_vision()
```

## エラーハンドリング

```python
@dataclass
class LLMProviderError(CompanyResearchAgentError):
    """LLMプロバイダーエラー."""
    message: str
    provider: str | None = None
    model: str | None = None
```

各プロバイダー固有のエラーはLLMProviderErrorでラップして統一的に処理する。
