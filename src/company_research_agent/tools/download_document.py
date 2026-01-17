"""書類ダウンロードツール."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool

from company_research_agent.clients.edinet_client import EDINETClient
from company_research_agent.core.config import EDINETConfig
from company_research_agent.core.download_path import build_download_path
from company_research_agent.core.progress import print_info, print_status, print_success
from company_research_agent.services.local_cache_service import LocalCacheService

logger = logging.getLogger(__name__)

# ダウンロード先ディレクトリ
DOWNLOAD_DIR = Path("downloads")

# ローカルキャッシュサービス
_cache_service = LocalCacheService(DOWNLOAD_DIR)


@tool
async def download_document(
    doc_id: Annotated[str, "書類ID（S100XXXX形式）"],
    sec_code: Annotated[str | None, "証券コード（5桁）"] = None,
    filer_name: Annotated[str | None, "企業名"] = None,
    doc_type_code: Annotated[str | None, "書類種別コード（120=有報等）"] = None,
    period_end: Annotated[str | None, "決算期末日（YYYY-MM-DD形式）"] = None,
) -> str:
    """EDINET書類をダウンロードし、ローカルパスを返す。

    指定された書類IDのPDFをダウンロードし、ローカルファイルとして保存する。
    既にダウンロード済みの場合は、既存のファイルパスを返す（キャッシュ優先）。

    ダウンロード先は階層構造:
    downloads/{sec_code}_{filer_name}/{doc_type_code}_{doc_type_name}/{YYYYMM}/{doc_id}.pdf

    Args:
        doc_id: 書類ID（S100XXXX形式）
        sec_code: 証券コード（5桁、例: "72030"）
        filer_name: 企業名（例: "トヨタ自動車株式会社"）
        doc_type_code: 書類種別コード（例: "120" = 有価証券報告書）
        period_end: 決算期末日（YYYY-MM-DD形式）

    Returns:
        ダウンロードしたPDFのローカルパス

    Example:
        >>> pdf_path = await download_document(
        ...     doc_id="S100ABCD",
        ...     sec_code="72030",
        ...     filer_name="トヨタ自動車株式会社",
        ...     doc_type_code="120",
        ...     period_end="2025-03-31",
        ... )
        >>> print(pdf_path)
        "downloads/72030_トヨタ自動車株式会社/120_有価証券報告書/202503/S100ABCD.pdf"
    """
    print_status(f"書類を検索中: {doc_id}")
    logger.info(f"Downloading document: {doc_id}")

    # 1. まずローカルキャッシュを検索
    cached = _cache_service.find_by_doc_id(doc_id)
    if cached and cached.file_path.exists():
        print_success(f"キャッシュから取得: {cached.file_path}")
        logger.info(f"Document found in cache: {cached.file_path}")
        return str(cached.file_path)

    # 2. キャッシュにない場合は階層パスを生成
    save_path = build_download_path(
        base_dir=DOWNLOAD_DIR,
        sec_code=sec_code,
        filer_name=filer_name,
        doc_type_code=doc_type_code,
        period_end=period_end,
        doc_id=doc_id,
    )

    # 3. パスが既に存在する場合はスキップ
    if save_path.exists():
        print_success(f"ダウンロード済み: {save_path}")
        logger.info(f"Document already exists: {save_path}")
        return str(save_path)

    # 4. EDINET APIからダウンロード
    print_status(f"EDINETからダウンロード中: {doc_id}")
    print_info(f"保存先: {save_path}")

    config = EDINETConfig()  # type: ignore[call-arg]
    async with EDINETClient(config) as client:
        result_path = await client.download_document(doc_id, 2, save_path)

    print_success(f"ダウンロード完了: {result_path}")
    logger.info(f"Document downloaded: {result_path}")
    return str(result_path)
