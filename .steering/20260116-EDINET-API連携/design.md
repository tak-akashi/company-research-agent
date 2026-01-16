# 設計書

## アーキテクチャ概要

レイヤードアーキテクチャに従い、EDINETクライアントを`clients/`レイヤーに配置する。

```
┌─────────────────────────────────────────────────────────────┐
│   将来: api/ (REST API)                                     │
├─────────────────────────────────────────────────────────────┤
│   将来: services/ (ビジネスロジック)                         │
├─────────────────────────────────────────────────────────────┤
│   clients/                                                   │
│   └── edinet_client.py  ← 今回実装                          │
├─────────────────────────────────────────────────────────────┤
│   core/                                                      │
│   ├── config.py         ← 今回実装                          │
│   ├── exceptions.py     ← 今回実装                          │
│   └── types.py          ← 今回実装                          │
├─────────────────────────────────────────────────────────────┤
│   schemas/                                                   │
│   └── edinet_schemas.py ← 今回実装                          │
└─────────────────────────────────────────────────────────────┘
```

## コンポーネント設計

### 1. EDINETClient (clients/edinet_client.py)

**責務**:
- EDINET APIとのHTTP通信
- 書類一覧の取得（メタデータ/詳細）
- 書類ファイルのダウンロード（XBRL/PDF/CSV）
- リトライ処理の実行

**実装の要点**:
- httpxを使用した非同期HTTP通信
- tenacityを使用した指数バックオフリトライ
- セッション管理（接続の再利用）
- タイムアウト設定（書類一覧: 30秒、ダウンロード: 60秒）

**クラス設計**:
```python
class EDINETClient:
    def __init__(self, config: EDINETConfig) -> None: ...

    async def get_document_list(
        self, date: date, include_details: bool = True
    ) -> DocumentListResponse: ...

    async def download_document(
        self, doc_id: str, doc_type: DocumentDownloadType, save_path: Path
    ) -> Path: ...

    async def close(self) -> None: ...
```

### 2. EDINETConfig (core/config.py)

**責務**:
- APIキーの管理
- ベースURLの管理
- タイムアウト設定の管理

**実装の要点**:
- pydantic-settingsを使用した環境変数の読み込み
- デフォルト値の定義
- バリデーション

**クラス設計**:
```python
class EDINETConfig(BaseSettings):
    api_key: str = Field(..., alias="EDINET_API_KEY")
    base_url: str = "https://api.edinet-fsa.go.jp/api/v2"
    timeout_list: int = 30
    timeout_download: int = 60

    model_config = SettingsConfigDict(env_file=".env")
```

### 3. カスタム例外 (core/exceptions.py)

**責務**:
- EDINET API固有のエラー表現
- エラー情報の構造化

**実装の要点**:
- dataclassベースの例外クラス
- ステータスコード、メッセージ、エンドポイントの保持

**クラス設計**:
```python
class CompanyResearchAgentError(Exception): ...

@dataclass
class EDINETAPIError(CompanyResearchAgentError):
    status_code: int
    message: str
    endpoint: str

class EDINETAuthenticationError(EDINETAPIError): ...  # 401
class EDINETNotFoundError(EDINETAPIError): ...       # 404
class EDINETServerError(EDINETAPIError): ...         # 500
```

### 4. Pydanticスキーマ (schemas/edinet_schemas.py)

**責務**:
- APIレスポンスのバリデーション
- 型安全なデータアクセス

**実装の要点**:
- EDINET APIレスポンス構造に合わせたスキーマ定義
- Optional/Noneの適切な処理
- フラグ値（xbrl_flag等）のbool変換

**主要スキーマ**:
```python
class DocumentMetadata(BaseModel):
    doc_id: str
    edinet_code: str
    sec_code: str | None
    filer_name: str
    doc_type_code: str
    doc_description: str
    submit_datetime: str
    xbrl_flag: bool
    pdf_flag: bool
    csv_flag: bool

class DocumentListResponse(BaseModel):
    metadata: ResponseMetadata
    results: list[DocumentMetadata] | None
```

### 5. 型定義 (core/types.py)

**責務**:
- プロジェクト共通の型エイリアス定義

**実装の要点**:
- Literalを使用した厳密な型定義
- 再利用可能な型エイリアス

```python
type DocumentDownloadType = Literal[1, 2, 3, 4, 5]
# 1: XBRL(ZIP), 2: PDF, 3: 添付文書(ZIP), 4: 英文(ZIP), 5: CSV(ZIP)
```

## データフロー

### 書類一覧取得フロー
```
1. ユーザーが日付を指定してget_document_list()を呼び出す
2. EDINETClientがリクエストパラメータを構築
3. httpxで EDINET API /documents.json にGETリクエスト
4. レスポンスのContent-Typeを確認
5. JSONをパースしてDocumentListResponseに変換
6. metadata.statusを確認（200以外はエラー）
7. 結果を返却
```

### 書類ダウンロードフロー
```
1. ユーザーがdoc_id, doc_type, save_pathを指定してdownload_document()を呼び出す
2. EDINETClientがリクエストパラメータを構築
3. httpxで EDINET API /documents/{doc_id} にGETリクエスト
4. レスポンスのContent-Typeを確認
   - application/json → エラーレスポンス → 例外をスロー
   - それ以外 → バイナリデータ
5. ファイルをsave_pathに保存
6. 保存パスを返却
```

## エラーハンドリング戦略

### カスタムエラークラス

| クラス | HTTPステータス | 発生条件 |
|--------|---------------|----------|
| EDINETAuthenticationError | 401 | APIキーが無効 |
| EDINETNotFoundError | 404 | 書類が見つからない |
| EDINETServerError | 500 | サーバーエラー |
| EDINETAPIError | その他 | その他のAPIエラー |

### エラーハンドリングパターン

```python
# サーバーエラー（5xx）のみリトライ
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(EDINETServerError),
)
async def _request(self, ...): ...
```

### レスポンス判定ロジック

1. HTTPステータスコードをチェック
2. Content-Typeをチェック
   - `application/json`の場合はJSONパース
   - バイナリデータの場合はそのまま処理
3. JSONの場合、`metadata.status`をチェック
   - "200"以外は内部エラーとして処理

## テスト戦略

### ユニットテスト
- EDINETClient.get_document_list(): 正常系、エラー系
- EDINETClient.download_document(): 正常系、エラー系
- EDINETConfig: 環境変数読み込み
- レスポンスパース: スキーマバリデーション

### 統合テスト
- 実際のEDINET APIへの接続（CI環境では環境変数が設定されている場合のみ）
- モックサーバーを使用したE2Eフロー

### モック戦略
- httpxのレスポンスをモック
- respxライブラリを使用

## 依存ライブラリ

```toml
# pyproject.toml
[project]
dependencies = [
    "httpx>=0.28.0",
    "tenacity>=9.0.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
]

[project.optional-dependencies]
dev = [
    "respx>=0.22.0",  # httpxモック用
]
```

## ディレクトリ構造

```
src/company_research_agent/
├── __init__.py
├── clients/
│   ├── __init__.py
│   └── edinet_client.py      # EDINETクライアント
├── core/
│   ├── __init__.py
│   ├── config.py             # 設定管理
│   ├── exceptions.py         # カスタム例外
│   └── types.py              # 型定義
└── schemas/
    ├── __init__.py
    └── edinet_schemas.py     # Pydanticスキーマ

tests/
├── unit/
│   ├── clients/
│   │   └── test_edinet_client.py
│   ├── core/
│   │   ├── test_config.py
│   │   └── test_exceptions.py
│   └── schemas/
│       └── test_edinet_schemas.py
└── conftest.py               # 共通フィクスチャ
```

## 実装の順序

1. core/exceptions.py - カスタム例外クラス
2. core/types.py - 型定義
3. core/config.py - 設定管理
4. schemas/edinet_schemas.py - Pydanticスキーマ
5. clients/edinet_client.py - EDINETクライアント
6. tests/ - ユニットテスト

## セキュリティ考慮事項

- APIキーは環境変数で管理（ソースコードにハードコードしない）
- APIキーをログに出力しない
- HTTPS通信のみ（TLS 1.2以上）

## パフォーマンス考慮事項

- httpxのセッション（AsyncClient）を再利用
- 適切なタイムアウト設定
- リトライ間隔は指数バックオフ（4秒→8秒→16秒、最大60秒）

## 将来の拡張性

- 書類検索機能の追加（複数日付横断）
- キャッシュ機能の追加（EDINETコードリスト等）
- バッチダウンロード機能
- 並列ダウンロード対応
