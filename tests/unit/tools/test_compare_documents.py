"""Tests for compare_documents tool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from company_research_agent.schemas.query_schemas import ComparisonItem, ComparisonReport
from company_research_agent.tools.compare_documents import compare_documents


@pytest.fixture
def sample_comparison_report() -> ComparisonReport:
    """Sample comparison report fixture."""
    return ComparisonReport(
        documents=["S100ABCD", "S100EFGH"],
        aspects=["事業内容", "財務状況"],
        comparisons=[
            ComparisonItem(
                aspect="事業内容",
                company_a="自動車製造",
                company_b="電機製造",
                difference="主力事業が異なる",
            ),
        ],
        summary="両社とも製造業だが、主力事業が異なる",
    )


class TestCompareDocuments:
    """Tests for compare_documents tool."""

    @pytest.mark.asyncio
    async def test_compare_documents_returns_report(
        self, sample_comparison_report: ComparisonReport
    ) -> None:
        """compare_documents should return comparison report."""
        mock_parser = MagicMock()
        mock_parse_result = MagicMock()
        mock_parse_result.text = "# テスト書類\n\nテスト内容"
        mock_parser.to_markdown.return_value = mock_parse_result

        mock_llm = AsyncMock()
        mock_llm.ainvoke_structured = AsyncMock(return_value=sample_comparison_report)

        with patch(
            "company_research_agent.tools.compare_documents.download_document"
        ) as mock_download:
            mock_download.ainvoke = AsyncMock(return_value="/tmp/test.pdf")

            with patch(
                "company_research_agent.tools.compare_documents.PDFParser"
            ) as mock_parser_class:
                mock_parser_class.return_value = mock_parser

                with patch(
                    "company_research_agent.tools.compare_documents.get_default_provider"
                ) as mock_get_provider:
                    mock_get_provider.return_value = mock_llm

                    result = await compare_documents.ainvoke(
                        {
                            "doc_ids": ["S100ABCD", "S100EFGH"],
                            "aspects": ["事業内容", "財務状況"],
                        }
                    )

                    assert result.documents == ["S100ABCD", "S100EFGH"]
                    assert result.aspects == ["事業内容", "財務状況"]
                    assert len(result.comparisons) == 1
                    assert result.summary == "両社とも製造業だが、主力事業が異なる"

    @pytest.mark.asyncio
    async def test_compare_documents_default_aspects(
        self, sample_comparison_report: ComparisonReport
    ) -> None:
        """compare_documents should use default aspects when not specified."""
        mock_parser = MagicMock()
        mock_parse_result = MagicMock()
        mock_parse_result.text = "# テスト書類\n\nテスト内容"
        mock_parser.to_markdown.return_value = mock_parse_result

        mock_llm = AsyncMock()
        mock_llm.ainvoke_structured = AsyncMock(return_value=sample_comparison_report)

        with patch(
            "company_research_agent.tools.compare_documents.download_document"
        ) as mock_download:
            mock_download.ainvoke = AsyncMock(return_value="/tmp/test.pdf")

            with patch(
                "company_research_agent.tools.compare_documents.PDFParser"
            ) as mock_parser_class:
                mock_parser_class.return_value = mock_parser

                with patch(
                    "company_research_agent.tools.compare_documents.get_default_provider"
                ) as mock_get_provider:
                    mock_get_provider.return_value = mock_llm

                    result = await compare_documents.ainvoke({"doc_ids": ["S100ABCD", "S100EFGH"]})

                    # Default aspects should be set
                    assert result.aspects == ["事業内容", "財務状況", "リスク"]

    @pytest.mark.asyncio
    async def test_compare_documents_requires_at_least_two_docs(self) -> None:
        """compare_documents should raise error with less than 2 documents."""
        with pytest.raises(ValueError, match="At least 2 document IDs are required"):
            await compare_documents.ainvoke({"doc_ids": ["S100ABCD"]})

    @pytest.mark.asyncio
    async def test_compare_documents_downloads_all_documents(
        self, sample_comparison_report: ComparisonReport
    ) -> None:
        """compare_documents should download all specified documents."""
        mock_parser = MagicMock()
        mock_parse_result = MagicMock()
        mock_parse_result.text = "# テスト書類\n\nテスト内容"
        mock_parser.to_markdown.return_value = mock_parse_result

        mock_llm = AsyncMock()
        mock_llm.ainvoke_structured = AsyncMock(return_value=sample_comparison_report)

        with patch(
            "company_research_agent.tools.compare_documents.download_document"
        ) as mock_download:
            mock_download.ainvoke = AsyncMock(return_value="/tmp/test.pdf")

            with patch(
                "company_research_agent.tools.compare_documents.PDFParser"
            ) as mock_parser_class:
                mock_parser_class.return_value = mock_parser

                with patch(
                    "company_research_agent.tools.compare_documents.get_default_provider"
                ) as mock_get_provider:
                    mock_get_provider.return_value = mock_llm

                    await compare_documents.ainvoke(
                        {"doc_ids": ["S100ABCD", "S100EFGH", "S100IJKL"]}
                    )

                    # Should download all 3 documents
                    assert mock_download.ainvoke.call_count == 3
