# Company Research Agent

AI-powered Corporate Research Agent - 企業情報収集・分析エージェント

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

### 動作確認

```bash
# .envファイルにEDINET_API_KEYを設定（初回のみ）
cp .env.example .env
# .envファイルを編集してEDINET_API_KEYを設定

# 動作確認スクリプトを実行（.envから自動読み込み）
uv run python scripts/test_edinet_api.py

# 特定の日付を指定
uv run python scripts/test_edinet_api.py --date 2024-06-28

# PDFダウンロードも実行
uv run python scripts/test_edinet_api.py --download

# 有価証券報告書の表示件数を指定（デフォルト: 5件）
uv run python scripts/test_edinet_api.py --limit 10

# 有価証券報告書を全件表示
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
