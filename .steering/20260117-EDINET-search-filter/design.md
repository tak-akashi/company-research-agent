# 設計書

## アーキテクチャ概要

レイヤードアーキテクチャに従い、サービスレイヤーに検索・フィルタリング機能を追加する。

```
┌─────────────────────────────────────────────────────────┐
│   サービスレイヤー (services/)                            │
│   └─ EDINETDocumentService                              │
│       - search_documents()                              │
│       - _filter_by_sec_code()                           │
│       - _filter_by_edinet_code()                        │
│       - _filter_by_company_name()                       │
│       - _filter_by_doc_type()                           │
├─────────────────────────────────────────────────────────┤
│   クライアントレイヤー (clients/)                         │
│   └─ EDINETClient                                       │
│       - get_document_list() ← 既存                       │
│       - download_document() ← 既存                       │
├─────────────────────────────────────────────────────────┤
│   スキーマレイヤー (schemas/)                             │
│   └─ DocumentMetadata ← 既存                            │
│   └─ DocumentFilter ← 新規                              │
└─────────────────────────────────────────────────────────┘
```

## コンポーネント設計

### 1. DocumentFilter（データクラス）

**ファイル**: `src/company_research_agent/schemas/document_filter.py`

**責務**:
- 検索条件を保持するデータクラス
- 複合条件の指定に対応

**実装の要点**:
- `dataclass` を使用（内部ドメインモデル）
- 全フィールドはオプショナル
- 機能設計書の定義に準拠

```python
@dataclass
class DocumentFilter:
    """書類検索フィルタ"""
    edinet_code: str | None = None       # EDINETコード
    sec_code: str | None = None          # 証券コード
    company_name: str | None = None      # 企業名（部分一致）
    doc_type_codes: list[str] | None = None  # 書類種別コード
    start_date: date | None = None       # 期間（開始）
    end_date: date | None = None         # 期間（終了）
```

### 2. EDINETDocumentService（サービスクラス）

**ファイル**: `src/company_research_agent/services/edinet_document_service.py`

**責務**:
- 検索条件に基づく書類検索
- EDINETClientを使用したAPI呼び出し
- フィルタリングロジックの実装

**実装の要点**:
- EDINETClientを依存性注入
- 非同期メソッド（async/await）
- 複合フィルタリングの実装

```python
class EDINETDocumentService:
    def __init__(self, client: EDINETClient) -> None:
        self._client = client

    async def search_documents(
        self,
        filter: DocumentFilter,
    ) -> list[DocumentMetadata]:
        """書類を検索する（複数条件対応）"""
        ...
```

### 3. サービス層の__init__.py

**ファイル**: `src/company_research_agent/services/__init__.py`

**責務**:
- サービス層のエクスポート管理

## データフロー

### 検索処理フロー
```
1. ユーザーがDocumentFilterを指定してsearch_documents()を呼び出す
2. サービスがstart_date〜end_dateの期間をループ
3. 各日付でEDINETClient.get_document_list()を呼び出し
4. 取得した書類リストにフィルタリングを適用
5. 結果を集約して返却
```

### フィルタリング順序
```
1. 期間でループして書類を収集
2. sec_code / edinet_codeでフィルタ（完全一致）
3. company_nameでフィルタ（部分一致）
4. doc_type_codesでフィルタ（複数値のOR条件）
```

## エラーハンドリング戦略

### カスタムエラークラス

既存の例外クラスを継承して使用:
- `EDINETAPIError` - API呼び出しエラー
- `EDINETServerError` - サーバーエラー（リトライ対象）

### エラーハンドリングパターン

- API呼び出しエラーはそのまま上位に伝播
- 期間内の特定日付でエラーが発生した場合はログを記録し、他の日付は処理継続
- フィルタリングエラーは発生しない設計（入力検証はPydanticで実施）

## テスト戦略

### ユニットテスト

**ファイル**: `tests/unit/services/test_edinet_document_service.py`

- `TestSearchDocuments`
  - `test_search_by_sec_code_returns_filtered_results`
  - `test_search_by_edinet_code_returns_filtered_results`
  - `test_search_by_company_name_partial_match`
  - `test_search_by_doc_type_codes_single`
  - `test_search_by_doc_type_codes_multiple`
  - `test_search_by_date_range_multiple_days`
  - `test_search_with_combined_filters`
  - `test_search_with_no_results_returns_empty_list`
  - `test_search_with_empty_filter_returns_all`

### モック戦略
- `EDINETClient.get_document_list()` をモック
- 複数日付のレスポンスをシミュレート
- `respx` は不要（サービス層のテストはクライアントをモック）

## 依存ライブラリ

追加の依存関係なし（既存のライブラリで対応可能）

## ディレクトリ構造

```
src/company_research_agent/
├── services/                          # 新規ディレクトリ
│   ├── __init__.py                   # 新規
│   └── edinet_document_service.py    # 新規
├── schemas/
│   ├── __init__.py                   # 更新（エクスポート追加）
│   ├── edinet_schemas.py             # 既存
│   └── document_filter.py            # 新規
tests/
└── unit/
    └── services/                      # 新規ディレクトリ
        └── test_edinet_document_service.py  # 新規
```

## 実装の順序

1. `DocumentFilter` データクラスを作成
2. `services/` ディレクトリと `__init__.py` を作成
3. `EDINETDocumentService` のスケルトンを作成
4. フィルタリングメソッドを実装
5. `search_documents()` メソッドを実装
6. ユニットテストを作成
7. スキーマの `__init__.py` を更新

## セキュリティ考慮事項

- 入力検証はPydanticで実施（既存のDocumentFilterの型ヒントで対応）
- APIキーはEDINETClient内部で管理（サービス層からは参照しない）

## パフォーマンス考慮事項

- 期間が長い場合（例: 1年分）は多数のAPI呼び出しが発生
- EDINET APIのレート制限（60回/分）に注意
- 将来的にはキャッシュ機構の追加を検討（スコープ外）
- 非同期処理で並列呼び出しも検討可能（初期実装は逐次処理）

## 将来の拡張性

- キャッシュ機構の追加
- 並列処理による高速化
- REST APIエンドポイントの追加
- データベースとの連携
