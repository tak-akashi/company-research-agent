"""Tests for IR tools."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from company_research_agent.schemas.ir_schemas import ImpactPoint, IRDocument, IRSummary


class TestFetchIrDocuments:
    """Tests for fetch_ir_documents tool."""

    @pytest.mark.asyncio
    async def test_fetch_returns_documents(self) -> None:
        """IR資料を取得できること."""
        from company_research_agent.tools.ir_tools import fetch_ir_documents

        with patch(
            "company_research_agent.services.ir_scraper_service.IRScraperService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.fetch_ir_documents = AsyncMock(
                return_value=[
                    IRDocument(
                        title="決算説明会資料",
                        url="https://example.com/doc.pdf",
                        category="earnings",
                        published_date=date.today(),
                        summary=IRSummary(
                            overview="増収増益",
                            impact_points=[ImpactPoint(label="bullish", content="売上高20%増")],
                        ),
                    )
                ]
            )

            result = await fetch_ir_documents.ainvoke(
                {"sec_code": "72030", "category": "earnings", "since_days": 90}
            )

            # 新しい戻り値の構造をチェック
            assert "period" in result
            assert "since_date" in result
            assert "count" in result
            assert "documents" in result
            assert result["count"] == 1
            assert len(result["documents"]) == 1
            assert result["documents"][0]["title"] == "決算説明会資料"
            assert result["documents"][0]["category"] == "earnings"
            assert "summary" in result["documents"][0]
            assert result["documents"][0]["summary"]["overview"] == "増収増益"

    @pytest.mark.asyncio
    async def test_fetch_with_default_since(self) -> None:
        """デフォルトのsince_daysが設定値であること."""
        from company_research_agent.core.config import get_config
        from company_research_agent.tools.ir_tools import fetch_ir_documents

        config = get_config()
        default_since_days = config.ir_scraper.default_since_days

        with patch(
            "company_research_agent.services.ir_scraper_service.IRScraperService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.fetch_ir_documents = AsyncMock(return_value=[])

            await fetch_ir_documents.ainvoke({"sec_code": "72030"})

            call_kwargs = mock_service.fetch_ir_documents.call_args.kwargs
            # since が today - default_since_days 前後であることを確認
            expected_since = date.today() - timedelta(days=default_since_days)
            assert call_kwargs["since"] == expected_since


class TestFetchIrNews:
    """Tests for fetch_ir_news tool."""

    @pytest.mark.asyncio
    async def test_fetch_news_returns_list(self) -> None:
        """IRニュースを取得できること."""
        from company_research_agent.tools.ir_tools import fetch_ir_news

        with patch(
            "company_research_agent.services.ir_scraper_service.IRScraperService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.fetch_ir_documents = AsyncMock(
                return_value=[
                    IRDocument(
                        title="新製品発表",
                        url="https://example.com/news.pdf",
                        category="news",
                        published_date=date.today(),
                    )
                ]
            )

            result = await fetch_ir_news.ainvoke(
                {"sec_code": "72030", "limit": 10, "since_days": 30}
            )

            assert len(result) == 1
            assert result[0]["title"] == "新製品発表"
            assert "summary" not in result[0]  # ニュースには要約なし

    @pytest.mark.asyncio
    async def test_fetch_news_respects_limit(self) -> None:
        """limitパラメータが適用されること."""
        from company_research_agent.tools.ir_tools import fetch_ir_news

        with patch(
            "company_research_agent.services.ir_scraper_service.IRScraperService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            # 10件の結果を返す
            mock_service.fetch_ir_documents = AsyncMock(
                return_value=[
                    IRDocument(
                        title=f"News {i}",
                        url=f"https://example.com/news{i}.pdf",
                        category="news",
                    )
                    for i in range(10)
                ]
            )

            result = await fetch_ir_news.ainvoke(
                {"sec_code": "72030", "limit": 5, "since_days": 30}
            )

            assert len(result) == 5


class TestExploreIrPage:
    """Tests for explore_ir_page tool."""

    @pytest.mark.asyncio
    async def test_explore_returns_documents(self) -> None:
        """IRページを探索できること."""
        from company_research_agent.tools.ir_tools import explore_ir_page

        with patch(
            "company_research_agent.services.ir_scraper_service.IRScraperService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.explore_ir_page = AsyncMock(
                return_value=[
                    IRDocument(
                        title="発見した資料",
                        url="https://example.com/doc.pdf",
                        category="disclosures",
                        published_date=date.today(),
                        summary=IRSummary(overview="業績予想を上方修正"),
                    )
                ]
            )

            result = await explore_ir_page.ainvoke(
                {"url": "https://example.com/ir/", "since_days": 60}
            )

            assert len(result) == 1
            assert result[0]["title"] == "発見した資料"
            assert result[0]["category"] == "disclosures"
            assert "summary" in result[0]
