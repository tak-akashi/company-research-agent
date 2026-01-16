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

## フェーズ1: 基盤実装（core/）

- [x] pyproject.tomlに依存ライブラリを追加
  - [x] httpx>=0.28.0
  - [x] tenacity>=9.0.0
  - [x] pydantic>=2.10.0
  - [x] pydantic-settings>=2.7.0
  - [x] devにrespx>=0.22.0を追加

- [x] ディレクトリ構造を作成
  - [x] src/company_research_agent/core/ ディレクトリ作成
  - [x] src/company_research_agent/clients/ ディレクトリ作成
  - [x] src/company_research_agent/schemas/ ディレクトリ作成
  - [x] 各ディレクトリに__init__.pyを作成

- [x] core/exceptions.pyを実装
  - [x] CompanyResearchAgentError基底クラス
  - [x] EDINETAPIErrorクラス（status_code, message, endpoint）
  - [x] EDINETAuthenticationError（401）
  - [x] EDINETNotFoundError（404）
  - [x] EDINETServerError（500）

- [x] core/types.pyを実装
  - [x] DocumentDownloadType型エイリアス（Literal[1, 2, 3, 4, 5]）

- [x] core/config.pyを実装
  - [x] EDINETConfigクラス（pydantic-settings使用）
  - [x] api_key（環境変数EDINET_API_KEY）
  - [x] base_url（デフォルト値）
  - [x] timeout_list, timeout_download

## フェーズ2: スキーマ実装（schemas/）

- [x] schemas/edinet_schemas.pyを実装
  - [x] RequestParameterスキーマ
  - [x] ResultSetスキーマ
  - [x] ResponseMetadataスキーマ
  - [x] DocumentMetadataスキーマ（全フィールド対応）
  - [x] DocumentListResponseスキーマ
  - [x] フラグ値のbool変換（validator）

## フェーズ3: クライアント実装（clients/）

- [x] clients/edinet_client.pyを実装
  - [x] EDINETClientクラスの基本構造
  - [x] __init__（AsyncClient初期化）
  - [x] close（リソース解放）
  - [x] __aenter__, __aexit__（コンテキストマネージャ）

- [x] get_document_listメソッドを実装
  - [x] リクエストパラメータ構築
  - [x] API呼び出し
  - [x] レスポンスパース
  - [x] エラーハンドリング

- [x] download_documentメソッドを実装
  - [x] リクエストパラメータ構築
  - [x] API呼び出し
  - [x] Content-Type判定
  - [x] ファイル保存
  - [x] エラーハンドリング

- [x] リトライ処理を実装
  - [x] tenacityデコレータ適用
  - [x] 指数バックオフ設定
  - [x] EDINETServerErrorのみリトライ

## フェーズ4: テスト実装

- [x] tests/conftest.pyを作成
  - [x] 共通フィクスチャ定義

- [x] tests/unit/core/test_exceptions.pyを実装
  - [x] 各例外クラスのテスト

- [x] tests/unit/core/test_config.pyを実装
  - [x] 環境変数読み込みテスト
  - [x] デフォルト値テスト

- [x] tests/unit/schemas/test_edinet_schemas.pyを実装
  - [x] DocumentMetadataパーステスト
  - [x] DocumentListResponseパーステスト
  - [x] フラグ変換テスト

- [x] tests/unit/clients/test_edinet_client.pyを実装
  - [x] get_document_list正常系テスト
  - [x] get_document_listエラー系テスト
  - [x] download_document正常系テスト
  - [x] download_documentエラー系テスト
  - [x] リトライ処理テスト

## フェーズ5: 品質チェックと修正

- [x] すべてのテストが通ることを確認
  - [x] `uv run pytest`
- [x] リントエラーがないことを確認
  - [x] `uv run ruff check .`
- [x] 型エラーがないことを確認
  - [x] `uv run mypy src/`

## フェーズ6: ドキュメント更新

- [x] .env.exampleを作成（EDINET_API_KEY）
- [x] 動作確認スクリプトを作成（scripts/test_edinet_api.py）
- [x] README.mdを更新（使用例、動作確認方法）
- [x] 実装後の振り返り（このファイルの下部に記録）

---

## 実装後の振り返り

### 実装完了日
2026-01-16

### 計画と実績の差分

**計画と異なった点**:
- pyproject.tomlのhatch設定でpackages指定を修正（`["src"]`から`["src/company_research_agent", "src/mcp_servers"]`へ）
- pydantic-settingsのpopulate_by_name=True設定が必要だった（aliasと直接の属性名の両方で値を受け取るため）
- mypy設定にmypy_path、packages、explicit_package_basesを追加（src layoutでの型チェック対応）
- py.typedマーカーファイルの作成が必要だった

**新たに必要になったタスク**:
- src/company_research_agent/__init__.pyの作成（パッケージとして認識させるため）
- テストディレクトリ構造の作成（tests/unit/core/, tests/unit/clients/, tests/unit/schemas/）
- 動作確認スクリプトの作成（scripts/test_edinet_api.py）- ユーザーからの追加要望
- README.md更新 - テンプレートには含まれていたが、tasklist.md作成時に漏れていた

**技術的理由でスキップしたタスク**:
- なし（全タスク完了）

### 学んだこと

**技術的な学び**:
- pydantic-settingsでaliasを使う場合、populate_by_name=Trueが必要
- httpxのAsyncClientはbase_urlとparamsをコンストラクタで設定可能
- respxはhttpxの優秀なモックライブラリで、side_effectでリトライテストが書きやすい
- tenacityのretryデコレータは例外タイプを指定してリトライ可能
- EDINET APIはHTTP 200を返しつつJSONのmetadata.statusで内部エラーを通知するパターンがある

**プロセス上の改善点**:
- tasklist.mdの詳細なタスク分解により、実装漏れがなかった
- フェーズごとの実装でテストを最後にまとめて書くより、コンポーネントごとにテストを書く方が効率的
- 品質チェック（pytest, ruff, mypy）を最後にまとめて実行することで問題を一括修正できた

### 次回への改善提案
- パッケージ設定（pyproject.toml）のテンプレートを用意しておく
- テストディレクトリ構造をタスクリストに明示的に含める
- py.typedマーカーの作成をデフォルトタスクに含める
- pydantic-settingsの設定パターンを文書化しておく
- テンプレートのタスクを漏らさないよう、tasklist.md作成時にテンプレートを参照する
- 動作確認スクリプトは機能実装後に作成すると有用（テンプレートに追加済み）
