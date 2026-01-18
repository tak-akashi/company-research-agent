"""Tests for search_documents tool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from company_research_agent.schemas.edinet_schemas import DocumentMetadata
from company_research_agent.tools.search_documents import search_documents


@pytest.fixture
def sample_document_metadata() -> DocumentMetadata:
    """Sample document metadata fixture."""
    return DocumentMetadata(
        seqNumber=1,
        docID="S100TEST",
        edinetCode="E02144",
        secCode="72030",
        JCN="6000012010023",
        filerName="トヨタ自動車株式会社",
        fundCode=None,
        ordinanceCode="010",
        formCode="030000",
        docTypeCode="120",
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


class TestSearchDocuments:
    """Tests for search_documents tool."""

    @pytest.mark.asyncio
    async def test_search_documents_returns_metadata(
        self, sample_document_metadata: DocumentMetadata
    ) -> None:
        """search_documents should return document metadata from service."""
        mock_service = AsyncMock()
        mock_service.search_documents = AsyncMock(return_value=[sample_document_metadata])

        with patch(
            "company_research_agent.tools.search_documents.EDINETConfig"
        ) as mock_config_class:
            mock_config_class.return_value = MagicMock()

            with patch(
                "company_research_agent.tools.search_documents.EDINETClient"
            ) as mock_client_class:
                mock_client = MagicMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                with patch(
                    "company_research_agent.tools.search_documents.EDINETDocumentService"
                ) as mock_service_class:
                    mock_service_class.return_value = mock_service

                    result = await search_documents.ainvoke(
                        {"edinet_code": "E02144", "doc_type_codes": ["120"]}
                    )

                    assert len(result) == 1
                    # Result is serialized as dict for LangChain ToolMessage compatibility
                    assert result[0]["doc_id"] == "S100TEST"
                    mock_service.search_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_documents_with_date_range(
        self, sample_document_metadata: DocumentMetadata
    ) -> None:
        """search_documents should parse date strings correctly."""
        mock_service = AsyncMock()
        mock_service.search_documents = AsyncMock(return_value=[sample_document_metadata])

        with patch(
            "company_research_agent.tools.search_documents.EDINETConfig"
        ) as mock_config_class:
            mock_config_class.return_value = MagicMock()

            with patch(
                "company_research_agent.tools.search_documents.EDINETClient"
            ) as mock_client_class:
                mock_client = MagicMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                with patch(
                    "company_research_agent.tools.search_documents.EDINETDocumentService"
                ) as mock_service_class:
                    mock_service_class.return_value = mock_service

                    await search_documents.ainvoke(
                        {
                            "edinet_code": "E02144",
                            "start_date": "2024-01-01",
                            "end_date": "2024-12-31",
                        }
                    )

                    call_args = mock_service.search_documents.call_args
                    doc_filter = call_args[0][0]
                    assert doc_filter.edinet_code == "E02144"
                    assert doc_filter.start_date is not None
                    assert doc_filter.end_date is not None
