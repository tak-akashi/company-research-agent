"""Tests for EDINET code list client."""

import io
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from company_research_agent.clients.edinet_code_list_client import EDINETCodeListClient
from company_research_agent.core.exceptions import CodeListDownloadError


@pytest.fixture
def sample_csv_content() -> bytes:
    """Sample EDINET code list CSV content."""
    return """ダウンロード日時: 2024-01-15 10:00
ＥＤＩＮＥＴコード,提出者業種,提出者名,提出者名（カナ）,提出者名（英字）,所在地,証券コード,上場区分
E02144,輸送用機器,トヨタ自動車株式会社,トヨタジドウシャ,TOYOTA MOTOR,愛知県,72030,上場
E02158,輸送用機器,トヨタ紡織株式会社,トヨタボウショク,TOYOTA BOSHOKU,愛知県,35990,上場
E02160,輸送用機器,トヨタ車体株式会社,トヨタシャタイ,TOYOTA AUTO BODY,愛知県,71160,上場
E00001,サービス業,テスト株式会社,テスト,TEST CORP.,,00000,非上場
""".encode("cp932")


@pytest.fixture
def sample_zip_content(sample_csv_content: bytes) -> bytes:
    """Sample EDINET code list ZIP content."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("EdinetcodeDlInfo.csv", sample_csv_content)
    return zip_buffer.getvalue()


@pytest.fixture
def tmp_cache_dir(tmp_path: Path) -> Path:
    """Temporary cache directory."""
    cache_dir = tmp_path / "edinet_code_list"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


class TestEDINETCodeListClientInit:
    """Tests for EDINETCodeListClient initialization."""

    def test_init_default(self) -> None:
        """Should initialize with default values."""
        client = EDINETCodeListClient()
        assert client._cache_dir == EDINETCodeListClient.CACHE_DIR
        assert client._cache_validity_days == EDINETCodeListClient.CACHE_VALIDITY_DAYS
        assert client._companies is None

    def test_init_custom_cache_dir(self, tmp_cache_dir: Path) -> None:
        """Should accept custom cache directory."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir)
        assert client._cache_dir == tmp_cache_dir


class TestCacheValidation:
    """Tests for cache validation."""

    def test_cache_invalid_when_csv_missing(self, tmp_cache_dir: Path) -> None:
        """Cache should be invalid when CSV file is missing."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir)
        assert not client._is_cache_valid()

    def test_cache_invalid_when_timestamp_missing(
        self, tmp_cache_dir: Path, sample_csv_content: bytes
    ) -> None:
        """Cache should be invalid when timestamp file is missing."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir)
        (tmp_cache_dir / "EdinetcodeDlInfo.csv").write_bytes(sample_csv_content)
        assert not client._is_cache_valid()

    def test_cache_valid_within_expiry(
        self, tmp_cache_dir: Path, sample_csv_content: bytes
    ) -> None:
        """Cache should be valid within expiry period."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir, cache_validity_days=7)
        (tmp_cache_dir / "EdinetcodeDlInfo.csv").write_bytes(sample_csv_content)
        (tmp_cache_dir / ".timestamp").write_text(datetime.now().isoformat())
        assert client._is_cache_valid()

    def test_cache_invalid_after_expiry(
        self, tmp_cache_dir: Path, sample_csv_content: bytes
    ) -> None:
        """Cache should be invalid after expiry period."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir, cache_validity_days=7)
        (tmp_cache_dir / "EdinetcodeDlInfo.csv").write_bytes(sample_csv_content)
        expired_time = datetime.now() - timedelta(days=8)
        (tmp_cache_dir / ".timestamp").write_text(expired_time.isoformat())
        assert not client._is_cache_valid()


class TestDownloadAndExtract:
    """Tests for download and extract functionality."""

    @pytest.mark.asyncio
    async def test_download_success(self, tmp_cache_dir: Path, sample_zip_content: bytes) -> None:
        """Should download and extract ZIP successfully."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir)

        mock_response = MagicMock()
        mock_response.content = sample_zip_content
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await client._download_and_extract()

        assert (tmp_cache_dir / "EdinetcodeDlInfo.csv").exists()
        assert (tmp_cache_dir / ".timestamp").exists()

    @pytest.mark.asyncio
    async def test_download_http_error(self, tmp_cache_dir: Path) -> None:
        """Should raise CodeListDownloadError on HTTP error."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError(
                    "Server Error", request=MagicMock(), response=mock_response
                )
            )
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(CodeListDownloadError):
                await client._download_and_extract()


class TestLoadFromCache:
    """Tests for loading from cache."""

    def test_load_from_cache(self, tmp_cache_dir: Path, sample_csv_content: bytes) -> None:
        """Should load companies from cache."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir)
        (tmp_cache_dir / "EdinetcodeDlInfo.csv").write_bytes(sample_csv_content)

        client._load_from_cache()

        assert client._companies is not None
        assert len(client._companies) == 4
        assert client._companies_by_edinet_code is not None
        assert "E02144" in client._companies_by_edinet_code
        assert client._companies_by_sec_code is not None
        assert "72030" in client._companies_by_sec_code


class TestSearchCompanies:
    """Tests for company search functionality."""

    @pytest.mark.asyncio
    async def test_search_by_name(self, tmp_cache_dir: Path, sample_csv_content: bytes) -> None:
        """Should find companies by name with similarity score."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir)
        (tmp_cache_dir / "EdinetcodeDlInfo.csv").write_bytes(sample_csv_content)
        (tmp_cache_dir / ".timestamp").write_text(datetime.now().isoformat())

        candidates = await client.search_companies("トヨタ")

        assert len(candidates) >= 1
        # First result should be Toyota (highest score)
        assert "トヨタ" in candidates[0].company.company_name
        # Verify Toyota companies are ranked high
        toyota_candidates = [c for c in candidates if "トヨタ" in c.company.company_name]
        assert len(toyota_candidates) >= 1

    @pytest.mark.asyncio
    async def test_search_by_edinet_code(
        self, tmp_cache_dir: Path, sample_csv_content: bytes
    ) -> None:
        """Should find company by EDINET code with 100% match."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir)
        (tmp_cache_dir / "EdinetcodeDlInfo.csv").write_bytes(sample_csv_content)
        (tmp_cache_dir / ".timestamp").write_text(datetime.now().isoformat())

        candidates = await client.search_companies("E02144")

        assert len(candidates) == 1
        assert candidates[0].company.edinet_code == "E02144"
        assert candidates[0].similarity_score == 100.0
        assert candidates[0].match_field == "edinet_code"

    @pytest.mark.asyncio
    async def test_search_by_sec_code(self, tmp_cache_dir: Path, sample_csv_content: bytes) -> None:
        """Should find company by securities code."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir)
        (tmp_cache_dir / "EdinetcodeDlInfo.csv").write_bytes(sample_csv_content)
        (tmp_cache_dir / ".timestamp").write_text(datetime.now().isoformat())

        candidates = await client.search_companies("7203")

        assert len(candidates) == 1
        assert candidates[0].company.sec_code == "72030"
        assert candidates[0].similarity_score == 100.0
        assert candidates[0].match_field == "sec_code"

    @pytest.mark.asyncio
    async def test_exact_match_scores_highest(
        self, tmp_cache_dir: Path, sample_csv_content: bytes
    ) -> None:
        """Exact matches should score highest."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir)
        (tmp_cache_dir / "EdinetcodeDlInfo.csv").write_bytes(sample_csv_content)
        (tmp_cache_dir / ".timestamp").write_text(datetime.now().isoformat())

        candidates = await client.search_companies("トヨタ自動車")

        assert len(candidates) >= 1
        # First result should be the best match
        assert candidates[0].company.company_name == "トヨタ自動車株式会社"


class TestGetByCode:
    """Tests for get by code methods."""

    @pytest.mark.asyncio
    async def test_get_by_edinet_code_found(
        self, tmp_cache_dir: Path, sample_csv_content: bytes
    ) -> None:
        """Should return company when EDINET code exists."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir)
        (tmp_cache_dir / "EdinetcodeDlInfo.csv").write_bytes(sample_csv_content)
        (tmp_cache_dir / ".timestamp").write_text(datetime.now().isoformat())

        company = await client.get_by_edinet_code("E02144")

        assert company is not None
        assert company.edinet_code == "E02144"
        assert company.company_name == "トヨタ自動車株式会社"

    @pytest.mark.asyncio
    async def test_get_by_edinet_code_not_found(
        self, tmp_cache_dir: Path, sample_csv_content: bytes
    ) -> None:
        """Should return None when EDINET code does not exist."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir)
        (tmp_cache_dir / "EdinetcodeDlInfo.csv").write_bytes(sample_csv_content)
        (tmp_cache_dir / ".timestamp").write_text(datetime.now().isoformat())

        company = await client.get_by_edinet_code("E99999")

        assert company is None

    @pytest.mark.asyncio
    async def test_get_by_sec_code_found(
        self, tmp_cache_dir: Path, sample_csv_content: bytes
    ) -> None:
        """Should return company when securities code exists."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir)
        (tmp_cache_dir / "EdinetcodeDlInfo.csv").write_bytes(sample_csv_content)
        (tmp_cache_dir / ".timestamp").write_text(datetime.now().isoformat())

        company = await client.get_by_sec_code("72030")

        assert company is not None
        assert company.sec_code == "72030"
        assert company.company_name == "トヨタ自動車株式会社"

    @pytest.mark.asyncio
    async def test_get_by_sec_code_4digit(
        self, tmp_cache_dir: Path, sample_csv_content: bytes
    ) -> None:
        """Should handle 4-digit securities code (add leading zero)."""
        client = EDINETCodeListClient(cache_dir=tmp_cache_dir)
        (tmp_cache_dir / "EdinetcodeDlInfo.csv").write_bytes(sample_csv_content)
        (tmp_cache_dir / ".timestamp").write_text(datetime.now().isoformat())

        company = await client.get_by_sec_code("7203")

        assert company is not None
        assert company.sec_code == "72030"
