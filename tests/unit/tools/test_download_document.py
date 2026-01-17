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
        expected_path = tmp_path / "S100ABCD.pdf"

        with patch("company_research_agent.tools.download_document.DOWNLOAD_DIR", tmp_path):
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

                    result = await download_document.ainvoke({"doc_id": "S100ABCD"})

                    assert result == str(expected_path)
                    mock_client.download_document.assert_called_once_with(
                        "S100ABCD", 2, expected_path
                    )

    @pytest.mark.asyncio
    async def test_download_document_skips_if_exists(self, tmp_path: Path) -> None:
        """download_document should skip download if file already exists."""
        existing_file = tmp_path / "S100ABCD.pdf"
        existing_file.touch()  # Create an empty file

        with patch("company_research_agent.tools.download_document.DOWNLOAD_DIR", tmp_path):
            with patch(
                "company_research_agent.tools.download_document.EDINETClient"
            ) as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client

                result = await download_document.ainvoke({"doc_id": "S100ABCD"})

                assert result == str(existing_file)
                # Should NOT call download
                mock_client_class.assert_not_called()

    @pytest.mark.asyncio
    async def test_download_document_uses_pdf_format(self, tmp_path: Path) -> None:
        """download_document should use PDF format (type=2)."""
        expected_path = tmp_path / "S100EFGH.pdf"

        with patch("company_research_agent.tools.download_document.DOWNLOAD_DIR", tmp_path):
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

                    await download_document.ainvoke({"doc_id": "S100EFGH"})

                    # Check that type=2 (PDF format) is passed
                    mock_client.download_document.assert_called_once()
                    call_args = mock_client.download_document.call_args
                    assert call_args[0][1] == 2  # type parameter

    @pytest.mark.asyncio
    async def test_download_document_creates_correct_filename(self, tmp_path: Path) -> None:
        """download_document should create filename from doc_id."""
        with patch("company_research_agent.tools.download_document.DOWNLOAD_DIR", tmp_path):
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
                        return_value=tmp_path / "S100TEST.pdf"
                    )
                    mock_client_class.return_value = mock_client

                    result = await download_document.ainvoke({"doc_id": "S100TEST"})

                    assert "S100TEST.pdf" in result
