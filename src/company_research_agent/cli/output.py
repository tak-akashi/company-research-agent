"""CLI output utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from company_research_agent.cli.config import DOC_TYPE_NAMES

if TYPE_CHECKING:
    from company_research_agent.schemas.edinet_schemas import DocumentMetadata
    from company_research_agent.schemas.query_schemas import CompanyInfo


def print_header(title: str) -> None:
    """セクションヘッダーを表示."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_error(message: str) -> None:
    """エラーメッセージを表示."""
    print(f"[ERROR] {message}")


def print_success(message: str) -> None:
    """成功メッセージを表示."""
    print(f"[OK] {message}")


def print_info(message: str) -> None:
    """情報メッセージを表示."""
    print(f"[INFO] {message}")


def print_company_info(company: CompanyInfo) -> None:
    """企業情報の詳細を表示."""
    print(f"企業名: {company.company_name}")
    if company.company_name_kana:
        print(f"カナ: {company.company_name_kana}")
    if company.company_name_en:
        print(f"英名: {company.company_name_en}")
    print(f"EDINETコード: {company.edinet_code}")
    print(f"証券コード: {company.sec_code or '(未上場)'}")
    if company.industry_code:
        print(f"業種コード: {company.industry_code}")


def print_documents_table(documents: list[DocumentMetadata]) -> None:
    """書類一覧をテーブル形式で表示."""
    print(f"{'No':>3} | {'提出日':^10} | {'書類ID':^12} | {'種別':^16} | 企業名")
    print("-" * 80)

    for i, doc in enumerate(documents, 1):
        doc_type_code = doc.doc_type_code or ""
        doc_type = DOC_TYPE_NAMES.get(doc_type_code, doc_type_code)
        # submit_date_time は文字列 (YYYY-MM-DD hh:mm 形式)
        submit_date = doc.submit_date_time[:10] if doc.submit_date_time else "-"
        print(f"{i:3} | {submit_date:^10} | {doc.doc_id:^12} | {doc_type:^16} | {doc.filer_name}")
