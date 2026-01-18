"""Tests for cli/output.py - CLI output utilities."""

from __future__ import annotations

from io import StringIO
from unittest.mock import patch

import pytest

from company_research_agent.cli.output import (
    print_company_info,
    print_documents_table,
    print_error,
    print_header,
    print_info,
    print_success,
)
from company_research_agent.schemas.edinet_schemas import DocumentMetadata
from company_research_agent.schemas.query_schemas import CompanyInfo


class TestPrintHeader:
    """print_header() のテスト."""

    def test_prints_title_with_decorations(self) -> None:
        """タイトルが装飾付きで出力されること."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_header("テストタイトル")
            output = mock_stdout.getvalue()

        assert "=" * 60 in output
        assert "テストタイトル" in output

    def test_title_is_indented(self) -> None:
        """タイトルがインデントされていること."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_header("タイトル")
            output = mock_stdout.getvalue()

        # タイトル行にスペースが含まれる
        assert "  タイトル" in output


class TestPrintError:
    """print_error() のテスト."""

    def test_prints_error_prefix(self) -> None:
        """[ERROR] プレフィックスが付くこと."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_error("エラーメッセージ")
            output = mock_stdout.getvalue()

        assert "[ERROR]" in output
        assert "エラーメッセージ" in output


class TestPrintSuccess:
    """print_success() のテスト."""

    def test_prints_success_prefix(self) -> None:
        """[OK] プレフィックスが付くこと."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_success("成功メッセージ")
            output = mock_stdout.getvalue()

        assert "[OK]" in output
        assert "成功メッセージ" in output


class TestPrintInfo:
    """print_info() のテスト."""

    def test_prints_info_prefix(self) -> None:
        """[INFO] プレフィックスが付くこと."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_info("情報メッセージ")
            output = mock_stdout.getvalue()

        assert "[INFO]" in output
        assert "情報メッセージ" in output


class TestPrintCompanyInfo:
    """print_company_info() のテスト."""

    @pytest.fixture
    def sample_company(self) -> CompanyInfo:
        """サンプル企業情報を作成."""
        return CompanyInfo(
            edinet_code="E02144",
            sec_code="72030",
            company_name="トヨタ自動車株式会社",
            company_name_kana="トヨタジドウシャ",
            company_name_en="TOYOTA MOTOR CORPORATION",
            listing_code="1",
            industry_code="3700",
        )

    def test_prints_company_name(self, sample_company: CompanyInfo) -> None:
        """企業名が出力されること."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_company_info(sample_company)
            output = mock_stdout.getvalue()

        assert "トヨタ自動車株式会社" in output

    def test_prints_edinet_code(self, sample_company: CompanyInfo) -> None:
        """EDINETコードが出力されること."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_company_info(sample_company)
            output = mock_stdout.getvalue()

        assert "E02144" in output

    def test_prints_sec_code(self, sample_company: CompanyInfo) -> None:
        """証券コードが出力されること."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_company_info(sample_company)
            output = mock_stdout.getvalue()

        assert "72030" in output

    def test_prints_kana_when_available(self, sample_company: CompanyInfo) -> None:
        """カナ名が存在する場合に出力されること."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_company_info(sample_company)
            output = mock_stdout.getvalue()

        assert "トヨタジドウシャ" in output

    def test_prints_en_name_when_available(self, sample_company: CompanyInfo) -> None:
        """英語名が存在する場合に出力されること."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_company_info(sample_company)
            output = mock_stdout.getvalue()

        assert "TOYOTA MOTOR CORPORATION" in output

    def test_handles_missing_sec_code(self) -> None:
        """証券コードがない場合に (未上場) と表示されること."""
        company = CompanyInfo(
            edinet_code="E05031",
            sec_code=None,
            company_name="トヨタファイナンス株式会社",
            company_name_kana=None,
            company_name_en=None,
            listing_code=None,
            industry_code=None,
        )
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_company_info(company)
            output = mock_stdout.getvalue()

        assert "(未上場)" in output


class TestPrintDocumentsTable:
    """print_documents_table() のテスト."""

    @pytest.fixture
    def sample_documents(self) -> list[DocumentMetadata]:
        """サンプル書類リストを作成."""
        return [
            DocumentMetadata(
                seqNumber=1,
                docID="S100ABCD",
                edinetCode="E02144",
                secCode="72030",
                filerName="トヨタ自動車株式会社",
                docTypeCode="120",
                submitDateTime="2024-06-20 15:30",
                withdrawalStatus="0",
                xbrlFlag="1",
                pdfFlag="1",
                attachDocFlag="0",
                englishDocFlag="0",
                csvFlag="0",
                legalStatus="1",
            ),
            DocumentMetadata(
                seqNumber=2,
                docID="S100EFGH",
                edinetCode="E02144",
                secCode="72030",
                filerName="トヨタ自動車株式会社",
                docTypeCode="140",
                submitDateTime="2024-08-10 16:00",
                withdrawalStatus="0",
                xbrlFlag="1",
                pdfFlag="1",
                attachDocFlag="0",
                englishDocFlag="0",
                csvFlag="0",
                legalStatus="1",
            ),
        ]

    def test_prints_header_row(self, sample_documents: list[DocumentMetadata]) -> None:
        """ヘッダー行が出力されること."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_documents_table(sample_documents)
            output = mock_stdout.getvalue()

        assert "No" in output
        assert "提出日" in output
        assert "書類ID" in output
        assert "種別" in output
        assert "企業名" in output

    def test_prints_separator_line(self, sample_documents: list[DocumentMetadata]) -> None:
        """区切り線が出力されること."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_documents_table(sample_documents)
            output = mock_stdout.getvalue()

        assert "-" * 80 in output

    def test_prints_document_rows(self, sample_documents: list[DocumentMetadata]) -> None:
        """書類行が出力されること."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_documents_table(sample_documents)
            output = mock_stdout.getvalue()

        assert "S100ABCD" in output
        assert "S100EFGH" in output
        assert "トヨタ自動車株式会社" in output

    def test_translates_doc_type_code(self, sample_documents: list[DocumentMetadata]) -> None:
        """書類種別コードが日本語に変換されること."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_documents_table(sample_documents)
            output = mock_stdout.getvalue()

        assert "有価証券報告書" in output
        assert "四半期報告書" in output

    def test_extracts_date_from_datetime(self, sample_documents: list[DocumentMetadata]) -> None:
        """日時から日付部分のみが抽出されること."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_documents_table(sample_documents)
            output = mock_stdout.getvalue()

        assert "2024-06-20" in output
        assert "2024-08-10" in output

    def test_handles_empty_list(self) -> None:
        """空リストでもエラーにならないこと."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_documents_table([])
            output = mock_stdout.getvalue()

        # ヘッダーは出力される
        assert "No" in output
