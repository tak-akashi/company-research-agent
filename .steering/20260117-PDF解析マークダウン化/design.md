# 設計書

## アーキテクチャ概要

レイヤードアーキテクチャに基づき、`parsers/`レイヤーにPDF解析ロジックを配置する。

```
┌─────────────────────────────────────────────────────────────┐
│   サービスレイヤー (services/)                                │
│   └─ PDFParser を利用してビジネスロジックを実装               │
├─────────────────────────────────────────────────────────────┤
│   パーサーレイヤー (parsers/)  ← 今回の実装対象               │
│   └─ PDFParser: PDF解析の実装                               │
├─────────────────────────────────────────────────────────────┤
│   コアレイヤー (core/)                                        │
│   └─ exceptions.py: PDFParseError                           │
│   └─ types.py: ParseStrategy                                │
└─────────────────────────────────────────────────────────────┘
```

## コンポーネント設計

### 1. PDFParser（src/company_research_agent/parsers/pdf_parser.py）

**責務**:
- PDFファイルのメタデータ取得
- テキスト抽出
- マークダウン形式への変換
- 段階的解析戦略の制御

**実装の要点**:
- `pdfplumber`を基本的なテキスト抽出に使用
- `pymupdf4llm`を構造を保持したマークダウン変換に使用
- 将来的な拡張（yomitoku, Gemini）を考慮した設計

**クラス構造**:
```python
from dataclasses import dataclass
from pathlib import Path
from company_research_agent.core.types import ParseStrategy

@dataclass
class PDFInfo:
    """PDFメタデータ."""
    file_name: str
    file_path: str
    total_pages: int
    page_size: dict[str, float] | None
    metadata: dict[str, str]
    table_of_contents: list[str]

@dataclass
class ParsedPDFContent:
    """解析されたPDFコンテンツ."""
    text: str
    pages: int
    strategy_used: ParseStrategy
    metadata: dict[str, object]

class PDFParser:
    """PDF解析クラス."""

    def get_info(self, pdf_path: Path) -> PDFInfo:
        """PDFのメタデータを取得する."""
        ...

    def extract_text(
        self,
        pdf_path: Path,
        start_page: int = 1,
        end_page: int | None = None,
    ) -> str:
        """指定ページ範囲のテキストを抽出する."""
        ...

    def to_markdown(
        self,
        pdf_path: Path,
        start_page: int | None = None,
        end_page: int | None = None,
        strategy: ParseStrategy = "auto",
    ) -> ParsedPDFContent:
        """PDFをマークダウン形式に変換する."""
        ...
```

### 2. 型定義の拡張（src/company_research_agent/core/types.py）

**追加する型**:
```python
type ParseStrategy = Literal["auto", "pdfplumber", "pymupdf4llm"]
```

### 3. カスタム例外（src/company_research_agent/core/exceptions.py）

**追加する例外**:
```python
class PDFParseError(CompanyResearchAgentError):
    """PDF解析に関するエラー."""
    pass
```

## データフロー

### PDF → マークダウン変換
```
1. ユーザーがPDFパスと解析戦略を指定
2. PDFParser.to_markdown() が呼び出される
3. 戦略に応じた解析ライブラリを使用
   - auto: pymupdf4llmを使用
   - pdfplumber: pdfplumberのテキスト抽出を使用
   - pymupdf4llm: pymupdf4llmを使用
4. ParsedPDFContent として結果を返却
```

## エラーハンドリング戦略

### カスタムエラークラス

```python
class PDFParseError(CompanyResearchAgentError):
    """PDF解析に関するエラー.

    Attributes:
        message: エラーメッセージ
        pdf_path: 解析対象のPDFパス
        strategy: 使用された解析戦略
    """
    message: str
    pdf_path: str
    strategy: str | None = None
```

### エラーハンドリングパターン

- **ファイル不存在**: FileNotFoundErrorをそのまま送出（標準的な挙動）
- **解析失敗**: PDFParseErrorをメッセージと共に送出
- **ページ範囲エラー**: ValueError（無効なページ番号）

## テスト戦略

### ユニットテスト
- `test_pdf_parser.py`
  - PDFInfo取得のテスト
  - テキスト抽出のテスト
  - マークダウン変換のテスト
  - エラーケースのテスト（ファイル不存在等）

### テストデータ
- テスト用の小さなPDFファイル（`tests/fixtures/`に配置予定）
- モック使用によるライブラリ依存の分離

## 依存ライブラリ

既存のpyproject.tomlで定義済み:

```toml
[project]
dependencies = [
    "pdfplumber>=0.11.0",
    "pymupdf4llm>=0.0.17",
]
```

## ディレクトリ構造

```
src/company_research_agent/
├── core/
│   ├── exceptions.py      # PDFParseError 追加
│   └── types.py           # ParseStrategy 追加
├── parsers/
│   ├── __init__.py        # 新規作成
│   └── pdf_parser.py      # 新規作成
└── ...

tests/
├── unit/
│   └── parsers/
│       ├── __init__.py    # 新規作成
│       └── test_pdf_parser.py  # 新規作成
└── fixtures/
    └── sample.pdf         # テスト用PDF（新規作成）
```

## 実装の順序

1. 型定義の追加（types.py）
2. 例外クラスの追加（exceptions.py）
3. parsers/__init__.py の作成
4. PDFParser クラスの実装
5. ユニットテストの作成
6. 品質チェック（pytest, ruff, mypy）

## セキュリティ考慮事項

- パストラバーサル攻撃の防止（ユーザー入力のパスをそのまま使用しない）
- メモリ使用量の制限（大きなPDFの処理時）

## パフォーマンス考慮事項

- 大規模PDF（100ページ超）では処理時間が長くなる可能性
- ページ範囲指定による部分的な処理のサポート

## 将来の拡張性

- yomitoku統合のための`ParseStrategy`への追加（"yomitoku"）
- Gemini API統合のための`ParseStrategy`への追加（"gemini"）
- 表抽出機能の追加（extract_tables メソッド）
- 非同期処理のサポート（async版メソッドの追加）
