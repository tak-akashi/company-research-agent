"""PDF処理ハンドラー."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pdfplumber

if TYPE_CHECKING:
    PdfPlumberPDF = Any
else:
    PdfPlumberPDF = Any
import pymupdf4llm  # type: ignore[import-untyped]


def get_pdf_info(pdf_path: str) -> dict[str, Any]:
    """PDFのメタデータとページ情報を取得する.

    Args:
        pdf_path: PDFファイルのパス

    Returns:
        メタデータを含む辞書
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    with pdfplumber.open(path) as pdf:
        info: dict[str, Any] = {
            "file_name": path.name,
            "file_path": str(path.absolute()),
            "total_pages": len(pdf.pages),
            "metadata": pdf.metadata or {},
        }

        # 最初のページのサイズ情報
        if pdf.pages:
            first_page = pdf.pages[0]
            info["page_size"] = {
                "width": first_page.width,
                "height": first_page.height,
            }

        # 目次を抽出（あれば）
        toc = _extract_toc_from_text(pdf)
        if toc:
            info["table_of_contents"] = toc

    return info


def _extract_toc_from_text(pdf: PdfPlumberPDF) -> list[str]:
    """最初の数ページから目次らしき内容を抽出する."""
    toc_items: list[str] = []

    # 最初の5ページから目次を探す
    for page in pdf.pages[:5]:
        text = page.extract_text() or ""
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            # 目次っぽい行を検出（数字で始まる or ページ番号を含む）
            if line and (
                any(line.startswith(f"{n}.") for n in range(1, 20))
                or "....." in line
                or (len(line) > 5 and line[-1].isdigit() and " " in line)
            ):
                toc_items.append(line)

    return toc_items[:30]  # 最大30項目


def read_pages(
    pdf_path: str,
    start_page: int = 1,
    end_page: int | None = None,
) -> str:
    """指定ページ範囲のテキストを抽出する.

    Args:
        pdf_path: PDFファイルのパス
        start_page: 開始ページ（1始まり）
        end_page: 終了ページ（None の場合は最終ページまで）

    Returns:
        抽出したテキスト
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    with pdfplumber.open(path) as pdf:
        total_pages = len(pdf.pages)

        # ページ範囲を調整
        start_idx = max(0, start_page - 1)
        end_idx = min(total_pages, end_page) if end_page else total_pages

        texts: list[str] = []
        for i in range(start_idx, end_idx):
            page = pdf.pages[i]
            text = page.extract_text() or ""
            texts.append(f"--- Page {i + 1} ---\n{text}")

    return "\n\n".join(texts)


def to_markdown(
    pdf_path: str,
    start_page: int | None = None,
    end_page: int | None = None,
) -> str:
    """PDFをマークダウンに変換する.

    Args:
        pdf_path: PDFファイルのパス
        start_page: 開始ページ（1始まり、None の場合は最初から）
        end_page: 終了ページ（None の場合は最終ページまで）

    Returns:
        マークダウン形式のテキスト
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # pymupdf4llmでマークダウン変換
    # ページ範囲が指定されている場合
    pages: list[int] | None = None
    if start_page is not None or end_page is not None:
        with pdfplumber.open(path) as pdf:
            total_pages = len(pdf.pages)
        start_idx = (start_page or 1) - 1
        end_idx = end_page or total_pages
        pages = list(range(start_idx, end_idx))

    md_text: str = pymupdf4llm.to_markdown(str(path), pages=pages)
    return md_text


def extract_tables(
    pdf_path: str,
    page_number: int | None = None,
) -> str:
    """PDFから表を抽出する.

    Args:
        pdf_path: PDFファイルのパス
        page_number: 特定ページのみ抽出（None の場合は全ページ）

    Returns:
        JSON形式の表データ
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    tables_data: list[dict[str, Any]] = []

    with pdfplumber.open(path) as pdf:
        pages_to_process = [pdf.pages[page_number - 1]] if page_number else pdf.pages

        for i, page in enumerate(pages_to_process):
            page_num = page_number if page_number else i + 1
            page_tables = page.extract_tables()

            if page_tables:
                for table_idx, table in enumerate(page_tables):
                    if table and len(table) > 0:
                        tables_data.append(
                            {
                                "page": page_num,
                                "table_index": table_idx,
                                "rows": len(table),
                                "columns": len(table[0]) if table[0] else 0,
                                "data": table,
                            }
                        )

    return json.dumps(tables_data, ensure_ascii=False, indent=2)
