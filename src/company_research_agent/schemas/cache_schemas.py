"""Schemas for local cache functionality."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class CachedDocumentInfo:
    """Information about a cached document.

    Parsed from the hierarchical folder structure:
    {sec_code}_{company_name}/{doc_type_code}_{doc_type_name}/{YYYYMM}/{doc_id}.pdf

    Attributes:
        doc_id: Document ID (e.g., "S100ABCD").
        sec_code: Securities code (e.g., "72030"), or None if not parseable.
        company_name: Company name (e.g., "トヨタ自動車"), or None if not parseable.
        doc_type_code: Document type code (e.g., "120"), or None if not parseable.
        period: Period in YYYYMM format (e.g., "202512"), or None if not parseable.
        file_path: Full path to the cached PDF file.
    """

    doc_id: str
    sec_code: str | None
    company_name: str | None
    doc_type_code: str | None
    period: str | None
    file_path: Path

    @classmethod
    def from_path(cls, file_path: Path) -> CachedDocumentInfo:
        """Create CachedDocumentInfo from a file path.

        Parses the hierarchical folder structure to extract metadata.

        Args:
            file_path: Path to the cached PDF file.

        Returns:
            CachedDocumentInfo with parsed metadata.

        Example:
            >>> path = Path("downloads/72030_トヨタ自動車/120_有価証券報告書/202512/S100ABCD.pdf")
            >>> info = CachedDocumentInfo.from_path(path)
            >>> info.sec_code
            '72030'
            >>> info.doc_type_code
            '120'
        """
        doc_id = file_path.stem  # S100ABCD

        # Try to parse folder structure
        parts = file_path.parts

        sec_code = None
        company_name = None
        doc_type_code = None
        period = None

        # Expected: .../company_folder/doc_type_folder/period_folder/doc_id.pdf
        if len(parts) >= 4:
            # Period folder (YYYYMM)
            period_folder = parts[-2]
            if period_folder.isdigit() and len(period_folder) == 6:
                period = period_folder

            # Document type folder (doc_type_code_doc_type_name)
            doc_type_folder = parts[-3]
            if "_" in doc_type_folder:
                doc_type_code = doc_type_folder.split("_")[0]

            # Company folder (sec_code_company_name)
            company_folder = parts[-4]
            if "_" in company_folder:
                folder_parts = company_folder.split("_", 1)
                sec_code = folder_parts[0]
                if len(folder_parts) > 1:
                    company_name = folder_parts[1]

        return cls(
            doc_id=doc_id,
            sec_code=sec_code,
            company_name=company_name,
            doc_type_code=doc_type_code,
            period=period,
            file_path=file_path,
        )
