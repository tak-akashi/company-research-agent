# 受入条件チェック結果

## 機能: EDINET API連携
## 日時: 2026-01-17
## 保存先: .steering/20260116-EDINET-API連携/acceptance-check.md

---

### カバレッジサマリ

| # | 受入条件 | 実装 | テスト | 状態 |
|---|---------|------|-------|------|
| 1 | 企業コード（証券コード/EDINETコード）で書類を検索できる | ❌ | ❌ | 未実装 |
| 2 | 企業名（部分一致）で書類を検索できる | ❌ | ❌ | 未実装 |
| 3 | 期間を指定して検索結果を絞り込める | ❌ | ⚠️ | 未実装 |
| 4 | 書類種別でフィルタリングできる | ⚠️ | ❌ | 部分的 |
| 5 | PDF/XBRLファイルをダウンロードできる | ✅ | ✅ | **完了** |
| 6 | APIレート制限に対応したリトライ機構を持つ | ✅ | ✅ | **完了** |

**全体カバレッジ: 2/6 (33%)**

---

### 検証詳細

#### 条件1: 企業コード（証券コード/EDINETコード）で書類を検索できる

- **実装**: ❌ 未実装
  - EDINETClient (`clients/edinet_client.py`) は日付(date)パラメータのみでAPIを呼び出し
  - EDINET APIは日付単位でしか検索できない仕様のため、サービスレイヤーでのフィルタリングが必要
- **テスト**: ❌ なし
- **検証方法**: 7203(トヨタ)、9984(ソフトバンクG)、6758(ソニー)で書類一覧を取得

**必要な実装**:
- `services/edinet_service.py` に `search_by_sec_code()` メソッドを追加
- 日付範囲で書類を取得後、`sec_code` フィールドでフィルタリング

---

#### 条件2: 企業名（部分一致）で書類を検索できる

- **実装**: ❌ 未実装
  - スキーマに `filer_name` フィールドは存在 (`schemas/edinet_schemas.py:91`)
  - フィルタリングロジックは未実装
- **テスト**: ❌ なし
- **検証方法**: 「トヨタ」「ソフトバンク」で部分一致検索、関連企業が複数ヒット

**必要な実装**:
- `services/edinet_service.py` に `search_by_company_name()` メソッドを追加
- `filer_name` フィールドで部分一致検索

---

#### 条件3: 期間を指定して検索結果を絞り込める

- **実装**: ❌ 未実装
  - EDINET APIは1日単位でしかデータを返さない（API仕様の制限）
  - `get_document_list()` は `target_date: date` のみサポート
  - 期間検索には複数日付のループ処理と結果集約が必要
- **テスト**: ⚠️ 部分的
  - `test_get_document_list_success` (`tests/unit/clients/test_edinet_client.py:62-77`) - 1日単位のみ
- **検証方法**: 2023-01-01〜2024-12-31で指定期間内の書類のみ返却

**必要な実装**:
- `services/edinet_service.py` に `search_by_period()` メソッドを追加
- 営業日単位でループし、結果を集約

---

#### 条件4: 書類種別（有価証券報告書、四半期報告書、臨時報告書）でフィルタリングできる

- **実装**: ⚠️ 部分的
  - スキーマに `doc_type_code` フィールドが定義 (`schemas/edinet_schemas.py:95`)
  - フィルタリングロジックは未実装
  - 書類種別コード: 120(有報), 140(四半期), 180(臨時報告) - `docs/research/edinet-api-specification.md:584-598`
- **テスト**: ❌ なし
- **検証方法**: ordinance_code=010で有価証券報告書のみフィルタ

**必要な実装**:
- `services/edinet_service.py` に `filter_by_doc_type()` メソッドを追加
- `doc_type_code` フィールドでフィルタリング

---

#### 条件5: PDF/XBRLファイルをダウンロードできる

- **実装**: ✅ 完了
  - `clients/edinet_client.py:278-331` - `download_document()` メソッド
  - 5形式対応: XBRL(ZIP), PDF, 添付文書, 英文, CSV
  - 親ディレクトリ自動作成、バイナリ保存
- **テスト**: ✅ 完全カバー (6テスト)
  - `test_download_document_pdf_success` (L199-221)
  - `test_download_document_zip_success` (L224-246) - XBRL
  - `test_download_document_creates_parent_dirs` (L249-269)
  - `test_download_document_401_error` (L272-289)
  - `test_download_document_404_error` (L292-309)
  - `test_download_document_json_error_response` (L312-340)
- **検証方法**: 3社の最新有報でPDF/XBRL両方ダウンロード成功

---

#### 条件6: APIレート制限に対応したリトライ機構を持つ

- **実装**: ✅ 完了
  - `clients/edinet_client.py:226-230, 272-276` - `@retry` デコレーター
  - tenacityライブラリ使用
  - 指数バックオフ: min=4秒, max=60秒
  - 最大3回リトライ
  - EDINETServerError (5xx) のみリトライ対象
- **テスト**: ✅ 完全カバー (3テスト)
  - `test_get_document_list_500_error_triggers_retry` (L157-171)
  - `test_get_document_list_500_error_max_retries` (L174-191)
  - `test_download_document_retry_on_500` (L343-360)
- **検証方法**: 意図的にレート制限を発生させ、指数バックオフで最大3回リトライ

---

### 実装済みコンポーネント

```
clients/edinet_client.py
├── EDINETClient クラス
│   ├── get_document_list()  - 日付指定で書類一覧取得
│   ├── download_document()  - 書類ダウンロード（5形式）
│   └── @retry デコレーター  - リトライ機構

schemas/edinet_schemas.py
├── DocumentMetadata      - 書類メタデータ（53フィールド）
├── DocumentListResponse  - APIレスポンス構造
└── フラグ値の自動変換

core/exceptions.py
├── EDINETAPIError           - 基底例外
├── EDINETAuthenticationError - 401エラー
├── EDINETNotFoundError      - 404エラー
└── EDINETServerError        - 5xxエラー（リトライ対象）

core/config.py
└── EDINETConfig - API設定（キー、URL、タイムアウト）
```

---

### 不足項目

1. **サービスレイヤー未実装** - `services/edinet_service.py` が存在しない
   - 企業コード検索機能
   - 企業名検索機能
   - 期間指定検索機能
   - 書類種別フィルタリング機能

2. **テスト不足**
   - 検索機能のユニットテスト（実装後に追加必要）
   - 統合テスト/E2Eテストが存在しない

3. **API層未実装** - `api/` ディレクトリにEDINET関連エンドポイントなし

---

### PRD検証方法との対応

| 検証項目 | テストデータ | 合格基準 | 現状 |
|---------|------------|---------|------|
| 企業コード検索 | 7203, 9984, 6758 | 3社全て書類一覧を取得 | ❌ 未実装 |
| 企業名検索 | 「トヨタ」「ソフトバンク」 | 関連企業が複数ヒット | ❌ 未実装 |
| 期間指定 | 2023-01-01〜2024-12-31 | 指定期間内の書類のみ返却 | ❌ 未実装 |
| 書類種別フィルタ | 有価証券報告書のみ | ordinance_code=010で正しくフィルタ | ❌ 未実装 |
| ファイルダウンロード | 3社の最新有報 | PDF/XBRL両方ダウンロード成功 | ✅ 完了 |
| リトライ機構 | レート制限発生 | 指数バックオフで最大3回リトライ | ✅ 完了 |

---

### 次のアクション

#### 優先度 P0（必須）

- [ ] `services/edinet_service.py` を新規作成し、以下のメソッドを実装:
  - [ ] `search_by_sec_code()` - 証券コード検索
  - [ ] `search_by_edinet_code()` - EDINETコード検索
  - [ ] `search_by_company_name()` - 企業名部分一致検索
  - [ ] `search_by_period()` - 期間指定検索
  - [ ] `filter_by_doc_type()` - 書類種別フィルタリング

- [ ] 上記メソッドに対応するユニットテストを追加:
  - [ ] `tests/unit/services/test_edinet_service.py`

#### 優先度 P1（重要）

- [ ] 統合テストの追加:
  - [ ] `tests/integration/test_edinet_integration.py`
  - [ ] 実際のEDINET APIを使用した検証（モック不使用）

- [ ] E2Eテストの追加:
  - [ ] PRD検証方法に基づく10社テストデータでの検証

#### 優先度 P2（推奨）

- [ ] FastAPI エンドポイントの追加 (`api/routers/edinet.py`)
- [ ] OpenAPI仕様の自動生成確認

---

### 参考ドキュメント

- PRD: `docs/product-requirements.md` L80-102
- EDINET API仕様: `docs/research/edinet-api-specification.md`
- 機能設計書: `docs/functional-design.md` L295-300
