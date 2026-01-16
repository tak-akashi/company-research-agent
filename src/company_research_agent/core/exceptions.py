"""Custom exceptions for Company Research Agent."""

from dataclasses import dataclass


class CompanyResearchAgentError(Exception):
    """Base exception for all Company Research Agent errors."""

    pass


@dataclass
class EDINETAPIError(CompanyResearchAgentError):
    """Base exception for EDINET API errors.

    Attributes:
        status_code: HTTP status code or internal EDINET status code.
        message: Error message describing the issue.
        endpoint: The API endpoint that was called.
    """

    status_code: int
    message: str
    endpoint: str

    def __str__(self) -> str:
        return f"EDINET API Error [{self.status_code}] at {self.endpoint}: {self.message}"


@dataclass
class EDINETAuthenticationError(EDINETAPIError):
    """Raised when EDINET API authentication fails (401).

    This typically occurs when:
    - The API key is invalid or expired.
    - The API key is missing from the request.
    """

    pass


@dataclass
class EDINETNotFoundError(EDINETAPIError):
    """Raised when the requested resource is not found (404).

    This typically occurs when:
    - The document ID does not exist.
    - The document has been removed.
    """

    pass


@dataclass
class EDINETServerError(EDINETAPIError):
    """Raised when EDINET API returns a server error (5xx).

    This error is retryable as it may be a transient issue.
    """

    pass
