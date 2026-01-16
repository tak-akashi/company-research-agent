# 機能設計書 (Functional Design Document)

## システム構成図

```mermaid
graph TB
    subgraph "ユーザーインターフェース"
        Jupyter[Jupyter Notebook]
        Streamlit[Streamlit UI]
        API[REST API]
    end

    subgraph "サービスレイヤー"
        EDINETClient[EDINET Client]
        XBRLParser[XBRL Parser]
        PDFParser[PDF Parser]
        FinancialAnalyzer[Financial Analyzer]
        LLMAnalyzer[LLM Analyzer]
        VectorSearch[Vector Search]
    end

    subgraph "データレイヤー"
        PostgreSQL[(PostgreSQL)]
        pgvector[(pgvector)]
        FileStorage[File Storage]
    end

    subgraph "外部サービス"
        EDINET[EDINET API]
        Gemini[Gemini API]
        CompanyWeb[企業Webサイト]
    end

    Jupyter --> EDINETClient
    Jupyter --> XBRLParser
    Jupyter --> PDFParser
    Jupyter --> FinancialAnalyzer
    Streamlit --> API
    API --> EDINETClient
    API --> XBRLParser
    API --> FinancialAnalyzer

    EDINETClient --> EDINET
    PDFParser --> Gemini
    LLMAnalyzer --> Gemini

    EDINETClient --> FileStorage
    XBRLParser --> FileStorage
    PDFParser --> FileStorage

    FinancialAnalyzer --> PostgreSQL
    VectorSearch --> pgvector
    LLMAnalyzer --> pgvector
```

## 技術スタック

| 分類 | 技術 | 選定理由 |
|------|------|----------|
| 言語 | Python 3.11+ | データ分析エコシステム、型ヒント完備 |
| Webフレームワーク | FastAPI | 高速、型安全、OpenAPI自動生成 |
| PDF解析 | pdfplumber + pymupdf4llm + YOMITOKU | 段階的解析（コスト効率重視） |
| XBRL解析 | edinet-xbrl + BeautifulSoup/lxml | 基本対応 + フォールバック |
| データベース | PostgreSQL 15+ | 安定性、pgvector対応 |
| ベクトル検索 | pgvector | PostgreSQLネイティブ対応 |
| 簡易UI | Streamlit | 高速プロトタイピング |
| テスト | pytest | 標準的なテストフレームワーク |
| 型チェック | mypy | 静的型チェック |
| フォーマッタ | ruff | 高速なLinter/Formatter |

---

## データモデル定義

### エンティティ: Company（企業）

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Company:
    """企業エンティティ"""
    id: str                              # UUID
    edinet_code: str                     # EDINETコード（6桁）
    sec_code: str | None                 # 証券コード（5桁）、未上場はNone
    jcn: str | None                      # 法人番号（13桁）
    name: str                            # 企業名
    name_en: str | None                  # 企業名（英語）
    industry_code: str | None            # 業種コード
    accounting_standard: str | None      # 会計基準（JGAAP/IFRS/US-GAAP）
    fiscal_year_end: str | None          # 決算月（例: "03"）
    created_at: datetime                 # 作成日時
    updated_at: datetime                 # 更新日時
```

**制約**:
- `edinet_code`: 必須、6桁の英数字、一意
- `sec_code`: 5桁の数字、上場企業のみ
- `name`: 必須、1-200文字

### エンティティ: Document（開示書類）

```python
from dataclasses import dataclass
from datetime import datetime, date
from typing import Literal

type DocumentType = Literal[
    "annual_report",        # 有価証券報告書
    "quarterly_report",     # 四半期報告書
    "semiannual_report",    # 半期報告書
    "extraordinary_report", # 臨時報告書
    "securities_registration", # 有価証券届出書
    "other"
]

type DocumentStatus = Literal["pending", "downloaded", "parsed", "failed"]

@dataclass
class Document:
    """開示書類エンティティ"""
    id: str                              # UUID
    company_id: str                      # 企業ID（FK）
    doc_id: str                          # EDINET書類管理番号（8桁）
    doc_type: DocumentType               # 書類種別
    doc_type_code: str                   # 書類種別コード（3桁）
    ordinance_code: str                  # 府令コード（3桁）
    form_code: str                       # 様式コード（6桁）
    period_start: date | None            # 対象期間（開始）
    period_end: date | None              # 対象期間（終了）
    submit_datetime: datetime            # 提出日時
    doc_description: str                 # 書類概要
    withdrawal_status: int               # 取下区分（0:通常, 1:取下書, 2:取り下げ済）
    xbrl_flag: bool                      # XBRL有無
    pdf_flag: bool                       # PDF有無
    csv_flag: bool                       # CSV有無
    status: DocumentStatus               # 処理ステータス
    file_path: str | None                # ダウンロードファイルパス
    created_at: datetime                 # 作成日時
    updated_at: datetime                 # 更新日時
```

**制約**:
- `doc_id`: 必須、8桁、一意
- `company_id`: 必須、Companyテーブルへの外部キー

### エンティティ: FinancialStatement（財務諸表）

```python
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from typing import Literal

type StatementType = Literal[
    "balance_sheet",        # 貸借対照表
    "income_statement",     # 損益計算書
    "cash_flow_statement",  # キャッシュフロー計算書
    "statement_of_changes_in_equity"  # 株主資本等変動計算書
]

type ConsolidationType = Literal["consolidated", "non_consolidated"]

@dataclass
class FinancialStatement:
    """財務諸表エンティティ"""
    id: str                              # UUID
    document_id: str                     # 書類ID（FK）
    company_id: str                      # 企業ID（FK）
    statement_type: StatementType        # 財務諸表種別
    consolidation_type: ConsolidationType # 連結/単体
    fiscal_year: int                     # 会計年度
    fiscal_period: str                   # 会計期間（"FY", "Q1", "Q2", "Q3", "H1"）
    period_start: date                   # 対象期間（開始）
    period_end: date                     # 対象期間（終了）
    currency: str                        # 通貨（"JPY"）
    unit_scale: int                      # 単位スケール（0:円, 3:千円, 6:百万円）
    created_at: datetime                 # 作成日時
    updated_at: datetime                 # 更新日時
```

### エンティティ: FinancialItem（財務項目）

```python
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass
class FinancialItem:
    """財務項目エンティティ"""
    id: str                              # UUID
    statement_id: str                    # 財務諸表ID（FK）
    element_name: str                    # XBRL要素名（例: "jppfs_cor:NetSales"）
    label_ja: str                        # 日本語ラベル（例: "売上高"）
    label_en: str | None                 # 英語ラベル
    value: Decimal                       # 金額（円単位に正規化）
    context_ref: str                     # コンテキスト参照
    is_current_period: bool              # 当期フラグ
    created_at: datetime                 # 作成日時
```

**制約**:
- `value`: 円単位に正規化して保存
- `element_name`: XBRL要素名をそのまま保存

### エンティティ: FinancialIndicator（財務指標）

```python
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from typing import Literal

type IndicatorCategory = Literal[
    "profitability",   # 収益性
    "safety",          # 安全性
    "efficiency",      # 効率性
    "growth"           # 成長性
]

@dataclass
class FinancialIndicator:
    """財務指標エンティティ"""
    id: str                              # UUID
    company_id: str                      # 企業ID（FK）
    document_id: str                     # 書類ID（FK）
    fiscal_year: int                     # 会計年度
    fiscal_period: str                   # 会計期間
    period_end: date                     # 対象期間（終了）
    indicator_name: str                  # 指標名（例: "ROE"）
    indicator_category: IndicatorCategory # 指標カテゴリ
    value: Decimal                       # 指標値（%の場合は小数で保存、例: 12.5% → 0.125）
    numerator: Decimal | None            # 分子
    denominator: Decimal | None          # 分母
    created_at: datetime                 # 作成日時
```

### ER図

```mermaid
erDiagram
    COMPANY ||--o{ DOCUMENT : submits
    COMPANY ||--o{ FINANCIAL_STATEMENT : has
    COMPANY ||--o{ FINANCIAL_INDICATOR : has
    DOCUMENT ||--o{ FINANCIAL_STATEMENT : contains
    DOCUMENT ||--o{ FINANCIAL_INDICATOR : generates
    FINANCIAL_STATEMENT ||--o{ FINANCIAL_ITEM : contains

    COMPANY {
        string id PK
        string edinet_code UK
        string sec_code
        string name
        string accounting_standard
        datetime created_at
    }
    DOCUMENT {
        string id PK
        string company_id FK
        string doc_id UK
        string doc_type
        datetime submit_datetime
        string status
    }
    FINANCIAL_STATEMENT {
        string id PK
        string document_id FK
        string company_id FK
        string statement_type
        string consolidation_type
        int fiscal_year
    }
    FINANCIAL_ITEM {
        string id PK
        string statement_id FK
        string element_name
        string label_ja
        decimal value
    }
    FINANCIAL_INDICATOR {
        string id PK
        string company_id FK
        string document_id FK
        string indicator_name
        decimal value
    }
```

---

## コンポーネント設計

### EDINETClient（EDINET APIクライアント）

**責務**:
- EDINET APIとの通信
- 書類一覧の取得
- 書類ファイル（ZIP/PDF/XBRL）のダウンロード
- レート制限対応とリトライ処理

**インターフェース**:
```python
from typing import Protocol
from dataclasses import dataclass
from datetime import date
from pathlib import Path

@dataclass
class DocumentSearchParams:
    """書類検索パラメータ"""
    date: date                           # ファイル日付
    include_details: bool = True         # 詳細情報を含む

@dataclass
class DocumentFilter:
    """書類フィルタ"""
    edinet_code: str | None = None       # EDINETコード
    sec_code: str | None = None          # 証券コード
    company_name: str | None = None      # 企業名（部分一致）
    doc_type_codes: list[str] | None = None  # 書類種別コード
    start_date: date | None = None       # 期間（開始）
    end_date: date | None = None         # 期間（終了）

@dataclass
class DocumentMetadata:
    """書類メタデータ"""
    doc_id: str
    edinet_code: str
    sec_code: str | None
    filer_name: str | None
    doc_type_code: str
    doc_description: str | None
    submit_datetime: str | None
    xbrl_flag: bool
    pdf_flag: bool

class EDINETClientProtocol(Protocol):
    """EDINET APIクライアントプロトコル"""

    def get_document_list(
        self,
        params: DocumentSearchParams
    ) -> list[DocumentMetadata]:
        """書類一覧を取得する"""
        ...

    def search_documents(
        self,
        filter: DocumentFilter
    ) -> list[DocumentMetadata]:
        """書類を検索する（複数日付を横断）"""
        ...

    def download_xbrl(
        self,
        doc_id: str,
        save_dir: Path
    ) -> Path:
        """XBRLファイル（ZIP）をダウンロードする"""
        ...

    def download_pdf(
        self,
        doc_id: str,
        save_path: Path
    ) -> Path:
        """PDFファイルをダウンロードする"""
        ...

    def download_csv(
        self,
        doc_id: str,
        save_dir: Path
    ) -> Path:
        """CSVファイル（ZIP）をダウンロードする"""
        ...
```

**依存関係**:
- `requests` または `httpx`: HTTP通信
- `tenacity`: リトライ処理

### XBRLParser（XBRL解析）

**責務**:
- XBRLファイルの解析
- 財務三表（BS/PL/CF）のデータ抽出
- コンテキスト（期間、連結/単体）の解析
- 複数要素名候補によるフォールバック

**インターフェース**:
```python
from typing import Protocol
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import pandas as pd

@dataclass
class ParsedFinancialData:
    """解析された財務データ"""
    company_info: dict                   # 企業情報
    balance_sheet: pd.DataFrame          # 貸借対照表
    income_statement: pd.DataFrame       # 損益計算書
    cash_flow_statement: pd.DataFrame    # キャッシュフロー計算書
    metadata: dict                       # メタデータ（期間、連結/単体等）

@dataclass
class XBRLParseOptions:
    """XBRL解析オプション"""
    consolidation_type: str = "consolidated"  # "consolidated" or "non_consolidated"
    include_prior_period: bool = True    # 前期データを含む
    normalize_unit: bool = True          # 金額を円単位に正規化

class XBRLParserProtocol(Protocol):
    """XBRL解析プロトコル"""

    def parse(
        self,
        xbrl_path: Path,
        options: XBRLParseOptions | None = None
    ) -> ParsedFinancialData:
        """XBRLファイルを解析する"""
        ...

    def extract_element(
        self,
        xbrl_path: Path,
        element_names: list[str],
        context_pattern: str | None = None
    ) -> Decimal | None:
        """特定の要素を抽出する（フォールバック対応）"""
        ...
```

**依存関係**:
- `edinet-xbrl`: 基本的なXBRL解析
- `beautifulsoup4` + `lxml`: フォールバック解析
- `pandas`: データフレーム変換

**実装戦略**:
1. まず`edinet-xbrl`で解析を試行
2. 失敗または不足データがある場合、`BeautifulSoup + lxml`でフォールバック
3. 複数の要素名候補を順番に試行

### PDFParser（PDF解析）

**責務**:
- PDFファイルからのテキスト抽出
- 表データのマークダウン変換
- 段階的な解析戦略によるコスト最適化

**段階的解析戦略**:

| 段階 | ライブラリ | 用途 | コスト |
|------|-----------|------|--------|
| 1. 基本 | pdfplumber | テキスト抽出、シンプルな表 | 無料 |
| 2. 中間 | pymupdf4llm | マークダウン変換、構造化 | 無料 |
| 3. 高精度 | YOMITOKU | 複雑な日本語表、スキャンPDF | 無料 |
| 4. 最終手段 | Gemini API | 上記で解析困難な場合 | API課金 |

```mermaid
flowchart TD
    A[PDF入力] --> B{テキストPDF?}
    B -->|Yes| C[pdfplumber でテキスト抽出]
    B -->|No/スキャン| F[YOMITOKU でOCR]
    C --> D{表が複雑?}
    D -->|No| E[完了]
    D -->|Yes| G[pymupdf4llm でマークダウン変換]
    G --> H{日本語表の精度OK?}
    H -->|Yes| E
    H -->|No| F
    F --> I{解析成功?}
    I -->|Yes| E
    I -->|No| J[Gemini API で解析]
    J --> E
```

**インターフェース**:
```python
from typing import Protocol, Literal
from dataclasses import dataclass
from pathlib import Path

type ParseStrategy = Literal["auto", "pdfplumber", "pymupdf4llm", "yomitoku", "gemini"]

@dataclass
class ParsedPDFContent:
    """解析されたPDFコンテンツ"""
    text: str                            # 抽出されたテキスト
    tables: list[str]                    # マークダウン形式の表
    pages: int                           # ページ数
    metadata: dict                       # メタデータ
    strategy_used: ParseStrategy         # 使用された解析戦略

@dataclass
class PDFParseOptions:
    """PDF解析オプション"""
    start_page: int | None = None        # 開始ページ
    end_page: int | None = None          # 終了ページ
    extract_tables: bool = True          # 表を抽出する
    strategy: ParseStrategy = "auto"     # 解析戦略（auto=段階的に試行）
    fallback_to_gemini: bool = False     # Gemini APIへのフォールバックを許可

class PDFParserProtocol(Protocol):
    """PDF解析プロトコル"""

    def parse(
        self,
        pdf_path: Path,
        options: PDFParseOptions | None = None
    ) -> ParsedPDFContent:
        """PDFファイルを解析する"""
        ...

    def extract_tables(
        self,
        pdf_path: Path,
        page_numbers: list[int] | None = None
    ) -> list[str]:
        """表をマークダウン形式で抽出する"""
        ...

    def get_info(
        self,
        pdf_path: Path
    ) -> dict:
        """PDFのメタデータを取得する（ページ数、目次等）"""
        ...
```

**依存関係**:
- `pdfplumber`: 基本的なPDF処理（テキスト抽出、シンプルな表）
- `pymupdf4llm`: マークダウン変換（pymupdf/fitz ベース）
- `yomitoku`: 日本語OCR（複雑な表、スキャンPDF）
- `google-generativeai`: Gemini API（最終手段）

### FinancialAnalyzer（財務分析）

**責務**:
- 財務指標の計算
- 指標の正規化と検証
- 計算結果のDataFrame変換

**インターフェース**:
```python
from typing import Protocol
from dataclasses import dataclass
from decimal import Decimal
import pandas as pd

@dataclass
class FinancialIndicators:
    """財務指標"""
    # 収益性指標
    roe: Decimal | None                  # 自己資本利益率
    roa: Decimal | None                  # 総資産利益率
    operating_margin: Decimal | None     # 営業利益率
    ordinary_margin: Decimal | None      # 経常利益率
    net_profit_margin: Decimal | None    # 売上高純利益率

    # 安全性指標
    equity_ratio: Decimal | None         # 自己資本比率
    current_ratio: Decimal | None        # 流動比率
    fixed_ratio: Decimal | None          # 固定比率
    debt_ratio: Decimal | None           # 負債比率

    # 効率性指標
    total_asset_turnover: Decimal | None # 総資産回転率
    inventory_turnover: Decimal | None   # 棚卸資産回転率
    receivables_turnover: Decimal | None # 売上債権回転率

class FinancialAnalyzerProtocol(Protocol):
    """財務分析プロトコル"""

    def calculate_indicators(
        self,
        financial_data: ParsedFinancialData
    ) -> FinancialIndicators:
        """財務指標を計算する"""
        ...

    def to_dataframe(
        self,
        indicators: FinancialIndicators
    ) -> pd.DataFrame:
        """指標をDataFrameに変換する"""
        ...

    def compare_periods(
        self,
        current: FinancialIndicators,
        prior: FinancialIndicators
    ) -> pd.DataFrame:
        """期間比較を行う"""
        ...
```

**依存関係**:
- `pandas`: データフレーム処理
- `decimal`: 高精度計算

### Database（データベース）

**責務**:
- PostgreSQLへのデータ保存・取得
- トランザクション管理
- 重複排除と冪等性の担保

**インターフェース**:
```python
from typing import Protocol
from dataclasses import dataclass

class DatabaseProtocol(Protocol):
    """データベースプロトコル"""

    def save_company(self, company: Company) -> str:
        """企業を保存する（upsert）"""
        ...

    def save_document(self, document: Document) -> str:
        """書類を保存する（upsert）"""
        ...

    def save_financial_statement(
        self,
        statement: FinancialStatement,
        items: list[FinancialItem]
    ) -> str:
        """財務諸表と項目を保存する"""
        ...

    def save_indicators(
        self,
        indicators: list[FinancialIndicator]
    ) -> None:
        """財務指標を保存する"""
        ...

    def get_company_by_code(
        self,
        edinet_code: str | None = None,
        sec_code: str | None = None
    ) -> Company | None:
        """企業を取得する"""
        ...

    def get_financial_history(
        self,
        company_id: str,
        years: int = 5
    ) -> list[FinancialStatement]:
        """財務履歴を取得する"""
        ...
```

**依存関係**:
- `sqlalchemy`: ORM
- `asyncpg` または `psycopg`: PostgreSQL接続

---

## ユースケース図

### ユースケース1: 企業の財務データ取得

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant Client as EDINETClient
    participant Parser as XBRLParser
    participant Analyzer as FinancialAnalyzer
    participant DB as Database
    participant EDINET as EDINET API

    User->>Client: search_documents(filter)
    Client->>EDINET: GET /documents.json
    EDINET-->>Client: 書類一覧
    Client-->>User: DocumentMetadata[]

    User->>Client: download_xbrl(doc_id)
    Client->>EDINET: GET /documents/{doc_id}?type=1
    EDINET-->>Client: ZIP file
    Client-->>User: xbrl_path

    User->>Parser: parse(xbrl_path)
    Parser->>Parser: edinet-xbrlで解析
    alt 解析失敗または不足
        Parser->>Parser: BeautifulSoup+lxmlでフォールバック
    end
    Parser-->>User: ParsedFinancialData

    User->>Analyzer: calculate_indicators(data)
    Analyzer-->>User: FinancialIndicators

    User->>DB: save_financial_statement(data)
    DB-->>User: statement_id
```

**フロー説明**:
1. ユーザーがフィルタ条件を指定して書類を検索
2. EDINET APIから書類一覧を取得
3. 目的の書類のXBRLファイルをダウンロード
4. XBRLParserで財務データを解析（edinet-xbrl優先、フォールバックあり）
5. FinancialAnalyzerで財務指標を計算
6. 結果をデータベースに保存

### ユースケース2: 日次バッチ処理

```mermaid
sequenceDiagram
    participant Batch as BatchProcessor
    participant Client as EDINETClient
    participant Parser as XBRLParser
    participant Analyzer as FinancialAnalyzer
    participant DB as Database
    participant EDINET as EDINET API

    Batch->>Client: get_document_list(today)
    Client->>EDINET: GET /documents.json?date={today}
    EDINET-->>Client: 書類一覧

    loop 各書類について
        Batch->>DB: document_exists?(doc_id)
        alt 未処理の書類
            Batch->>Client: download_xbrl(doc_id)
            Client->>EDINET: GET /documents/{doc_id}
            EDINET-->>Client: ZIP file

            Batch->>Parser: parse(xbrl_path)
            Parser-->>Batch: ParsedFinancialData

            Batch->>Analyzer: calculate_indicators(data)
            Analyzer-->>Batch: FinancialIndicators

            Batch->>DB: save_all(data, indicators)
            DB-->>Batch: success
        end
    end

    Batch->>Batch: ログ出力・完了通知
```

**フロー説明**:
1. 当日の書類一覧を取得
2. 各書類について未処理かチェック
3. 未処理の書類のみダウンロード・解析・保存
4. 処理完了をログ出力

---

## アルゴリズム設計

### 財務指標計算アルゴリズム

**目的**: 抽出した財務データから主要な財務指標を計算する

#### 収益性指標

##### ROE（自己資本利益率）

**計算式**:
```
ROE = 当期純利益 / 自己資本 × 100
```

**実装**:
```python
def calculate_roe(
    net_income: Decimal,
    equity: Decimal
) -> Decimal | None:
    """ROEを計算する"""
    if equity == 0:
        return None
    return (net_income / equity) * 100
```

##### ROA（総資産利益率）

**計算式**:
```
ROA = 当期純利益 / 総資産 × 100
```

**実装**:
```python
def calculate_roa(
    net_income: Decimal,
    total_assets: Decimal
) -> Decimal | None:
    """ROAを計算する"""
    if total_assets == 0:
        return None
    return (net_income / total_assets) * 100
```

##### 営業利益率

**計算式**:
```
営業利益率 = 営業利益 / 売上高 × 100
```

**実装**:
```python
def calculate_operating_margin(
    operating_income: Decimal,
    net_sales: Decimal
) -> Decimal | None:
    """営業利益率を計算する"""
    if net_sales == 0:
        return None
    return (operating_income / net_sales) * 100
```

#### 安全性指標

##### 自己資本比率

**計算式**:
```
自己資本比率 = 自己資本 / 総資産 × 100
```

**実装**:
```python
def calculate_equity_ratio(
    equity: Decimal,
    total_assets: Decimal
) -> Decimal | None:
    """自己資本比率を計算する"""
    if total_assets == 0:
        return None
    return (equity / total_assets) * 100
```

##### 流動比率

**計算式**:
```
流動比率 = 流動資産 / 流動負債 × 100
```

**実装**:
```python
def calculate_current_ratio(
    current_assets: Decimal,
    current_liabilities: Decimal
) -> Decimal | None:
    """流動比率を計算する"""
    if current_liabilities == 0:
        return None
    return (current_assets / current_liabilities) * 100
```

#### 効率性指標

##### 総資産回転率

**計算式**:
```
総資産回転率 = 売上高 / 総資産
```

**実装**:
```python
def calculate_total_asset_turnover(
    net_sales: Decimal,
    total_assets: Decimal
) -> Decimal | None:
    """総資産回転率を計算する"""
    if total_assets == 0:
        return None
    return net_sales / total_assets
```

### XBRL要素名フォールバックアルゴリズム

**目的**: 企業や会計基準により異なる要素名に対応する

**計算ロジック**:

```python
# 売上高の要素名候補
NET_SALES_CANDIDATES = [
    "jppfs_cor:NetSales",           # 日本基準・一般
    "jppfs_cor:Revenue",            # 日本基準・一部企業
    "jpigp_cor:Revenue",            # IFRS
    "jppfs_cor:OperatingRevenue",   # 金融業等
    "jppfs_cor:OrdinaryRevenues",   # 保険業
]

def extract_net_sales(
    soup: BeautifulSoup,
    context_pattern: str = r"CurrentYear.*Duration"
) -> Decimal | None:
    """売上高を抽出する（フォールバック対応）"""
    for element_name in NET_SALES_CANDIDATES:
        tags = soup.find_all('ix:nonfraction', attrs={'name': element_name})
        for tag in tags:
            context_ref = tag.get('contextRef', '')
            if re.search(context_pattern, context_ref):
                value = parse_numeric_value(tag)
                if value is not None:
                    return value
    return None

def parse_numeric_value(tag) -> Decimal | None:
    """ix:nonfractionタグから数値を正しく取得する"""
    try:
        value_text = tag.get_text().replace(',', '').strip()
        value = Decimal(value_text)

        # scale属性の処理
        scale = tag.get('scale')
        if scale:
            value *= Decimal(10) ** int(scale)

        # sign属性の処理（負数）
        sign = tag.get('sign')
        if sign == '-':
            value *= -1

        return value
    except (ValueError, InvalidOperation):
        return None
```

---

## API設計

### REST API エンドポイント

#### 書類検索

```
GET /api/v1/documents
```

**クエリパラメータ**:
| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| edinet_code | string | No | EDINETコード |
| sec_code | string | No | 証券コード |
| company_name | string | No | 企業名（部分一致） |
| doc_type | string | No | 書類種別（annual_report等） |
| start_date | date | No | 期間（開始） |
| end_date | date | No | 期間（終了） |

**レスポンス**:
```json
{
  "documents": [
    {
      "doc_id": "S100XXXX",
      "edinet_code": "E10001",
      "sec_code": "7203",
      "filer_name": "トヨタ自動車株式会社",
      "doc_type": "annual_report",
      "doc_description": "有価証券報告書－第120期",
      "submit_datetime": "2024-06-25T15:30:00",
      "xbrl_flag": true,
      "pdf_flag": true
    }
  ],
  "total": 1
}
```

#### 財務データ取得

```
GET /api/v1/companies/{edinet_code}/financials
```

**パスパラメータ**:
| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| edinet_code | string | Yes | EDINETコード |

**クエリパラメータ**:
| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| fiscal_year | int | No | 会計年度 |
| consolidation | string | No | consolidated/non_consolidated |

**レスポンス**:
```json
{
  "company": {
    "edinet_code": "E10001",
    "sec_code": "7203",
    "name": "トヨタ自動車株式会社"
  },
  "fiscal_year": 2024,
  "consolidation_type": "consolidated",
  "balance_sheet": {
    "total_assets": 90000000000000,
    "current_assets": 30000000000000,
    "noncurrent_assets": 60000000000000,
    "total_liabilities": 50000000000000,
    "net_assets": 40000000000000
  },
  "income_statement": {
    "net_sales": 45000000000000,
    "operating_income": 3500000000000,
    "ordinary_income": 4000000000000,
    "net_income": 2800000000000
  },
  "indicators": {
    "roe": 7.0,
    "roa": 3.1,
    "operating_margin": 7.8,
    "equity_ratio": 44.4
  }
}
```

**エラーレスポンス**:
- 400 Bad Request: パラメータが不正な場合
- 404 Not Found: 企業が見つからない場合
- 500 Internal Server Error: サーバーエラー

---

## エラーハンドリング

### エラーの分類

| エラー種別 | 処理 | ユーザーへの表示 |
|-----------|------|-----------------|
| EDINET API エラー（401） | リトライ不可、処理中断 | "EDINET APIキーが無効です。.envファイルのEDINET_API_KEYを確認してください" |
| EDINET API エラー（404） | スキップ、ログ記録 | "書類が見つかりません (doc_id: {id})" |
| EDINET API エラー（500） | リトライ（3回まで） | "EDINET APIが一時的に利用できません。再試行中..." |
| XBRL解析エラー | フォールバック試行 | "XBRL解析に失敗しました。フォールバック処理を試行中..." |
| 要素が見つからない | Noneを返す、ログ記録 | "売上高データが見つかりません" |
| 計算エラー（ゼロ除算） | Noneを返す | "ROEを計算できません（自己資本がゼロ）" |
| データベースエラー | ロールバック、リトライ | "データの保存に失敗しました。再試行中..." |

### カスタム例外クラス

```python
class EDINETAssistantError(Exception):
    """基底例外クラス"""
    pass

class EDINETAPIError(EDINETAssistantError):
    """EDINET API関連のエラー"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"EDINET API Error ({status_code}): {message}")

class XBRLParseError(EDINETAssistantError):
    """XBRL解析エラー"""
    pass

class FinancialCalculationError(EDINETAssistantError):
    """財務計算エラー"""
    pass

class DatabaseError(EDINETAssistantError):
    """データベースエラー"""
    pass
```

---

## パフォーマンス最適化

- **EDINET API呼び出し**: セッション（requests.Session）を使い回し、接続のオーバーヘッドを削減
- **バッチ処理**: 書類ダウンロードを並列化（concurrent.futures使用、同時接続数制限あり）
- **XBRL解析**: lxmlのiterparseを使用し、メモリ効率を向上（大きなファイル対応）
- **データベース**: バルクインサートを使用、インデックスの最適化
- **キャッシュ**: EDINETコードリストをメモリキャッシュ

---

## セキュリティ考慮事項

- **APIキー管理**: 環境変数または設定ファイル（.env）で管理、ソースコードにハードコードしない
- **データベース接続**: SSL接続を推奨、接続文字列の暗号化
- **ログ出力**: APIキー、認証情報をログに出力しない
- **入力検証**: ユーザー入力（企業コード等）のバリデーション
- **ファイル操作**: パストラバーサル攻撃の防止

---

## テスト戦略

### ユニットテスト

- **XBRLParser**: 各財務項目の抽出ロジック、フォールバック処理
- **FinancialAnalyzer**: 各財務指標の計算ロジック、エッジケース（ゼロ除算等）
- **EDINETClient**: レスポンスのパース、エラーハンドリング

### 統合テスト

- **EDINET API連携**: 実際のAPIを使用した書類取得（テスト用書類）
- **データベース**: CRUD操作、トランザクション処理
- **エンドツーエンド**: 検索→ダウンロード→解析→保存の一連のフロー

### E2Eテスト

- **実企業データ**: 10社程度の実データでの動作確認
- **異なる会計基準**: 日本基準、IFRS企業でのテスト
- **異なる業種**: 製造業、金融業、サービス業でのテスト

---

**作成日**: 2026年1月16日
**バージョン**: 1.0
**ステータス**: ドラフト
