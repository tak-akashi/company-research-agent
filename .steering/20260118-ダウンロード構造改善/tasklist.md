# タスクリスト: ダウンロード構造改善

## Phase 1: ログ機能改善

- [ ] `pyproject.toml` に `rich` 依存関係追加
- [ ] `core/logging.py` 作成 - ログ設定の集中管理
- [ ] `core/progress.py` 作成 - richベースの進捗表示ユーティリティ
- [ ] `core/config.py` に LoggingConfig 追加
- [ ] `__init__.py` でログ初期化呼び出し

## Phase 2: フォルダ構造変更

- [ ] `core/doc_type_mapping.py` 作成 - 書類種別コードマッピング
- [ ] `core/download_path.py` 作成 - パス生成ユーティリティ
- [ ] ユニットテスト作成 (`tests/unit/core/test_download_path.py`)

## Phase 3: キャッシュ検索機能

- [ ] `schemas/cache_schemas.py` 作成 - CachedDocumentInfo
- [ ] `services/local_cache_service.py` 作成 - キャッシュ検索サービス
- [ ] ユニットテスト作成 (`tests/unit/services/test_local_cache_service.py`)

## Phase 4: ツール更新

- [ ] `tools/download_document.py` 更新
  - [ ] DocumentMetadata引数追加
  - [ ] キャッシュ優先検索ロジック
  - [ ] 階層パスでの保存
  - [ ] 進捗表示追加
- [ ] `tools/search_documents.py` に進捗表示追加
- [ ] `tools/search_company.py` に進捗表示追加

## Phase 5: 統合・検証

- [ ] 全体テスト実行 (`uv run pytest`)
- [ ] 実際のダウンロードで動作確認
- [ ] ログ出力の確認

---

## 完了条件

1. ダウンロードしたファイルが階層構造で保存される
2. 既存キャッシュがある場合はEDINET API呼び出しがスキップされる
3. 処理中に進捗メッセージがコンソールに表示される
