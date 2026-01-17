# 要件定義書

## 概要

LLM分析機能およびPDF解析（ビジョン機能）を複数プロバイダー対応にし、環境変数で切り替え可能にする。

## 背景

現在の実装はGemini 2.5 Flash固定であり、以下の課題がある：
- 他のLLMモデル（Claude、GPT-4o等）との比較検証ができない
- ローカルLLM（Ollama）での動作確認ができない
- プロバイダー障害時の代替手段がない

## 機能要件

### FR-1: LLMプロバイダーの切り替え

| ID | 要件 | 優先度 |
|----|------|--------|
| FR-1.1 | 環境変数`LLM_PROVIDER`でテキスト分析用プロバイダーを切り替え可能 | 必須 |
| FR-1.2 | 環境変数`LLM_VISION_PROVIDER`でビジョン用プロバイダーを個別指定可能 | 必須 |
| FR-1.3 | 環境変数`LLM_MODEL`でモデル名を指定可能 | 必須 |
| FR-1.4 | プロバイダー未指定時はGoogleをデフォルトとする | 必須 |

### FR-2: 対応プロバイダー

| ID | プロバイダー | テキスト分析 | ビジョン | 備考 |
|----|-------------|-------------|---------|------|
| FR-2.1 | OpenAI | GPT-4o, GPT-5-mini等 | GPT-4o | langchain-openai |
| FR-2.2 | Google | Gemini 2.5 Flash/Pro | 同左 | langchain-google-genai |
| FR-2.3 | Anthropic | Claude Sonnet/Opus | 同左 | langchain-anthropic |
| FR-2.4 | Ollama | llama3.2, gpt-oss-20b等 | llava | langchain-ollama |

### FR-3: 設定項目

| 環境変数 | 説明 | デフォルト |
|---------|------|-----------|
| LLM_PROVIDER | テキスト分析用プロバイダー | google |
| LLM_MODEL | テキスト分析用モデル | プロバイダー依存 |
| LLM_VISION_PROVIDER | ビジョン用プロバイダー | LLM_PROVIDERと同じ |
| LLM_VISION_MODEL | ビジョン用モデル | プロバイダー依存 |
| LLM_TIMEOUT | タイムアウト秒数 | 120 |
| LLM_MAX_RETRIES | 最大リトライ回数 | 3 |
| LLM_RPM_LIMIT | レート制限（RPM） | 60 |
| OPENAI_API_KEY | OpenAI APIキー | - |
| GOOGLE_API_KEY | Google APIキー | - |
| ANTHROPIC_API_KEY | Anthropic APIキー | - |
| OLLAMA_BASE_URL | Ollama URL | http://localhost:11434 |

### FR-4: 機能互換性

| ID | 要件 | 優先度 |
|----|------|--------|
| FR-4.1 | 既存の5つの分析ノードが全プロバイダーで動作する | 必須 |
| FR-4.2 | Structured Output（Pydanticスキーマ）が全プロバイダーで動作する | 必須 |
| FR-4.3 | PDF解析（ビジョン機能）が対応プロバイダーで動作する | 必須 |
| FR-4.4 | 既存のプロンプトを変更せずに動作する | 必須 |

## 非機能要件

### NFR-1: 保守性

| ID | 要件 |
|----|------|
| NFR-1.1 | 新規プロバイダーの追加が容易（プロバイダークラス追加のみ） |
| NFR-1.2 | プロバイダー固有のロジックが抽象化されている |
| NFR-1.3 | 型ヒントによる静的型チェックが可能 |

### NFR-2: パフォーマンス

| ID | 要件 |
|----|------|
| NFR-2.1 | プロバイダー切り替えによるオーバーヘッドが最小限 |
| NFR-2.2 | モデルインスタンスの遅延初期化・キャッシュ |

### NFR-3: エラーハンドリング

| ID | 要件 |
|----|------|
| NFR-3.1 | APIキー未設定時に明確なエラーメッセージ |
| NFR-3.2 | プロバイダー固有のエラーを統一エラークラスでラップ |
| NFR-3.3 | ビジョン非対応プロバイダー/モデルでの明確なエラー |

## 制約事項

- LangChainのラッパーライブラリを使用する
- 既存のワークフロー構造（LangGraph）を維持する
- 既存のテストが引き続きパスする

## 受入条件

1. 環境変数`LLM_PROVIDER=google`で既存と同等の動作
2. 環境変数`LLM_PROVIDER=openai`でOpenAI GPT-4oでの分析が動作
3. 環境変数`LLM_PROVIDER=anthropic`でClaude Sonnetでの分析が動作
4. 環境変数`LLM_PROVIDER=ollama`でローカルモデルでの分析が動作
5. ビジョン機能が各プロバイダーで動作
6. 既存のE2Eテストがパス
7. 型チェック（mypy）がパス
