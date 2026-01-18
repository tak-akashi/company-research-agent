"""Tests for document type code mapping."""

from company_research_agent.core.doc_type_mapping import (
    DOC_TYPE_NAMES,
    get_doc_type_name,
)


class TestDocTypeMapping:
    """Tests for doc type mapping."""

    def test_yuho_mapping(self) -> None:
        """有価証券報告書 should be correctly mapped."""
        assert get_doc_type_name("120") == "有価証券報告書"

    def test_quarterly_report_mapping(self) -> None:
        """四半期報告書 should be correctly mapped."""
        assert get_doc_type_name("140") == "四半期報告書"

    def test_unknown_code_returns_other(self) -> None:
        """Unknown code should return 'その他'."""
        assert get_doc_type_name("999") == "その他"

    def test_none_returns_other(self) -> None:
        """None should return 'その他'."""
        assert get_doc_type_name(None) == "その他"

    def test_mapping_dict_not_empty(self) -> None:
        """DOC_TYPE_NAMES should not be empty."""
        assert len(DOC_TYPE_NAMES) > 0

    def test_all_values_are_strings(self) -> None:
        """All values should be Japanese strings."""
        for code, name in DOC_TYPE_NAMES.items():
            assert isinstance(code, str)
            assert isinstance(name, str)
            assert len(name) > 0
