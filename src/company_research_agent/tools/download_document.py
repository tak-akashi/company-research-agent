"""書類ダウンロードツール."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool

from company_research_agent.clients.edinet_client import EDINETClient
from company_research_agent.core.config import EDINETConfig

logger = logging.getLogger(__name__)

# ダウンロード先ディレクトリ
DOWNLOAD_DIR = Path("downloads/pdfs")


@tool
async def download_document(
    doc_id: Annotated[str, "書類ID（S100XXXX形式）"],
) -> str:
    """EDINET書類をダウンロードし、ローカルパスを返す。

    指定された書類IDのPDFをダウンロードし、ローカルファイルとして保存する。
    既にダウンロード済みの場合は、既存のファイルパスを返す。

    Args:
        doc_id: 書類ID（S100XXXX形式）

    Returns:
        ダウンロードしたPDFのローカルパス

    Example:
        >>> pdf_path = await download_document("S100ABCD")
        >>> print(pdf_path)
        "downloads/pdfs/S100ABCD.pdf"
    """
    logger.info(f"Downloading document: {doc_id}")

    # 保存先パスを生成
    save_path = DOWNLOAD_DIR / f"{doc_id}.pdf"

    # 既にダウンロード済みの場合はスキップ
    if save_path.exists():
        logger.info(f"Document already exists: {save_path}")
        return str(save_path)

    # PDF形式でダウンロード（type=2）
    config = EDINETConfig()  # type: ignore[call-arg]
    async with EDINETClient(config) as client:
        result_path = await client.download_document(doc_id, 2, save_path)

    logger.info(f"Document downloaded: {result_path}")
    return str(result_path)
