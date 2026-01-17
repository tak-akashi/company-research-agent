"""Tests for local cache service."""

from pathlib import Path

from company_research_agent.schemas.cache_schemas import CachedDocumentInfo
from company_research_agent.services.local_cache_service import LocalCacheService


class TestCachedDocumentInfo:
    """Tests for CachedDocumentInfo dataclass."""

    def test_from_path_full_hierarchy(self) -> None:
        """Should parse full hierarchy correctly."""
        path = Path("downloads/72030_トヨタ自動車/120_有価証券報告書/202512/S100ABCD.pdf")
        info = CachedDocumentInfo.from_path(path)

        assert info.doc_id == "S100ABCD"
        assert info.sec_code == "72030"
        assert info.company_name == "トヨタ自動車"
        assert info.doc_type_code == "120"
        assert info.period == "202512"
        assert info.file_path == path

    def test_from_path_flat_structure(self) -> None:
        """Should handle flat structure gracefully."""
        path = Path("downloads/S100ABCD.pdf")
        info = CachedDocumentInfo.from_path(path)

        assert info.doc_id == "S100ABCD"
        assert info.sec_code is None
        assert info.company_name is None
        assert info.file_path == path


class TestLocalCacheService:
    """Tests for LocalCacheService."""

    def test_init_with_default_directory(self) -> None:
        """Should use default directory when none provided."""
        service = LocalCacheService()
        assert service.download_dir == Path("downloads")

    def test_init_with_custom_directory(self, tmp_path: Path) -> None:
        """Should use custom directory when provided."""
        service = LocalCacheService(tmp_path)
        assert service.download_dir == tmp_path

    def test_find_by_doc_id_not_found(self, tmp_path: Path) -> None:
        """Should return None when document not found."""
        service = LocalCacheService(tmp_path)
        result = service.find_by_doc_id("S100NOTFOUND")
        assert result is None

    def test_find_by_doc_id_found(self, tmp_path: Path) -> None:
        """Should find document in hierarchy."""
        # Create test file
        test_file = tmp_path / "72030_Test" / "120_有報" / "202501" / "S100FOUND.pdf"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test content")

        service = LocalCacheService(tmp_path)
        result = service.find_by_doc_id("S100FOUND")

        assert result is not None
        assert result.doc_id == "S100FOUND"
        assert result.file_path == test_file

    def test_find_by_filter(self, tmp_path: Path) -> None:
        """Should find documents matching filter."""
        # Create test files
        file1 = tmp_path / "72030_Test" / "120_有報" / "202501" / "S100A.pdf"
        file2 = tmp_path / "72030_Test" / "140_四半期" / "202501" / "S100B.pdf"
        file1.parent.mkdir(parents=True, exist_ok=True)
        file2.parent.mkdir(parents=True, exist_ok=True)
        file1.write_text("test1")
        file2.write_text("test2")

        service = LocalCacheService(tmp_path)

        # Filter by sec_code and doc_type_code
        results = service.find_by_filter(sec_code="72030", doc_type_code="120")
        assert len(results) == 1
        assert results[0].doc_id == "S100A"

    def test_list_all(self, tmp_path: Path) -> None:
        """Should list all documents."""
        # Create test files
        file1 = tmp_path / "72030_A" / "120_有報" / "202501" / "S100A.pdf"
        file2 = tmp_path / "99050_B" / "120_有報" / "202502" / "S100B.pdf"
        file1.parent.mkdir(parents=True, exist_ok=True)
        file2.parent.mkdir(parents=True, exist_ok=True)
        file1.write_text("test1")
        file2.write_text("test2")

        service = LocalCacheService(tmp_path)
        results = service.list_all()

        assert len(results) == 2

    def test_get_cache_stats(self, tmp_path: Path) -> None:
        """Should return cache statistics."""
        # Create test files
        file1 = tmp_path / "72030_A" / "120_有報" / "202501" / "S100A.pdf"
        file2 = tmp_path / "99050_B" / "120_有報" / "202502" / "S100B.pdf"
        file1.parent.mkdir(parents=True, exist_ok=True)
        file2.parent.mkdir(parents=True, exist_ok=True)
        file1.write_text("test1")
        file2.write_text("test2")

        service = LocalCacheService(tmp_path)
        stats = service.get_cache_stats()

        assert stats["total_documents"] == 2
        assert stats["total_companies"] == 2

    def test_nonexistent_directory(self) -> None:
        """Should handle non-existent directory gracefully."""
        service = LocalCacheService(Path("/nonexistent/path"))

        assert service.find_by_doc_id("S100TEST") is None
        assert service.list_all() == []
        assert service.get_cache_stats() == {"total_documents": 0, "total_companies": 0}
