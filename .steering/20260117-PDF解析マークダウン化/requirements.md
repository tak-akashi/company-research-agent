# 要求内容

## 概要

PDFファイルを解析してマークダウン形式に変換する機能を`src/company_research_agent/parsers/`に実装する。段階的な解析戦略（pdfplumber → pymupdf4llm）を採用し、将来的なyomitoku/Gemini APIへの拡張も考慮する。

## 背景

- EDINET/TDnetからダウンロードしたPDFの書類（有価証券報告書、決算短信等）を自動解析し、構造化された形式で利用可能にする必要がある
- 既存の`src/mcp_servers/pdf_tools/handlers.py`にMCPサーバー用の実装があるが、`company_research_agent`パッケージ内にビジネスロジックとして組み込む必要がある
- 段階的な解析戦略により、テキストPDFは軽量な処理で、複雑なPDFは高精度な処理で対応する

## 実装対象の機能

### 1. PDFパーサー基本機能

- PDFファイルのメタデータ取得（ページ数、サイズ、目次等）
- ページ範囲を指定したテキスト抽出
- マークダウン形式への変換（pymupdf4llm使用）

### 2. 段階的解析戦略

- `auto`モード: 自動的に最適な解析戦略を選択
- `pdfplumber`モード: 基本的なテキスト抽出
- `pymupdf4llm`モード: 構造を保持したマークダウン変換

### 3. エラーハンドリング

- カスタム例外クラス（PDFParseError）の定義
- 解析失敗時の適切なエラーメッセージ

## 受け入れ条件

### PDFパーサー基本機能
- [x] PDFファイルのパスを指定して、メタデータ（ページ数、ファイル名、サイズ）を取得できる
- [x] 開始・終了ページを指定してテキスト抽出できる
- [x] PDFをマークダウン形式に変換できる
- [x] 存在しないファイルを指定した場合、適切なエラーが発生する

### 段階的解析戦略
- [x] `ParseStrategy`型で解析戦略を指定できる
- [x] `auto`モードではpymupdf4llmでマークダウン変換を試みる
- [x] 各モードで期待される形式の出力が得られる

### テスト
- [x] ユニットテストがすべて通る
- [x] 型チェック（mypy）がエラーなく通る
- [x] リント（ruff）がエラーなく通る

## 成功指標

- PDFParserクラスが`docs/functional-design.md`のインターフェース定義と整合性を持つ
- 既存のコーディング規約・命名規則に準拠している
- テストカバレッジが80%以上

## スコープ外

以下はこのフェーズでは実装しません:

- yomitoku（日本語OCR）による高精度解析
- Gemini APIによるLLM解析（最終手段）
- 表データの構造化抽出（JSON形式への変換）
- データベースへの保存処理
- APIエンドポイントの追加

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書
- `docs/functional-design.md` - 機能設計書（PDFParserインターフェース定義）
- `docs/architecture.md` - アーキテクチャ設計書（PDF解析の段階的戦略）
- `docs/repository-structure.md` - リポジトリ構造定義書（parsers/の役割）
- `src/mcp_servers/pdf_tools/handlers.py` - 参考実装（MCPサーバー用）
