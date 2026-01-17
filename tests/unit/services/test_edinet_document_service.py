"""Tests for EDINET document service."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from company_research_agent.schemas.document_filter import DocumentFilter
from company_research_agent.schemas.edinet_schemas import (
    DocumentListResponse,
    DocumentMetadata,
    RequestParameter,
    ResponseMetadata,
    ResultSet,
)
from company_research_agent.services.edinet_document_service import EDINETDocumentService


def create_sample_document(
    seq_number: int = 1,
    doc_id: str = "S100TEST",
    edinet_code: str = "E10001",
    sec_code: str = "10000",
    filer_name: str = "テスト株式会社",
    doc_type_code: str = "120",
) -> DocumentMetadata:
    """Create a sample DocumentMetadata for testing."""
    return DocumentMetadata(
        seqNumber=seq_number,
        docID=doc_id,
        edinetCode=edinet_code,
        secCode=sec_code,
        JCN="6000012010023",
        filerName=filer_name,
        fundCode=None,
        ordinanceCode="010",
        formCode="030000",
        docTypeCode=doc_type_code,
        periodStart="2023-04-01",
        periodEnd="2024-03-31",
        submitDateTime="2024-01-15 09:00",
        docDescription="有価証券報告書－第10期",
        issuerEdinetCode=None,
        subjectEdinetCode=None,
        subsidiaryEdinetCode=None,
        currentReportReason=None,
        parentDocID=None,
        opeDateTime=None,
        withdrawalStatus="0",
        docInfoEditStatus="0",
        disclosureStatus="0",
        xbrlFlag=True,
        pdfFlag=True,
        attachDocFlag=False,
        englishDocFlag=False,
        csvFlag=True,
        legalStatus="1",
    )


def create_document_list_response(
    documents: list[DocumentMetadata],
) -> DocumentListResponse:
    """Create a sample DocumentListResponse for testing."""
    return DocumentListResponse(
        metadata=ResponseMetadata(
            title="提出された書類を把握するためのAPI",
            parameter=RequestParameter(date="2024-01-15", type="2"),
            resultset=ResultSet(count=len(documents)),
            processDateTime="2024-01-15 10:00",
            status="200",
            message="OK",
        ),
        results=documents,
    )


@pytest.fixture
def mock_edinet_client() -> MagicMock:
    """Create a mock EDINETClient."""
    return MagicMock()


@pytest.fixture
def sample_documents() -> list[DocumentMetadata]:
    """Create sample documents for testing."""
    return [
        create_sample_document(
            seq_number=1,
            doc_id="S100DOC1",
            edinet_code="E10001",
            sec_code="72030",
            filer_name="トヨタ自動車株式会社",
            doc_type_code="120",
        ),
        create_sample_document(
            seq_number=2,
            doc_id="S100DOC2",
            edinet_code="E10002",
            sec_code="72030",
            filer_name="トヨタ自動車株式会社",
            doc_type_code="140",
        ),
        create_sample_document(
            seq_number=3,
            doc_id="S100DOC3",
            edinet_code="E20001",
            sec_code="99840",
            filer_name="ソフトバンクグループ株式会社",
            doc_type_code="120",
        ),
        create_sample_document(
            seq_number=4,
            doc_id="S100DOC4",
            edinet_code="E30001",
            sec_code="68610",
            filer_name="キーエンス",
            doc_type_code="180",
        ),
    ]


class TestEDINETDocumentServiceInit:
    """Tests for EDINETDocumentService initialization."""

    def test_init_with_client(self, mock_edinet_client: MagicMock) -> None:
        """EDINETDocumentService should accept client on initialization."""
        service = EDINETDocumentService(mock_edinet_client)
        assert service._client == mock_edinet_client


class TestSearchBySecCode:
    """Tests for search by securities code."""

    @pytest.mark.asyncio
    async def test_search_by_sec_code_returns_filtered_results(
        self,
        mock_edinet_client: MagicMock,
        sample_documents: list[DocumentMetadata],
    ) -> None:
        """search_documents should return only documents matching sec_code."""
        mock_edinet_client.get_document_list = AsyncMock(
            return_value=create_document_list_response(sample_documents)
        )

        service = EDINETDocumentService(mock_edinet_client)
        filter_criteria = DocumentFilter(
            sec_code="72030",
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
        )

        results = await service.search_documents(filter_criteria)

        assert len(results) == 2
        assert all(doc.sec_code == "72030" for doc in results)
        assert {doc.doc_id for doc in results} == {"S100DOC1", "S100DOC2"}


class TestSearchByEdinetCode:
    """Tests for search by EDINET code."""

    @pytest.mark.asyncio
    async def test_search_by_edinet_code_returns_filtered_results(
        self,
        mock_edinet_client: MagicMock,
        sample_documents: list[DocumentMetadata],
    ) -> None:
        """search_documents should return only documents matching edinet_code."""
        mock_edinet_client.get_document_list = AsyncMock(
            return_value=create_document_list_response(sample_documents)
        )

        service = EDINETDocumentService(mock_edinet_client)
        filter_criteria = DocumentFilter(
            edinet_code="E20001",
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
        )

        results = await service.search_documents(filter_criteria)

        assert len(results) == 1
        assert results[0].edinet_code == "E20001"
        assert results[0].doc_id == "S100DOC3"


class TestSearchByCompanyName:
    """Tests for search by company name."""

    @pytest.mark.asyncio
    async def test_search_by_company_name_partial_match(
        self,
        mock_edinet_client: MagicMock,
        sample_documents: list[DocumentMetadata],
    ) -> None:
        """search_documents should return documents with partial company name match."""
        mock_edinet_client.get_document_list = AsyncMock(
            return_value=create_document_list_response(sample_documents)
        )

        service = EDINETDocumentService(mock_edinet_client)
        filter_criteria = DocumentFilter(
            company_name="トヨタ",
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
        )

        results = await service.search_documents(filter_criteria)

        assert len(results) == 2
        assert all(doc.filer_name is not None and "トヨタ" in doc.filer_name for doc in results)


class TestSearchByDocTypeCodes:
    """Tests for search by document type codes."""

    @pytest.mark.asyncio
    async def test_search_by_doc_type_codes_single(
        self,
        mock_edinet_client: MagicMock,
        sample_documents: list[DocumentMetadata],
    ) -> None:
        """search_documents should filter by single document type code."""
        mock_edinet_client.get_document_list = AsyncMock(
            return_value=create_document_list_response(sample_documents)
        )

        service = EDINETDocumentService(mock_edinet_client)
        filter_criteria = DocumentFilter(
            doc_type_codes=["120"],
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
        )

        results = await service.search_documents(filter_criteria)

        assert len(results) == 2
        assert all(doc.doc_type_code == "120" for doc in results)

    @pytest.mark.asyncio
    async def test_search_by_doc_type_codes_multiple(
        self,
        mock_edinet_client: MagicMock,
        sample_documents: list[DocumentMetadata],
    ) -> None:
        """search_documents should filter by multiple document type codes (OR logic)."""
        mock_edinet_client.get_document_list = AsyncMock(
            return_value=create_document_list_response(sample_documents)
        )

        service = EDINETDocumentService(mock_edinet_client)
        filter_criteria = DocumentFilter(
            doc_type_codes=["120", "140"],
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
        )

        results = await service.search_documents(filter_criteria)

        assert len(results) == 3
        assert all(doc.doc_type_code in ["120", "140"] for doc in results)


class TestSearchByDateRange:
    """Tests for search by date range."""

    @pytest.mark.asyncio
    async def test_search_by_date_range_multiple_days(
        self,
        mock_edinet_client: MagicMock,
    ) -> None:
        """search_documents should fetch documents from multiple dates."""
        day1_docs = [
            create_sample_document(seq_number=1, doc_id="S100DAY1"),
        ]
        day2_docs = [
            create_sample_document(seq_number=2, doc_id="S100DAY2"),
        ]
        day3_docs = [
            create_sample_document(seq_number=3, doc_id="S100DAY3"),
        ]

        mock_edinet_client.get_document_list = AsyncMock(
            side_effect=[
                create_document_list_response(day1_docs),
                create_document_list_response(day2_docs),
                create_document_list_response(day3_docs),
            ]
        )

        service = EDINETDocumentService(mock_edinet_client)
        filter_criteria = DocumentFilter(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 17),
        )

        results = await service.search_documents(filter_criteria)

        assert len(results) == 3
        assert mock_edinet_client.get_document_list.call_count == 3
        assert {doc.doc_id for doc in results} == {"S100DAY1", "S100DAY2", "S100DAY3"}


class TestSearchWithCombinedFilters:
    """Tests for search with combined filters."""

    @pytest.mark.asyncio
    async def test_search_with_combined_filters(
        self,
        mock_edinet_client: MagicMock,
        sample_documents: list[DocumentMetadata],
    ) -> None:
        """search_documents should apply multiple filters with AND logic."""
        mock_edinet_client.get_document_list = AsyncMock(
            return_value=create_document_list_response(sample_documents)
        )

        service = EDINETDocumentService(mock_edinet_client)
        filter_criteria = DocumentFilter(
            sec_code="72030",
            doc_type_codes=["120"],
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
        )

        results = await service.search_documents(filter_criteria)

        assert len(results) == 1
        assert results[0].sec_code == "72030"
        assert results[0].doc_type_code == "120"
        assert results[0].doc_id == "S100DOC1"


class TestSearchEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_search_with_no_results_returns_empty_list(
        self,
        mock_edinet_client: MagicMock,
        sample_documents: list[DocumentMetadata],
    ) -> None:
        """search_documents should return empty list when no documents match."""
        mock_edinet_client.get_document_list = AsyncMock(
            return_value=create_document_list_response(sample_documents)
        )

        service = EDINETDocumentService(mock_edinet_client)
        filter_criteria = DocumentFilter(
            sec_code="99999",  # Non-existent code
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
        )

        results = await service.search_documents(filter_criteria)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_with_empty_filter_returns_all(
        self,
        mock_edinet_client: MagicMock,
        sample_documents: list[DocumentMetadata],
    ) -> None:
        """search_documents should return all documents when no filters specified."""
        mock_edinet_client.get_document_list = AsyncMock(
            return_value=create_document_list_response(sample_documents)
        )

        service = EDINETDocumentService(mock_edinet_client)
        filter_criteria = DocumentFilter(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
        )

        results = await service.search_documents(filter_criteria)

        assert len(results) == 4
