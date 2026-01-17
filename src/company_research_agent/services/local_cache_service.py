"""Local cache service for downloaded documents."""

from __future__ import annotations

import logging
from pathlib import Path

from company_research_agent.schemas.cache_schemas import CachedDocumentInfo

logger = logging.getLogger(__name__)


class LocalCacheService:
    """Service for searching and managing locally cached documents.

    Provides methods to search the hierarchical download folder structure
    for previously downloaded documents.

    Example:
        >>> service = LocalCacheService(Path("downloads"))
        >>> cached = service.find_by_doc_id("S100ABCD")
        >>> if cached:
        ...     print(f"Found: {cached.file_path}")
    """

    def __init__(self, download_dir: Path | None = None) -> None:
        """Initialize the local cache service.

        Args:
            download_dir: Base download directory. Defaults to "downloads".
        """
        self._download_dir = download_dir or Path("downloads")

    @property
    def download_dir(self) -> Path:
        """Get the download directory."""
        return self._download_dir

    def find_by_doc_id(self, doc_id: str) -> CachedDocumentInfo | None:
        """Find a cached document by its document ID.

        Searches the entire download directory hierarchy for a matching file.

        Args:
            doc_id: Document ID to find (e.g., "S100ABCD").

        Returns:
            CachedDocumentInfo if found, None otherwise.

        Example:
            >>> service = LocalCacheService()
            >>> info = service.find_by_doc_id("S100ABCD")
            >>> if info:
            ...     print(info.file_path)
        """
        if not self._download_dir.exists():
            logger.debug(f"Download directory does not exist: {self._download_dir}")
            return None

        # Search recursively for the document
        pattern = f"**/{doc_id}.pdf"
        matches = list(self._download_dir.glob(pattern))

        if matches:
            logger.info(f"Found cached document: {matches[0]}")
            return CachedDocumentInfo.from_path(matches[0])

        logger.debug(f"Document not found in cache: {doc_id}")
        return None

    def find_by_filter(
        self,
        sec_code: str | None = None,
        doc_type_code: str | None = None,
        period: str | None = None,
    ) -> list[CachedDocumentInfo]:
        """Find cached documents matching the given filter criteria.

        Args:
            sec_code: Filter by securities code.
            doc_type_code: Filter by document type code.
            period: Filter by period (YYYYMM format).

        Returns:
            List of matching CachedDocumentInfo objects.

        Example:
            >>> service = LocalCacheService()
            >>> docs = service.find_by_filter(sec_code="72030", doc_type_code="120")
            >>> for doc in docs:
            ...     print(doc.doc_id)
        """
        if not self._download_dir.exists():
            return []

        # Build glob pattern based on filters
        pattern_parts = []

        if sec_code:
            pattern_parts.append(f"{sec_code}_*")
        else:
            pattern_parts.append("*")

        if doc_type_code:
            pattern_parts.append(f"{doc_type_code}_*")
        else:
            pattern_parts.append("*")

        if period:
            pattern_parts.append(period)
        else:
            pattern_parts.append("*")

        pattern_parts.append("*.pdf")

        pattern = "/".join(pattern_parts)
        matches = list(self._download_dir.glob(pattern))

        results = [CachedDocumentInfo.from_path(path) for path in matches]
        logger.info(f"Found {len(results)} cached documents matching filter")
        return results

    def list_all(self) -> list[CachedDocumentInfo]:
        """List all cached documents.

        Returns:
            List of all CachedDocumentInfo objects in the download directory.

        Example:
            >>> service = LocalCacheService()
            >>> all_docs = service.list_all()
            >>> print(f"Total cached: {len(all_docs)}")
        """
        if not self._download_dir.exists():
            return []

        pattern = "**/*.pdf"
        matches = list(self._download_dir.glob(pattern))

        results = [CachedDocumentInfo.from_path(path) for path in matches]
        logger.info(f"Found {len(results)} total cached documents")
        return results

    def get_cache_stats(self) -> dict[str, int]:
        """Get statistics about the cache.

        Returns:
            Dictionary with cache statistics.

        Example:
            >>> service = LocalCacheService()
            >>> stats = service.get_cache_stats()
            >>> print(stats)
            {'total_documents': 42, 'total_companies': 5}
        """
        if not self._download_dir.exists():
            return {"total_documents": 0, "total_companies": 0}

        all_docs = self.list_all()
        companies = set(doc.sec_code for doc in all_docs if doc.sec_code)

        return {
            "total_documents": len(all_docs),
            "total_companies": len(companies),
        }
