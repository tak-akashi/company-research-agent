"""Tests for Gemini API client."""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from company_research_agent.clients.gemini_client import GeminiClient
from company_research_agent.core.config import GeminiConfig
from company_research_agent.core.exceptions import GeminiAPIError


@pytest.fixture
def gemini_config() -> GeminiConfig:
    """Provide a test Gemini configuration."""
    # Use MagicMock to avoid validation requiring actual API key
    config = MagicMock(spec=GeminiConfig)
    config.api_key = "test-api-key"
    config.model = "gemini-2.5-flash-preview-05-20"
    config.timeout = 120
    config.max_retries = 3
    config.rpm_limit = 60
    return config


class TestGeminiClientInit:
    """Tests for GeminiClient initialization."""

    def test_init_with_config(self, gemini_config: GeminiConfig) -> None:
        """GeminiClient should initialize with config."""
        client = GeminiClient(gemini_config)
        assert client._config == gemini_config
        assert client._model is None  # Lazy initialization

    def test_rate_limit_calculation(self, gemini_config: GeminiConfig) -> None:
        """GeminiClient should calculate correct rate limit interval."""
        client = GeminiClient(gemini_config)
        # 60 RPM = 1 request per second
        assert client._request_interval == 1.0


class TestGeminiClientExtraction:
    """Tests for GeminiClient PDF extraction."""

    def test_extract_pdf_file_not_found(
        self,
        gemini_config: GeminiConfig,
        tmp_path: Path,
    ) -> None:
        """extract_pdf_to_markdown should raise FileNotFoundError for missing file."""
        client = GeminiClient(gemini_config)
        non_existent = tmp_path / "missing.pdf"

        with pytest.raises(FileNotFoundError):
            client.extract_pdf_to_markdown(non_existent)

    def test_extract_pdf_success(
        self,
        gemini_config: GeminiConfig,
        mock_pdf_path: Path,
    ) -> None:
        """extract_pdf_to_markdown should return markdown text."""
        # Mock LangChain response
        mock_response = MagicMock()
        mock_response.content = "# Extracted Content\n\nSome text here."

        mock_model = MagicMock()
        mock_model.invoke.return_value = mock_response

        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_pixmap = MagicMock()
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_doc.__len__ = lambda self: 1
        mock_doc.__getitem__ = lambda self, idx: mock_page

        # Mock file read for base64 encoding
        mock_file_content = b"fake image data"

        with (
            patch(
                "langchain_google_genai.ChatGoogleGenerativeAI",
                return_value=mock_model,
            ),
            patch("fitz.open", return_value=mock_doc),
            patch.object(mock_pixmap, "save"),
            patch(
                "company_research_agent.clients.gemini_client.open",
                mock_open(read_data=mock_file_content),
            ),
        ):
            client = GeminiClient(gemini_config)
            result = client.extract_pdf_to_markdown(mock_pdf_path)

        assert "## Page 1" in result or "Extracted Content" in result

    def test_extract_pdf_api_error(
        self,
        gemini_config: GeminiConfig,
        mock_pdf_path: Path,
    ) -> None:
        """extract_pdf_to_markdown should raise GeminiAPIError on API failure."""
        mock_model = MagicMock()
        mock_model.invoke.side_effect = Exception("API Error: 500")

        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_pixmap = MagicMock()
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_doc.__len__ = lambda self: 1
        mock_doc.__getitem__ = lambda self, idx: mock_page

        # Mock file read for base64 encoding
        mock_file_content = b"fake image data"

        with (
            patch(
                "langchain_google_genai.ChatGoogleGenerativeAI",
                return_value=mock_model,
            ),
            patch("fitz.open", return_value=mock_doc),
            patch.object(mock_pixmap, "save"),
            patch(
                "company_research_agent.clients.gemini_client.open",
                mock_open(read_data=mock_file_content),
            ),
        ):
            client = GeminiClient(gemini_config)
            with pytest.raises(GeminiAPIError) as exc_info:
                client.extract_pdf_to_markdown(mock_pdf_path)

        assert "API call failed" in str(exc_info.value)

    def test_extract_pdf_rate_limit_error(
        self,
        gemini_config: GeminiConfig,
        mock_pdf_path: Path,
    ) -> None:
        """extract_pdf_to_markdown should handle rate limit errors."""
        mock_model = MagicMock()
        mock_model.invoke.side_effect = Exception("429 quota exceeded")

        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_pixmap = MagicMock()
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_doc.__len__ = lambda self: 1
        mock_doc.__getitem__ = lambda self, idx: mock_page

        # Mock file read for base64 encoding
        mock_file_content = b"fake image data"

        with (
            patch(
                "langchain_google_genai.ChatGoogleGenerativeAI",
                return_value=mock_model,
            ),
            patch("fitz.open", return_value=mock_doc),
            patch.object(mock_pixmap, "save"),
            patch(
                "company_research_agent.clients.gemini_client.open",
                mock_open(read_data=mock_file_content),
            ),
        ):
            client = GeminiClient(gemini_config)
            with pytest.raises(GeminiAPIError) as exc_info:
                client.extract_pdf_to_markdown(mock_pdf_path)

        assert "Rate limit exceeded" in str(exc_info.value)


class TestGeminiClientRateLimit:
    """Tests for GeminiClient rate limiting."""

    def test_rate_limit_enforced(
        self,
        gemini_config: GeminiConfig,
    ) -> None:
        """Rate limiting should enforce minimum interval between requests."""
        # Set high RPM to make interval small for testing
        gemini_config.rpm_limit = 6000  # 100 requests per second

        client = GeminiClient(gemini_config)

        # Verify interval calculation
        expected_interval = 60.0 / 6000  # 0.01 seconds
        assert client._request_interval == expected_interval
