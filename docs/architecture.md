# 技術仕様書 (Architecture Design Document)

## テクノロジースタック

### 言語・ランタイム

| 技術 | バージョン | 選定理由 |
|------|-----------|----------|
| Python | 3.11+ | 型ヒント（PEP 604/612）の完全サポート、データ分析エコシステム、asyncioによる非同期処理 |
| uv | 0.5+ | Rust製の高速パッケージマネージャ（pip比で10-100倍高速）、pyproject.tomlによる統一的な依存関係管理 |

### フレームワーク・ライブラリ

| 技術 | バージョン | 用途 | 選定理由 |
|------|-----------|------|----------|
| FastAPI | 0.115+ | REST API | 高速、型安全、OpenAPI自動生成、asyncio対応 |
| SQLAlchemy | 2.0+ | ORM | 型安全なクエリビルダー、asyncio対応、PostgreSQL最適化 |
| asyncpg | 0.30+ | PostgreSQL接続 | 高速な非同期PostgreSQLドライバー |
| pandas | 2.2+ | データ処理 | 財務データの操作・変換、DataFrame形式での提供 |
| edinet-xbrl | 0.2+ | XBRL解析（基本） | EDINET特化、シンプルなAPI |
| beautifulsoup4 | 4.12+ | XBRL解析（フォールバック） | 柔軟なXML/HTML解析、名前空間対応 |
| lxml | 5.0+ | XML解析 | 高速なXMLパーサー、XPath対応 |
| httpx | 0.28+ | HTTP通信 | 非同期対応、リトライ機能、モダンなAPI |
| tenacity | 9.0+ | リトライ処理 | 柔軟なリトライロジック、指数バックオフ |
| pydantic | 2.10+ | バリデーション | 型安全なデータバリデーション、シリアライゼーション |
| Streamlit | 1.40+ | 簡易UI | 高速プロトタイピング、Pythonのみで構築可能 |

### PDF解析

| 技術 | バージョン | 用途 | 選定理由 |
|------|-----------|------|----------|
| pdfplumber | 0.11+ | PDF基本解析 | テキスト抽出、シンプルな表解析、軽量 |
| pymupdf4llm | 0.0.17+ | マークダウン変換 | 構造を保持したマークダウン出力、高速 |
| yomitoku | 0.7+ | 日本語OCR | 日本語表認識に特化、高精度、無料 |

**PDF解析の段階的戦略**:
```
1. pdfplumber（基本）
   └─ テキストPDFの抽出、シンプルな表

2. pymupdf4llm（中間）
   └─ 構造化されたマークダウン変換

3. YOMITOKU（高精度）
   └─ 複雑な日本語表、スキャンPDF

4. Gemini API（最終手段）
   └─ 上記で解析困難な場合のLLM解析
```

### AI/ML関連

| 技術 | バージョン | 用途 | 選定理由 |
|------|-----------|------|----------|
| LangGraph | 1.0+ | エージェントオーケストレーション | 状態管理、ワークフロー制御、マルチエージェント対応 |
| LangChain | 1.0+ | LLM基盤フレームワーク | プロンプト管理、チェーン構築、ツール統合 |
| langchain-google-genai | 2.1+ | Gemini API連携 | LangChain統合、Gemini 2.5 Flash対応 |
| langchain-openai | 0.3+ | OpenAI API連携 | GPT-4o対応、Structured Output |
| langchain-anthropic | 0.3+ | Anthropic API連携 | Claude Sonnet/Opus対応 |
| langchain-ollama | 0.2+ | Ollama連携 | ローカルLLM実行、llama3.2/llava対応 |
| pgvector | 0.3+ | ベクトル検索 | PostgreSQLネイティブ、LangChain連携 |

### 開発ツール

| 技術 | バージョン | 用途 | 選定理由 |
|------|-----------|------|----------|
| ruff | 0.8+ | Linter/Formatter | Rust製で高速、flake8/black/isortを統合 |
| mypy | 1.14+ | 型チェック | 静的型チェックによるランタイムエラーの事前検出 |
| pytest | 8.0+ | テスト | 標準的なテストフレームワーク、豊富なプラグイン |
| pytest-asyncio | 0.24+ | 非同期テスト | asyncio関数のテスト対応 |
| pytest-cov | 6.0+ | カバレッジ | テストカバレッジの計測 |

### インフラ・データベース

| 技術 | バージョン | 用途 | 選定理由 |
|------|-----------|------|----------|
| PostgreSQL | 15+ | RDB | 安定性、pgvector対応、JSONサポート |
| pgvector | 0.7+ | ベクトル拡張 | PostgreSQLネイティブなベクトル検索 |
| Docker | 24+ | コンテナ | 開発環境の統一、クロスプラットフォーム対応 |
| Docker Compose | 2.0+ | オーケストレーション | ローカル開発環境・ユーザー実行環境の構築 |

### 実行環境

本プロジェクトは2つの実行環境をサポートします:

| 環境 | 対象 | 用途 |
|------|------|------|
| ローカル環境（uv） | 開発者（Mac） | 開発・デバッグ、高速な開発サイクル |
| Docker環境 | 開発者・ユーザー（Windows/Mac/Linux） | クロスプラットフォーム対応、環境構築の簡易化 |

**Docker構成**:
```
┌─────────────────────────────────────────────────────────────┐
│   docker-compose.yml                                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   app       │  │  postgres   │  │   pgvector          │  │
│  │  (Python)   │──│  (DB)       │──│   (extension)       │  │
│  │             │  │  port:5432  │  │                     │  │
│  │  port:8000  │  └─────────────┘  └─────────────────────┘  │
│  └─────────────┘                                            │
│         │                                                   │
│         ├── /app (ソースコード)                              │
│         └── /data (ボリュームマウント)                        │
└─────────────────────────────────────────────────────────────┘
```

**Dockerイメージ構成**:
- **ベースイメージ**: `python:3.11-slim`（軽量、セキュリティ更新が頻繁）
- **マルチステージビルド**: 開発用と本番用を分離
- **ボリューム**: データディレクトリは永続化（ホストマウント）

---

## アーキテクチャパターン

### レイヤードアーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│   UIレイヤー                                             │
│   ├─ Jupyter Notebook（Python API直接利用）              │
│   ├─ Streamlit（簡易Web UI）                            │
│   └─ REST API（FastAPI）                                │
├─────────────────────────────────────────────────────────┤
│   サービスレイヤー                                        │
│   ├─ EDINETDocumentService（書類検索）✅ 実装済          │
│   ├─ EDINETClient（EDINET API連携）✅ 実装済            │
│   ├─ LLMProvider（マルチLLM抽象化）✅ 実装済            │
│   │   ├─ OpenAI / Google / Anthropic / Ollama         │
│   ├─ VisionLLMClient（PDF解析用ビジョンLLM）✅ 実装済   │
│   ├─ XBRLParser（XBRL解析）                             │
│   ├─ PDFParser（PDF解析）✅ 実装済                      │
│   ├─ FinancialAnalyzer（財務分析）                       │
│   ├─ AnalysisWorkflow（LangGraph LLM分析）✅ 実装済    │
│   └─ VectorSearchService（ベクトル検索）                 │
├─────────────────────────────────────────────────────────┤
│   リポジトリレイヤー                                      │
│   ├─ CompanyRepository                                  │
│   ├─ DocumentRepository                                 │
│   ├─ FinancialStatementRepository                       │
│   └─ FinancialIndicatorRepository                       │
├─────────────────────────────────────────────────────────┤
│   データレイヤー                                          │
│   ├─ PostgreSQL（構造化データ）                          │
│   ├─ pgvector（ベクトルデータ）                          │
│   └─ FileStorage（ダウンロードファイル）                  │
└─────────────────────────────────────────────────────────┘
```

#### UIレイヤー
- **責務**: ユーザー入力の受付、バリデーション、結果の表示
- **許可される操作**: サービスレイヤーの呼び出し
- **禁止される操作**: リポジトリ・データレイヤーへの直接アクセス

```python
# OK: サービスレイヤーを呼び出す
class DocumentAPI:
    def __init__(self, document_service: EDINETDocumentService) -> None:
        self.document_service = document_service

    async def search(self, filter: DocumentFilter) -> list[DocumentMetadata]:
        return await self.document_service.search_documents(filter)

# NG: クライアントやリポジトリを直接呼び出す
# async def search(self, filter: DocumentFilter):
#     return await self.edinet_client.get_document_list(date.today())  # ❌
#     return await self.document_repository.find_by_filter(filter)  # ❌
```

#### サービスレイヤー
- **責務**: ビジネスロジックの実装、外部APIとの連携、データ変換
- **許可される操作**: リポジトリレイヤーの呼び出し、外部API呼び出し
- **禁止される操作**: UIレイヤーへの依存

```python
class FinancialAnalyzer:
    def __init__(self, repository: FinancialStatementRepository) -> None:
        self.repository = repository

    async def calculate_indicators(
        self,
        company_id: str,
        fiscal_year: int
    ) -> FinancialIndicators:
        statement = await self.repository.get_by_company_and_year(
            company_id, fiscal_year
        )
        return self._calculate(statement)
```

#### リポジトリレイヤー
- **責務**: データアクセスの抽象化、CRUD操作
- **許可される操作**: データレイヤーへのアクセス
- **禁止される操作**: ビジネスロジックの実装

```python
class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, document: Document) -> str:
        self.session.add(document)
        await self.session.commit()
        return document.id

    async def find_by_doc_id(self, doc_id: str) -> Document | None:
        result = await self.session.execute(
            select(Document).where(Document.doc_id == doc_id)
        )
        return result.scalar_one_or_none()
```

#### データレイヤー
- **責務**: データの永続化、ファイルシステムへのアクセス
- **許可される操作**: PostgreSQL、ファイルシステムへのアクセス
- **禁止される操作**: ビジネスロジックの実装

---

## データ永続化戦略

### ストレージ方式

| データ種別 | ストレージ | フォーマット | 理由 |
|-----------|----------|-------------|------|
| 企業情報 | PostgreSQL | テーブル | リレーショナルデータ、検索性能 |
| 書類メタデータ | PostgreSQL | テーブル | リレーショナルデータ、インデックス |
| 財務諸表データ | PostgreSQL | テーブル | 構造化データ、集計クエリ |
| 財務指標 | PostgreSQL | テーブル | 時系列データ、比較分析 |
| ベクトル埋め込み | pgvector | vector型 | 類似検索、セマンティック検索 |
| XBRLファイル | ファイルシステム | ZIP | 元データの保持、再解析対応 |
| PDFファイル | ファイルシステム | PDF | 元データの保持、再解析対応 |
| 一時ファイル | ファイルシステム | 各種 | 処理中間データ、削除可能 |

### ファイルストレージ構造

```
data/
├── downloads/                    # ダウンロードファイル
│   ├── xbrl/                    # XBRLファイル（ZIP解凍後）
│   │   └── {doc_id}/
│   │       ├── PublicDoc/
│   │       └── XBRL/
│   └── pdf/                     # PDFファイル
│       └── {doc_id}.pdf
├── cache/                       # キャッシュデータ
│   └── edinet_code_list.json   # EDINETコードリスト
└── temp/                        # 一時ファイル（定期削除）
```

### バックアップ戦略

- **データベース**:
  - **頻度**: 日次（深夜バッチ処理前）
  - **方式**: pg_dump による論理バックアップ
  - **世代管理**: 最新7世代を保持
  - **保存先**: 別ストレージ（S3等、本番環境の場合）

- **ファイルストレージ**:
  - **頻度**: 週次
  - **方式**: rsync によるミラーリング
  - **世代管理**: 最新4世代を保持

- **復元方法**:
  ```bash
  # データベース復元
  pg_restore -d company_research_agent backup.dump

  # ファイル復元
  rsync -av backup/data/ data/
  ```

---

## パフォーマンス要件

### レスポンスタイム

| 操作 | 目標時間 | 測定環境 |
|------|---------|---------|
| 書類一覧検索（EDINET API） | 3秒以内 | EDINET APIレスポンス依存 |
| 書類ダウンロード（ZIP 10MB） | 10秒以内 | ネットワーク帯域依存 |
| XBRL解析（有価証券報告書1件） | 5秒以内 | CPU Core i5相当、メモリ8GB |
| 財務指標計算 | 100ms以内 | 同上 |
| データベース検索（企業検索） | 500ms以内 | PostgreSQL、インデックス使用 |
| ベクトル検索（類似企業10件） | 1秒以内 | pgvector、HNSW索引 |
| PDF解析（100ページ） | 5分以内 | Gemini API依存 |

### リソース使用量

| リソース | 上限 | 理由 |
|---------|------|------|
| メモリ（サービス） | 2GB | 大規模XBRLファイルの解析対応 |
| メモリ（バッチ処理） | 4GB | 並列処理時の最大使用量 |
| CPU | 制限なし | バッチ処理時に使用可能なリソースを活用 |
| ディスク（ダウンロード） | 100GB | 過去10年分の書類保持 |
| ディスク（データベース） | 50GB | 財務データ + ベクトル埋め込み |

### スループット

| 処理 | 目標 | 備考 |
|------|------|------|
| 日次バッチ処理 | 200件/4時間 | 新規開示書類の処理 |
| EDINET API呼び出し | 60回/分 | レート制限対応 |
| XBRL解析（並列） | 10件/分 | 5並列処理 |

---

## セキュリティアーキテクチャ

### データ保護

- **暗号化**:
  - データベース接続: SSL/TLS必須
  - 機密データ（APIキー等）: 環境変数で管理、ログ出力禁止

- **アクセス制御**:
  - ファイルパーミッション: 600（所有者のみ読み書き）
  - データベース: 専用ユーザー、最小権限の原則

- **機密情報管理**:
  ```bash
  # .env ファイル（.gitignore対象）
  EDINET_API_KEY=xxxxx

  # LLMプロバイダー設定
  LLM_PROVIDER=google  # openai / google / anthropic / ollama
  LLM_MODEL=gemini-2.5-flash-preview-05-20

  # APIキー（使用するプロバイダーに応じて設定）
  GOOGLE_API_KEY=xxxxx
  OPENAI_API_KEY=xxxxx
  ANTHROPIC_API_KEY=xxxxx
  OLLAMA_BASE_URL=http://localhost:11434

  DATABASE_URL=postgresql://user:pass@localhost/db

  # ソースコードにハードコードしない
  # ログに出力しない
  ```

### 入力検証

- **バリデーション**:
  ```python
  from pydantic import BaseModel, Field, field_validator

  class DocumentSearchRequest(BaseModel):
      edinet_code: str | None = Field(None, pattern=r"^E\d{5}$")
      sec_code: str | None = Field(None, pattern=r"^\d{5}$")
      start_date: date | None = None
      end_date: date | None = None

      @field_validator("end_date")
      @classmethod
      def validate_date_range(cls, v: date | None, info) -> date | None:
          if v and info.data.get("start_date") and v < info.data["start_date"]:
              raise ValueError("end_date must be after start_date")
          return v
  ```

- **サニタイゼーション**:
  - SQLクエリ: SQLAlchemyのパラメータバインディング使用
  - ファイルパス: パストラバーサル攻撃の防止

- **エラーハンドリング**:
  - スタックトレースを本番環境で非表示
  - 機密情報をエラーメッセージに含めない

---

## スケーラビリティ設計

### データ増加への対応

- **想定データ量**:
  - 企業数: 約4,000社（上場企業）
  - 書類数: 約50,000件/年（新規開示）
  - 財務データ: 約200,000レコード/年

- **パフォーマンス劣化対策**:
  - インデックス最適化（企業コード、提出日、書類種別）
  - パーティショニング（年度別）
  - クエリ最適化（EXPLAIN ANALYZEによる分析）

- **アーカイブ戦略**:
  - 10年以上前のデータ: 別テーブル（アーカイブ）に移動
  - ダウンロードファイル: 5年以上前のファイルは圧縮保存

### 機能拡張性

- **プラグインシステム**:
  - データソース追加: 抽象クラス `DataSourceClient` を継承
  - 財務指標追加: 設定ファイル（YAML）で定義
  - 解析ロジック追加: `Parser` インターフェースを実装

  ```python
  from abc import ABC, abstractmethod

  class DataSourceClient(ABC):
      """データソースクライアントの基底クラス"""

      @abstractmethod
      async def search_documents(
          self, filter: DocumentFilter
      ) -> list[DocumentMetadata]:
          ...

      @abstractmethod
      async def download_document(
          self, doc_id: str, save_path: Path
      ) -> Path:
          ...

  # 新しいデータソースの追加
  class TDnetClient(DataSourceClient):
      """TDnetクライアント（将来実装）"""
      ...
  ```

- **設定のカスタマイズ**:
  - 財務指標の計算式: YAML設定ファイル
  - XBRL要素名マッピング: JSON設定ファイル
  - バッチ処理スケジュール: 環境変数

- **API拡張性**:
  - OpenAPI仕様に基づくバージョニング（/api/v1/, /api/v2/）
  - 後方互換性の維持

---

## LangGraph LLM分析ワークフロー

### ワークフロー構成

LLM分析機能はLangGraphを使用して構造化されたワークフローとして実装する。
各分析機能をノードとして独立させ、並列実行と個別出力の両方に対応する。

```
┌─────────────────────────────────────────────────────────────────────┐
│   LangGraph Analysis Workflow                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────┐     ┌─────────────┐                               │
│   │ EDINETNode  │────▶│PDFParseNode │                               │
│   │ (書類取得)   │     │(マークダウン) │                               │
│   └─────────────┘     └──────┬──────┘                               │
│                              │                                      │
│            ┌─────────────────┼─────────────────┐                    │
│            │                 │                 │                    │
│            ▼                 ▼                 ▼                    │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐              │
│   │ Business    │   │   Risk      │   │ Financial   │              │
│   │ Summary     │   │ Extraction  │   │ Analysis    │              │
│   │    Node     │   │    Node     │   │    Node     │  ← 並列実行   │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘              │
│          │                 │                 │                      │
│          └─────────────────┼─────────────────┘                      │
│                            ▼                                        │
│                   ┌─────────────┐                                   │
│                   │  Period     │                                   │
│                   │ Comparison  │                                   │
│                   │    Node     │                                   │
│                   └──────┬──────┘                                   │
│                          ▼                                          │
│                   ┌─────────────┐                                   │
│                   │ Aggregator  │                                   │
│                   │    Node     │                                   │
│                   └─────────────┘                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### ノード構成

| ノード | 責務 | 依存 | 出力型 |
|-------|------|------|--------|
| EDINETNode | EDINET書類取得 | EDINETClient | pdf_path |
| PDFParseNode | PDF→マークダウン変換 | PDFParser, VisionLLMClient | markdown_content |
| BusinessSummaryNode | 事業要約・戦略分析 | LLMProvider | BusinessSummary |
| RiskExtractionNode | リスク要因抽出・分類 | LLMProvider | RiskAnalysis |
| FinancialAnalysisNode | 財務状況・業績分析 | LLMProvider | FinancialAnalysis |
| PeriodComparisonNode | 前期との比較分析 | LLMProvider | PeriodComparison |
| AggregatorNode | 結果統合・レポート生成 | LLMProvider | ComprehensiveReport |

### ファイル構成

```
src/company_research_agent/
├── llm/                          # LLMプロバイダー抽象化レイヤー ✅ 実装済
│   ├── __init__.py
│   ├── types.py                 # LLMProviderType enum
│   ├── config.py                # LLMConfig設定クラス
│   ├── provider.py              # LLMProviderプロトコル
│   ├── factory.py               # create_llm_provider(), get_default_provider()
│   └── providers/
│       ├── __init__.py
│       ├── base.py              # BaseLLMProvider基底クラス
│       ├── openai.py            # OpenAIProvider
│       ├── google.py            # GoogleProvider
│       ├── anthropic.py         # AnthropicProvider
│       └── ollama.py            # OllamaProvider
├── clients/
│   └── vision_client.py         # VisionLLMClient（PDF解析用） ✅ 実装済
├── workflows/                    # LangGraphワークフロー
│   ├── __init__.py
│   ├── state.py                 # AnalysisState定義
│   ├── graph.py                 # グラフ構築・実行
│   └── nodes/                   # 各ノード実装
│       ├── __init__.py
│       ├── base.py              # ノード基底クラス
│       ├── edinet_node.py       # EDINET書類取得
│       ├── pdf_parse_node.py    # PDF解析
│       ├── business_summary_node.py   # 事業要約
│       ├── risk_extraction_node.py    # リスク抽出
│       ├── financial_analysis_node.py # 財務分析
│       ├── period_comparison_node.py  # 前期比較
│       └── aggregator_node.py   # 結果統合
├── schemas/
│   └── llm_analysis.py          # 分析結果スキーマ
└── prompts/                     # プロンプトテンプレート
    ├── __init__.py
    ├── business_summary.py
    ├── risk_extraction.py
    ├── financial_analysis.py
    └── period_comparison.py
```

### 依存関係

ワークフローモジュールは以下の既存モジュールに依存する:

- `clients/edinet_client.py` - EDINET API通信
- `clients/vision_client.py` - ビジョンLLM通信（PDF解析用）
- `llm/` - LLMプロバイダー抽象化レイヤー
- `parsers/pdf_parser.py` - PDF解析

---

## テスト戦略

### ユニットテスト
- **フレームワーク**: pytest
- **対象**:
  - XBRLParser: 各財務項目の抽出ロジック
  - FinancialAnalyzer: 財務指標の計算ロジック
  - バリデーション: 入力検証ロジック
  - LLMモジュール: プロバイダー抽象化レイヤー ✅ 実装済（106テスト）
    - `tests/unit/llm/test_types.py`: LLMProviderType enum（8テスト）
    - `tests/unit/llm/test_config.py`: LLMConfig設定クラス（22テスト）
    - `tests/unit/llm/test_factory.py`: ファクトリーメソッド（18テスト）
    - `tests/unit/llm/test_providers.py`: 各プロバイダー（58テスト）
- **カバレッジ目標**: 80%以上
- **モック**: pytest-mockによる外部依存のモック

```python
import pytest
from decimal import Decimal
from company_research_agent.services import FinancialAnalyzer

def test_calculate_roe():
    """ROEの計算テスト"""
    analyzer = FinancialAnalyzer()
    result = analyzer.calculate_roe(
        net_income=Decimal("1000000000"),
        equity=Decimal("10000000000")
    )
    assert result == Decimal("10.0")

def test_calculate_roe_zero_equity():
    """自己資本ゼロの場合のROE計算"""
    analyzer = FinancialAnalyzer()
    result = analyzer.calculate_roe(
        net_income=Decimal("1000000000"),
        equity=Decimal("0")
    )
    assert result is None
```

### 統合テスト
- **方法**: テスト用データベース（PostgreSQL）を使用
- **対象**:
  - リポジトリ: CRUD操作、トランザクション
  - サービス: 複数コンポーネントの連携
- **フィクスチャ**: pytest-fixturesによるセットアップ

```python
import pytest
from company_research_agent.repositories import DocumentRepository

@pytest.fixture
async def db_session():
    """テスト用データベースセッション"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(test_engine) as session:
        yield session
        await session.rollback()

async def test_save_and_find_document(db_session):
    """書類の保存と検索テスト"""
    repo = DocumentRepository(db_session)
    document = Document(doc_id="S100TEST", ...)
    await repo.save(document)

    found = await repo.find_by_doc_id("S100TEST")
    assert found is not None
    assert found.doc_id == "S100TEST"
```

### E2Eテスト
- **ツール**: pytest + httpx（APIテスト）
- **シナリオ**:
  1. 企業検索 → 書類取得 → XBRL解析 → 指標計算
  2. 日次バッチ処理の完全実行
  3. 10社程度の実データでの動作確認

```python
async def test_e2e_financial_analysis():
    """E2Eテスト: 財務分析フロー"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 書類検索
        response = await client.get(
            "/api/v1/documents",
            params={"sec_code": "7203", "doc_type": "annual_report"}
        )
        assert response.status_code == 200
        documents = response.json()["documents"]
        assert len(documents) > 0

        # 財務データ取得
        response = await client.get(
            f"/api/v1/companies/E00001/financials",
            params={"fiscal_year": 2024}
        )
        assert response.status_code == 200
        financials = response.json()
        assert "indicators" in financials
        assert "roe" in financials["indicators"]
```

---

## 技術的制約

### 環境要件

#### ローカル開発環境（Mac推奨）
- **OS**: macOS 12+
- **最小メモリ**: 8GB（推奨16GB）
- **必要ディスク容量**: 200GB（データ保存領域含む）
- **必要な外部依存**:
  - Python 3.11+
  - uv 0.5+
  - PostgreSQL 15+（Docker経由）
  - Docker / Docker Compose

#### Docker環境（クロスプラットフォーム）
- **OS**: Windows 10+, macOS 12+, Linux (Ubuntu 22.04+)
- **Windows**: Docker Desktop for Windows（WSL2バックエンド推奨）
- **最小メモリ**: Docker用に4GB以上割り当て（推奨8GB）
- **必要ディスク容量**: 50GB（Dockerイメージ + データ）
- **必要な外部依存**:
  - Docker 24+
  - Docker Compose 2.0+

**Windows固有の注意点**:
- ファイルパスの長さ制限（260文字）に注意
- 改行コードはLF（.gitattributesで設定）
- Docker Desktopのリソース設定でメモリを十分に割り当てる

### パフォーマンス制約
- EDINET APIのレスポンス時間に依存（通常1-3秒）
- Gemini APIのレート制限（RPM/TPM）
- 大規模XBRLファイル（100MB超）の解析にはメモリが必要

### セキュリティ制約
- EDINET APIキーの定期的な更新推奨
- 本番環境ではSSL/TLS接続必須
- 機密情報のログ出力禁止

---

## 依存関係管理

### バージョン管理方針

```toml
# pyproject.toml
[project]
dependencies = [
    # コアライブラリ: マイナーバージョンアップは許可
    "fastapi>=0.115.0,<1.0.0",
    "sqlalchemy>=2.0.0,<3.0.0",
    "pandas>=2.2.0,<3.0.0",
    "pydantic>=2.10.0,<3.0.0",
    "httpx>=0.28.0,<1.0.0",

    # XBRL解析: 固定（破壊的変更のリスク）
    "edinet-xbrl==0.2.0",
    "beautifulsoup4>=4.12.0,<5.0.0",
    "lxml>=5.0.0,<6.0.0",

    # PDF解析: 段階的解析戦略
    "pdfplumber>=0.11.0,<1.0.0",
    "pymupdf4llm>=0.0.17",
    "yomitoku>=0.7.0,<1.0.0",

    # データベース
    "asyncpg>=0.30.0,<1.0.0",
    "pgvector>=0.3.0,<1.0.0",

    # AI/ML（エージェント、LLM分析、PDF解析の最終手段）
    "langgraph>=1.0.0,<2.0.0",
    "langchain>=1.0.0,<2.0.0",
    "langchain-google-genai>=2.1.0,<3.0.0",
    "langchain-openai>=0.3.0,<1.0.0",
    "langchain-anthropic>=0.3.0,<1.0.0",
    "langchain-ollama>=0.2.0,<1.0.0",
]

[project.optional-dependencies]
dev = [
    # 開発ツール: 最新を許可
    "ruff>=0.8.0",
    "mypy>=1.14.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
]
```

### 依存関係一覧

| ライブラリ | 用途 | バージョン管理方針 |
|-----------|------|-------------------|
| fastapi | REST API | 範囲指定（>=0.115,<1.0） |
| sqlalchemy | ORM | 範囲指定（>=2.0,<3.0） |
| pandas | データ処理 | 範囲指定（>=2.2,<3.0） |
| edinet-xbrl | XBRL解析 | 固定（==0.2.0） |
| beautifulsoup4 | XML解析 | 範囲指定（>=4.12,<5.0） |
| httpx | HTTP通信 | 範囲指定（>=0.28,<1.0） |
| pdfplumber | PDF基本解析 | 範囲指定（>=0.11,<1.0） |
| pymupdf4llm | PDFマークダウン変換 | 最新許可（>=0.0.17） |
| yomitoku | 日本語OCR | 範囲指定（>=0.7,<1.0） |
| langgraph | エージェントオーケストレーション | 範囲指定（>=1.0,<2.0） |
| langchain | LLM基盤フレームワーク | 範囲指定（>=1.0,<2.0） |
| langchain-google-genai | Gemini API連携 | 範囲指定（>=2.1,<3.0） |
| langchain-openai | OpenAI API連携 | 範囲指定（>=0.3,<1.0） |
| langchain-anthropic | Anthropic API連携 | 範囲指定（>=0.3,<1.0） |
| langchain-ollama | Ollama連携 | 範囲指定（>=0.2,<1.0） |
| ruff | Linter | 最新許可（>=0.8） |
| mypy | 型チェック | 最新許可（>=1.14） |
| pytest | テスト | 最新許可（>=8.0） |

---

**作成日**: 2026年1月16日
**更新日**: 2026年1月17日
**バージョン**: 1.2
**ステータス**: 実装完了（LLMマルチプロバイダー対応）
