# リポジトリ構造定義書 (Repository Structure Document)

## プロジェクト構造

```
company-research-agent/
├── src/
│   └── company_research_agent/         # メインパッケージ
│       ├── api/                  # REST API (FastAPI)
│       ├── clients/              # 外部APIクライアント
│       ├── parsers/              # 解析処理
│       ├── services/             # ビジネスロジック
│       ├── repositories/         # データアクセス
│       ├── models/               # データモデル
│       ├── schemas/              # Pydanticスキーマ
│       └── core/                 # 共通機能
├── tests/                        # テストコード
│   ├── unit/                     # ユニットテスト
│   ├── integration/              # 統合テスト
│   └── e2e/                      # E2Eテスト
├── docs/                         # プロジェクトドキュメント
│   ├── ideas/                    # アイデアメモ
│   └── research/                 # 技術調査レポート
├── notebooks/                    # Jupyter Notebook
├── scripts/                      # ユーティリティスクリプト
├── config/                       # 設定ファイル
├── data/                         # データディレクトリ（.gitignore）
│   ├── downloads/                # ダウンロードファイル
│   ├── cache/                    # キャッシュデータ
│   └── temp/                     # 一時ファイル
└── docker/                       # Docker設定
```

---

## ディレクトリ詳細

### src/company_research_agent/ (メインパッケージ)

#### api/

**役割**: REST APIエンドポイントの実装（FastAPI）

**配置ファイル**:
- `main.py`: FastAPIアプリケーションのエントリーポイント
- `routers/`: APIルーター（エンドポイント定義）
- `dependencies.py`: 依存性注入の定義

**命名規則**:
- ルーターファイル: `{リソース名}_router.py`
- 例: `documents_router.py`, `companies_router.py`

**依存関係**:
- 依存可能: services/, schemas/
- 依存禁止: repositories/, clients/（サービス経由でアクセス）

**例**:
```
api/
├── __init__.py
├── main.py                      # FastAPIアプリ
├── dependencies.py              # DI設定
└── routers/
    ├── __init__.py
    ├── documents_router.py      # 書類関連API
    ├── companies_router.py      # 企業関連API
    └── financials_router.py     # 財務データAPI
```

#### clients/

**役割**: 外部APIとの通信を担当するクライアント

**配置ファイル**:
- `edinet_client.py`: EDINET API クライアント
- `gemini_client.py`: Gemini API クライアント
- `base_client.py`: 共通クライアント基底クラス

**命名規則**:
- ファイル名: `{サービス名}_client.py`
- クラス名: `{サービス名}Client`

**依存関係**:
- 依存可能: core/, models/
- 依存禁止: services/, repositories/

**例**:
```
clients/
├── __init__.py
├── base_client.py               # 基底クライアント
├── edinet_client.py             # EDINET APIクライアント
└── gemini_client.py             # Gemini APIクライアント
```

#### parsers/

**役割**: ファイル解析処理（XBRL、PDF）

**配置ファイル**:
- `xbrl_parser.py`: XBRL解析（edinet-xbrl + BeautifulSoup）
- `pdf_parser.py`: PDF解析（pdfplumber + pymupdf4llm + YOMITOKU）
- `element_mapping.py`: XBRL要素名マッピング

**命名規則**:
- ファイル名: `{対象形式}_parser.py`
- クラス名: `{対象形式}Parser`

**依存関係**:
- 依存可能: core/, models/
- 依存禁止: services/, repositories/, clients/

**例**:
```
parsers/
├── __init__.py
├── xbrl_parser.py               # XBRL解析
├── pdf_parser.py                # PDF解析
├── element_mapping.py           # XBRL要素名マッピング
└── fallback_parser.py           # BeautifulSoup フォールバック
```

#### services/

**役割**: ビジネスロジックの実装

**配置ファイル**:
- `document_service.py`: 書類検索・取得サービス
- `financial_analyzer.py`: 財務分析サービス
- `batch_processor.py`: バッチ処理サービス
- `llm_analyzer.py`: LLM分析サービス
- `vector_search_service.py`: ベクトル検索サービス

**命名規則**:
- ファイル名: `{機能名}_service.py` または `{機能名}_analyzer.py`
- クラス名: `{機能名}Service` または `{機能名}Analyzer`

**依存関係**:
- 依存可能: repositories/, clients/, parsers/, models/, core/
- 依存禁止: api/

**例**:
```
services/
├── __init__.py
├── document_service.py          # 書類検索・取得
├── financial_analyzer.py        # 財務分析
├── indicator_calculator.py      # 財務指標計算
├── batch_processor.py           # バッチ処理
├── llm_analyzer.py              # LLM分析
└── vector_search_service.py     # ベクトル検索
```

#### repositories/

**役割**: データアクセスの抽象化（CRUD操作）

**配置ファイル**:
- `company_repository.py`: 企業データリポジトリ
- `document_repository.py`: 書類データリポジトリ
- `financial_statement_repository.py`: 財務諸表リポジトリ
- `financial_indicator_repository.py`: 財務指標リポジトリ
- `base_repository.py`: 共通リポジトリ基底クラス

**命名規則**:
- ファイル名: `{エンティティ名}_repository.py`
- クラス名: `{エンティティ名}Repository`

**依存関係**:
- 依存可能: models/, core/
- 依存禁止: services/, api/, clients/

**例**:
```
repositories/
├── __init__.py
├── base_repository.py           # 基底リポジトリ
├── company_repository.py        # 企業リポジトリ
├── document_repository.py       # 書類リポジトリ
├── financial_statement_repository.py  # 財務諸表リポジトリ
└── financial_indicator_repository.py  # 財務指標リポジトリ
```

#### models/

**役割**: データモデル（SQLAlchemyモデル、dataclass）

**配置ファイル**:
- `company.py`: 企業エンティティ
- `document.py`: 書類エンティティ
- `financial_statement.py`: 財務諸表エンティティ
- `financial_indicator.py`: 財務指標エンティティ
- `base.py`: SQLAlchemy Base定義

**命名規則**:
- ファイル名: `{エンティティ名}.py`（単数形、snake_case）
- クラス名: `{エンティティ名}`（単数形、PascalCase）

**依存関係**:
- 依存可能: core/（型定義のみ）
- 依存禁止: 他のすべてのディレクトリ

**例**:
```
models/
├── __init__.py
├── base.py                      # SQLAlchemy Base
├── company.py                   # 企業モデル
├── document.py                  # 書類モデル
├── financial_statement.py       # 財務諸表モデル
├── financial_item.py            # 財務項目モデル
└── financial_indicator.py       # 財務指標モデル
```

#### schemas/

**役割**: Pydanticスキーマ（API入出力、バリデーション）

**配置ファイル**:
- `document_schemas.py`: 書類関連スキーマ
- `company_schemas.py`: 企業関連スキーマ
- `financial_schemas.py`: 財務データスキーマ

**命名規則**:
- ファイル名: `{リソース名}_schemas.py`
- クラス名: `{リソース名}{操作}Schema`
  - 例: `DocumentSearchRequest`, `DocumentResponse`

**依存関係**:
- 依存可能: core/（型定義のみ）
- 依存禁止: models/, services/, repositories/

**例**:
```
schemas/
├── __init__.py
├── document_schemas.py          # 書類スキーマ
├── company_schemas.py           # 企業スキーマ
├── financial_schemas.py         # 財務スキーマ
└── common_schemas.py            # 共通スキーマ
```

#### core/

**役割**: 共通機能（設定、例外、ユーティリティ）

**配置ファイル**:
- `config.py`: アプリケーション設定
- `database.py`: データベース接続設定
- `exceptions.py`: カスタム例外クラス
- `logging.py`: ロギング設定
- `types.py`: 型エイリアス定義

**命名規則**:
- ファイル名: `{機能名}.py`

**依存関係**:
- 依存可能: なし（他のモジュールに依存しない）
- 依存禁止: すべてのディレクトリ

**例**:
```
core/
├── __init__.py
├── config.py                    # 設定
├── database.py                  # DB接続
├── exceptions.py                # 例外クラス
├── logging.py                   # ロギング
└── types.py                     # 型定義
```

---

### tests/ (テストディレクトリ)

#### unit/

**役割**: ユニットテストの配置

**構造**:
```
tests/unit/
├── conftest.py                  # 共通フィクスチャ
├── parsers/
│   ├── test_xbrl_parser.py
│   └── test_pdf_parser.py
├── services/
│   ├── test_financial_analyzer.py
│   └── test_indicator_calculator.py
└── repositories/
    └── test_company_repository.py
```

**命名規則**:
- パターン: `test_{テスト対象ファイル名}.py`
- 例: `xbrl_parser.py` → `test_xbrl_parser.py`

#### integration/

**役割**: 統合テストの配置

**構造**:
```
tests/integration/
├── conftest.py                  # DB設定等
├── test_edinet_api.py           # EDINET API連携
├── test_xbrl_parsing.py         # XBRL解析フロー
└── test_database.py             # データベース操作
```

#### e2e/

**役割**: E2Eテストの配置

**構造**:
```
tests/e2e/
├── conftest.py
├── test_financial_analysis_flow.py  # 財務分析フロー
└── test_batch_processing.py         # バッチ処理
```

---

### docs/ (ドキュメントディレクトリ)

**配置ドキュメント**:
- `product-requirements.md`: プロダクト要求定義書
- `functional-design.md`: 機能設計書
- `architecture.md`: アーキテクチャ設計書
- `repository-structure.md`: リポジトリ構造定義書（本ドキュメント）
- `development-guidelines.md`: 開発ガイドライン
- `glossary.md`: 用語集

**サブディレクトリ**:
- `ideas/`: アイデアメモ、壁打ち結果
- `research/`: 技術調査レポート

---

### notebooks/ (Jupyter Notebookディレクトリ)

**役割**: 分析用ノートブック、サンプルコード

**構造**:
```
notebooks/
├── examples/                    # サンプルノートブック
│   ├── 01_basic_usage.ipynb     # 基本的な使い方
│   ├── 02_financial_analysis.ipynb  # 財務分析
│   └── 03_batch_processing.ipynb    # バッチ処理
└── analysis/                    # 分析用ノートブック
```

---

### scripts/ (スクリプトディレクトリ)

**役割**: ユーティリティスクリプト、開発補助

**配置ファイル**:
- `init_db.py`: データベース初期化
- `download_edinet_code_list.py`: EDINETコードリスト取得
- `run_batch.py`: バッチ処理実行

**例**:
```
scripts/
├── init_db.py                   # DB初期化
├── download_edinet_code_list.py # コードリスト取得
├── run_batch.py                 # バッチ実行
└── export_data.py               # データエクスポート
```

---

### config/ (設定ディレクトリ)

**役割**: 設定ファイルの配置

**配置ファイル**:
- `element_mapping.yaml`: XBRL要素名マッピング
- `indicators.yaml`: 財務指標定義
- `logging.yaml`: ロギング設定

**例**:
```
config/
├── element_mapping.yaml         # XBRL要素マッピング
├── indicators.yaml              # 財務指標定義
└── logging.yaml                 # ロギング設定
```

---

### docker/ (Docker設定ディレクトリ)

**役割**: Docker関連設定（クロスプラットフォーム対応）

本プロジェクトは開発者向けのローカル環境（Mac + uv）に加え、Windows等でも実行できるDocker環境を提供します。

**構造**:
```
docker/
├── Dockerfile                   # 本番用（マルチステージビルド）
├── Dockerfile.dev               # 開発環境用（ホットリロード対応）
├── docker-compose.yml           # 開発環境（全サービス起動）
├── docker-compose.prod.yml      # 本番環境（最適化設定）
├── docker-compose.db.yml        # DBのみ起動（ローカル開発併用）
├── .env.example                 # Docker用環境変数サンプル
└── scripts/
    ├── entrypoint.sh            # コンテナ起動スクリプト
    └── wait-for-db.sh           # DB起動待機スクリプト
```

**ファイル詳細**:

| ファイル | 用途 | 対象ユーザー |
|---------|------|------------|
| `Dockerfile` | 本番用イメージ（軽量、最適化） | 本番デプロイ |
| `Dockerfile.dev` | 開発用イメージ（デバッグツール含む） | 開発者（Docker環境） |
| `docker-compose.yml` | 全サービス起動（app + db） | 開発者（Docker環境）、一般ユーザー |
| `docker-compose.db.yml` | DBのみ起動 | 開発者（ローカル環境 + Docker DB） |
| `.env.example` | 環境変数テンプレート | 全ユーザー |

**使用シーン別**:
- **Windows/Linuxユーザー**: `docker-compose.yml` で全環境を起動
- **Mac開発者（uv使用）**: `docker-compose.db.yml` でDBのみ起動、アプリはuvで実行
- **本番デプロイ**: `docker-compose.prod.yml` を使用

---

### data/ (データディレクトリ)

**役割**: ダウンロードファイル、キャッシュ（.gitignore対象）

**構造**:
```
data/
├── downloads/                   # ダウンロードファイル
│   ├── xbrl/                    # XBRL（ZIP解凍後）
│   │   └── {doc_id}/
│   └── pdf/                     # PDF
│       └── {doc_id}.pdf
├── cache/                       # キャッシュ
│   └── edinet_code_list.json
└── temp/                        # 一時ファイル
```

---

## ファイル配置規則

### ソースファイル

| ファイル種別 | 配置先 | 命名規則 | 例 |
|------------|--------|---------|-----|
| APIルーター | api/routers/ | `{リソース}_router.py` | `documents_router.py` |
| 外部クライアント | clients/ | `{サービス}_client.py` | `edinet_client.py` |
| パーサー | parsers/ | `{形式}_parser.py` | `xbrl_parser.py` |
| サービス | services/ | `{機能}_service.py` | `document_service.py` |
| リポジトリ | repositories/ | `{エンティティ}_repository.py` | `company_repository.py` |
| モデル | models/ | `{エンティティ}.py` | `company.py` |
| スキーマ | schemas/ | `{リソース}_schemas.py` | `document_schemas.py` |

### テストファイル

| テスト種別 | 配置先 | 命名規則 | 例 |
|-----------|--------|---------|-----|
| ユニットテスト | tests/unit/{layer}/ | `test_{対象}.py` | `test_xbrl_parser.py` |
| 統合テスト | tests/integration/ | `test_{機能}.py` | `test_edinet_api.py` |
| E2Eテスト | tests/e2e/ | `test_{シナリオ}.py` | `test_financial_analysis_flow.py` |

### 設定ファイル

| ファイル種別 | 配置先 | 命名規則 |
|------------|--------|---------|
| アプリ設定 | config/ | `{設定名}.yaml` |
| 環境変数 | プロジェクトルート | `.env`（.gitignore対象） |
| ツール設定 | プロジェクトルート | `pyproject.toml` |
| Docker設定 | docker/ | `Dockerfile`, `docker-compose*.yml` |
| 改行コード設定 | プロジェクトルート | `.gitattributes` |

### プロジェクトルートファイル

```
company-research-agent/
├── pyproject.toml               # プロジェクト設定（uv, ruff, mypy等）
├── uv.lock                      # 依存関係ロックファイル
├── .env.example                 # 環境変数テンプレート
├── .gitignore                   # Git除外設定
├── .gitattributes               # 改行コード設定（LF統一）
├── .pre-commit-config.yaml      # pre-commitフック設定
├── README.md                    # プロジェクト概要
└── CLAUDE.md                    # Claude Code設定
```

---

## 命名規則

### ディレクトリ名

- **レイヤーディレクトリ**: 複数形、snake_case
  - 例: `services/`, `repositories/`, `parsers/`
- **機能ディレクトリ**: 単数形、snake_case
  - 例: `financial_analysis/`, `batch_processing/`

### ファイル名

- **モジュールファイル**: snake_case
  - 例: `edinet_client.py`, `xbrl_parser.py`
- **定数ファイル**: snake_case
  - 例: `element_mapping.py`, `error_messages.py`

### クラス名

- **サービスクラス**: `{機能名}Service`
  - 例: `DocumentService`, `FinancialAnalyzer`
- **リポジトリクラス**: `{エンティティ名}Repository`
  - 例: `CompanyRepository`, `DocumentRepository`
- **クライアントクラス**: `{サービス名}Client`
  - 例: `EDINETClient`, `GeminiClient`

---

## 依存関係のルール

### レイヤー間の依存

```
┌─────────────────┐
│     api/        │ ← UIレイヤー
├─────────────────┤
         ↓ (OK)
├─────────────────┤
│   services/     │ ← サービスレイヤー
├─────────────────┤
         ↓ (OK)
├─────────────────┤
│  repositories/  │ ← リポジトリレイヤー
│   clients/      │
│   parsers/      │
├─────────────────┤
         ↓ (OK)
├─────────────────┤
│    models/      │ ← データレイヤー
│    schemas/     │
│     core/       │
└─────────────────┘
```

**許可される依存**:
- `api/` → `services/`, `schemas/`
- `services/` → `repositories/`, `clients/`, `parsers/`, `models/`, `core/`
- `repositories/` → `models/`, `core/`
- `clients/` → `models/`, `core/`
- `parsers/` → `models/`, `core/`

**禁止される依存**:
- `repositories/` → `services/`, `api/`（❌）
- `models/` → 他のすべてのディレクトリ（❌）
- `services/` → `api/`（❌）
- 循環依存（❌）

### 循環依存の回避

**問題のあるコード**:
```python
# services/document_service.py
from services.financial_service import FinancialService  # 循環依存リスク
```

**解決策: Protocolを使用**
```python
# core/protocols.py
from typing import Protocol

class IFinancialService(Protocol):
    async def calculate_indicators(self, data: ParsedFinancialData) -> FinancialIndicators: ...

# services/document_service.py
from core.protocols import IFinancialService

class DocumentService:
    def __init__(self, financial_service: IFinancialService) -> None:
        self.financial_service = financial_service
```

---

## スケーリング戦略

### 機能の追加

新しい機能を追加する際の配置方針:

1. **小規模機能**: 既存ディレクトリに配置
2. **中規模機能**: サブディレクトリを作成
3. **大規模機能**: 独立したモジュールとして分離

**例: TDnet連携の追加（将来）**:
```
src/company_research_agent/
├── clients/
│   ├── edinet_client.py         # 既存
│   └── tdnet_client.py          # 新規追加
├── services/
│   ├── document_service.py      # 既存（拡張）
│   └── tdnet_service.py         # 新規追加（必要に応じて）
```

### ファイルサイズの管理

**ファイル分割の目安**:
- 1ファイル: 300行以下を推奨
- 300-500行: リファクタリングを検討
- 500行以上: 分割を強く推奨

**分割例**:
```python
# Before: 1ファイルに全機能
# services/financial_analyzer.py (600行)

# After: 責務ごとに分割
# services/financial_analyzer.py (200行) - メイン分析
# services/indicator_calculator.py (200行) - 指標計算
# services/ratio_calculator.py (150行) - 比率計算
```

---

## 特殊ディレクトリ

### .steering/ (ステアリングファイル)

**役割**: 特定の開発作業における「今回何をするか」を定義

**構造**:
```
.steering/
└── {YYYYMMDD}-{task-name}/
    ├── requirements.md          # 今回の作業の要求内容
    ├── design.md                # 変更内容の設計
    └── tasklist.md              # タスクリスト
```

**命名規則**: `20260116-add-pdf-parsing` 形式

### .claude/ (Claude Code設定)

**役割**: Claude Code設定とカスタマイズ

**構造**:
```
.claude/
├── commands/                    # スラッシュコマンド
├── skills/                      # タスクモード別スキル
└── agents/                      # サブエージェント定義
```

---

## 除外設定

### .gitignore

```gitignore
# Python
.venv/
__pycache__/
*.pyc
*.pyo
.mypy_cache/
.ruff_cache/
.pytest_cache/

# 環境設定
.env
.env.local

# データディレクトリ
data/

# ステアリングファイル
.steering/

# IDE
.idea/
.vscode/
*.swp

# ビルド成果物
dist/
build/
*.egg-info/

# カバレッジ
htmlcov/
.coverage
coverage.xml

# ログ
*.log

# OS
.DS_Store
Thumbs.db
```

---

**作成日**: 2026年1月16日
**バージョン**: 1.0
**ステータス**: ドラフト
