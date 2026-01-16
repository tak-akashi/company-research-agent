"""EDINET API client for fetching corporate disclosure documents."""

from datetime import date
from pathlib import Path
from typing import Self

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from company_research_agent.core.config import EDINETConfig
from company_research_agent.core.exceptions import (
    EDINETAPIError,
    EDINETAuthenticationError,
    EDINETNotFoundError,
    EDINETServerError,
)
from company_research_agent.core.types import DocumentDownloadType
from company_research_agent.schemas.edinet_schemas import DocumentListResponse


class EDINETClient:
    """Async client for EDINET API.

    This client provides methods to:
    - Fetch document lists for a specific date
    - Download documents in various formats (XBRL, PDF, CSV)

    The client uses httpx for async HTTP requests and implements
    automatic retry with exponential backoff for server errors.

    Example:
        async with EDINETClient(config) as client:
            docs = await client.get_document_list(date(2024, 1, 15))
            for doc in docs.results or []:
                if doc.pdf_flag:
                    await client.download_document(
                        doc.doc_id, 2, Path(f"downloads/{doc.doc_id}.pdf")
                    )
    """

    def __init__(self, config: EDINETConfig) -> None:
        """Initialize the EDINET client.

        Args:
            config: Configuration containing API key and settings.
        """
        self._config = config
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client.

        Returns:
            The httpx AsyncClient instance.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._config.base_url,
                params={"Subscription-Key": self._config.api_key},
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> Self:
        """Enter async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit async context manager and close client."""
        await self.close()

    def _raise_for_status(self, response: httpx.Response, endpoint: str) -> None:
        """Check HTTP response status and raise appropriate exceptions.

        Args:
            response: The httpx response object.
            endpoint: The API endpoint that was called.

        Raises:
            EDINETAuthenticationError: For 401 status.
            EDINETNotFoundError: For 404 status.
            EDINETServerError: For 5xx status.
            EDINETAPIError: For other error status codes.
        """
        if response.status_code == 200:
            return

        status_code = response.status_code
        message = f"HTTP {status_code}"

        # Try to extract message from JSON response
        try:
            data = response.json()
            message = data.get("message", message)
        except Exception:
            pass

        if status_code == 401:
            raise EDINETAuthenticationError(
                status_code=status_code,
                message=message,
                endpoint=endpoint,
            )
        elif status_code == 404:
            raise EDINETNotFoundError(
                status_code=status_code,
                message=message,
                endpoint=endpoint,
            )
        elif status_code >= 500:
            raise EDINETServerError(
                status_code=status_code,
                message=message,
                endpoint=endpoint,
            )
        else:
            raise EDINETAPIError(
                status_code=status_code,
                message=message,
                endpoint=endpoint,
            )

    def _check_internal_status(self, data: dict[str, object], endpoint: str) -> None:
        """Check EDINET's internal status code in JSON response.

        EDINET API may return HTTP 200 but with an internal error status.
        The error can be in two formats:
        1. Top-level: {"statusCode": 401, "message": "..."}
        2. Nested: {"metadata": {"status": "404", "message": "..."}}

        Args:
            data: The parsed JSON response.
            endpoint: The API endpoint that was called.

        Raises:
            EDINETAuthenticationError: For internal status 401.
            EDINETNotFoundError: For internal status 404.
            EDINETServerError: For internal status 5xx.
            EDINETAPIError: For other non-200 internal status.
        """
        # Check top-level statusCode (format 1)
        if "statusCode" in data:
            status_code_value = data.get("statusCode")
            if isinstance(status_code_value, int) and status_code_value != 200:
                message_value = data.get("message", "Unknown error")
                message = str(message_value) if message_value else "Unknown error"
                self._raise_for_internal_status(status_code_value, message, endpoint)
                return

        # Check nested metadata.status (format 2)
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            return

        status_str = metadata.get("status", "200")
        if not isinstance(status_str, str):
            return

        if status_str == "200":
            return

        try:
            status_code = int(status_str)
        except ValueError:
            status_code = 0

        message_value = metadata.get("message", "Unknown error")
        message = str(message_value) if message_value else "Unknown error"

        self._raise_for_internal_status(status_code, message, endpoint)

    def _raise_for_internal_status(self, status_code: int, message: str, endpoint: str) -> None:
        """Raise appropriate exception for internal status code.

        Args:
            status_code: The internal status code.
            message: The error message.
            endpoint: The API endpoint that was called.

        Raises:
            EDINETAuthenticationError: For status 401.
            EDINETNotFoundError: For status 404.
            EDINETServerError: For status 5xx.
            EDINETAPIError: For other non-200 status.
        """
        if status_code == 401:
            raise EDINETAuthenticationError(
                status_code=status_code,
                message=message,
                endpoint=endpoint,
            )
        elif status_code == 404:
            raise EDINETNotFoundError(
                status_code=status_code,
                message=message,
                endpoint=endpoint,
            )
        elif status_code >= 500:
            raise EDINETServerError(
                status_code=status_code,
                message=message,
                endpoint=endpoint,
            )
        else:
            raise EDINETAPIError(
                status_code=status_code,
                message=message,
                endpoint=endpoint,
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(EDINETServerError),
        reraise=True,
    )
    async def get_document_list(
        self,
        target_date: date,
        include_details: bool = True,
    ) -> DocumentListResponse:
        """Fetch document list for a specific date.

        Args:
            target_date: The date to fetch documents for.
            include_details: If True, include full document details (type=2).
                           If False, only fetch metadata with counts (type=1).

        Returns:
            DocumentListResponse containing metadata and optionally document list.

        Raises:
            EDINETAuthenticationError: If API key is invalid.
            EDINETNotFoundError: If no data exists for the date.
            EDINETServerError: If server error occurs (retried up to 3 times).
            EDINETAPIError: For other API errors.
        """
        endpoint = "/documents.json"
        client = await self._get_client()

        response = await client.get(
            endpoint,
            params={
                "date": target_date.strftime("%Y-%m-%d"),
                "type": "2" if include_details else "1",
            },
            timeout=self._config.timeout_list,
        )

        self._raise_for_status(response, endpoint)

        data = response.json()
        self._check_internal_status(data, endpoint)

        return DocumentListResponse.model_validate(data)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(EDINETServerError),
        reraise=True,
    )
    async def download_document(
        self,
        doc_id: str,
        doc_type: DocumentDownloadType,
        save_path: Path,
    ) -> Path:
        """Download a document and save it to the specified path.

        Args:
            doc_id: The document management number (8 characters).
            doc_type: The type of document to download:
                     1=XBRL (ZIP), 2=PDF, 3=Attachments (ZIP),
                     4=English (ZIP), 5=CSV (ZIP).
            save_path: The path to save the downloaded file.

        Returns:
            The path where the document was saved.

        Raises:
            EDINETAuthenticationError: If API key is invalid.
            EDINETNotFoundError: If document is not found.
            EDINETServerError: If server error occurs (retried up to 3 times).
            EDINETAPIError: For other API errors including when
                          the requested format is not available.
        """
        endpoint = f"/documents/{doc_id}"
        client = await self._get_client()

        response = await client.get(
            endpoint,
            params={"type": str(doc_type)},
            timeout=self._config.timeout_download,
        )

        self._raise_for_status(response, endpoint)

        # Check Content-Type for error response
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            # Error response in JSON format
            data = response.json()
            self._check_internal_status(data, endpoint)
            # If no internal error but still JSON, it's an unexpected response
            raise EDINETAPIError(
                status_code=0,
                message="Unexpected JSON response for document download",
                endpoint=endpoint,
            )

        # Save binary content to file
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(response.content)

        return save_path
