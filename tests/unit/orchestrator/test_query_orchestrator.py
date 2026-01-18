"""Tests for QueryOrchestrator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from company_research_agent.orchestrator.query_orchestrator import QueryOrchestrator


class TestQueryOrchestratorInit:
    """Tests for QueryOrchestrator initialization."""

    def test_init_default(self) -> None:
        """Should initialize with default provider and tools."""
        with patch(
            "company_research_agent.orchestrator.query_orchestrator.get_default_provider"
        ) as mock_get_provider:
            mock_provider = MagicMock()
            mock_get_provider.return_value = mock_provider

            orchestrator = QueryOrchestrator()

            assert orchestrator._llm_provider == mock_provider
            assert len(orchestrator._tools) == 6  # 6 default tools
            assert orchestrator._agent is None

    def test_init_custom_provider(self) -> None:
        """Should accept custom LLM provider."""
        mock_provider = MagicMock()

        orchestrator = QueryOrchestrator(llm_provider=mock_provider)

        assert orchestrator._llm_provider == mock_provider


class TestDefaultTools:
    """Tests for default tools."""

    def test_default_tools_list(self) -> None:
        """Should return 6 default tools."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()
            tools = orchestrator._default_tools()

            assert len(tools) == 6
            tool_names = [t.name for t in tools]
            assert "search_company" in tool_names
            assert "search_documents" in tool_names
            assert "download_document" in tool_names
            assert "analyze_document" in tool_names
            assert "compare_documents" in tool_names
            assert "summarize_document" in tool_names


class TestInferIntent:
    """Tests for intent inference."""

    def test_infer_intent_analyze(self) -> None:
        """Should infer 'analyze' intent."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            intent = orchestrator._infer_intent(
                ["search_company", "search_documents", "analyze_document"]
            )

            assert intent == "分析"

    def test_infer_intent_compare(self) -> None:
        """Should infer 'compare' intent."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            intent = orchestrator._infer_intent(
                ["search_company", "search_documents", "compare_documents"]
            )

            assert intent == "比較"

    def test_infer_intent_summarize(self) -> None:
        """Should infer 'summarize' intent."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            intent = orchestrator._infer_intent(["search_documents", "summarize_document"])

            assert intent == "要約"

    def test_infer_intent_download(self) -> None:
        """Should infer 'download' intent."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            intent = orchestrator._infer_intent(
                ["search_company", "search_documents", "download_document"]
            )

            assert intent == "取得"

    def test_infer_intent_search(self) -> None:
        """Should infer 'search' intent."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            intent = orchestrator._infer_intent(["search_company", "search_documents"])

            assert intent == "検索"


class TestParseResult:
    """Tests for result parsing."""

    def test_parse_result_extracts_tools(self) -> None:
        """Should extract used tools from messages."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            # Mock messages with tool calls
            mock_msg1 = MagicMock()
            mock_msg1.tool_calls = [{"name": "search_company"}]
            mock_msg2 = MagicMock()
            mock_msg2.tool_calls = [{"name": "search_documents"}]
            mock_msg3 = MagicMock()
            mock_msg3.tool_calls = None
            mock_msg3.content = "検索結果です"

            result = orchestrator._parse_result(
                "トヨタの有報を探して",
                {"messages": [mock_msg1, mock_msg2, mock_msg3]},
            )

            assert result.query == "トヨタの有報を探して"
            assert result.tools_used == ["search_company", "search_documents"]
            assert result.intent == "検索"
            assert result.result == "検索結果です"

    def test_parse_result_extracts_document_metadata(self) -> None:
        """Should extract document metadata from tool messages."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            # Mock message with metadata from analyze_document
            mock_tool_msg = MagicMock()
            mock_tool_msg.tool_calls = None
            mock_tool_msg.content = {
                "report": MagicMock(),
                "metadata": {
                    "doc_id": "S100ABCD",
                    "filer_name": "トヨタ自動車株式会社",
                    "doc_description": "有価証券報告書－第120期(2023/04/01－2024/03/31)",
                    "period_start": "2023-04-01",
                    "period_end": "2024-03-31",
                },
            }

            mock_final_msg = MagicMock()
            mock_final_msg.tool_calls = None
            mock_final_msg.content = "分析結果です"

            result = orchestrator._parse_result(
                "トヨタの有報を分析して",
                {"messages": [mock_tool_msg, mock_final_msg]},
            )

            assert len(result.documents) == 1
            assert result.documents[0].doc_id == "S100ABCD"
            assert result.documents[0].filer_name == "トヨタ自動車株式会社"
            assert (
                result.documents[0].doc_description
                == "有価証券報告書－第120期(2023/04/01－2024/03/31)"
            )
            assert result.documents[0].period_start == "2023-04-01"
            assert result.documents[0].period_end == "2024-03-31"

    def test_parse_result_documents_empty_when_no_metadata(self) -> None:
        """Should return empty documents list when no metadata."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            mock_msg = MagicMock()
            mock_msg.tool_calls = None
            mock_msg.content = "検索結果です"

            result = orchestrator._parse_result(
                "トヨタの有報を探して",
                {"messages": [mock_msg]},
            )

            assert result.documents == []


class TestExtractDocumentMetadata:
    """Tests for _extract_document_metadata method."""

    def test_extract_single_document_metadata(self) -> None:
        """Should extract metadata from single document."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            mock_msg = MagicMock()
            mock_msg.content = {
                "report": MagicMock(),
                "metadata": {
                    "doc_id": "S100WXYZ",
                    "filer_name": "ソフトバンクグループ株式会社",
                    "doc_description": "有価証券報告書－第45期(2024/04/01－2025/03/31)",
                    "period_start": "2024-04-01",
                    "period_end": "2025-03-31",
                },
            }

            documents = orchestrator._extract_document_metadata([mock_msg])

            assert len(documents) == 1
            assert documents[0].doc_id == "S100WXYZ"
            assert documents[0].filer_name == "ソフトバンクグループ株式会社"
            assert documents[0].doc_description == "有価証券報告書－第45期(2024/04/01－2025/03/31)"
            assert documents[0].period_start == "2024-04-01"
            assert documents[0].period_end == "2025-03-31"

    def test_extract_multiple_documents_metadata(self) -> None:
        """Should extract metadata from multiple documents."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            mock_msg1 = MagicMock()
            mock_msg1.content = {
                "report": MagicMock(),
                "metadata": {
                    "doc_id": "S100AAAA",
                    "filer_name": "トヨタ自動車株式会社",
                    "doc_description": "有価証券報告書－第120期",
                    "period_start": "2023-04-01",
                    "period_end": "2024-03-31",
                },
            }
            mock_msg2 = MagicMock()
            mock_msg2.content = {
                "report": MagicMock(),
                "metadata": {
                    "doc_id": "S100BBBB",
                    "filer_name": "本田技研工業株式会社",
                    "doc_description": "有価証券報告書－第100期",
                    "period_start": "2023-04-01",
                    "period_end": "2024-03-31",
                },
            }

            documents = orchestrator._extract_document_metadata([mock_msg1, mock_msg2])

            assert len(documents) == 2
            assert documents[0].doc_id == "S100AAAA"
            assert documents[0].filer_name == "トヨタ自動車株式会社"
            assert documents[1].doc_id == "S100BBBB"
            assert documents[1].filer_name == "本田技研工業株式会社"

    def test_extract_metadata_empty_when_no_content(self) -> None:
        """Should return empty list when no content."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            mock_msg = MagicMock(spec=[])  # No content attribute

            documents = orchestrator._extract_document_metadata([mock_msg])

            assert documents == []

    def test_extract_metadata_skips_non_dict_content(self) -> None:
        """Should skip messages with non-dict content."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            mock_msg1 = MagicMock()
            mock_msg1.content = "これはテキストです"

            mock_msg2 = MagicMock()
            mock_msg2.content = {
                "report": MagicMock(),
                "metadata": {
                    "doc_id": "S100CCCC",
                    "filer_name": "任天堂株式会社",
                    "doc_description": None,
                    "period_start": None,
                    "period_end": None,
                },
            }

            documents = orchestrator._extract_document_metadata([mock_msg1, mock_msg2])

            assert len(documents) == 1
            assert documents[0].doc_id == "S100CCCC"
            assert documents[0].filer_name == "任天堂株式会社"

    def test_extract_metadata_skips_without_doc_id(self) -> None:
        """Should skip metadata without doc_id."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            mock_msg = MagicMock()
            mock_msg.content = {
                "metadata": {
                    "filer_name": "テスト企業",
                    # doc_id is missing
                },
            }

            documents = orchestrator._extract_document_metadata([mock_msg])

            assert documents == []


class TestProcess:
    """Tests for process method."""

    @pytest.mark.asyncio
    async def test_process_invokes_agent(self) -> None:
        """Should invoke agent with query."""
        with patch(
            "company_research_agent.orchestrator.query_orchestrator.get_default_provider"
        ) as mock_get_provider:
            mock_provider = MagicMock()
            mock_model = MagicMock()
            mock_provider.get_model.return_value = mock_model
            mock_get_provider.return_value = mock_provider

            with patch(
                "company_research_agent.orchestrator.query_orchestrator.create_react_agent"
            ) as mock_create_agent:
                mock_agent = AsyncMock()
                mock_msg = MagicMock()
                mock_msg.tool_calls = None
                mock_msg.content = "結果です"
                mock_agent.ainvoke = AsyncMock(return_value={"messages": [mock_msg]})
                mock_create_agent.return_value = mock_agent

                orchestrator = QueryOrchestrator()
                result = await orchestrator.process("トヨタの有報を探して")

                mock_agent.ainvoke.assert_called_once()
                assert result.query == "トヨタの有報を探して"
