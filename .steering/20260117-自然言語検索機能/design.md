# 設計書

## アーキテクチャ概要

ReActエージェント + ツール群のアーキテクチャを採用し、ユーザーの自然言語クエリに対して適切なツールを動的に選択・実行する。

```
ユーザークエリ: 「トヨタの有報を分析して」
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  QueryOrchestrator (ReActエージェント)                   │
│                                                         │
│  1. クエリを解釈                                         │
│  2. 意図を判定: 検索/分析/比較/要約                       │
│  3. 必要なツールを選択・実行                              │
│  4. 結果を統合して返却                                   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  ツール群                                        │   │
│  │                                                 │   │
│  │  [検索系]                                       │   │
│  │  - search_company      企業名→候補リスト        │   │
│  │  - search_documents    条件→書類リスト          │   │
│  │  - download_document   書類→PDFパス            │   │
│  │                                                 │   │
│  │  [分析系]                                       │   │
│  │  - analyze_document    AnalysisGraph wrapper   │   │
│  │  - compare_documents   PDFParser + LLM比較     │   │
│  │  - summarize_document  PDFParser + LLM要約     │   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 処理フロー例

### 例1: 検索のみ（「トヨタの有報を探して」）

```
Step 1: オーケストレーターがクエリを解釈
┌─────────────────────────────────────┐
│ 意図: 検索                          │
│ 企業名: トヨタ                       │
│ 書類種別: 有価証券報告書              │
└─────────────────────────────────────┘

Step 2: search_company ツール呼び出し
┌─────────────────────────────────────┐
│ 入力: "トヨタ"                       │
│ 出力:                               │
│ 1. トヨタ自動車 (E02144) - 95点     │
│ 2. トヨタ紡織 (E02158) - 80点       │
│ 3. トヨタ車体 (E02160) - 75点       │
└─────────────────────────────────────┘

Step 3: search_documents ツール呼び出し
┌─────────────────────────────────────┐
│ 入力: edinet_code="E02144",         │
│       doc_type_codes=["120"]        │
│ 出力: 書類リスト                     │
└─────────────────────────────────────┘

Step 4: 結果を返却
```

### 例2: 分析まで実行（「トヨタの有報を分析して」）

```
Step 1-3: 検索フローと同じ

Step 4: download_document ツール呼び出し
┌─────────────────────────────────────┐
│ 入力: doc_id="S100XXXX"             │
│ 出力: PDFパス                        │
└─────────────────────────────────────┘

Step 5: analyze_document ツール呼び出し
┌─────────────────────────────────────┐
│ 入力: doc_id="S100XXXX"             │
│ 内部: AnalysisGraph実行              │
│ 出力: ComprehensiveReport           │
└─────────────────────────────────────┘
```

## コンポーネント設計

### 1. ツール定義

**ディレクトリ**: `src/company_research_agent/tools/`

```
tools/
├── __init__.py
├── search_company.py      # 企業検索ツール
├── search_documents.py    # 書類検索ツール
├── download_document.py   # 書類ダウンロードツール
├── analyze_document.py    # 分析ツール（AnalysisGraph wrapper）
├── compare_documents.py   # 比較ツール（PDFParser + LLM）
└── summarize_document.py  # 要約ツール（PDFParser + LLM）
```

#### 1.1 search_company

```python
from langchain_core.tools import tool

@tool
async def search_company(query: str, limit: int = 10) -> list[CompanyCandidate]:
    """企業名で検索し、類似度スコア付き候補リストを返す。

    Args:
        query: 検索クエリ（企業名、EDINETコード、証券コード）
        limit: 返却する候補の最大数

    Returns:
        類似度スコア付きの企業候補リスト
    """
    client = EDINETCodeListClient()
    await client.ensure_code_list()
    return await client.search_companies(query, limit)
```

#### 1.2 search_documents

```python
@tool
async def search_documents(
    edinet_code: str,
    doc_type_codes: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[DocumentMetadata]:
    """EDINET書類を検索する。

    Args:
        edinet_code: 企業のEDINETコード
        doc_type_codes: 書類種別コード（120=有報, 140=四半期等）
        start_date: 検索開始日（YYYY-MM-DD）
        end_date: 検索終了日（YYYY-MM-DD）

    Returns:
        書類メタデータのリスト
    """
    filter = DocumentFilter(
        edinet_code=edinet_code,
        doc_type_codes=doc_type_codes,
        start_date=parse_date(start_date),
        end_date=parse_date(end_date),
    )
    async with EDINETClient(EDINETConfig()) as client:
        service = EDINETDocumentService(client)
        return await service.search_documents(filter)
```

#### 1.3 download_document

```python
@tool
async def download_document(doc_id: str) -> str:
    """EDINET書類をダウンロードし、ローカルパスを返す。

    Args:
        doc_id: 書類ID（S100XXXX形式）

    Returns:
        ダウンロードしたPDFのローカルパス
    """
    async with EDINETClient(EDINETConfig()) as client:
        return await client.download_document(doc_id, DocumentDownloadType.PDF)
```

#### 1.4 analyze_document

```python
@tool
async def analyze_document(doc_id: str) -> ComprehensiveReport:
    """書類を分析し、統合レポートを生成する。

    既存のAnalysisGraphを利用。

    Args:
        doc_id: 書類ID

    Returns:
        事業概要、リスク分析、財務分析を含む統合レポート
    """
    graph = AnalysisGraph()
    result = await graph.ainvoke({"doc_id": doc_id})
    return result["comprehensive_report"]
```

#### 1.5 compare_documents

```python
@tool
async def compare_documents(
    doc_ids: list[str],
    aspects: list[str] | None = None,
) -> ComparisonReport:
    """複数の書類を比較分析する。

    PDFParserでマークダウン化し、LLMで比較分析。

    Args:
        doc_ids: 比較する書類IDのリスト
        aspects: 比較観点（事業内容、財務、リスク等）

    Returns:
        比較分析レポート
    """
    parser = PDFParser()
    llm = get_default_provider()

    # 各書類をマークダウン化
    contents = []
    for doc_id in doc_ids:
        pdf_path = await download_document(doc_id)
        markdown = await parser.to_markdown(pdf_path)
        contents.append(markdown)

    # LLMで比較分析
    prompt = COMPARE_DOCUMENTS_PROMPT.format(
        documents=contents,
        aspects=aspects or ["事業内容", "財務状況", "リスク"],
    )
    return await llm.ainvoke_structured(prompt, ComparisonReport)
```

#### 1.6 summarize_document

```python
@tool
async def summarize_document(
    doc_id: str,
    focus: str | None = None,
) -> Summary:
    """書類を要約する。

    PDFParserでマークダウン化し、LLMで要約。

    Args:
        doc_id: 書類ID
        focus: 要約の焦点（事業概要、リスク、財務等）

    Returns:
        要約レポート
    """
    parser = PDFParser()
    llm = get_default_provider()

    pdf_path = await download_document(doc_id)
    markdown = await parser.to_markdown(pdf_path)

    prompt = SUMMARIZE_DOCUMENT_PROMPT.format(
        content=markdown,
        focus=focus or "全体",
    )
    return await llm.ainvoke_structured(prompt, Summary)
```

### 2. オーケストレーター

**ファイル**: `src/company_research_agent/orchestrator/query_orchestrator.py`

```python
from langgraph.prebuilt import create_react_agent

class QueryOrchestrator:
    """自然言語クエリを処理するReActエージェント"""

    def __init__(
        self,
        llm_provider: BaseLLMProvider | None = None,
        tools: list[BaseTool] | None = None,
    ) -> None:
        self._llm = llm_provider or get_default_provider()
        self._tools = tools or self._default_tools()
        self._agent = self._build_agent()

    def _default_tools(self) -> list[BaseTool]:
        return [
            search_company,
            search_documents,
            download_document,
            analyze_document,
            compare_documents,
            summarize_document,
        ]

    def _build_agent(self) -> CompiledStateGraph:
        """ReActエージェントを構築"""
        return create_react_agent(
            model=self._llm.get_model(),
            tools=self._tools,
            state_modifier=ORCHESTRATOR_SYSTEM_PROMPT,
        )

    async def process(self, query: str) -> OrchestratorResult:
        """クエリを処理し、結果を返す"""
        result = await self._agent.ainvoke({"messages": [("user", query)]})
        return self._parse_result(result)
```

### 3. スキーマ

**ファイル**: `src/company_research_agent/schemas/query_schemas.py`

```python
from dataclasses import dataclass
from pydantic import BaseModel, Field

@dataclass
class CompanyInfo:
    """企業情報"""
    edinet_code: str
    sec_code: str | None
    company_name: str
    company_name_kana: str | None
    company_name_en: str | None
    listing_code: str | None
    industry_code: str | None

@dataclass
class CompanyCandidate:
    """企業候補（検索結果）"""
    company: CompanyInfo
    similarity_score: float  # 0-100
    match_field: str  # "company_name" | "company_name_kana"

class ComparisonItem(BaseModel):
    """比較項目"""
    aspect: str = Field(description="比較観点")
    company_a: str = Field(description="企業Aの内容")
    company_b: str = Field(description="企業Bの内容")
    difference: str = Field(description="主な違い")

class ComparisonReport(BaseModel):
    """比較分析レポート"""
    documents: list[str] = Field(description="比較した書類ID")
    aspects: list[str] = Field(description="比較観点")
    comparisons: list[ComparisonItem] = Field(description="比較結果")
    summary: str = Field(description="総括")

class Summary(BaseModel):
    """要約レポート"""
    doc_id: str = Field(description="書類ID")
    focus: str | None = Field(description="要約の焦点")
    key_points: list[str] = Field(description="重要ポイント")
    summary_text: str = Field(description="要約テキスト")

class OrchestratorResult(BaseModel):
    """オーケストレーター結果"""
    query: str = Field(description="元のクエリ")
    intent: str = Field(description="判定された意図")
    result: Any = Field(description="処理結果")
    tools_used: list[str] = Field(description="使用したツール")
```

### 4. 基盤クライアント

**ファイル**: `src/company_research_agent/clients/edinet_code_list_client.py`

```python
class EDINETCodeListClient:
    """EDINETコードリストのダウンロード・キャッシュ・検索"""

    CACHE_DIR = Path("data/cache/edinet_code_list")
    CACHE_VALIDITY_DAYS = 7
    CODE_LIST_URL = "https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Edinetcode.zip"

    async def ensure_code_list(self, force_refresh: bool = False) -> Path:
        """コードリストを確保（必要に応じてダウンロード）"""

    async def search_companies(
        self,
        query: str,
        limit: int = 10,
    ) -> list[CompanyCandidate]:
        """企業名で検索（rapidfuzzで類似度計算）"""

    async def get_by_edinet_code(self, code: str) -> CompanyInfo | None:
        """EDINETコードで検索"""

    async def get_by_sec_code(self, code: str) -> CompanyInfo | None:
        """証券コードで検索"""
```

### 5. プロンプト

**ディレクトリ**: `src/company_research_agent/prompts/`

#### orchestrator_system.py

```python
ORCHESTRATOR_SYSTEM_PROMPT = """あなたは企業リサーチを支援するAIアシスタントです。

ユーザーの質問に対して、適切なツールを選択・実行し、結果を返してください。

## 利用可能なツール

### 検索系
- search_company: 企業名で検索し、候補リストを返す
- search_documents: EDINET書類を検索する
- download_document: 書類をダウンロードする

### 分析系
- analyze_document: 書類を詳細に分析し、統合レポートを生成する
- compare_documents: 複数の書類を比較分析する
- summarize_document: 書類を要約する

## ユーザーの意図の判定

- 「探して」「検索して」→ 検索のみ（search_company + search_documents）
- 「分析して」「詳しく教えて」→ 分析まで実行（+ analyze_document）
- 「比較して」→ 比較分析（+ compare_documents）
- 「要約して」「まとめて」→ 要約（+ summarize_document）

## 処理の流れ

1. ユーザーの意図を判定
2. 必要なツールを順番に実行
3. 結果をわかりやすく返却

## 注意事項

- 企業名が曖昧な場合は、候補リストを提示してユーザーに確認
- 書類が見つからない場合は、検索条件を変えて再試行
- エラーが発生した場合は、ユーザーにわかりやすく説明
"""
```

#### compare_documents.py

```python
COMPARE_DOCUMENTS_PROMPT = """以下の書類を比較分析してください。

## 書類
{documents}

## 比較観点
{aspects}

## 出力形式
各観点について、それぞれの書類の内容と主な違いを説明してください。
最後に総括を記載してください。
"""
```

#### summarize_document.py

```python
SUMMARIZE_DOCUMENT_PROMPT = """以下の書類を要約してください。

## 書類内容
{content}

## 焦点
{focus}

## 出力形式
重要ポイントを箇条書きで列挙し、その後に要約テキストを記載してください。
"""
```

## ディレクトリ構造

```
src/company_research_agent/
├── clients/
│   ├── edinet_client.py              # 既存
│   └── edinet_code_list_client.py    # 新規
├── services/
│   └── edinet_document_service.py    # 既存
├── tools/                             # 新規ディレクトリ
│   ├── __init__.py
│   ├── search_company.py
│   ├── search_documents.py
│   ├── download_document.py
│   ├── analyze_document.py
│   ├── compare_documents.py
│   └── summarize_document.py
├── orchestrator/                      # 新規ディレクトリ
│   ├── __init__.py
│   └── query_orchestrator.py
├── schemas/
│   ├── edinet_schemas.py             # 既存
│   ├── document_filter.py            # 既存
│   └── query_schemas.py              # 新規
├── prompts/
│   ├── orchestrator_system.py        # 新規
│   ├── compare_documents.py          # 新規
│   └── summarize_document.py         # 新規
├── parsers/
│   └── pdf_parser.py                 # 既存（compare/summarizeで利用）
└── workflows/
    └── graph.py                      # 既存（analyze_documentで利用）

tests/unit/
├── clients/
│   └── test_edinet_code_list_client.py
├── tools/
│   ├── test_search_company.py
│   ├── test_search_documents.py
│   ├── test_analyze_document.py
│   ├── test_compare_documents.py
│   └── test_summarize_document.py
└── orchestrator/
    └── test_query_orchestrator.py
```

## 依存ライブラリ

```toml
# pyproject.toml に追加
dependencies = [
    "rapidfuzz>=3.0.0,<4.0.0",  # 類似度計算
]
```

既存の依存関係で対応:
- `langgraph`: ReActエージェント
- `langchain-core`: ツール定義
- `httpx`: ZIPダウンロード
- `pydantic`: スキーマ定義

## エラーハンドリング

### カスタム例外

```python
class CompanyNotFoundError(CompanyResearchAgentError):
    """企業が見つからない場合"""

class CodeListDownloadError(CompanyResearchAgentError):
    """コードリストのダウンロードに失敗した場合"""

class DocumentNotFoundError(CompanyResearchAgentError):
    """書類が見つからない場合"""

class AnalysisError(CompanyResearchAgentError):
    """分析に失敗した場合"""
```

### リトライ戦略

- コードリストダウンロード: 3回リトライ（指数バックオフ）
- EDINET API: 既存のEDINETClientのリトライ設定を使用
- LLM呼び出し: 既存のLLMProviderのリトライ設定を使用

## テスト戦略

### ユニットテスト

- 各ツールの単体テスト（モック使用）
- オーケストレーターの意図判定テスト

### 統合テスト

- Jupyterでの手動テスト
- E2Eフロー確認

## パフォーマンス考慮事項

- 企業数: 約4,000社（メモリ使用量: 約5MB）
- 企業名検索: rapidfuzzで高速マッチング
- 初回起動時のみダウンロード（約30秒）
- キャッシュ有効期限: 7日
