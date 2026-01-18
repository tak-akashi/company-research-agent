"""Download path utilities for hierarchical folder structure."""

from __future__ import annotations

import re
from pathlib import Path

from company_research_agent.core.doc_type_mapping import get_doc_type_name

# Characters not allowed in file/folder names
INVALID_CHARS_PATTERN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Default download directory
DEFAULT_DOWNLOAD_DIR = Path("downloads")


def sanitize_filename(name: str | None) -> str:
    """Sanitize a string for use in file/folder names.

    Replaces invalid characters with underscores and removes leading/trailing spaces.

    Args:
        name: The string to sanitize.

    Returns:
        Sanitized string safe for use in file names.

    Example:
        >>> sanitize_filename("トヨタ/自動車")
        'トヨタ_自動車'
        >>> sanitize_filename(None)
        'unknown'
    """
    if name is None:
        return "unknown"

    # Replace invalid characters with underscore
    sanitized = INVALID_CHARS_PATTERN.sub("_", name)

    # Remove leading/trailing whitespace
    sanitized = sanitized.strip()

    # Replace multiple consecutive underscores with single underscore
    sanitized = re.sub(r"_+", "_", sanitized)

    return sanitized or "unknown"


def parse_period_to_yyyymm(period_end: str | None) -> str:
    """Parse period_end date to YYYYMM format.

    Args:
        period_end: Period end date in YYYY-MM-DD format, or None.

    Returns:
        YYYYMM format string, or "unknown" if parsing fails.

    Example:
        >>> parse_period_to_yyyymm("2025-12-31")
        '202512'
        >>> parse_period_to_yyyymm(None)
        'unknown'
    """
    if period_end is None:
        return "unknown"

    # Expected format: YYYY-MM-DD
    parts = period_end.split("-")
    if len(parts) >= 2:
        return f"{parts[0]}{parts[1]}"

    return "unknown"


def build_download_path(
    base_dir: Path | None,
    sec_code: str | None,
    filer_name: str | None,
    doc_type_code: str | None,
    period_end: str | None,
    doc_id: str,
) -> Path:
    """Build hierarchical download path for a document.

    Creates path in format:
    {base_dir}/{sec_code}_{filer_name}/{doc_type_code}_{doc_type_name}/{YYYYMM}/{doc_id}.pdf

    Args:
        base_dir: Base download directory. Defaults to "downloads".
        sec_code: Securities code (e.g., "72030").
        filer_name: Company name (e.g., "トヨタ自動車").
        doc_type_code: Document type code (e.g., "120").
        period_end: Period end date in YYYY-MM-DD format.
        doc_id: Document ID (e.g., "S100ABCD").

    Returns:
        Full path for the document.

    Example:
        >>> path = build_download_path(
        ...     base_dir=Path("downloads"),
        ...     sec_code="72030",
        ...     filer_name="トヨタ自動車株式会社",
        ...     doc_type_code="120",
        ...     period_end="2025-03-31",
        ...     doc_id="S100ABCD",
        ... )
        >>> str(path)
        'downloads/72030_トヨタ自動車株式会社/120_有価証券報告書/202503/S100ABCD.pdf'
    """
    if base_dir is None:
        base_dir = DEFAULT_DOWNLOAD_DIR

    # Build company folder name: {sec_code}_{filer_name}
    sec_code_safe = sec_code or "unknown"
    filer_name_safe = sanitize_filename(filer_name)
    company_folder = f"{sec_code_safe}_{filer_name_safe}"

    # Build document type folder name: {doc_type_code}_{doc_type_name}
    doc_type_code_safe = doc_type_code or "unknown"
    doc_type_name = get_doc_type_name(doc_type_code)
    doc_type_folder = f"{doc_type_code_safe}_{doc_type_name}"

    # Build period folder name: YYYYMM
    period_folder = parse_period_to_yyyymm(period_end)

    # Construct full path
    return base_dir / company_folder / doc_type_folder / period_folder / f"{doc_id}.pdf"


def find_document_in_hierarchy(
    base_dir: Path,
    doc_id: str,
) -> Path | None:
    """Find a document by doc_id in the hierarchical folder structure.

    Searches recursively through the download directory.

    Args:
        base_dir: Base download directory to search.
        doc_id: Document ID to find.

    Returns:
        Path to the document if found, None otherwise.

    Example:
        >>> path = find_document_in_hierarchy(Path("downloads"), "S100ABCD")
        >>> path is not None
        True
    """
    if not base_dir.exists():
        return None

    # Search for the file recursively
    pattern = f"**/{doc_id}.pdf"
    matches = list(base_dir.glob(pattern))

    if matches:
        return matches[0]

    return None
