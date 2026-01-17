# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

### 必須ルール
- **全てのタスクを`[x]`にすること**
- 「時間の都合により別タスクとして実施予定」は禁止
- 「実装が複雑すぎるため後回し」は禁止
- 未完了タスク（`[ ]`）を残したまま作業を終了しない

### 実装可能なタスクのみを計画
- 計画段階で「実装可能なタスク」のみをリストアップ
- 「将来やるかもしれないタスク」は含めない
- 「検討中のタスク」は含めない

### タスクスキップが許可される唯一のケース
以下の技術的理由に該当する場合のみスキップ可能:
- 実装方針の変更により、機能自体が不要になった
- アーキテクチャ変更により、別の実装方法に置き換わった
- 依存関係の変更により、タスクが実行不可能になった

スキップ時は必ず理由を明記:
```markdown
- [x] ~~タスク名~~（実装方針変更により不要: 具体的な技術的理由）
```

### タスクが大きすぎる場合
- タスクを小さなサブタスクに分割
- 分割したサブタスクをこのファイルに追加
- サブタスクを1つずつ完了させる

---

## フェーズ1: スキーマとサービス基盤

- [x] `DocumentFilter` データクラスを作成
  - [x] `src/company_research_agent/schemas/document_filter.py` を新規作成
  - [x] dataclassとして定義（edinet_code, sec_code, company_name, doc_type_codes, start_date, end_date）
  - [x] `schemas/__init__.py` にエクスポートを追加

- [x] `services/` ディレクトリを作成
  - [x] `src/company_research_agent/services/__init__.py` を新規作成
  - [x] `src/company_research_agent/services/edinet_document_service.py` を新規作成（スケルトン）

## フェーズ2: サービス実装

- [x] `EDINETDocumentService` クラスを実装
  - [x] コンストラクタ（EDINETClientを依存性注入）
  - [x] `_filter_by_sec_code()` メソッドを実装
  - [x] `_filter_by_edinet_code()` メソッドを実装
  - [x] `_filter_by_company_name()` メソッドを実装（部分一致）
  - [x] `_filter_by_doc_type_codes()` メソッドを実装
  - [x] `_apply_filters()` メソッドを実装（複合フィルタ適用）
  - [x] `search_documents()` メソッドを実装（期間ループ + フィルタ）

## フェーズ3: テスト実装

- [x] テスト用ディレクトリを作成
  - [x] `tests/unit/services/` ディレクトリを作成

- [x] ユニットテストを実装
  - [x] `tests/unit/services/test_edinet_document_service.py` を新規作成
  - [x] テスト用フィクスチャ（モックEDINETClient、サンプルDocumentMetadata）を作成
  - [x] `test_search_by_sec_code_returns_filtered_results` を実装
  - [x] `test_search_by_edinet_code_returns_filtered_results` を実装
  - [x] `test_search_by_company_name_partial_match` を実装
  - [x] `test_search_by_doc_type_codes_single` を実装
  - [x] `test_search_by_doc_type_codes_multiple` を実装
  - [x] `test_search_by_date_range_multiple_days` を実装
  - [x] `test_search_with_combined_filters` を実装
  - [x] `test_search_with_no_results_returns_empty_list` を実装
  - [x] `test_search_with_empty_filter_returns_all` を実装

## フェーズ4: 品質チェックと修正

- [x] すべてのテストが通ることを確認
  - [x] `uv run pytest tests/unit/services/`
- [x] リントエラーがないことを確認
  - [x] `uv run ruff check src/company_research_agent/services/ src/company_research_agent/schemas/document_filter.py`
- [x] 型エラーがないことを確認
  - [x] `uv run mypy src/company_research_agent/services/ src/company_research_agent/schemas/document_filter.py`
- [x] 全体テストが通ることを確認
  - [x] `uv run pytest`

## フェーズ5: 仕上げ

- [x] `services/__init__.py` にエクスポートを追加
- [x] 実装後の振り返り（このファイルの下部に記録）

---

## 実装後の振り返り

### 実装完了日
2026-01-17

### 計画と実績の差分

**計画と異なった点**:
- 検証フェーズで指摘された改善点を対応:
  - テストコードの型アノテーション修正（フラグフィールドのbool型、Noneチェック追加）
  - サービスのエラーハンドリング強化（EDINETAPIError対応、ロギング追加）

**新たに必要になったタスク**:
- 検証結果に基づく改善対応（実装検証サブエージェントにて検出）

**技術的理由でスキップしたタスク**:
- なし

### 学んだこと

**技術的な学び**:
- EDINETAPIは日付単位でしか検索できないため、サービス層で期間ループとクライアントサイドフィルタリングを実装する設計が有効
- dataclassをフィルタ条件に使用し、Pydantic BaseModelはAPIレスポンスに使用する使い分けが明確になった
- AsyncMockを使用したサービス層のユニットテストパターンを確立

**プロセス上の改善点**:
- 既存のテストパターン（conftest.py、test_edinet_client.py）を参考にすることで、一貫性のあるテストを効率的に作成できた
- タスクリストを細かく分割することで進捗管理がしやすかった

### 次回への改善提案
- 受入条件5-6（ダウンロード、リトライ）は既に実装済みだったので、事前の実装調査が重要
- 入力バリデーション機能の追加を検討（start_date > end_dateのチェックなど）
- 大きな日付範囲でのパフォーマンス最適化を検討（並列処理、セマフォによるレート制限）
- 統合テストの追加を検討（実際のAPIとの連携テスト）
