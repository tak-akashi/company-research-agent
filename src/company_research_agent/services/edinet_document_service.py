"""EDINET document service for searching and filtering documents."""

import logging
from datetime import date, timedelta

from company_research_agent.clients.edinet_client import EDINETClient
from company_research_agent.core.exceptions import EDINETAPIError
from company_research_agent.schemas.document_filter import DocumentFilter, SearchOrder
from company_research_agent.schemas.edinet_schemas import DocumentMetadata

# start_date省略時のデフォルト検索期間（5年）
DEFAULT_SEARCH_PERIOD_DAYS = 365 * 5

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

        The search order can be controlled via filter.search_order:
        - NEWEST_FIRST (default): Search from end_date to start_date
        - OLDEST_FIRST: Search from start_date to end_date

        Args:
            filter: Filter criteria for document search.

        Returns:
            List of DocumentMetadata matching the filter criteria,
            sorted by submit_date_time in descending order (newest first).

        Raises:
            EDINETAPIError: If API call fails.
            EDINETAuthenticationError: If API key is invalid.
            EDINETServerError: If server error occurs.
        """
        # Determine date range
        end_date = filter.end_date or date.today()
        # start_date省略時は過去5年分を検索（有報は年1回のため十分な期間が必要）
        start_date = filter.start_date or (end_date - timedelta(days=DEFAULT_SEARCH_PERIOD_DAYS))

        # Collect documents from all dates in range
        all_documents: list[DocumentMetadata] = []

        # Determine iteration direction based on search_order
        if filter.search_order == SearchOrder.NEWEST_FIRST:
            # Iterate from end_date to start_date (newest first)
            current_date = end_date
            date_step = timedelta(days=-1)

            def should_continue(d: date) -> bool:
                return d >= start_date

        else:
            # Iterate from start_date to end_date (oldest first)
            current_date = start_date
            date_step = timedelta(days=1)

            def should_continue(d: date) -> bool:
                return d <= end_date

        while should_continue(current_date):
            try:
                response = await self._client.get_document_list(current_date)
                if response.results:
                    # Apply filters immediately to support early termination
                    filtered = self._apply_filters(response.results, filter)
                    all_documents.extend(filtered)

                    # Check early termination
                    if filter.max_documents and len(all_documents) >= filter.max_documents:
                        logger.info(
                            "Early termination: reached max_documents=%d",
                            filter.max_documents,
                        )
                        all_documents = all_documents[: filter.max_documents]
                        break
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
            current_date += date_step

        # Sort results by submit_date_time (newest first)
        return self._sort_by_date(all_documents)

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
        logger.debug("Before filtering: %d documents", len(documents))

        if filter.sec_code is not None:
            result = self._filter_by_sec_code(result, filter.sec_code)
            logger.debug("After sec_code filter: %d documents", len(result))

        if filter.edinet_code is not None:
            result = self._filter_by_edinet_code(result, filter.edinet_code)
            logger.debug("After edinet_code filter: %d documents", len(result))

        if filter.company_name is not None:
            result = self._filter_by_company_name(result, filter.company_name)
            logger.debug("After company_name filter: %d documents", len(result))

        if filter.doc_type_codes is not None:
            result = self._filter_by_doc_type_codes(result, filter.doc_type_codes)
            logger.debug("After doc_type_codes filter: %d documents", len(result))

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
        logger.debug("Filter doc_type_codes: %s", doc_type_codes)
        result = [doc for doc in documents if doc.doc_type_code in doc_type_codes]
        # Log unmatched documents only when filtered results differ significantly
        if documents and not result:
            unmatched_types = {doc.doc_type_code for doc in documents if doc.doc_type_code}
            logger.debug(
                "No documents matched. Found doc_type_codes: %s",
                sorted(unmatched_types),
            )
        return result

    def _sort_by_date(
        self,
        documents: list[DocumentMetadata],
    ) -> list[DocumentMetadata]:
        """Sort documents by submit_date_time in descending order (newest first).

        Args:
            documents: List of documents to sort.

        Returns:
            Sorted list of documents (newest first).
        """
        return sorted(
            documents,
            key=lambda doc: doc.submit_date_time or "",
            reverse=True,
        )
