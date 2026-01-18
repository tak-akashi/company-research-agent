"""Tests for download_document tool."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from company_research_agent.tools.download_document import download_document


class TestDownloadDocument:
    """Tests for download_document tool."""

    @pytest.mark.asyncio
    async def test_download_document_returns_path(self, tmp_path: Path) -> None:
        """download_document should return local file path."""
        # Create hierarchical path structure
        expected_path = tmp_path / "72030_トヨタ" / "120_有価証券報告書" / "202503" / "S100ABCD.pdf"

        with patch("company_research_agent.tools.download_document.DOWNLOAD_DIR", tmp_path):
            with patch(
                "company_research_agent.tools.download_document._cache_service"
            ) as mock_cache:
                mock_cache.find_by_doc_id.return_value = None  # No cache hit

                with patch(
                    "company_research_agent.tools.download_document.EDINETConfig"
                ) as mock_config_class:
                    mock_config_class.return_value = MagicMock()

                    with patch(
                        "company_research_agent.tools.download_document.EDINETClient"
                    ) as mock_client_class:
                        mock_client = MagicMock()
                        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                        mock_client.__aexit__ = AsyncMock(return_value=None)
                        mock_client.download_document = AsyncMock(return_value=expected_path)
                        mock_client_class.return_value = mock_client

                        result = await download_document.ainvoke(
                            {
                                "doc_id": "S100ABCD",
                                "sec_code": "72030",
                                "filer_name": "トヨタ",
                                "doc_type_code": "120",
                                "period_end": "2025-03-31",
                            }
                        )

                        assert result == str(expected_path)
                        mock_client.download_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_document_skips_if_cached(self, tmp_path: Path) -> None:
        """download_document should skip download if file found in cache."""
        # Create cached file with hierarchy structure
        cached_path = tmp_path / "72030_トヨタ" / "120_有価証券報告書" / "202503" / "S100ABCD.pdf"
        cached_path.parent.mkdir(parents=True, exist_ok=True)
        cached_path.touch()

        mock_cached_info = MagicMock()
        mock_cached_info.file_path = cached_path

        with patch("company_research_agent.tools.download_document.DOWNLOAD_DIR", tmp_path):
            with patch(
                "company_research_agent.tools.download_document._cache_service"
            ) as mock_cache:
                mock_cache.find_by_doc_id.return_value = mock_cached_info

                with patch(
                    "company_research_agent.tools.download_document.EDINETClient"
                ) as mock_client_class:
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client

                    result = await download_document.ainvoke({"doc_id": "S100ABCD"})

                    assert result == str(cached_path)
                    # Should NOT call download
                    mock_client_class.assert_not_called()

    @pytest.mark.asyncio
    async def test_download_document_skips_if_path_exists(self, tmp_path: Path) -> None:
        """download_document should skip download if computed path already exists."""
        # Create file at the computed hierarchical path
        existing_path = tmp_path / "72030_トヨタ" / "120_有価証券報告書" / "202503" / "S100ABCD.pdf"
        existing_path.parent.mkdir(parents=True, exist_ok=True)
        existing_path.touch()

        with patch("company_research_agent.tools.download_document.DOWNLOAD_DIR", tmp_path):
            with patch(
                "company_research_agent.tools.download_document._cache_service"
            ) as mock_cache:
                mock_cache.find_by_doc_id.return_value = None  # No cache hit

                with patch(
                    "company_research_agent.tools.download_document.EDINETClient"
                ) as mock_client_class:
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client

                    result = await download_document.ainvoke(
                        {
                            "doc_id": "S100ABCD",
                            "sec_code": "72030",
                            "filer_name": "トヨタ",
                            "doc_type_code": "120",
                            "period_end": "2025-03-31",
                        }
                    )

                    assert result == str(existing_path)
                    # Should NOT call download
                    mock_client_class.assert_not_called()

    @pytest.mark.asyncio
    async def test_download_document_uses_pdf_format(self, tmp_path: Path) -> None:
        """download_document should use PDF format (type=2)."""
        expected_path = tmp_path / "72030_Test" / "120_有価証券報告書" / "202501" / "S100EFGH.pdf"

        with patch("company_research_agent.tools.download_document.DOWNLOAD_DIR", tmp_path):
            with patch(
                "company_research_agent.tools.download_document._cache_service"
            ) as mock_cache:
                mock_cache.find_by_doc_id.return_value = None

                with patch(
                    "company_research_agent.tools.download_document.EDINETConfig"
                ) as mock_config_class:
                    mock_config_class.return_value = MagicMock()

                    with patch(
                        "company_research_agent.tools.download_document.EDINETClient"
                    ) as mock_client_class:
                        mock_client = MagicMock()
                        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                        mock_client.__aexit__ = AsyncMock(return_value=None)
                        mock_client.download_document = AsyncMock(return_value=expected_path)
                        mock_client_class.return_value = mock_client

                        await download_document.ainvoke(
                            {
                                "doc_id": "S100EFGH",
                                "sec_code": "72030",
                                "filer_name": "Test",
                                "doc_type_code": "120",
                                "period_end": "2025-01-31",
                            }
                        )

                        # Check that type=2 (PDF format) is passed
                        mock_client.download_document.assert_called_once()
                        call_args = mock_client.download_document.call_args
                        assert call_args[0][1] == 2  # type parameter

    @pytest.mark.asyncio
    async def test_download_document_creates_hierarchical_path(self, tmp_path: Path) -> None:
        """download_document should create hierarchical path from metadata."""
        with patch("company_research_agent.tools.download_document.DOWNLOAD_DIR", tmp_path):
            with patch(
                "company_research_agent.tools.download_document._cache_service"
            ) as mock_cache:
                mock_cache.find_by_doc_id.return_value = None

                with patch(
                    "company_research_agent.tools.download_document.EDINETConfig"
                ) as mock_config_class:
                    mock_config_class.return_value = MagicMock()

                    with patch(
                        "company_research_agent.tools.download_document.EDINETClient"
                    ) as mock_client_class:
                        mock_client = MagicMock()
                        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                        mock_client.__aexit__ = AsyncMock(return_value=None)
                        mock_client.download_document = AsyncMock(
                            side_effect=lambda doc_id, doc_type, save_path: save_path
                        )
                        mock_client_class.return_value = mock_client

                        result = await download_document.ainvoke(
                            {
                                "doc_id": "S100TEST",
                                "sec_code": "99050",
                                "filer_name": "ソニーグループ株式会社",
                                "doc_type_code": "140",
                                "period_end": "2025-06-30",
                            }
                        )

                        # Check hierarchical path structure
                        assert "99050_ソニーグループ株式会社" in result
                        assert "140_四半期報告書" in result
                        assert "202506" in result
                        assert "S100TEST.pdf" in result
