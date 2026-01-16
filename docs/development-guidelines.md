# 開発ガイドライン (Development Guidelines)

## コーディング規約

### 命名規則

#### 変数・関数

**Python**:
```python
# ✅ 良い例
edinet_code = "E00001"
fiscal_year_documents = fetch_documents_by_year(2024)

def calculate_operating_margin(
    operating_income: Decimal,
    revenue: Decimal
) -> Decimal | None:
    ...

# ❌ 悪い例
code = "E00001"
docs = fetch(2024)

def calc(inc: Decimal, rev: Decimal) -> Decimal | None:
    ...
```

**原則**:
- 変数: `snake_case`、名詞または名詞句
- 関数: `snake_case`、動詞で始める（`get_`, `fetch_`, `calculate_`, `parse_`, `save_`）
- 定数: `UPPER_SNAKE_CASE`
- Boolean: `is_`, `has_`, `should_`, `can_` で始める

**プロジェクト固有の命名**:
```python
# EDINETコード関連
edinet_code: str       # E00001形式
sec_code: str          # 5桁の証券コード（例: 72030）
company_name: str      # 企業名

# 書類関連
doc_id: str            # EDINET書類ID（例: S100XXXX）
doc_type: str          # 書類種別（annual_report, quarterly_report等）
filing_date: date      # 提出日

# 財務関連
fiscal_year: int       # 会計年度
fiscal_period: int     # 会計期間（1=Q1, 2=Q2, 3=Q3, 4=通期）
```

#### クラス・型

```python
from typing import Protocol, Literal
from dataclasses import dataclass

# クラス: PascalCase、名詞
class EDINETClient: ...
class XBRLParser: ...
class FinancialAnalyzer: ...

# Protocol: PascalCase、末尾に Repository, Service, Client 等
class DocumentRepository(Protocol):
    async def save(self, document: Document) -> str: ...
    async def find_by_doc_id(self, doc_id: str) -> Document | None: ...

# Pydantic モデル: PascalCase
class DocumentSearchRequest(BaseModel): ...
class FinancialStatementResponse(BaseModel): ...

# 型エイリアス
type DocumentType = Literal["annual_report", "quarterly_report", "securities_report"]
type FiscalPeriod = Literal[1, 2, 3, 4]
```

#### ファイル名・モジュール名

```python
# ファイル名: snake_case
edinet_client.py
xbrl_parser.py
financial_analyzer.py
document_repository.py

# テストファイル: test_ プレフィックス
test_edinet_client.py
test_xbrl_parser.py

# 設定ファイル
config.py
settings.py
```

### コードフォーマット

**インデント**: 4スペース（PEP 8準拠）

**行の長さ**: 最大100文字

**例**:
```python
# リスト内包表記
filtered_documents = [
    doc
    for doc in documents
    if doc.doc_type == "annual_report" and doc.fiscal_year >= 2020
]

# 長い関数呼び出し
response = await edinet_client.search_documents(
    edinet_code="E00001",
    doc_type="annual_report",
    start_date=date(2020, 1, 1),
    end_date=date(2024, 12, 31),
)

# 辞書
financial_indicators = {
    "roe": calculate_roe(net_income, equity),
    "roa": calculate_roa(net_income, total_assets),
    "operating_margin": calculate_operating_margin(operating_income, revenue),
}
```

**ツール設定 (pyproject.toml)**:
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM"]
ignore = ["E501"]  # 行長さはformatterで対応

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### コメント規約

**関数・クラスのドキュメント (Google Style Docstring)**:
```python
async def search_documents(
    edinet_code: str | None = None,
    sec_code: str | None = None,
    doc_type: DocumentType | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[DocumentMetadata]:
    """EDINET APIから書類メタデータを検索する。

    Args:
        edinet_code: EDINETコード（E00001形式）
        sec_code: 証券コード（5桁）
        doc_type: 書類種別
        start_date: 検索開始日
        end_date: 検索終了日

    Returns:
        書類メタデータのリスト

    Raises:
        EDINETAPIError: API呼び出しに失敗した場合
        ValidationError: 入力パラメータが不正な場合

    Example:
        >>> documents = await search_documents(
        ...     edinet_code="E00001",
        ...     doc_type="annual_report"
        ... )
    """
    ...
```

**インラインコメント**:
```python
# ✅ 良い例: なぜそうするかを説明
# EDINET APIは過去10年分のみ提供のため、それ以前は除外
if filing_date < date.today() - timedelta(days=365 * 10):
    return None

# 複数の要素名候補を試行（企業によりXBRL要素名が異なる）
for element_name in REVENUE_ELEMENT_NAMES:
    value = xbrl_doc.find(element_name)
    if value is not None:
        return value

# ❌ 悪い例: 何をしているか(コードを見れば分かる)
# 売上高を取得する
revenue = xbrl_doc.find("Revenue")
```

### 型ヒント

**必須の型ヒント**:
```python
from decimal import Decimal
from datetime import date
from collections.abc import Sequence

# 関数の引数と戻り値には必ず型を付ける
def calculate_roe(
    net_income: Decimal,
    equity: Decimal
) -> Decimal | None:
    if equity == 0:
        return None
    return (net_income / equity) * 100

# Optional よりも X | None を使用（Python 3.10+）
def find_company(company_id: str) -> Company | None:
    ...

# list よりも Sequence を使用（読み取り専用の場合）
def process_documents(documents: Sequence[Document]) -> list[ProcessedDocument]:
    ...

# 可変長引数
def aggregate_financials(*statements: FinancialStatement) -> AggregatedData:
    ...
```

**mypy設定 (pyproject.toml)**:
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true

[[tool.mypy.overrides]]
module = ["edinet_xbrl.*", "yomitoku.*"]
ignore_missing_imports = true
```

### データ構造の使い分け

本プロジェクトでは、用途に応じて以下のデータ構造を使い分けます。

| 用途 | 推奨 | 理由 |
|------|------|------|
| APIリクエスト/レスポンス | `pydantic.BaseModel` | バリデーション、シリアライゼーション、OpenAPI生成 |
| 内部ドメインモデル | `dataclass` | 軽量、シンプル、バリデーション不要 |
| インターフェース定義 | `Protocol` | 依存性逆転、テスト時のモック化 |
| 辞書の型ヒント | `TypedDict` | 既存dict APIとの互換性 |

#### pydantic.BaseModel（外部境界）

**用途**: API層での入出力、設定ファイル読み込み、外部データのバリデーション

```python
from pydantic import BaseModel, Field, field_validator
from datetime import date

class DocumentSearchRequest(BaseModel):
    """書類検索リクエスト（API入力）"""
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

class DocumentResponse(BaseModel):
    """書類レスポンス（API出力）"""
    doc_id: str
    company_name: str
    filing_date: date
    doc_type: str

    class Config:
        from_attributes = True  # ORMモデルからの変換を許可
```

**選定理由**:
- ランタイムでの自動バリデーション
- FastAPIとの統合（OpenAPIスキーマ自動生成）
- JSON シリアライゼーション/デシリアライゼーション

#### dataclass（内部ドメイン）

**用途**: サービス層・リポジトリ層での内部データ構造、値オブジェクト

```python
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import date

@dataclass
class FinancialItem:
    """財務項目（内部モデル）"""
    element_name: str
    value: Decimal
    label: str
    unit: str = "JPY"
    scale: int = 1

@dataclass
class FinancialStatement:
    """財務諸表（内部モデル）"""
    fiscal_year: int
    fiscal_period: int
    statement_type: str
    items: list[FinancialItem] = field(default_factory=list)
    is_consolidated: bool = True

@dataclass(frozen=True)
class CompanyId:
    """企業ID値オブジェクト（イミュータブル）"""
    edinet_code: str

    def __post_init__(self) -> None:
        if not self.edinet_code.startswith("E") or len(self.edinet_code) != 6:
            raise ValueError(f"Invalid EDINET code: {self.edinet_code}")
```

**選定理由**:
- 軽量（pydanticより高速）
- シンプルな構文
- `frozen=True` でイミュータブルな値オブジェクトを作成可能
- `__post_init__` で簡易バリデーション可能

#### Protocol（インターフェース定義）

**用途**: 依存性逆転、抽象化、テスト時のモック化

```python
from typing import Protocol
from collections.abc import Sequence

class DocumentRepository(Protocol):
    """書類リポジトリのインターフェース"""

    async def save(self, document: Document) -> str:
        """書類を保存し、IDを返す"""
        ...

    async def find_by_doc_id(self, doc_id: str) -> Document | None:
        """書類IDで検索"""
        ...

    async def find_by_company(
        self,
        edinet_code: str,
        doc_type: str | None = None,
    ) -> Sequence[Document]:
        """企業の書類を検索"""
        ...

class XBRLParserProtocol(Protocol):
    """XBRLパーサーのインターフェース"""

    async def parse(self, file_path: Path) -> FinancialStatement:
        """XBRLファイルを解析"""
        ...

# サービス層での使用例
class FinancialService:
    def __init__(
        self,
        repository: DocumentRepository,  # Protocolを型として使用
        parser: XBRLParserProtocol,
    ) -> None:
        self.repository = repository
        self.parser = parser
```

**選定理由**:
- 構造的サブタイピング（明示的な継承不要）
- テスト時にモッククラスを簡単に作成可能
- 依存性逆転の原則を実現

#### TypedDict（辞書の型ヒント）

**用途**: 外部APIレスポンス、JSON構造、既存dictとの互換性が必要な場合

```python
from typing import TypedDict, NotRequired

class XBRLContext(TypedDict):
    """XBRLコンテキスト情報"""
    period_start: str
    period_end: str
    is_consolidated: bool
    instant: NotRequired[str]  # オプショナルフィールド

class EDINETAPIResponse(TypedDict):
    """EDINET APIレスポンス構造"""
    metadata: dict[str, str]
    results: list[dict[str, str | int | None]]

# 使用例
def parse_context(ctx: XBRLContext) -> tuple[date, date]:
    return (
        date.fromisoformat(ctx["period_start"]),
        date.fromisoformat(ctx["period_end"]),
    )
```

**選定理由**:
- 辞書アクセス構文（`d["key"]`）をそのまま使用可能
- 外部APIのレスポンス構造を型安全に表現
- JSONデータとの相性が良い

#### 使い分けの判断フロー

```
外部からのデータ入力？
  ├─ Yes → pydantic.BaseModel（バリデーション必要）
  └─ No
      ├─ インターフェース定義？
      │   ├─ Yes → Protocol
      │   └─ No
      │       ├─ 辞書形式が必要？
      │       │   ├─ Yes → TypedDict
      │       │   └─ No → dataclass
      │       └─ イミュータブル？
      │           ├─ Yes → @dataclass(frozen=True)
      │           └─ No → @dataclass
```

### エラーハンドリング

**例外クラス定義**:
```python
from dataclasses import dataclass
from typing import Any

# ベース例外
class EDINETAssistantError(Exception):
    """EDINET Assistant の基底例外クラス"""
    pass

# API関連エラー
@dataclass
class EDINETAPIError(EDINETAssistantError):
    """EDINET API呼び出しエラー"""
    status_code: int
    message: str
    endpoint: str

    def __str__(self) -> str:
        return f"EDINET API Error [{self.status_code}]: {self.message} (endpoint={self.endpoint})"

# バリデーションエラー
@dataclass
class ValidationError(EDINETAssistantError):
    """入力バリデーションエラー"""
    field: str
    message: str
    value: Any

    def __str__(self) -> str:
        return f"Validation Error: {self.message} (field={self.field}, value={self.value})"

# リソース不存在エラー
@dataclass
class NotFoundError(EDINETAssistantError):
    """リソースが見つからないエラー"""
    resource_type: str
    resource_id: str

    def __str__(self) -> str:
        return f"{self.resource_type} not found: {self.resource_id}"

# XBRL解析エラー
@dataclass
class XBRLParseError(EDINETAssistantError):
    """XBRL解析エラー"""
    doc_id: str
    message: str
    element_name: str | None = None

    def __str__(self) -> str:
        return f"XBRL Parse Error [{self.doc_id}]: {self.message}"
```

**エラーハンドリングパターン**:
```python
# サービス層でのエラーハンドリング
async def fetch_and_parse_xbrl(doc_id: str) -> FinancialStatement:
    try:
        # 書類ダウンロード
        xbrl_path = await edinet_client.download_document(doc_id)
    except EDINETAPIError as e:
        logger.error(f"書類ダウンロード失敗: {e}")
        raise

    try:
        # XBRL解析
        return await xbrl_parser.parse(xbrl_path)
    except XBRLParseError as e:
        logger.warning(f"XBRL解析失敗、フォールバック実行: {e}")
        # フォールバック処理
        return await xbrl_parser.parse_with_fallback(xbrl_path)

# API層でのエラーハンドリング（FastAPI）
from fastapi import HTTPException

@app.get("/api/v1/documents/{doc_id}")
async def get_document(doc_id: str) -> DocumentResponse:
    try:
        document = await document_service.get_by_id(doc_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except EDINETAPIError as e:
        raise HTTPException(status_code=502, detail=f"EDINET API error: {e.message}")
    return DocumentResponse.from_entity(document)
```

**リトライ処理（tenacity）**:
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(EDINETAPIError),
)
async def call_edinet_api(endpoint: str, params: dict) -> dict:
    """EDINET APIを呼び出す（リトライ付き）"""
    response = await httpx_client.get(endpoint, params=params)
    if response.status_code != 200:
        raise EDINETAPIError(
            status_code=response.status_code,
            message=response.text,
            endpoint=endpoint,
        )
    return response.json()
```

> **Note**: EDINET APIはHTTP 200を返しながらレスポンスボディにエラーステータスを含む場合があります。
> トップレベル形式`{"statusCode": 401, ...}`とメタデータ形式`{"metadata": {"status": "404", ...}}`の両方に対応する必要があります。
> 実装例は`EDINETClient._check_internal_status()`を参照してください。

---

## Git運用ルール

### ブランチ戦略

**Git Flow採用**:

```
main                          # 本番リリース可能な状態
  └─ develop                  # 開発の最新状態
      ├─ feature/edinet-api   # EDINET API連携機能
      ├─ feature/xbrl-parser  # XBRL解析機能
      ├─ feature/pdf-parser   # PDF解析機能
      ├─ fix/api-retry        # APIリトライ処理の修正
      └─ refactor/repository  # リポジトリ層のリファクタリング
```

**ブランチ種別**:
| プレフィックス | 用途 | 例 |
|--------------|------|-----|
| `feature/` | 新機能開発 | `feature/edinet-api` |
| `fix/` | バグ修正 | `fix/xbrl-parsing-error` |
| `refactor/` | リファクタリング | `refactor/service-layer` |
| `docs/` | ドキュメント更新 | `docs/api-specification` |
| `test/` | テスト追加・修正 | `test/integration-tests` |

**マージルール**:
- `feature/*` → `develop`: Squash merge
- `fix/*` → `develop`: Squash merge
- `develop` → `main`: Merge commit（履歴を保持）

### コミットメッセージ規約

**Conventional Commits形式**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
| Type | 用途 |
|------|------|
| `feat` | 新機能 |
| `fix` | バグ修正 |
| `docs` | ドキュメント |
| `style` | コードフォーマット（動作に影響しない） |
| `refactor` | リファクタリング |
| `test` | テスト追加・修正 |
| `chore` | ビルド、補助ツール、設定変更 |
| `perf` | パフォーマンス改善 |

**Scope（このプロジェクト固有）**:
| Scope | 対象 |
|-------|------|
| `edinet` | EDINET API連携 |
| `xbrl` | XBRL解析 |
| `pdf` | PDF解析 |
| `financial` | 財務分析 |
| `db` | データベース |
| `api` | REST API |
| `ui` | Streamlit UI |

**例**:
```
feat(edinet): 書類一覧APIの連携機能を実装

- EDINETClientクラスを追加
- 書類メタデータの検索機能を実装
- レート制限対応のためのリトライ機能を追加

Closes #12
```

```
fix(xbrl): 売上高要素の取得失敗を修正

一部の企業でXBRL要素名が異なるため、
複数の要素名候補を試行するフォールバック処理を追加。

対象要素:
- jppfs_cor:NetSales
- jppfs_cor:Revenue
- jppfs_cor:OperatingRevenue

Fixes #45
```

### プルリクエストプロセス

**作成前のチェック**:
```bash
# 1. テストの実行
uv run pytest

# 2. 型チェック
uv run mypy src/

# 3. Lint・フォーマット
uv run ruff check src/
uv run ruff format src/

# 4. 競合の確認
git fetch origin
git rebase origin/develop
```

**PRテンプレート**:
```markdown
## 概要
[変更内容の簡潔な説明]

## 変更理由
[なぜこの変更が必要か]

## 変更内容
- [変更点1]
- [変更点2]

## テスト
- [ ] ユニットテスト追加/更新
- [ ] 統合テスト追加/更新
- [ ] 手動テスト実施

## チェックリスト
- [ ] 型ヒントを追加している
- [ ] Docstringを記述している
- [ ] テストがパスする
- [ ] ruff/mypyエラーがない

## 関連Issue
Closes #[Issue番号]
```

**レビュープロセス**:
1. セルフレビュー（PR作成者が確認）
2. CI自動テスト実行
3. レビュアーアサイン
4. レビューフィードバック対応
5. 承認後、Squash mergeで統合

---

## テスト戦略

### テストの種類

#### ユニットテスト

**対象**: 個別の関数・クラス
**カバレッジ目標**: 80%以上
**ディレクトリ**: `tests/unit/`

```python
# tests/unit/services/test_financial_analyzer.py
import pytest
from decimal import Decimal
from company_research_agent.services import FinancialAnalyzer

class TestFinancialAnalyzer:
    """FinancialAnalyzer のテスト"""

    class TestCalculateROE:
        """calculate_roe メソッドのテスト"""

        def test_with_valid_values_returns_percentage(self) -> None:
            """正常な値でROEを計算できる"""
            analyzer = FinancialAnalyzer()
            result = analyzer.calculate_roe(
                net_income=Decimal("1000000000"),
                equity=Decimal("10000000000"),
            )
            assert result == Decimal("10.0")

        def test_with_zero_equity_returns_none(self) -> None:
            """自己資本ゼロの場合Noneを返す"""
            analyzer = FinancialAnalyzer()
            result = analyzer.calculate_roe(
                net_income=Decimal("1000000000"),
                equity=Decimal("0"),
            )
            assert result is None

        def test_with_negative_net_income_returns_negative(self) -> None:
            """純損失の場合負のROEを返す"""
            analyzer = FinancialAnalyzer()
            result = analyzer.calculate_roe(
                net_income=Decimal("-500000000"),
                equity=Decimal("10000000000"),
            )
            assert result == Decimal("-5.0")
```

#### 統合テスト

**対象**: 複数コンポーネントの連携
**ディレクトリ**: `tests/integration/`

```python
# tests/integration/test_document_flow.py
import pytest
from company_research_agent.services import EDINETClient, XBRLParser
from company_research_agent.repositories import DocumentRepository

@pytest.fixture
async def db_session():
    """テスト用データベースセッション"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(test_engine) as session:
        yield session
        await session.rollback()

class TestDocumentFlow:
    """書類処理フローの統合テスト"""

    async def test_fetch_and_save_document(
        self,
        db_session: AsyncSession,
        mock_edinet_client: EDINETClient,
    ) -> None:
        """書類の取得と保存ができる"""
        repository = DocumentRepository(db_session)

        # 書類検索
        documents = await mock_edinet_client.search_documents(
            edinet_code="E00001",
            doc_type="annual_report",
        )
        assert len(documents) > 0

        # 書類保存
        for doc in documents:
            await repository.save(doc)

        # 保存確認
        saved = await repository.find_by_doc_id(documents[0].doc_id)
        assert saved is not None
        assert saved.edinet_code == "E00001"
```

#### E2Eテスト

**対象**: ユーザーシナリオ全体
**ディレクトリ**: `tests/e2e/`

```python
# tests/e2e/test_financial_analysis_flow.py
import pytest
from httpx import AsyncClient
from company_research_agent.main import app

class TestFinancialAnalysisFlow:
    """財務分析フローのE2Eテスト"""

    async def test_complete_analysis_flow(self) -> None:
        """企業検索→書類取得→財務分析の完全フロー"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 1. 企業検索
            response = await client.get(
                "/api/v1/companies",
                params={"name": "トヨタ"},
            )
            assert response.status_code == 200
            companies = response.json()["companies"]
            assert len(companies) > 0
            company_id = companies[0]["id"]

            # 2. 書類取得
            response = await client.get(
                f"/api/v1/companies/{company_id}/documents",
                params={"doc_type": "annual_report", "fiscal_year": 2024},
            )
            assert response.status_code == 200
            documents = response.json()["documents"]
            assert len(documents) > 0

            # 3. 財務指標取得
            response = await client.get(
                f"/api/v1/companies/{company_id}/financials",
                params={"fiscal_year": 2024},
            )
            assert response.status_code == 200
            financials = response.json()
            assert "indicators" in financials
            assert "roe" in financials["indicators"]
```

### テスト命名規則

**パターン**: `test_[メソッド名]_[条件]_[期待結果]`

```python
# ✅ 良い例
def test_calculate_roe_with_zero_equity_returns_none(self) -> None:
    """自己資本ゼロの場合Noneを返す"""
    ...

def test_search_documents_with_invalid_code_raises_validation_error(self) -> None:
    """不正なEDINETコードの場合ValidationErrorをスローする"""
    ...

async def test_download_document_with_network_error_retries(self) -> None:
    """ネットワークエラー時にリトライする"""
    ...

# ❌ 悪い例
def test_1(self) -> None: ...
def test_roe(self) -> None: ...
def test_should_work_correctly(self) -> None: ...
```

### モック・スタブの使用

**原則**:
- 外部API（EDINET API, Gemini API）: モック化
- データベース: 統合テストではテスト用DB、ユニットテストではモック
- ファイルシステム: 一時ディレクトリまたはモック

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
import tempfile

@pytest.fixture
def mock_edinet_client() -> MagicMock:
    """EDINETClientのモック"""
    client = MagicMock(spec=EDINETClient)
    client.search_documents = AsyncMock(return_value=[
        DocumentMetadata(
            doc_id="S100TEST",
            edinet_code="E00001",
            doc_type="annual_report",
            filing_date=date(2024, 6, 20),
        )
    ])
    client.download_document = AsyncMock(return_value=Path("/tmp/test.zip"))
    return client

@pytest.fixture
def mock_xbrl_parser() -> MagicMock:
    """XBRLParserのモック"""
    parser = MagicMock(spec=XBRLParser)
    parser.parse = AsyncMock(return_value=FinancialStatement(
        fiscal_year=2024,
        items=[
            FinancialItem(name="売上高", value=Decimal("1000000000000")),
            FinancialItem(name="営業利益", value=Decimal("100000000000")),
        ],
    ))
    return parser

@pytest.fixture
def temp_download_dir() -> Path:
    """テスト用一時ダウンロードディレクトリ"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
```

---

## コードレビュー基準

### レビューポイント

**機能性**:
- [ ] 要件を満たしているか
- [ ] エッジケースが考慮されているか（空リスト、None、境界値）
- [ ] エラーハンドリングが適切か
- [ ] EDINET API/XBRLの仕様に準拠しているか

**可読性**:
- [ ] 命名が明確か（プロジェクトの命名規則に従っているか）
- [ ] Docstringが適切か（Google Style）
- [ ] 複雑なロジックが説明されているか
- [ ] 型ヒントが付いているか

**保守性**:
- [ ] 重複コードがないか
- [ ] レイヤー間の責務が明確か（UI→Service→Repository→Data）
- [ ] 変更の影響範囲が限定的か
- [ ] 設定値がハードコードされていないか

**パフォーマンス**:
- [ ] 不要なAPI呼び出しがないか
- [ ] N+1クエリが発生していないか
- [ ] 大量データの処理が効率的か

**セキュリティ**:
- [ ] 入力検証が適切か（Pydantic使用）
- [ ] APIキーがハードコードされていないか
- [ ] SQLインジェクション対策がされているか（SQLAlchemyのパラメータバインディング）

### レビューコメントの書き方

**建設的なフィードバック**:
```markdown
## ✅ 良い例
[推奨] この実装だと、書類数が増えた時にN+1クエリが発生します。
代わりに、一括取得するクエリを検討してはどうでしょうか？

```python
# Before
for doc in documents:
    financial = await repo.get_by_doc_id(doc.id)  # N回クエリ

# After
doc_ids = [doc.id for doc in documents]
financials = await repo.get_by_doc_ids(doc_ids)  # 1回クエリ
```

## ❌ 悪い例
この書き方は良くないです。
```

**優先度の明示**:
| プレフィックス | 意味 |
|--------------|------|
| `[必須]` | 修正必須（マージブロック） |
| `[推奨]` | 修正推奨（改善提案） |
| `[提案]` | 検討してほしい（任意） |
| `[質問]` | 理解のための質問 |
| `[nit]` | 些細な指摘（修正不要） |

---

## 開発環境セットアップ

本プロジェクトは2つの環境構築方法を提供します:

| 環境 | 対象 | メリット |
|------|------|---------|
| ローカル環境（uv） | Mac開発者 | 高速な開発サイクル、デバッグ容易 |
| Docker環境 | Windows/Linux/Mac | 環境構築が簡単、クロスプラットフォーム |

---

### 方法1: ローカル環境（Mac開発者向け）

開発時は高速な開発サイクルのため、uvによるローカル環境を推奨します。

#### 必要なツール

| ツール | バージョン | インストール方法 |
|--------|-----------|-----------------|
| Python | 3.11+ | pyenv, asdf, または公式インストーラー |
| uv | 0.5+ | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker | 24+ | Docker Desktop |

#### セットアップ手順

```bash
# 1. リポジトリのクローン
git clone https://github.com/your-org/company-research-agent.git
cd company-research-agent

# 2. Python環境のセットアップ
uv sync

# 3. 開発用依存関係のインストール
uv sync --dev

# 4. 環境変数の設定
cp .env.example .env
# .envファイルを編集して以下を設定:
# - EDINET_API_KEY
# - GEMINI_API_KEY
# - DATABASE_URL

# 5. PostgreSQLの起動（Docker）
docker compose -f docker/docker-compose.db.yml up -d

# 6. データベースマイグレーション
uv run alembic upgrade head

# 7. pre-commitフックのインストール
uv run pre-commit install

# 8. テストの実行
uv run pytest

# 9. 開発サーバーの起動（オプション）
uv run uvicorn company_research_agent.main:app --reload
```

---

### 方法2: Docker環境（Windows/Linux/Mac）

Docker環境はWindows等でも同一の環境を構築できます。

#### 必要なツール

| ツール | バージョン | インストール方法 |
|--------|-----------|-----------------|
| Docker | 24+ | Docker Desktop（Windows/Mac）または docker-ce（Linux） |
| Docker Compose | 2.0+ | Docker Desktopに同梱 |
| Git | 2.40+ | 公式インストーラー |

**Windows固有の設定**:
- Docker Desktop: WSL2バックエンドを有効化
- メモリ割り当て: 最低4GB（推奨8GB）
- Git: `git config --global core.autocrlf false`（改行コードLF維持）

#### セットアップ手順

```bash
# 1. リポジトリのクローン
git clone https://github.com/your-org/company-research-agent.git
cd company-research-agent

# 2. 環境変数の設定
cp docker/.env.example docker/.env
# docker/.envファイルを編集して以下を設定:
# - EDINET_API_KEY
# - GEMINI_API_KEY

# 3. Dockerイメージのビルドと起動
docker compose -f docker/docker-compose.yml up -d --build

# 4. ログの確認
docker compose -f docker/docker-compose.yml logs -f app

# 5. テストの実行
docker compose -f docker/docker-compose.yml exec app pytest

# 6. アプリケーションへのアクセス
# ブラウザで http://localhost:8000 を開く
```

#### よく使うDockerコマンド

```bash
# サービスの停止
docker compose -f docker/docker-compose.yml down

# サービスの再起動
docker compose -f docker/docker-compose.yml restart app

# コンテナ内でシェルを起動
docker compose -f docker/docker-compose.yml exec app bash

# ログの確認（リアルタイム）
docker compose -f docker/docker-compose.yml logs -f

# データベースのみ起動（ローカル開発との併用）
docker compose -f docker/docker-compose.db.yml up -d

# 全コンテナ・ボリューム削除（クリーンアップ）
docker compose -f docker/docker-compose.yml down -v
```

#### トラブルシューティング（Windows）

| 問題 | 原因 | 解決策 |
|------|------|--------|
| コンテナが起動しない | メモリ不足 | Docker Desktopでメモリ割り当てを増やす |
| ファイル変更が反映されない | WSL2のファイル監視 | `CHOKIDAR_USEPOLLING=true` を設定 |
| 改行コードエラー | CRLF問題 | `git config --global core.autocrlf false` |
| パス長エラー | Windows制限 | プロジェクトをCドライブ直下に配置 |

### 環境変数

```bash
# .env.example
# EDINET API
EDINET_API_KEY=your_edinet_api_key_here

# Gemini API（PDF解析用）
GEMINI_API_KEY=your_gemini_api_key_here

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/company_research_agent

# Logging
LOG_LEVEL=INFO

# Data directories
DATA_DIR=./data
DOWNLOAD_DIR=./data/downloads
CACHE_DIR=./data/cache
```

### 推奨開発ツール

| ツール | 用途 |
|--------|------|
| VSCode + Pylance | Python開発のメインIDE |
| Ruff Extension | リアルタイムのLint・フォーマット |
| Python Debugger | デバッグ実行 |
| PostgreSQL Extension | データベース確認 |
| Thunder Client | API動作確認 |

**VSCode設定 (.vscode/settings.json)**:
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    },
    "python.analysis.typeCheckingMode": "basic",
    "mypy-type-checker.args": ["--config-file=pyproject.toml"]
}
```

---

## CI/CD パイプライン

### pre-commit（ローカル）

コミット時に自動で ruff, ruff-format, mypy が実行されます。

```bash
# Git hooks のインストール（初回のみ）
uv run pre-commit install

# 手動で全ファイルに対して実行
uv run pre-commit run --all-files
```

**.pre-commit-config.yaml** で定義されるフック:
- `ruff`: Lint（自動修正付き）
- `ruff-format`: フォーマット
- `mypy`: 型チェック

### GitHub Actions設定

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "0.5.x"
      - name: Set up Python
        run: uv python install 3.12
      - name: Install dependencies
        run: uv sync --dev
      - name: Run ruff check
        run: uv run ruff check src/
      - name: Run ruff format check
        run: uv run ruff format --check src/

  type-check:
    name: Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "0.5.x"
      - name: Set up Python
        run: uv python install 3.12
      - name: Install dependencies
        run: uv sync --dev
      - name: Run mypy
        run: uv run mypy src/

  test:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "0.5.x"
      - name: Set up Python
        run: uv python install 3.12
      - name: Install dependencies
        run: uv sync --dev
      - name: Run pytest
        run: uv run pytest --cov=src/ --cov-report=xml
      - name: Upload coverage reports
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          fail_ci_if_error: false
        env:
          CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

### 品質ゲート

| チェック | 条件 | ブロック |
|---------|------|---------|
| ruff lint | エラー0件 | ✅ |
| ruff format | フォーマット済み | ✅ |
| mypy | エラー0件 | ✅ |
| pytest | 全テストパス | ✅ |
| カバレッジ | 80%以上 | ⚠️（警告） |

---

**作成日**: 2026年1月16日
**バージョン**: 1.0
**ステータス**: ドラフト
