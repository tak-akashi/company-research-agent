"""Tests for custom exceptions."""

import pytest

from company_research_agent.core.exceptions import (
    CompanyResearchAgentError,
    EDINETAPIError,
    EDINETAuthenticationError,
    EDINETNotFoundError,
    EDINETServerError,
)


class TestCompanyResearchAgentError:
    """Tests for CompanyResearchAgentError base class."""

    def test_is_exception(self) -> None:
        """CompanyResearchAgentError should be an Exception."""
        error = CompanyResearchAgentError("test error")
        assert isinstance(error, Exception)

    def test_message(self) -> None:
        """CompanyResearchAgentError should preserve message."""
        error = CompanyResearchAgentError("test message")
        assert str(error) == "test message"


class TestEDINETAPIError:
    """Tests for EDINETAPIError class."""

    def test_attributes(self) -> None:
        """EDINETAPIError should store status_code, message, and endpoint."""
        error = EDINETAPIError(
            status_code=400,
            message="Bad Request",
            endpoint="/documents.json",
        )
        assert error.status_code == 400
        assert error.message == "Bad Request"
        assert error.endpoint == "/documents.json"

    def test_str_representation(self) -> None:
        """EDINETAPIError should have informative string representation."""
        error = EDINETAPIError(
            status_code=400,
            message="Bad Request",
            endpoint="/documents.json",
        )
        error_str = str(error)
        assert "400" in error_str
        assert "Bad Request" in error_str
        assert "/documents.json" in error_str

    def test_is_company_research_agent_error(self) -> None:
        """EDINETAPIError should be a CompanyResearchAgentError."""
        error = EDINETAPIError(
            status_code=400,
            message="Bad Request",
            endpoint="/test",
        )
        assert isinstance(error, CompanyResearchAgentError)


class TestEDINETAuthenticationError:
    """Tests for EDINETAuthenticationError class."""

    def test_inheritance(self) -> None:
        """EDINETAuthenticationError should inherit from EDINETAPIError."""
        error = EDINETAuthenticationError(
            status_code=401,
            message="Unauthorized",
            endpoint="/documents.json",
        )
        assert isinstance(error, EDINETAPIError)
        assert isinstance(error, CompanyResearchAgentError)

    def test_typical_401_error(self) -> None:
        """EDINETAuthenticationError should handle typical 401 response."""
        error = EDINETAuthenticationError(
            status_code=401,
            message="Access denied due to invalid subscription key",
            endpoint="/documents.json",
        )
        assert error.status_code == 401
        assert "invalid subscription key" in error.message


class TestEDINETNotFoundError:
    """Tests for EDINETNotFoundError class."""

    def test_inheritance(self) -> None:
        """EDINETNotFoundError should inherit from EDINETAPIError."""
        error = EDINETNotFoundError(
            status_code=404,
            message="Not Found",
            endpoint="/documents/S100TEST",
        )
        assert isinstance(error, EDINETAPIError)
        assert isinstance(error, CompanyResearchAgentError)

    def test_typical_404_error(self) -> None:
        """EDINETNotFoundError should handle typical 404 response."""
        error = EDINETNotFoundError(
            status_code=404,
            message="Document not found",
            endpoint="/documents/S100INVALID",
        )
        assert error.status_code == 404
        assert "not found" in error.message.lower()


class TestEDINETServerError:
    """Tests for EDINETServerError class."""

    def test_inheritance(self) -> None:
        """EDINETServerError should inherit from EDINETAPIError."""
        error = EDINETServerError(
            status_code=500,
            message="Internal Server Error",
            endpoint="/documents.json",
        )
        assert isinstance(error, EDINETAPIError)
        assert isinstance(error, CompanyResearchAgentError)

    def test_various_5xx_codes(self) -> None:
        """EDINETServerError should handle various 5xx status codes."""
        for status_code in [500, 502, 503, 504]:
            error = EDINETServerError(
                status_code=status_code,
                message=f"Server error {status_code}",
                endpoint="/test",
            )
            assert error.status_code == status_code

    def test_can_be_caught_for_retry(self) -> None:
        """EDINETServerError should be catchable for retry logic."""
        error = EDINETServerError(
            status_code=503,
            message="Service Unavailable",
            endpoint="/documents.json",
        )

        with pytest.raises(EDINETServerError) as exc_info:
            raise error

        assert exc_info.value.status_code == 503
