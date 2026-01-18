# Company Research Agent

AI-powered Corporate Research Agent - 企業情報収集・分析エージェント

## プロジェクト概要

- **情報収集**: EDINET/TDnet/企業サイトからの開示書類・IR情報の統合収集
- **自動解析**: PDF/XBRLの自動解析による財務データの構造化
- **分析支援**: 財務指標の自動計算と時系列分析
- **エージェント**: LLMを活用した企業分析支援

## 技術スタック

| 分類 | 技術 |
|------|------|
| 言語 | Python 3.11+ |
| パッケージ管理 | uv 0.9+ |
| Webフレームワーク | FastAPI |
| ORM | SQLAlchemy 2.0+ (asyncpg) |
| データベース | PostgreSQL 15+ + pgvector |
| XBRL解析 | edinet-xbrl + BeautifulSoup/lxml |
| PDF解析 | pdfplumber + pymupdf4llm + yomitoku |
| 開発ツール | ruff, mypy, pytest, pre-commit |

## ディレクトリ構造

```
src/company_research_agent/
├── api/           # REST API (FastAPI)
├── cli/           # CLIツール (cra コマンド)
│   ├── main.py    # エントリーポイント
│   ├── commands/  # サブコマンド実装
│   │   ├── search.py     # 企業検索
│   │   ├── list.py       # 書類一覧
│   │   ├── download.py   # ダウンロード
│   │   ├── markdown.py   # PDF→マークダウン変換
│   │   ├── query.py      # 自然言語クエリ
│   │   ├── chat.py       # 対話モード
│   │   └── cache.py      # キャッシュ管理
│   ├── config.py  # CLI設定・定数
│   ├── output.py  # 出力ユーティリティ
│   └── rich_output.py  # Rich整形出力
├── clients/       # 外部APIクライアント (EDINET, Gemini)
├── llm/           # LLMプロバイダー抽象化レイヤー
├── observability/ # オブザーバビリティ (Langfuse統合)
├── orchestrator/  # 自然言語オーケストレーター
├── parsers/       # XBRL/PDF解析
├── services/      # ビジネスロジック
├── repositories/  # データアクセス
├── models/        # SQLAlchemyモデル
├── schemas/       # Pydanticスキーマ
├── tools/         # LangChainツール群
├── workflows/     # LangGraphワークフロー
└── core/          # 設定、例外、ユーティリティ

tests/
├── unit/          # ユニットテスト
├── integration/   # 統合テスト
└── e2e/           # E2Eテスト

docs/              # プロジェクトドキュメント
notebooks/         # Jupyter Notebook
scripts/           # ユーティリティスクリプト
config/            # 設定ファイル (YAML)
docker/            # Docker設定
```

## 開発コマンド

```bash
# 依存関係インストール
uv sync --dev

# pre-commit フックのインストール（初回のみ）
uv run pre-commit install

# テスト実行
uv run pytest

# 型チェック
uv run mypy src/

# Lint & フォーマット
uv run ruff check src/
uv run ruff format src/

# pre-commit 手動実行（全ファイル）
uv run pre-commit run --all-files

# 開発サーバー起動
uv run uvicorn company_research_agent.main:app --reload

# PostgreSQL起動 (Docker)
docker compose -f docker/docker-compose.db.yml up -d
```

## CLIツール

```bash
# 基本的な使用例
cra search --name "トヨタ"
cra list --sec-code 72030 --doc-types 120,140
cra download --sec-code 72030 --limit 3
cra markdown --doc-id S100VWVY
cra query "トヨタの有報を分析して"
cra chat

# デバッグモード（-v または LOG_LEVEL で詳細ログ表示）
cra -v list --sec-code 72030
LOG_LEVEL=DEBUG cra list --sec-code 72030
```

### ログレベル

| レベル | 説明 |
|--------|------|
| WARNING | デフォルト（静かに動作） |
| INFO | 基本情報 |
| DEBUG | 詳細ログ（-v オプションで有効化） |
| ERROR | エラーのみ |

## コーディング規約

### 命名規則

- 変数・関数: `snake_case`
- クラス: `PascalCase`
- 定数: `UPPER_SNAKE_CASE`
- Boolean: `is_`, `has_`, `should_` で始める

### プロジェクト固有の命名

```python
edinet_code: str    # EDINETコード (E00001形式)
sec_code: str       # 証券コード (5桁)
doc_id: str         # EDINET書類ID (S100XXXX形式)
fiscal_year: int    # 会計年度
```

### データ構造の使い分け

| 用途 | 推奨 |
|------|------|
| APIリクエスト/レスポンス | `pydantic.BaseModel` |
| 内部ドメインモデル | `dataclass` |
| インターフェース定義 | `Protocol` |
| 辞書の型ヒント | `TypedDict` |

### レイヤー間の依存ルール

```
api/ → services/ → repositories/ → models/
                 → clients/      → core/
                 → parsers/
```

- 上位レイヤーから下位レイヤーへの依存のみ許可
- 循環依存禁止

## Git運用

### ブランチ

- `main`: 本番リリース可能
- `develop`: 開発の最新状態
- `feature/xxx`: 新機能
- `fix/xxx`: バグ修正

### コミットメッセージ (Conventional Commits)

```
feat(edinet): 書類一覧APIの連携機能を実装
fix(xbrl): 売上高要素の取得失敗を修正
docs(api): APIドキュメントを更新
```

## 参考ドキュメント

詳細は `docs/` 配下を参照:

- `product-requirements.md` - プロダクト要求定義書
- `functional-design.md` - 機能設計書
- `architecture.md` - アーキテクチャ設計書
- `development-guidelines.md` - 開発ガイドライン
- `repository-structure.md` - リポジトリ構造定義書
- `glossary.md` - 用語集
