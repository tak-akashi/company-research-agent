"""Tests for download path utilities."""

from pathlib import Path

from company_research_agent.core.download_path import (
    build_download_path,
    find_document_in_hierarchy,
    parse_period_to_yyyymm,
    sanitize_filename,
)


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_normal_string(self) -> None:
        """Normal string should be unchanged."""
        assert sanitize_filename("トヨタ自動車") == "トヨタ自動車"

    def test_string_with_slash(self) -> None:
        """Slash should be replaced with underscore."""
        assert sanitize_filename("トヨタ/自動車") == "トヨタ_自動車"

    def test_string_with_colon(self) -> None:
        """Colon should be replaced with underscore."""
        assert sanitize_filename("Company:Name") == "Company_Name"

    def test_string_with_multiple_invalid_chars(self) -> None:
        """Multiple invalid chars should be replaced."""
        assert sanitize_filename("A<B>C:D") == "A_B_C_D"

    def test_none_returns_unknown(self) -> None:
        """None should return 'unknown'."""
        assert sanitize_filename(None) == "unknown"

    def test_empty_string_returns_unknown(self) -> None:
        """Empty string should return 'unknown'."""
        assert sanitize_filename("") == "unknown"

    def test_multiple_underscores_collapsed(self) -> None:
        """Multiple consecutive underscores should be collapsed."""
        assert sanitize_filename("A__B___C") == "A_B_C"


class TestParsePeriodToYYYYMM:
    """Tests for parse_period_to_yyyymm function."""

    def test_valid_date(self) -> None:
        """Valid date should be parsed correctly."""
        assert parse_period_to_yyyymm("2025-12-31") == "202512"

    def test_another_valid_date(self) -> None:
        """Another valid date."""
        assert parse_period_to_yyyymm("2024-03-31") == "202403"

    def test_none_returns_unknown(self) -> None:
        """None should return 'unknown'."""
        assert parse_period_to_yyyymm(None) == "unknown"

    def test_invalid_format_returns_unknown(self) -> None:
        """Invalid format should return 'unknown'."""
        assert parse_period_to_yyyymm("invalid") == "unknown"


class TestBuildDownloadPath:
    """Tests for build_download_path function."""

    def test_full_metadata(self) -> None:
        """Full metadata should create complete path."""
        path = build_download_path(
            base_dir=Path("downloads"),
            sec_code="72030",
            filer_name="トヨタ自動車株式会社",
            doc_type_code="120",
            period_end="2025-03-31",
            doc_id="S100ABCD",
        )
        assert path == Path(
            "downloads/72030_トヨタ自動車株式会社/120_有価証券報告書/202503/S100ABCD.pdf"
        )

    def test_partial_metadata(self) -> None:
        """Partial metadata should use 'unknown' placeholders."""
        path = build_download_path(
            base_dir=Path("downloads"),
            sec_code=None,
            filer_name=None,
            doc_type_code=None,
            period_end=None,
            doc_id="S100EFGH",
        )
        assert "unknown" in str(path)
        assert path.name == "S100EFGH.pdf"

    def test_default_base_dir(self) -> None:
        """None base_dir should use default."""
        path = build_download_path(
            base_dir=None,
            sec_code="72030",
            filer_name="Test",
            doc_type_code="120",
            period_end="2025-01-01",
            doc_id="S100TEST",
        )
        assert path.parts[0] == "downloads"


class TestFindDocumentInHierarchy:
    """Tests for find_document_in_hierarchy function."""

    def test_nonexistent_directory_returns_none(self) -> None:
        """Non-existent directory should return None."""
        result = find_document_in_hierarchy(
            Path("/nonexistent/directory"),
            "S100ABCD",
        )
        assert result is None

    def test_find_in_temp_directory(self, tmp_path: Path) -> None:
        """Should find document in hierarchy."""
        # Create test file
        test_file = tmp_path / "72030_Test" / "120_有報" / "202501" / "S100TEST.pdf"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test")

        result = find_document_in_hierarchy(tmp_path, "S100TEST")
        assert result is not None
        assert result == test_file

    def test_not_found_returns_none(self, tmp_path: Path) -> None:
        """Non-existent document should return None."""
        result = find_document_in_hierarchy(tmp_path, "S100NOTFOUND")
        assert result is None
