"""Shared test fixtures for Company Research Agent tests."""

import pytest

from company_research_agent.core.config import EDINETConfig


@pytest.fixture
def edinet_config() -> EDINETConfig:
    """Provide a test EDINET configuration."""
    return EDINETConfig(
        EDINET_API_KEY="test-api-key",
        base_url="https://api.edinet-fsa.go.jp/api/v2",
        timeout_list=30,
        timeout_download=60,
    )


@pytest.fixture
def sample_document_list_response() -> dict[str, object]:
    """Provide a sample EDINET document list API response."""
    return {
        "metadata": {
            "title": "提出された書類を把握するためのAPI",
            "parameter": {"date": "2024-01-15", "type": "2"},
            "resultset": {"count": 2},
            "processDateTime": "2024-01-15 10:00",
            "status": "200",
            "message": "OK",
        },
        "results": [
            {
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
            },
            {
                "seqNumber": 2,
                "docID": "S100TST2",
                "edinetCode": "E10002",
                "secCode": "20000",
                "JCN": "6000012010024",
                "filerName": "サンプル株式会社",
                "fundCode": None,
                "ordinanceCode": "010",
                "formCode": "043000",
                "docTypeCode": "140",
                "periodStart": "2023-10-01",
                "periodEnd": "2023-12-31",
                "submitDateTime": "2024-01-15 09:30",
                "docDescription": "四半期報告書－第10期第3四半期",
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
                "csvFlag": "0",
                "legalStatus": "1",
            },
        ],
    }


@pytest.fixture
def sample_metadata_only_response() -> dict[str, object]:
    """Provide a sample EDINET metadata-only (type=1) response."""
    return {
        "metadata": {
            "title": "提出された書類を把握するためのAPI",
            "parameter": {"date": "2024-01-15", "type": "1"},
            "resultset": {"count": 50},
            "processDateTime": "2024-01-15 10:00",
            "status": "200",
            "message": "OK",
        }
    }
