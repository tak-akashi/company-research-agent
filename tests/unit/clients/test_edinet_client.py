"""Tests for EDINET client."""

from datetime import date
from pathlib import Path

import httpx
import pytest
import respx

from company_research_agent.clients.edinet_client import EDINETClient
from company_research_agent.core.config import EDINETConfig
from company_research_agent.core.exceptions import (
    EDINETAuthenticationError,
    EDINETNotFoundError,
    EDINETServerError,
)


class TestEDINETClientInit:
    """Tests for EDINETClient initialization."""

    def test_init_with_config(self, edinet_config: EDINETConfig) -> None:
        """EDINETClient should accept config on initialization."""
        client = EDINETClient(edinet_config)
        assert client._config == edinet_config
        assert client._client is None


class TestEDINETClientContextManager:
    """Tests for EDINETClient context manager."""

    @pytest.mark.asyncio
    async def test_async_context_manager(self, edinet_config: EDINETConfig) -> None:
        """EDINETClient should work as async context manager."""
        async with EDINETClient(edinet_config) as client:
            assert isinstance(client, EDINETClient)

    @pytest.mark.asyncio
    async def test_close_releases_client(self, edinet_config: EDINETConfig) -> None:
        """close() should release the HTTP client."""
        client = EDINETClient(edinet_config)
        # Force client creation
        await client._get_client()
        assert client._client is not None

        await client.close()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_idempotent(self, edinet_config: EDINETConfig) -> None:
        """close() should be safe to call multiple times."""
        client = EDINETClient(edinet_config)
        await client.close()
        await client.close()  # Should not raise


@respx.mock
class TestGetDocumentList:
    """Tests for get_document_list method."""

    @pytest.mark.asyncio
    async def test_get_document_list_success(
        self,
        edinet_config: EDINETConfig,
        sample_document_list_response: dict[str, object],
    ) -> None:
        """get_document_list should return DocumentListResponse on success."""
        respx.get(
            "https://api.edinet-fsa.go.jp/api/v2/documents.json",
        ).mock(return_value=httpx.Response(200, json=sample_document_list_response))

        async with EDINETClient(edinet_config) as client:
            response = await client.get_document_list(date(2024, 1, 15))

        assert response.metadata.status == "200"
        assert response.results is not None
        assert len(response.results) == 2

    @pytest.mark.asyncio
    async def test_get_document_list_metadata_only(
        self,
        edinet_config: EDINETConfig,
        sample_metadata_only_response: dict[str, object],
    ) -> None:
        """get_document_list with include_details=False should return metadata only."""
        respx.get(
            "https://api.edinet-fsa.go.jp/api/v2/documents.json",
        ).mock(return_value=httpx.Response(200, json=sample_metadata_only_response))

        async with EDINETClient(edinet_config) as client:
            response = await client.get_document_list(date(2024, 1, 15), include_details=False)

        assert response.metadata.resultset.count == 50
        assert response.results is None

    @pytest.mark.asyncio
    async def test_get_document_list_401_error(self, edinet_config: EDINETConfig) -> None:
        """get_document_list should raise EDINETAuthenticationError on 401."""
        respx.get(
            "https://api.edinet-fsa.go.jp/api/v2/documents.json",
        ).mock(
            return_value=httpx.Response(
                401,
                json={"message": "Access denied due to invalid subscription key"},
            )
        )

        async with EDINETClient(edinet_config) as client:
            with pytest.raises(EDINETAuthenticationError) as exc_info:
                await client.get_document_list(date(2024, 1, 15))

        assert exc_info.value.status_code == 401
        assert "invalid subscription key" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_get_document_list_404_error(self, edinet_config: EDINETConfig) -> None:
        """get_document_list should raise EDINETNotFoundError on 404."""
        respx.get(
            "https://api.edinet-fsa.go.jp/api/v2/documents.json",
        ).mock(
            return_value=httpx.Response(
                404,
                json={"message": "Not Found"},
            )
        )

        async with EDINETClient(edinet_config) as client:
            with pytest.raises(EDINETNotFoundError) as exc_info:
                await client.get_document_list(date(2024, 1, 15))

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_document_list_internal_404_error(self, edinet_config: EDINETConfig) -> None:
        """get_document_list should handle EDINET internal 404 status."""
        error_response = {
            "metadata": {
                "title": "提出された書類を把握するためのAPI",
                "parameter": {"date": "2024-01-15", "type": "2"},
                "resultset": {"count": 0},
                "processDateTime": "2024-01-15 10:00",
                "status": "404",
                "message": "Not Found",
            }
        }
        respx.get(
            "https://api.edinet-fsa.go.jp/api/v2/documents.json",
        ).mock(return_value=httpx.Response(200, json=error_response))

        async with EDINETClient(edinet_config) as client:
            with pytest.raises(EDINETNotFoundError) as exc_info:
                await client.get_document_list(date(2024, 1, 15))

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_document_list_500_error_triggers_retry(
        self, edinet_config: EDINETConfig, sample_document_list_response: dict[str, object]
    ) -> None:
        """get_document_list should retry on 500 error."""
        route = respx.get("https://api.edinet-fsa.go.jp/api/v2/documents.json")
        route.side_effect = [
            httpx.Response(500, json={"message": "Internal Server Error"}),
            httpx.Response(200, json=sample_document_list_response),
        ]

        async with EDINETClient(edinet_config) as client:
            response = await client.get_document_list(date(2024, 1, 15))

        assert response.metadata.status == "200"
        assert route.call_count == 2

    @pytest.mark.asyncio
    async def test_get_document_list_500_error_max_retries(
        self, edinet_config: EDINETConfig
    ) -> None:
        """get_document_list should fail after max retries on persistent 500."""
        respx.get(
            "https://api.edinet-fsa.go.jp/api/v2/documents.json",
        ).mock(
            return_value=httpx.Response(
                500,
                json={"message": "Internal Server Error"},
            )
        )

        async with EDINETClient(edinet_config) as client:
            with pytest.raises(EDINETServerError) as exc_info:
                await client.get_document_list(date(2024, 1, 15))

        assert exc_info.value.status_code == 500


@respx.mock
class TestDownloadDocument:
    """Tests for download_document method."""

    @pytest.mark.asyncio
    async def test_download_document_pdf_success(
        self, edinet_config: EDINETConfig, tmp_path: Path
    ) -> None:
        """download_document should save PDF file on success."""
        pdf_content = b"%PDF-1.4 sample content"
        respx.get(
            "https://api.edinet-fsa.go.jp/api/v2/documents/S100TEST",
        ).mock(
            return_value=httpx.Response(
                200,
                content=pdf_content,
                headers={"Content-Type": "application/pdf"},
            )
        )

        save_path = tmp_path / "test.pdf"

        async with EDINETClient(edinet_config) as client:
            result_path = await client.download_document("S100TEST", 2, save_path)

        assert result_path == save_path
        assert save_path.exists()
        assert save_path.read_bytes() == pdf_content

    @pytest.mark.asyncio
    async def test_download_document_zip_success(
        self, edinet_config: EDINETConfig, tmp_path: Path
    ) -> None:
        """download_document should save ZIP file on success."""
        zip_content = b"PK\x03\x04 sample zip content"
        respx.get(
            "https://api.edinet-fsa.go.jp/api/v2/documents/S100TEST",
        ).mock(
            return_value=httpx.Response(
                200,
                content=zip_content,
                headers={"Content-Type": "application/octet-stream"},
            )
        )

        save_path = tmp_path / "test.zip"

        async with EDINETClient(edinet_config) as client:
            result_path = await client.download_document("S100TEST", 1, save_path)

        assert result_path == save_path
        assert save_path.exists()
        assert save_path.read_bytes() == zip_content

    @pytest.mark.asyncio
    async def test_download_document_creates_parent_dirs(
        self, edinet_config: EDINETConfig, tmp_path: Path
    ) -> None:
        """download_document should create parent directories if needed."""
        pdf_content = b"%PDF-1.4 sample content"
        respx.get(
            "https://api.edinet-fsa.go.jp/api/v2/documents/S100TEST",
        ).mock(
            return_value=httpx.Response(
                200,
                content=pdf_content,
                headers={"Content-Type": "application/pdf"},
            )
        )

        save_path = tmp_path / "nested" / "dir" / "test.pdf"

        async with EDINETClient(edinet_config) as client:
            await client.download_document("S100TEST", 2, save_path)

        assert save_path.exists()

    @pytest.mark.asyncio
    async def test_download_document_401_error(
        self, edinet_config: EDINETConfig, tmp_path: Path
    ) -> None:
        """download_document should raise EDINETAuthenticationError on 401."""
        respx.get(
            "https://api.edinet-fsa.go.jp/api/v2/documents/S100TEST",
        ).mock(
            return_value=httpx.Response(
                401,
                json={"message": "Access denied"},
            )
        )

        save_path = tmp_path / "test.pdf"

        async with EDINETClient(edinet_config) as client:
            with pytest.raises(EDINETAuthenticationError):
                await client.download_document("S100TEST", 2, save_path)

    @pytest.mark.asyncio
    async def test_download_document_404_error(
        self, edinet_config: EDINETConfig, tmp_path: Path
    ) -> None:
        """download_document should raise EDINETNotFoundError on 404."""
        respx.get(
            "https://api.edinet-fsa.go.jp/api/v2/documents/S100INVALID",
        ).mock(
            return_value=httpx.Response(
                404,
                json={"message": "Document not found"},
            )
        )

        save_path = tmp_path / "test.pdf"

        async with EDINETClient(edinet_config) as client:
            with pytest.raises(EDINETNotFoundError):
                await client.download_document("S100INVALID", 2, save_path)

    @pytest.mark.asyncio
    async def test_download_document_json_error_response(
        self, edinet_config: EDINETConfig, tmp_path: Path
    ) -> None:
        """download_document should handle JSON error in 200 response."""
        error_response = {
            "metadata": {
                "title": "書類取得API",
                "parameter": {},
                "resultset": {"count": 0},
                "processDateTime": "2024-01-15 10:00",
                "status": "404",
                "message": "該当する書類が存在しません",
            }
        }
        respx.get(
            "https://api.edinet-fsa.go.jp/api/v2/documents/S100TEST",
        ).mock(
            return_value=httpx.Response(
                200,
                json=error_response,
                headers={"Content-Type": "application/json"},
            )
        )

        save_path = tmp_path / "test.pdf"

        async with EDINETClient(edinet_config) as client:
            with pytest.raises(EDINETNotFoundError):
                await client.download_document("S100TEST", 2, save_path)

    @pytest.mark.asyncio
    async def test_download_document_retry_on_500(
        self, edinet_config: EDINETConfig, tmp_path: Path
    ) -> None:
        """download_document should retry on 500 error."""
        pdf_content = b"%PDF-1.4 sample content"
        route = respx.get("https://api.edinet-fsa.go.jp/api/v2/documents/S100TEST")
        route.side_effect = [
            httpx.Response(500, json={"message": "Internal Server Error"}),
            httpx.Response(200, content=pdf_content, headers={"Content-Type": "application/pdf"}),
        ]

        save_path = tmp_path / "test.pdf"

        async with EDINETClient(edinet_config) as client:
            await client.download_document("S100TEST", 2, save_path)

        assert save_path.exists()
        assert route.call_count == 2
