"""Tests for ir_fetch CLI command."""

import argparse
from unittest.mock import AsyncMock, patch

import pytest

from company_research_agent.cli.commands.ir_fetch import cmd_ir_fetch


class TestCmdIrFetch:
    """Tests for cmd_ir_fetch function."""

    @pytest.mark.asyncio
    async def test_requires_argument(self) -> None:
        """--sec-code, --url, --all のいずれかが必要であること."""
        args = argparse.Namespace(
            sec_code=None,
            url=None,
            all=False,
            category=None,
            since=None,
            force=False,
        )

        result = await cmd_ir_fetch(args)

        assert result == 1  # エラー

    @pytest.mark.asyncio
    async def test_fetch_by_sec_code(self) -> None:
        """--sec-code で資料を取得できること."""
        args = argparse.Namespace(
            sec_code="72030",
            url=None,
            all=False,
            category=None,
            since=None,
            force=False,
        )

        with patch(
            "company_research_agent.services.ir_scraper_service.IRScraperService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.fetch_ir_documents = AsyncMock(return_value=[])

            result = await cmd_ir_fetch(args)

            assert result == 0
            mock_service.fetch_ir_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_by_url(self) -> None:
        """--url でアドホック探索できること."""
        args = argparse.Namespace(
            sec_code=None,
            url="https://example.com/ir/",
            all=False,
            category=None,
            since=None,
            force=False,
        )

        with patch(
            "company_research_agent.services.ir_scraper_service.IRScraperService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.explore_ir_page = AsyncMock(return_value=[])

            result = await cmd_ir_fetch(args)

            assert result == 0
            mock_service.explore_ir_page.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_all(self) -> None:
        """--all で全登録企業を処理できること."""
        args = argparse.Namespace(
            sec_code=None,
            url=None,
            all=True,
            category=None,
            since=None,
            force=False,
        )

        with patch(
            "company_research_agent.services.ir_scraper_service.IRScraperService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.fetch_all_registered = AsyncMock(return_value={})

            result = await cmd_ir_fetch(args)

            assert result == 0
            mock_service.fetch_all_registered.assert_called_once()

    @pytest.mark.asyncio
    async def test_category_mapping(self) -> None:
        """--category が正しくマッピングされること."""
        args = argparse.Namespace(
            sec_code="72030",
            url=None,
            all=False,
            category="earnings",
            since=None,
            force=False,
        )

        with patch(
            "company_research_agent.services.ir_scraper_service.IRScraperService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.fetch_ir_documents = AsyncMock(return_value=[])

            await cmd_ir_fetch(args)

            call_kwargs = mock_service.fetch_ir_documents.call_args.kwargs
            assert call_kwargs["category"] == "earnings"

    @pytest.mark.asyncio
    async def test_invalid_date_format(self) -> None:
        """不正な日付フォーマットでエラーになること."""
        args = argparse.Namespace(
            sec_code="72030",
            url=None,
            all=False,
            category=None,
            since="2024/01/01",  # 不正なフォーマット
            force=False,
        )

        result = await cmd_ir_fetch(args)

        assert result == 1  # エラー
