"""EDINET document service for searching and filtering documents."""

import logging
from datetime import date, timedelta

from company_research_agent.clients.edinet_client import EDINETClient
from company_research_agent.core.exceptions import EDINETAPIError
from company_research_agent.schemas.document_filter import DocumentFilter
from company_research_agent.schemas.edinet_schemas import DocumentMetadata

logger = logging.getLogger(__name__)


class EDINETDocumentService:
    """Service for searching and filtering EDINET documents.

    This service provides business logic for document search operations,
    including filtering by company code, company name, document type,
    and date range.

    The service wraps EDINETClient and provides higher-level search
    functionality that combines API calls with client-side filtering.

    Example:
        async with EDINETClient(config) as client:
            service = EDINETDocumentService(client)
            filter = DocumentFilter(
                sec_code="72030",
                doc_type_codes=["120"],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
            )
            documents = await service.search_documents(filter)
    """

    def __init__(self, client: EDINETClient) -> None:
        """Initialize the service with an EDINET client.

        Args:
            client: EDINETClient instance for API calls.
        """
        self._client = client

    async def search_documents(
        self,
        filter: DocumentFilter,
    ) -> list[DocumentMetadata]:
        """Search documents with the specified filter criteria.

        This method fetches documents from EDINET API for each date in the
        specified period and applies client-side filtering based on the
        filter criteria.

        Args:
            filter: Filter criteria for document search.

        Returns:
            List of DocumentMetadata matching the filter criteria.

        Raises:
            EDINETAPIError: If API call fails.
            EDINETAuthenticationError: If API key is invalid.
            EDINETServerError: If server error occurs.
        """
        # Determine date range
        end_date = filter.end_date or date.today()
        start_date = filter.start_date or end_date

        # Collect documents from all dates in range
        all_documents: list[DocumentMetadata] = []
        current_date = start_date

        while current_date <= end_date:
            try:
                response = await self._client.get_document_list(current_date)
                if response.results:
                    all_documents.extend(response.results)
            except EDINETAPIError as e:
                logger.warning(
                    "Failed to fetch documents for %s: %s",
                    current_date,
                    e.message,
                )
            except Exception as e:
                logger.error(
                    "Unexpected error fetching documents for %s: %s",
                    current_date,
                    str(e),
                    exc_info=True,
                )
            current_date += timedelta(days=1)

        # Apply filters
        return self._apply_filters(all_documents, filter)

    def _apply_filters(
        self,
        documents: list[DocumentMetadata],
        filter: DocumentFilter,
    ) -> list[DocumentMetadata]:
        """Apply all filter criteria to the document list.

        Args:
            documents: List of documents to filter.
            filter: Filter criteria to apply.

        Returns:
            Filtered list of documents.
        """
        result = documents

        if filter.sec_code is not None:
            result = self._filter_by_sec_code(result, filter.sec_code)

        if filter.edinet_code is not None:
            result = self._filter_by_edinet_code(result, filter.edinet_code)

        if filter.company_name is not None:
            result = self._filter_by_company_name(result, filter.company_name)

        if filter.doc_type_codes is not None:
            result = self._filter_by_doc_type_codes(result, filter.doc_type_codes)

        return result

    def _filter_by_sec_code(
        self,
        documents: list[DocumentMetadata],
        sec_code: str,
    ) -> list[DocumentMetadata]:
        """Filter documents by securities code.

        Args:
            documents: List of documents to filter.
            sec_code: Securities code to match (exact match).

        Returns:
            Documents with matching securities code.
        """
        return [doc for doc in documents if doc.sec_code == sec_code]

    def _filter_by_edinet_code(
        self,
        documents: list[DocumentMetadata],
        edinet_code: str,
    ) -> list[DocumentMetadata]:
        """Filter documents by EDINET code.

        Args:
            documents: List of documents to filter.
            edinet_code: EDINET code to match (exact match).

        Returns:
            Documents with matching EDINET code.
        """
        return [doc for doc in documents if doc.edinet_code == edinet_code]

    def _filter_by_company_name(
        self,
        documents: list[DocumentMetadata],
        company_name: str,
    ) -> list[DocumentMetadata]:
        """Filter documents by company name (partial match).

        Args:
            documents: List of documents to filter.
            company_name: Company name substring to search for.

        Returns:
            Documents with filer name containing the search string.
        """
        return [
            doc
            for doc in documents
            if doc.filer_name is not None and company_name in doc.filer_name
        ]

    def _filter_by_doc_type_codes(
        self,
        documents: list[DocumentMetadata],
        doc_type_codes: list[str],
    ) -> list[DocumentMetadata]:
        """Filter documents by document type codes.

        Args:
            documents: List of documents to filter.
            doc_type_codes: List of document type codes to match (OR logic).

        Returns:
            Documents with document type code in the specified list.
        """
        return [doc for doc in documents if doc.doc_type_code in doc_type_codes]
