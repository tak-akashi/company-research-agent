# Company Research Agent

AI-powered Corporate Research Agent - 企業情報収集・分析エージェント
EDINETや企業ホームページを検索してその結果をまとめるエージェントの構築プロジェクト（構築中）

## セットアップ

```bash
# 依存関係のインストール
uv sync --dev

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してEDINET_API_KEYを設定
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
uv run python scripts/test_edinet_api.py

# 特定の日付を指定
uv run python scripts/test_edinet_api.py --date 2024-06-28

# 期間を指定して検索
uv run python scripts/test_edinet_api.py --start-date 2024-06-01 --end-date 2024-06-30

# 証券コードで検索（トヨタ自動車）
uv run python scripts/test_edinet_api.py --sec-code 72030 --start-date 2024-01-01

# 会社名で部分一致検索
uv run python scripts/test_edinet_api.py --company-name ソニー --start-date 2024-06-01

# 書類種別を指定（有価証券報告書のみ）
uv run python scripts/test_edinet_api.py --doc-types 120 --start-date 2024-06-01

# PDFダウンロードも実行
uv run python scripts/test_edinet_api.py --download

# 表示件数を指定（0で全件表示）
uv run python scripts/test_edinet_api.py --limit 0
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
