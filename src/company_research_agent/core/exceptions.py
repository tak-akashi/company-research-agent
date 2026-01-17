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


@dataclass
class PDFParseError(CompanyResearchAgentError):
    """Raised when PDF parsing fails.

    Attributes:
        message: Error message describing the issue.
        pdf_path: Path to the PDF file that failed to parse.
        strategy: The parsing strategy that was used when the error occurred.
    """

    message: str
    pdf_path: str
    strategy: str | None = None

    def __str__(self) -> str:
        if self.strategy:
            return f"PDF Parse Error [{self.strategy}] for {self.pdf_path}: {self.message}"
        return f"PDF Parse Error for {self.pdf_path}: {self.message}"


@dataclass
class GeminiAPIError(CompanyResearchAgentError):
    """Raised when Gemini API call fails.

    Attributes:
        message: Error message describing the issue.
        model: The Gemini model that was used.
    """

    message: str
    model: str | None = None

    def __str__(self) -> str:
        if self.model:
            return f"Gemini API Error [{self.model}]: {self.message}"
        return f"Gemini API Error: {self.message}"


@dataclass
class YomitokuError(CompanyResearchAgentError):
    """Raised when Yomitoku OCR fails.

    Attributes:
        message: Error message describing the issue.
        pdf_path: Path to the PDF file that failed to process.
    """

    message: str
    pdf_path: str | None = None

    def __str__(self) -> str:
        if self.pdf_path:
            return f"Yomitoku Error for {self.pdf_path}: {self.message}"
        return f"Yomitoku Error: {self.message}"


@dataclass
class LLMAnalysisError(CompanyResearchAgentError):
    """Raised when LLM analysis fails.

    Attributes:
        message: Error message describing the issue.
        node_name: Name of the node where the error occurred.
        model: The LLM model that was used.
    """

    message: str
    node_name: str | None = None
    model: str | None = None

    def __str__(self) -> str:
        parts = ["LLM Analysis Error"]
        if self.node_name:
            parts.append(f"[{self.node_name}]")
        if self.model:
            parts.append(f"({self.model})")
        parts.append(f": {self.message}")
        return "".join(parts)
