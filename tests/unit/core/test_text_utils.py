"""Tests for core/text_utils.py - Text extraction utilities."""

from __future__ import annotations

from company_research_agent.core.text_utils import extract_text_from_content


class TestExtractTextFromContent:
    """extract_text_from_content() のテスト."""

    def test_returns_empty_string_for_none(self) -> None:
        """Noneの場合は空文字列を返す."""
        result = extract_text_from_content(None)
        assert result == ""

    def test_returns_string_as_is(self) -> None:
        """文字列の場合はそのまま返す."""
        result = extract_text_from_content("これはテキストです")
        assert result == "これはテキストです"

    def test_returns_empty_string_for_empty_string(self) -> None:
        """空文字列の場合は空文字列を返す."""
        result = extract_text_from_content("")
        assert result == ""

    def test_extracts_text_from_single_text_block(self) -> None:
        """単一のtextブロックからテキストを抽出する."""
        content = [{"type": "text", "text": "これは回答です"}]
        result = extract_text_from_content(content)
        assert result == "これは回答です"

    def test_extracts_text_from_multiple_text_blocks(self) -> None:
        """複数のtextブロックからテキストを抽出し改行で結合する."""
        content = [
            {"type": "text", "text": "1行目"},
            {"type": "text", "text": "2行目"},
            {"type": "text", "text": "3行目"},
        ]
        result = extract_text_from_content(content)
        assert result == "1行目\n2行目\n3行目"

    def test_ignores_non_text_blocks(self) -> None:
        """textタイプ以外のブロックは無視する."""
        content = [
            {"type": "text", "text": "テキスト部分"},
            {"type": "image", "source": {"type": "base64", "data": "..."}},
            {"type": "tool_use", "id": "123", "name": "tool_name"},
        ]
        result = extract_text_from_content(content)
        assert result == "テキスト部分"

    def test_handles_mixed_text_and_other_blocks(self) -> None:
        """textと他のブロックが混在する場合もtextのみ抽出する."""
        content = [
            {"type": "text", "text": "最初のテキスト"},
            {"type": "image", "source": {}},
            {"type": "text", "text": "2番目のテキスト"},
        ]
        result = extract_text_from_content(content)
        assert result == "最初のテキスト\n2番目のテキスト"

    def test_returns_empty_for_empty_list(self) -> None:
        """空のリストの場合は空文字列を返す."""
        result = extract_text_from_content([])
        assert result == ""

    def test_returns_empty_for_list_with_no_text_blocks(self) -> None:
        """textブロックがないリストの場合は空文字列を返す."""
        content = [
            {"type": "image", "source": {}},
            {"type": "tool_use", "id": "123"},
        ]
        result = extract_text_from_content(content)
        assert result == ""

    def test_handles_dict_without_type_key(self) -> None:
        """typeキーがないdictは無視する."""
        content = [
            {"text": "これはtypeがない"},
            {"type": "text", "text": "これはtypeがある"},
        ]
        result = extract_text_from_content(content)
        assert result == "これはtypeがある"

    def test_handles_text_block_without_text_key(self) -> None:
        """textキーがないtextブロックは無視する."""
        content = [
            {"type": "text"},  # textキーがない
            {"type": "text", "text": "これはtextキーがある"},
        ]
        result = extract_text_from_content(content)
        assert result == "これはtextキーがある"

    def test_handles_text_block_with_non_string_text(self) -> None:
        """textの値が文字列でない場合は無視する."""
        content = [
            {"type": "text", "text": 123},  # 数値
            {"type": "text", "text": None},  # None
            {"type": "text", "text": "有効なテキスト"},
        ]
        result = extract_text_from_content(content)
        assert result == "有効なテキスト"

    def test_handles_text_block_with_empty_string(self) -> None:
        """空文字列のtextブロックは無視する."""
        content = [
            {"type": "text", "text": ""},
            {"type": "text", "text": "有効なテキスト"},
        ]
        result = extract_text_from_content(content)
        assert result == "有効なテキスト"

    def test_handles_string_items_in_list(self) -> None:
        """リスト内に直接文字列がある場合も抽出する."""
        content = ["最初の文字列", "2番目の文字列"]
        result = extract_text_from_content(content)
        assert result == "最初の文字列\n2番目の文字列"

    def test_handles_mixed_strings_and_dicts_in_list(self) -> None:
        """リスト内に文字列とdictが混在する場合."""
        content = [
            "直接の文字列",
            {"type": "text", "text": "dictのテキスト"},
        ]
        result = extract_text_from_content(content)
        assert result == "直接の文字列\ndictのテキスト"

    def test_handles_other_types_in_list(self) -> None:
        """リスト内の予期しない型は無視する."""
        content = [
            {"type": "text", "text": "有効なテキスト"},
            123,  # 数値
            None,  # None
            True,  # bool
        ]
        result = extract_text_from_content(content)
        assert result == "有効なテキスト"

    def test_converts_other_types_to_string(self) -> None:
        """リストでも文字列でもない場合はstr()で変換する."""
        result = extract_text_from_content(12345)
        assert result == "12345"

    def test_converts_dict_to_string(self) -> None:
        """dictの場合はstr()で変換する."""
        content = {"key": "value"}
        result = extract_text_from_content(content)
        assert result == str(content)

    def test_handles_object_that_raises_on_str(self) -> None:
        """str()が例外を発生させるオブジェクトの場合は空文字列を返す."""

        class BadObject:
            def __str__(self) -> str:
                raise ValueError("Cannot convert to string")

        result = extract_text_from_content(BadObject())
        assert result == ""


class TestExtractTextFromContentRealWorldScenarios:
    """実際のLangChain応答を模したテスト."""

    def test_typical_gemini_multimodal_response(self) -> None:
        """Geminiのマルチモーダル応答形式."""
        content = [
            {
                "type": "text",
                "text": (
                    "トヨタ自動車の有価証券報告書を分析した結果、"
                    "以下の点が確認できました。\n\n## 売上高\n- 2023年度: 37兆円"
                ),
            }
        ]
        result = extract_text_from_content(content)
        assert "トヨタ自動車" in result
        assert "## 売上高" in result

    def test_openai_style_response(self) -> None:
        """OpenAI形式の応答（通常は文字列）."""
        content = "これはOpenAI形式の回答です。"
        result = extract_text_from_content(content)
        assert result == "これはOpenAI形式の回答です。"

    def test_anthropic_style_multipart_response(self) -> None:
        """Anthropicスタイルのマルチパート応答."""
        content = [
            {"type": "text", "text": "まず、企業情報を検索します。"},
            {"type": "tool_use", "id": "toolu_01", "name": "search_company", "input": {}},
        ]
        result = extract_text_from_content(content)
        assert result == "まず、企業情報を検索します。"
