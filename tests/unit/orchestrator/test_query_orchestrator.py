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
            assert len(orchestrator._tools) == 9  # 9 default tools (6 base + 3 IR tools)
            assert orchestrator._agent is None

    def test_init_custom_provider(self) -> None:
        """Should accept custom LLM provider."""
        mock_provider = MagicMock()

        orchestrator = QueryOrchestrator(llm_provider=mock_provider)

        assert orchestrator._llm_provider == mock_provider


class TestDefaultTools:
    """Tests for default tools."""

    def test_default_tools_list(self) -> None:
        """Should return 9 default tools."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()
            tools = orchestrator._default_tools()

            assert len(tools) == 9  # 6 base + 3 IR tools
            tool_names = [t.name for t in tools]
            # Base tools
            assert "search_company" in tool_names
            assert "search_documents" in tool_names
            assert "download_document" in tool_names
            assert "analyze_document" in tool_names
            assert "compare_documents" in tool_names
            assert "summarize_document" in tool_names
            # IR tools
            assert "fetch_ir_documents" in tool_names
            assert "fetch_ir_news" in tool_names
            assert "explore_ir_page" in tool_names


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

    def test_extract_metadata_from_json_string(self) -> None:
        """Should extract metadata from JSON string content."""
        import json

        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            mock_msg = MagicMock()
            mock_msg.content = json.dumps(
                {
                    "report": {"key": "value"},
                    "metadata": {
                        "doc_id": "S100JSON",
                        "filer_name": "JSONテスト株式会社",
                        "doc_description": "有価証券報告書－第10期",
                        "period_start": "2024-01-01",
                        "period_end": "2024-12-31",
                    },
                }
            )

            documents = orchestrator._extract_document_metadata([mock_msg])

            assert len(documents) == 1
            assert documents[0].doc_id == "S100JSON"
            assert documents[0].filer_name == "JSONテスト株式会社"
            assert documents[0].doc_description == "有価証券報告書－第10期"
            assert documents[0].period_start == "2024-01-01"
            assert documents[0].period_end == "2024-12-31"

    def test_extract_metadata_skips_invalid_json_string(self) -> None:
        """Should skip messages with invalid JSON string."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            mock_msg = MagicMock()
            mock_msg.content = "これは有効なJSONではありません"

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


class TestProcessWithHistory:
    """Tests for process_with_history method."""

    @pytest.mark.asyncio
    async def test_process_with_history_initial_call(self) -> None:
        """Should handle initial call with empty history."""
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
                mock_msg.content = "トヨタの有報を見つけました"
                mock_agent.ainvoke = AsyncMock(
                    return_value={"messages": [("user", "トヨタの有報を探して"), mock_msg]}
                )
                mock_create_agent.return_value = mock_agent

                orchestrator = QueryOrchestrator()
                result, messages = await orchestrator.process_with_history("トヨタの有報を探して")

                assert result.query == "トヨタの有報を探して"
                assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_process_with_history_subsequent_call(self) -> None:
        """Should include previous history in subsequent calls."""
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
                mock_msg1 = MagicMock()
                mock_msg1.tool_calls = None
                mock_msg1.content = "トヨタの有報を見つけました"
                mock_msg2 = MagicMock()
                mock_msg2.tool_calls = None
                mock_msg2.content = "分析結果です"

                # First call returns initial messages
                first_messages = [("user", "トヨタの有報を探して"), mock_msg1]
                # Second call includes previous messages plus new
                second_messages = first_messages + [("user", "分析して"), mock_msg2]

                mock_agent.ainvoke = AsyncMock(
                    side_effect=[
                        {"messages": first_messages},
                        {"messages": second_messages},
                    ]
                )
                mock_create_agent.return_value = mock_agent

                orchestrator = QueryOrchestrator()

                # First call
                result1, history1 = await orchestrator.process_with_history("トヨタの有報を探して")
                assert result1.query == "トヨタの有報を探して"

                # Second call with history
                result2, history2 = await orchestrator.process_with_history("分析して", history1)
                assert result2.query == "分析して"

                # Verify agent was called with history
                calls = mock_agent.ainvoke.call_args_list
                assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_process_with_history_returns_updated_messages(self) -> None:
        """Should return updated message list."""
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
                expected_messages = [
                    ("user", "テストクエリ"),
                    MagicMock(content="回答", tool_calls=None),
                ]
                mock_agent.ainvoke = AsyncMock(return_value={"messages": expected_messages})
                mock_create_agent.return_value = mock_agent

                orchestrator = QueryOrchestrator()
                result, messages = await orchestrator.process_with_history("テストクエリ")

                assert messages == expected_messages

    @pytest.mark.asyncio
    async def test_process_with_history_none_messages(self) -> None:
        """Should handle None messages parameter."""
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
                mock_msg.content = "結果"
                mock_agent.ainvoke = AsyncMock(return_value={"messages": [mock_msg]})
                mock_create_agent.return_value = mock_agent

                orchestrator = QueryOrchestrator()
                result, messages = await orchestrator.process_with_history("クエリ", None)

                assert result.query == "クエリ"


class TestParseResultMultimodalContent:
    """Tests for _parse_result handling multimodal content."""

    def test_parse_result_extracts_text_from_list_content(self) -> None:
        """Should extract text from list-formatted content (multimodal)."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            # Mock message with list-formatted content (Gemini style)
            mock_msg = MagicMock()
            mock_msg.tool_calls = None
            mock_msg.content = [{"type": "text", "text": "これはマルチモーダル形式の回答です"}]

            result = orchestrator._parse_result(
                "テストクエリ",
                {"messages": [mock_msg]},
            )

            assert result.result == "これはマルチモーダル形式の回答です"

    def test_parse_result_extracts_text_from_multiple_blocks(self) -> None:
        """Should extract and join text from multiple blocks."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            mock_msg = MagicMock()
            mock_msg.tool_calls = None
            mock_msg.content = [
                {"type": "text", "text": "1行目の回答"},
                {"type": "text", "text": "2行目の回答"},
            ]

            result = orchestrator._parse_result(
                "テストクエリ",
                {"messages": [mock_msg]},
            )

            assert result.result == "1行目の回答\n2行目の回答"

    def test_parse_result_ignores_non_text_blocks(self) -> None:
        """Should ignore non-text blocks like tool_use."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            mock_msg = MagicMock()
            mock_msg.tool_calls = None
            mock_msg.content = [
                {"type": "text", "text": "テキスト部分"},
                {"type": "tool_use", "id": "toolu_01", "name": "search_company"},
            ]

            result = orchestrator._parse_result(
                "テストクエリ",
                {"messages": [mock_msg]},
            )

            assert result.result == "テキスト部分"

    def test_parse_result_handles_string_content(self) -> None:
        """Should handle regular string content."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            mock_msg = MagicMock()
            mock_msg.tool_calls = None
            mock_msg.content = "通常の文字列回答です"

            result = orchestrator._parse_result(
                "テストクエリ",
                {"messages": [mock_msg]},
            )

            assert result.result == "通常の文字列回答です"

    def test_parse_result_handles_none_content(self) -> None:
        """Should handle None content."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            mock_msg = MagicMock()
            mock_msg.tool_calls = None
            mock_msg.content = None

            result = orchestrator._parse_result(
                "テストクエリ",
                {"messages": [mock_msg]},
            )

            assert result.result is None

    def test_parse_result_handles_empty_list_content(self) -> None:
        """Should handle empty list content."""
        with patch("company_research_agent.orchestrator.query_orchestrator.get_default_provider"):
            orchestrator = QueryOrchestrator()

            mock_msg = MagicMock()
            mock_msg.tool_calls = None
            mock_msg.content = []

            result = orchestrator._parse_result(
                "テストクエリ",
                {"messages": [mock_msg]},
            )

            assert result.result is None
