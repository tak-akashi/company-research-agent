"""Tests for search_company tool."""

from unittest.mock import AsyncMock, patch

import pytest

from company_research_agent.schemas.query_schemas import CompanyCandidate, CompanyInfo
from company_research_agent.tools.search_company import search_company


@pytest.fixture
def sample_company_info() -> CompanyInfo:
    """Sample company info fixture."""
    return CompanyInfo(
        edinet_code="E02144",
        sec_code="72030",
        company_name="トヨタ自動車株式会社",
        company_name_kana="トヨタジドウシャ",
        company_name_en="TOYOTA MOTOR CORPORATION",
        listing_code="上場",
        industry_code="輸送用機器",
    )


@pytest.fixture
def sample_candidates(sample_company_info: CompanyInfo) -> list[CompanyCandidate]:
    """Sample candidates fixture."""
    return [
        CompanyCandidate(
            company=sample_company_info,
            similarity_score=95.0,
            match_field="company_name",
        ),
    ]


class TestSearchCompany:
    """Tests for search_company tool."""

    @pytest.mark.asyncio
    async def test_search_company_returns_candidates(
        self, sample_candidates: list[CompanyCandidate]
    ) -> None:
        """search_company should return candidates from EDINETCodeListClient."""
        with patch(
            "company_research_agent.tools.search_company.EDINETCodeListClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.search_companies = AsyncMock(return_value=sample_candidates)
            mock_client_class.return_value = mock_client

            result = await search_company.ainvoke({"query": "トヨタ"})

            assert len(result) == 1
            # Result is serialized as dict for LangChain ToolMessage compatibility
            assert result[0]["company"]["edinet_code"] == "E02144"
            mock_client.search_companies.assert_called_once_with("トヨタ", 10)

    @pytest.mark.asyncio
    async def test_search_company_with_limit(
        self, sample_candidates: list[CompanyCandidate]
    ) -> None:
        """search_company should respect limit parameter."""
        with patch(
            "company_research_agent.tools.search_company.EDINETCodeListClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.search_companies = AsyncMock(return_value=sample_candidates)
            mock_client_class.return_value = mock_client

            await search_company.ainvoke({"query": "トヨタ", "limit": 5})

            mock_client.search_companies.assert_called_once_with("トヨタ", 5)
