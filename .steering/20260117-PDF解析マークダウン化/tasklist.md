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

## フェーズ1: 基盤整備

- [x] 型定義の追加（core/types.py）
  - [x] `ParseStrategy`型の追加

- [x] 例外クラスの追加（core/exceptions.py）
  - [x] `PDFParseError`クラスの追加

- [x] parsersパッケージの初期化
  - [x] `parsers/__init__.py`の作成

## フェーズ2: PDFParserの実装

- [x] データクラスの定義（pdf_parser.py）
  - [x] `PDFInfo`データクラスの作成
  - [x] `ParsedPDFContent`データクラスの作成

- [x] `PDFParser.get_info()`メソッドの実装
  - [x] pdfplumberを使ったメタデータ取得
  - [x] 目次抽出ロジック（_extract_toc_from_text）

- [x] `PDFParser.extract_text()`メソッドの実装
  - [x] ページ範囲指定のテキスト抽出

- [x] `PDFParser.to_markdown()`メソッドの実装
  - [x] auto戦略の実装（pymupdf4llm使用）
  - [x] pdfplumber戦略の実装
  - [x] pymupdf4llm戦略の実装

## フェーズ3: テストの作成

- [x] テストディレクトリ構造の作成
  - [x] `tests/unit/parsers/__init__.py`の作成

- [x] テスト用フィクスチャの準備
  - [x] conftest.pyへのPDFフィクスチャ追加

- [x] ユニットテストの作成（test_pdf_parser.py）
  - [x] `test_get_info_success`
  - [x] `test_get_info_file_not_found`
  - [x] `test_extract_text_success`
  - [x] `test_extract_text_with_page_range`
  - [x] `test_to_markdown_auto_strategy`
  - [x] `test_to_markdown_pdfplumber_strategy`
  - [x] `test_to_markdown_pymupdf4llm_strategy`

## フェーズ4: 品質チェックと修正

- [x] すべてのテストが通ることを確認
  - [x] `uv run pytest`

- [x] リントエラーがないことを確認
  - [x] `uv run ruff check .`

- [x] 型エラーがないことを確認
  - [x] `uv run mypy src/`

## フェーズ5: ドキュメント更新

- [x] 実装後の振り返り（このファイルの下部に記録）

---

## 実装後の振り返り

### 実装完了日
2026-01-17

### 計画と実績の差分

**計画と異なった点**:
- 計画通りに実装完了。大きな差異なし
- TYPE_CHECKINGブロックを使用した型ヒントの処理（pdfplumberの型が不完全なため）

**新たに必要になったタスク**:
- 追加テストケース（empty metadata、invalid page range、parse error）
- これらは堅牢性を高めるために実装中に追加

**技術的理由でスキップしたタスク**:
- なし（全タスク完了）

### 学んだこと

**技術的な学び**:
- pdfplumberとpymupdf4llmの使い分け（基本抽出 vs 構造保持マークダウン変換）
- Python 3.12+ の `type` エイリアス構文の活用
- モック対象の適切な指定（`pdfplumber.open` をパッチ）

**プロセス上の改善点**:
- tasklist.mdによる段階的なタスク管理が効果的だった
- フェーズ分けにより、基盤→実装→テスト→検証の流れが明確になった
- 既存パターン（EDINETClient）の調査により、一貫性のある実装ができた

### 次回への改善提案
- 段階的パース戦略（pdfplumber → pymupdf4llm → yomitoku → Gemini）の拡張時は、共通インターフェースを維持する
- 複雑なPDF（スキャン画像、複雑なレイアウト）への対応はyomitoku/Gemini統合時に検討
- テストフィクスチャの共通化により、将来の拡張が容易になる設計を維持

---

## フェーズ6: 受入条件の検証テスト（追加）

受入条件チェック（acceptance-check.md）で特定された不足項目を実装。

### P0: 日本語精度測定フレームワーク

- [x] 精度測定フレームワークの設計・実装（accuracy_benchmark.py）
  - [x] BenchmarkItem/BenchmarkResultデータクラスの作成
  - [x] AccuracyBenchmarkクラスの実装
  - [x] 日本語数値正規化（△/▲対応、単位処理）
  - [x] 値比較ロジック（許容誤差1%）
  - [x] レポート生成機能
  - [x] parsers/__init__.pyへのエクスポート追加

- [x] 精度測定フレームワークのユニットテスト
  - [x] test_accuracy_benchmark.py（44テスト）

### P0: パフォーマンステスト

- [x] パフォーマンステストの作成
  - [x] pytest-benchmarkまたはtime-based計測の実装
  - [x] 処理時間計測テストの追加（6テスト）

### P1: 表抽出テスト

- [x] マークダウンテーブル形式の具体的検証テスト
  - [x] 表構造の検証テスト追加（9テスト）

### P1: 統合テスト環境

- [x] 統合テストの構造設計
  - [x] tests/integration/ディレクトリ構造の作成
  - [x] 統合テスト用フィクスチャの実装
  - [x] test_pdf_parser_integration.py（7テスト、3パス、4スキップ）

### 品質チェック

- [x] 全テスト実行（uv run pytest）: 140 passed, 4 skipped
- [x] リントチェック（uv run ruff check .）: All checks passed
- [x] 型チェック（uv run mypy src/）: Success: no issues found in 21 source files

---

## 実装後の振り返り（フェーズ6）

### 実装完了日
2026-01-17

### 計画と実績の差分

**計画と異なった点**:
- pdfplumber戦略は表のマークダウン変換を行わないことが判明（テキスト抽出のみ）
- 表のマークダウン変換はpymupdf4llm戦略で対応
- 統合テストは実PDFなしでも一部テスト可能な設計に

**追加で実装したもの**:
- AccuracyBenchmarkクラス（精度測定フレームワーク）
- 日本語数値正規化（△/▲対応、単位処理）
- パフォーマンステスト（time-based計測）
- 統合テスト用フィクスチャとマーカー

### 学んだこと

**技術的な学び**:
- pdfplumber: extract_text()とextract_tables()は別機能
- pymupdf4llm: to_markdown()でテーブル構造を保持
- 日本語財務数値: △/▲は負数インジケーター

**テスト設計の学び**:
- 実データが不要なテストとスキップ可能なテストを分離
- モック戦略はライブラリの実際の動作に合わせる必要がある

### 次回への改善提案
- 実EDINET書類での統合テスト実行
- 精度測定結果のCI/CD連携
- パフォーマンス監視の定期実行
