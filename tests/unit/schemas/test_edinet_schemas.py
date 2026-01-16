"""Tests for EDINET schemas."""

import pytest

from company_research_agent.schemas.edinet_schemas import (
    DocumentListResponse,
    DocumentMetadata,
    RequestParameter,
    ResponseMetadata,
    ResultSet,
)


class TestRequestParameter:
    """Tests for RequestParameter schema."""

    def test_parse_valid_data(self) -> None:
        """RequestParameter should parse valid data."""
        data = {"date": "2024-01-15", "type": "2"}
        param = RequestParameter.model_validate(data)
        assert param.date == "2024-01-15"
        assert param.type == "2"


class TestResultSet:
    """Tests for ResultSet schema."""

    def test_parse_valid_data(self) -> None:
        """ResultSet should parse valid data."""
        data = {"count": 100}
        resultset = ResultSet.model_validate(data)
        assert resultset.count == 100


class TestResponseMetadata:
    """Tests for ResponseMetadata schema."""

    def test_parse_valid_data(self) -> None:
        """ResponseMetadata should parse valid data."""
        data = {
            "title": "提出された書類を把握するためのAPI",
            "parameter": {"date": "2024-01-15", "type": "2"},
            "resultset": {"count": 50},
            "processDateTime": "2024-01-15 10:00",
            "status": "200",
            "message": "OK",
        }
        metadata = ResponseMetadata.model_validate(data)
        assert metadata.title == "提出された書類を把握するためのAPI"
        assert metadata.parameter.date == "2024-01-15"
        assert metadata.resultset.count == 50
        assert metadata.process_date_time == "2024-01-15 10:00"
        assert metadata.status == "200"
        assert metadata.message == "OK"


class TestDocumentMetadata:
    """Tests for DocumentMetadata schema."""

    @pytest.fixture
    def sample_document_data(self) -> dict[str, object]:
        """Provide sample document data."""
        return {
            "seqNumber": 1,
            "docID": "S100TEST",
            "edinetCode": "E10001",
            "secCode": "10000",
            "JCN": "6000012010023",
            "filerName": "テスト株式会社",
            "fundCode": None,
            "ordinanceCode": "010",
            "formCode": "030000",
            "docTypeCode": "120",
            "periodStart": "2023-04-01",
            "periodEnd": "2024-03-31",
            "submitDateTime": "2024-01-15 09:00",
            "docDescription": "有価証券報告書－第10期",
            "issuerEdinetCode": None,
            "subjectEdinetCode": None,
            "subsidiaryEdinetCode": None,
            "currentReportReason": None,
            "parentDocID": None,
            "opeDateTime": None,
            "withdrawalStatus": "0",
            "docInfoEditStatus": "0",
            "disclosureStatus": "0",
            "xbrlFlag": "1",
            "pdfFlag": "1",
            "attachDocFlag": "0",
            "englishDocFlag": "0",
            "csvFlag": "1",
            "legalStatus": "1",
        }

    def test_parse_valid_data(self, sample_document_data: dict[str, object]) -> None:
        """DocumentMetadata should parse valid data."""
        doc = DocumentMetadata.model_validate(sample_document_data)
        assert doc.seq_number == 1
        assert doc.doc_id == "S100TEST"
        assert doc.edinet_code == "E10001"
        assert doc.sec_code == "10000"
        assert doc.filer_name == "テスト株式会社"
        assert doc.doc_type_code == "120"
        assert doc.submit_date_time == "2024-01-15 09:00"

    def test_flag_conversion_true(self, sample_document_data: dict[str, object]) -> None:
        """Flag fields should convert '1' to True."""
        doc = DocumentMetadata.model_validate(sample_document_data)
        assert doc.xbrl_flag is True
        assert doc.pdf_flag is True
        assert doc.csv_flag is True

    def test_flag_conversion_false(self, sample_document_data: dict[str, object]) -> None:
        """Flag fields should convert '0' to False."""
        doc = DocumentMetadata.model_validate(sample_document_data)
        assert doc.attach_doc_flag is False
        assert doc.english_doc_flag is False

    def test_flag_conversion_from_bool(self, sample_document_data: dict[str, object]) -> None:
        """Flag fields should accept boolean values directly."""
        sample_document_data["xbrlFlag"] = True
        sample_document_data["pdfFlag"] = False
        doc = DocumentMetadata.model_validate(sample_document_data)
        assert doc.xbrl_flag is True
        assert doc.pdf_flag is False

    def test_flag_conversion_from_none(self, sample_document_data: dict[str, object]) -> None:
        """Flag fields should treat None as False."""
        sample_document_data["xbrlFlag"] = None
        doc = DocumentMetadata.model_validate(sample_document_data)
        assert doc.xbrl_flag is False

    def test_optional_fields_none(self, sample_document_data: dict[str, object]) -> None:
        """Optional fields should accept None values."""
        doc = DocumentMetadata.model_validate(sample_document_data)
        assert doc.fund_code is None
        assert doc.issuer_edinet_code is None
        assert doc.parent_doc_id is None

    def test_optional_fields_with_values(self, sample_document_data: dict[str, object]) -> None:
        """Optional fields should accept actual values."""
        sample_document_data["fundCode"] = "F00001"
        sample_document_data["parentDocID"] = "S100PARENT"
        doc = DocumentMetadata.model_validate(sample_document_data)
        assert doc.fund_code == "F00001"
        assert doc.parent_doc_id == "S100PARENT"

    def test_nullable_fields_accept_none(self, sample_document_data: dict[str, object]) -> None:
        """Nullable fields should accept None values."""
        sample_document_data["filerName"] = None
        sample_document_data["submitDateTime"] = None
        sample_document_data["docDescription"] = None
        doc = DocumentMetadata.model_validate(sample_document_data)
        assert doc.filer_name is None
        assert doc.submit_date_time is None
        assert doc.doc_description is None


class TestDocumentListResponse:
    """Tests for DocumentListResponse schema."""

    def test_parse_with_results(self, sample_document_list_response: dict[str, object]) -> None:
        """DocumentListResponse should parse response with results."""
        response = DocumentListResponse.model_validate(sample_document_list_response)
        assert response.metadata.status == "200"
        assert response.metadata.resultset.count == 2
        assert response.results is not None
        assert len(response.results) == 2
        assert response.results[0].doc_id == "S100TEST"
        assert response.results[1].doc_id == "S100TST2"

    def test_parse_metadata_only(self, sample_metadata_only_response: dict[str, object]) -> None:
        """DocumentListResponse should parse metadata-only (type=1) response."""
        response = DocumentListResponse.model_validate(sample_metadata_only_response)
        assert response.metadata.status == "200"
        assert response.metadata.parameter.type == "1"
        assert response.metadata.resultset.count == 50
        assert response.results is None

    def test_document_flags_parsed_correctly(
        self, sample_document_list_response: dict[str, object]
    ) -> None:
        """Document flags should be converted to boolean correctly."""
        response = DocumentListResponse.model_validate(sample_document_list_response)
        assert response.results is not None

        doc1 = response.results[0]
        assert doc1.xbrl_flag is True
        assert doc1.pdf_flag is True
        assert doc1.csv_flag is True
        assert doc1.attach_doc_flag is False

        doc2 = response.results[1]
        assert doc2.csv_flag is False  # Second doc has csvFlag: "0"
