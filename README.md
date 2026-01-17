# Company Research Agent

AI-powered Corporate Research Agent - 企業情報収集・分析エージェント
EDINETや企業ホームページを検索してその結果をまとめるエージェントの構築プロジェクト（構築中）

## セットアップ

```bash
# 依存関係のインストール
uv sync --dev

# 環境変数の設定
cp .env.example .env
# .envファイルを編集して以下を設定:
# - EDINET_API_KEY: EDINET APIキー
# - LLM_PROVIDER: LLMプロバイダー（google/openai/anthropic/ollama）
# - 対応するAPIキー（GOOGLE_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY）
```

## EDINET API連携

金融庁のEDINET APIを使用して、有価証券報告書等の開示書類を取得できます。

### APIキーの取得

1. [EDINET API](https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1)にアクセス
2. アカウント登録・APIキー発行

### 使用例

```python
import asyncio
from datetime import date
from pathlib import Path

from company_research_agent.clients.edinet_client import EDINETClient
from company_research_agent.core.config import EDINETConfig

async def main():
    config = EDINETConfig()  # 環境変数EDINET_API_KEYから自動読み込み

    async with EDINETClient(config) as client:
        # 書類一覧を取得
        docs = await client.get_document_list(date(2024, 6, 28))
        print(f"書類数: {docs.metadata.resultset.count}")

        # 有価証券報告書のPDFをダウンロード（最大10件）
        download_count = 0
        for doc in docs.results or []:
            if doc.doc_type_code == "120" and doc.pdf_flag:
                await client.download_document(
                    doc.doc_id, 2, Path(f"downloads/{doc.doc_id}.pdf")
                )
                download_count += 1
                if download_count >= 10:
                    break

asyncio.run(main())
```

### 書類検索サービスの使用例

`EDINETDocumentService`を使用すると、証券コード・会社名・書類種別などで柔軟に検索できます。

```python
import asyncio
from datetime import date

from company_research_agent.clients.edinet_client import EDINETClient
from company_research_agent.core.config import EDINETConfig
from company_research_agent.schemas.document_filter import DocumentFilter
from company_research_agent.services import EDINETDocumentService

async def main():
    config = EDINETConfig()

    async with EDINETClient(config) as client:
        service = EDINETDocumentService(client)

        # 証券コードで検索（トヨタ自動車: 72030）
        filter = DocumentFilter(
            sec_code="72030",
            doc_type_codes=["120"],  # 有価証券報告書
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        docs = await service.search_documents(filter)
        print(f"トヨタの有価証券報告書: {len(docs)}件")

        # 会社名で部分一致検索
        filter = DocumentFilter(
            company_name="ソニー",
            start_date=date(2024, 6, 1),
            end_date=date(2024, 6, 30),
        )
        docs = await service.search_documents(filter)
        print(f"ソニー関連の書類: {len(docs)}件")

asyncio.run(main())
```

### 動作確認

```bash
# .envファイルにEDINET_API_KEYを設定（初回のみ）
cp .env.example .env
# .envファイルを編集してEDINET_API_KEYを設定

# 動作確認スクリプトを実行（.envから自動読み込み）
uv run python scripts/validate_edinet_api.py

# 特定の日付を指定
uv run python scripts/validate_edinet_api.py --date 2024-06-28

# 期間を指定して検索
uv run python scripts/validate_edinet_api.py --start-date 2024-06-01 --end-date 2024-06-30

# 証券コードで検索（トヨタ自動車）
uv run python scripts/validate_edinet_api.py --sec-code 72030 --start-date 2024-01-01

# 会社名で部分一致検索
uv run python scripts/validate_edinet_api.py --company-name ソニー --start-date 2024-06-01

# 書類種別を指定（有価証券報告書のみ）
uv run python scripts/validate_edinet_api.py --doc-types 120 --start-date 2024-06-01

# PDFダウンロードも実行
uv run python scripts/validate_edinet_api.py --download

# 表示件数を指定（0で全件表示）
uv run python scripts/validate_edinet_api.py --limit 0
```

## PDF解析

有価証券報告書等のPDFファイルからテキストを抽出し、マークダウン形式に変換できます。

### 解析戦略

| 戦略 | 説明 | コスト |
|------|------|--------|
| `auto` | 自動選択（pymupdf4llm → yomitoku → gemini） | - |
| `pdfplumber` | 基本テキスト抽出 | 無料 |
| `pymupdf4llm` | 構造保持マークダウン変換 | 無料 |
| `yomitoku` | 日本語OCR（複雑な表、スキャンPDF） | 無料 |
| `gemini` | LLMベース抽出（最終手段） | API課金 |

### 使用例

```python
from pathlib import Path

from company_research_agent.parsers import PDFParser

# PDFParserを初期化
parser = PDFParser()

# PDFのメタデータを取得
info = parser.get_info(Path("document.pdf"))
print(f"ページ数: {info.total_pages}")
print(f"目次: {info.table_of_contents}")

# マークダウン形式に変換（自動戦略）
result = parser.to_markdown(Path("document.pdf"), strategy="auto")
print(f"使用戦略: {result.strategy_used}")
print(result.text)

# 特定のページ範囲を抽出
result = parser.to_markdown(
    Path("document.pdf"),
    start_page=1,
    end_page=10,
    strategy="pymupdf4llm"
)
```

### Gemini APIを使用する場合

Gemini APIを最終手段として使用する場合は、`GeminiConfig`を渡します。

```python
from pathlib import Path

from company_research_agent.core.config import GeminiConfig
from company_research_agent.parsers import PDFParser

# Gemini設定（環境変数GOOGLE_API_KEYから自動読み込み）
gemini_config = GeminiConfig()

# Gemini対応のPDFParserを初期化
parser = PDFParser(gemini_config=gemini_config)

# 自動戦略（Geminiへのフォールバックあり）
result = parser.to_markdown(Path("document.pdf"), strategy="auto")

# 直接Geminiを使用
result = parser.to_markdown(Path("document.pdf"), strategy="gemini")
```

## LLMプロバイダー設定

複数のLLMプロバイダーを切り替えて使用できます。

### 対応プロバイダー

| プロバイダー | 環境変数 | デフォルトモデル | ビジョン対応 |
|-------------|---------|-----------------|-------------|
| Google | `GOOGLE_API_KEY` | gemini-2.5-flash-preview-05-20 | ✅ |
| OpenAI | `OPENAI_API_KEY` | gpt-4o | ✅ |
| Anthropic | `ANTHROPIC_API_KEY` | claude-sonnet-4-20250514 | ✅ |
| Ollama | `OLLAMA_BASE_URL` | llama3.2 | ✅（llava等） |

### 設定例

```bash
# .env ファイル

# プロバイダー選択（google / openai / anthropic / ollama）
LLM_PROVIDER=google

# モデル指定（オプション、省略時はデフォルト）
# LLM_MODEL=gemini-2.5-flash-preview-05-20

# ビジョン用プロバイダー（オプション、省略時はLLM_PROVIDERと同じ）
# LLM_VISION_PROVIDER=google
# LLM_VISION_MODEL=gemini-2.5-flash-preview-05-20

# APIキー（選択したプロバイダーに応じて設定）
GOOGLE_API_KEY=your-api-key
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# OLLAMA_BASE_URL=http://localhost:11434
```

### 使用例

```python
from company_research_agent.llm import get_default_provider, create_llm_provider
from company_research_agent.llm.config import LLMConfig
from company_research_agent.llm.types import LLMProviderType

# 環境変数から自動設定
provider = get_default_provider()
print(f"Provider: {provider.provider_name}, Model: {provider.model_name}")

# 明示的にプロバイダーを指定
import os
os.environ["LLM_PROVIDER"] = "anthropic"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."
config = LLMConfig()
provider = create_llm_provider(config)

# 構造化出力でLLM呼び出し
from pydantic import BaseModel

class Summary(BaseModel):
    title: str
    points: list[str]

result = await provider.ainvoke_structured("要約してください: ...", Summary)
print(result.title)
```

## MCP Server

PDF処理用のMCPサーバーを含みます。

```bash
uv run python -m src.mcp_servers.pdf_tools.server
```

## 開発

```bash
# pre-commit フックのインストール（初回のみ）
uv run pre-commit install

# テスト実行
uv run pytest

# 型チェック
uv run mypy

# Lint & フォーマット
uv run ruff check src/
uv run ruff format src/

# pre-commit 手動実行（全ファイル）
uv run pre-commit run --all-files
```

コミット時に自動で ruff, ruff-format, mypy が実行されます。
