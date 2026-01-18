"""Tests for summarize_document tool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from company_research_agent.schemas.query_schemas import Summary
from company_research_agent.tools.summarize_document import summarize_document


@pytest.fixture
def sample_summary() -> Summary:
    """Sample summary fixture."""
    return Summary(
        doc_id="S100ABCD",
        focus="事業リスク",
        key_points=["為替リスクがある", "原材料価格の変動リスク"],
        summary_text="主に為替と原材料価格の変動がリスク要因である",
    )


class TestSummarizeDocument:
    """Tests for summarize_document tool."""

    @pytest.mark.asyncio
    async def test_summarize_document_returns_summary(self, sample_summary: Summary) -> None:
        """summarize_document should return summary."""
        mock_parser = MagicMock()
        mock_parse_result = MagicMock()
        mock_parse_result.text = "# 有価証券報告書\n\nリスク情報..."
        mock_parser.to_markdown.return_value = mock_parse_result

        mock_llm = AsyncMock()
        mock_llm.ainvoke_structured = AsyncMock(return_value=sample_summary)

        with patch(
            "company_research_agent.tools.summarize_document.download_document"
        ) as mock_download:
            mock_download.ainvoke = AsyncMock(return_value="/tmp/test.pdf")

            with patch(
                "company_research_agent.tools.summarize_document.PDFParser"
            ) as mock_parser_class:
                mock_parser_class.return_value = mock_parser

                with patch(
                    "company_research_agent.tools.summarize_document.get_default_provider"
                ) as mock_get_provider:
                    mock_get_provider.return_value = mock_llm

                    result = await summarize_document.ainvoke(
                        {"doc_id": "S100ABCD", "focus": "事業リスク"}
                    )

                    assert result.doc_id == "S100ABCD"
                    assert result.focus == "事業リスク"
                    assert len(result.key_points) == 2
                    assert "為替リスクがある" in result.key_points

    @pytest.mark.asyncio
    async def test_summarize_document_without_focus(self, sample_summary: Summary) -> None:
        """summarize_document should work without focus parameter."""
        # Create a summary without focus
        summary_no_focus = Summary(
            doc_id="S100ABCD",
            focus=None,
            key_points=["売上高増加", "海外展開"],
            summary_text="事業は順調に拡大している",
        )

        mock_parser = MagicMock()
        mock_parse_result = MagicMock()
        mock_parse_result.text = "# 有価証券報告書\n\n事業概要..."
        mock_parser.to_markdown.return_value = mock_parse_result

        mock_llm = AsyncMock()
        mock_llm.ainvoke_structured = AsyncMock(return_value=summary_no_focus)

        with patch(
            "company_research_agent.tools.summarize_document.download_document"
        ) as mock_download:
            mock_download.ainvoke = AsyncMock(return_value="/tmp/test.pdf")

            with patch(
                "company_research_agent.tools.summarize_document.PDFParser"
            ) as mock_parser_class:
                mock_parser_class.return_value = mock_parser

                with patch(
                    "company_research_agent.tools.summarize_document.get_default_provider"
                ) as mock_get_provider:
                    mock_get_provider.return_value = mock_llm

                    result = await summarize_document.ainvoke({"doc_id": "S100ABCD"})

                    assert result.doc_id == "S100ABCD"
                    # focus should be None (default focus "全体" is used in prompt)
                    assert result.focus is None

    @pytest.mark.asyncio
    async def test_summarize_document_calls_download_without_metadata(
        self, sample_summary: Summary
    ) -> None:
        """summarize_document should call download_document with None metadata."""
        mock_parser = MagicMock()
        mock_parse_result = MagicMock()
        mock_parse_result.text = "# 有価証券報告書\n\n内容..."
        mock_parser.to_markdown.return_value = mock_parse_result

        mock_llm = AsyncMock()
        mock_llm.ainvoke_structured = AsyncMock(return_value=sample_summary)

        with patch(
            "company_research_agent.tools.summarize_document.download_document"
        ) as mock_download:
            mock_download.ainvoke = AsyncMock(return_value="/tmp/test.pdf")

            with patch(
                "company_research_agent.tools.summarize_document.PDFParser"
            ) as mock_parser_class:
                mock_parser_class.return_value = mock_parser

                with patch(
                    "company_research_agent.tools.summarize_document.get_default_provider"
                ) as mock_get_provider:
                    mock_get_provider.return_value = mock_llm

                    await summarize_document.ainvoke({"doc_id": "S100ABCD"})

                    mock_download.ainvoke.assert_called_once_with(
                        {
                            "doc_id": "S100ABCD",
                            "sec_code": None,
                            "filer_name": None,
                            "doc_type_code": None,
                            "period_end": None,
                        }
                    )

    @pytest.mark.asyncio
    async def test_summarize_document_calls_download_with_metadata(
        self, sample_summary: Summary
    ) -> None:
        """summarize_document should pass metadata to download_document."""
        mock_parser = MagicMock()
        mock_parse_result = MagicMock()
        mock_parse_result.text = "# 有価証券報告書\n\n内容..."
        mock_parser.to_markdown.return_value = mock_parse_result

        mock_llm = AsyncMock()
        mock_llm.ainvoke_structured = AsyncMock(return_value=sample_summary)

        with patch(
            "company_research_agent.tools.summarize_document.download_document"
        ) as mock_download:
            mock_download.ainvoke = AsyncMock(return_value="/tmp/test.pdf")

            with patch(
                "company_research_agent.tools.summarize_document.PDFParser"
            ) as mock_parser_class:
                mock_parser_class.return_value = mock_parser

                with patch(
                    "company_research_agent.tools.summarize_document.get_default_provider"
                ) as mock_get_provider:
                    mock_get_provider.return_value = mock_llm

                    await summarize_document.ainvoke(
                        {
                            "doc_id": "S100ABCD",
                            "sec_code": "72030",
                            "filer_name": "株式会社パワーエックス",
                            "doc_type_code": "140",
                            "period_end": "2025-01-15",
                        }
                    )

                    mock_download.ainvoke.assert_called_once_with(
                        {
                            "doc_id": "S100ABCD",
                            "sec_code": "72030",
                            "filer_name": "株式会社パワーエックス",
                            "doc_type_code": "140",
                            "period_end": "2025-01-15",
                        }
                    )

    @pytest.mark.asyncio
    async def test_summarize_document_calls_pdf_parser(self, sample_summary: Summary) -> None:
        """summarize_document should call PDFParser.to_markdown."""
        mock_parser = MagicMock()
        mock_parse_result = MagicMock()
        mock_parse_result.text = "# 有価証券報告書\n\n内容..."
        mock_parser.to_markdown.return_value = mock_parse_result

        mock_llm = AsyncMock()
        mock_llm.ainvoke_structured = AsyncMock(return_value=sample_summary)

        with patch(
            "company_research_agent.tools.summarize_document.download_document"
        ) as mock_download:
            mock_download.ainvoke = AsyncMock(return_value="/tmp/test.pdf")

            with patch(
                "company_research_agent.tools.summarize_document.PDFParser"
            ) as mock_parser_class:
                mock_parser_class.return_value = mock_parser

                with patch(
                    "company_research_agent.tools.summarize_document.get_default_provider"
                ) as mock_get_provider:
                    mock_get_provider.return_value = mock_llm

                    await summarize_document.ainvoke({"doc_id": "S100ABCD"})

                    mock_parser.to_markdown.assert_called_once()
