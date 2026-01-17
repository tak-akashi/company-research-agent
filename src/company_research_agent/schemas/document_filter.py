"""Document filter data class for search parameters."""

from dataclasses import dataclass
from datetime import date


@dataclass
class DocumentFilter:
    """Filter criteria for document search.

    All fields are optional. When multiple fields are specified,
    they are combined with AND logic.

    Attributes:
        edinet_code: EDINET code (6 characters, e.g., "E00001").
        sec_code: Securities code (5 digits, e.g., "72030").
        company_name: Company name for partial match search.
        doc_type_codes: List of document type codes to filter.
            Common codes:
            - "120": Annual securities report (有価証券報告書)
            - "140": Quarterly securities report (四半期報告書)
            - "180": Extraordinary report (臨時報告書)
        start_date: Start date for search period (inclusive).
        end_date: End date for search period (inclusive).

    Example:
        # Search for Toyota's annual reports in 2024
        filter = DocumentFilter(
            sec_code="72030",
            doc_type_codes=["120"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
    """

    edinet_code: str | None = None
    sec_code: str | None = None
    company_name: str | None = None
    doc_type_codes: list[str] | None = None
    start_date: date | None = None
    end_date: date | None = None
