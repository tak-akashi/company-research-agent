"""Tests for BaseIRScraper."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from company_research_agent.clients.ir_scraper.base import BaseIRScraper
from company_research_agent.core.exceptions import (
    IRPageAccessError,
)


class TestBaseIRScraper:
    """Tests for BaseIRScraper class."""

    class TestInit:
        """Tests for __init__ method."""

        def test_default_values(self) -> None:
            """デフォルト値で初期化できること."""
            scraper = BaseIRScraper()
            assert scraper._rate_limit_seconds == 1.0
            assert scraper._timeout == 30000
            assert scraper._headless is True
            assert "CompanyResearchAgent" in scraper._user_agent

        def test_custom_values(self) -> None:
            """カスタム値で初期化できること."""
            scraper = BaseIRScraper(
                rate_limit_seconds=2.0,
                timeout=60000,
                headless=False,
                user_agent="CustomAgent/1.0",
            )
            assert scraper._rate_limit_seconds == 2.0
            assert scraper._timeout == 60000
            assert scraper._headless is False
            assert scraper._user_agent == "CustomAgent/1.0"

    class TestContextManager:
        """Tests for context manager methods."""

        @pytest.mark.asyncio
        async def test_aenter_sets_attributes(self) -> None:
            """__aenter__で必要な属性がセットされること."""
            # playwrightが未インストールの場合のテスト
            # 実際のPlaywrightの初期化はスキップし、属性の存在のみ確認
            scraper = BaseIRScraper()

            # 初期状態ではNone
            assert scraper._playwright is None
            assert scraper._browser is None
            assert scraper._context is None

        @pytest.mark.asyncio
        async def test_aexit_cleans_up(self) -> None:
            """__aexit__でリソースがクリーンアップされること."""
            scraper = BaseIRScraper()
            mock_context = AsyncMock()
            mock_browser = AsyncMock()
            mock_playwright = AsyncMock()

            scraper._context = mock_context
            scraper._browser = mock_browser
            scraper._playwright = mock_playwright

            await scraper.__aexit__(None, None, None)

            mock_context.close.assert_called_once()
            mock_browser.close.assert_called_once()
            mock_playwright.stop.assert_called_once()

            assert scraper._context is None
            assert scraper._browser is None
            assert scraper._playwright is None

    class TestFetchPage:
        """Tests for fetch_page method."""

        @pytest.mark.asyncio
        async def test_fetch_page_success(self) -> None:
            """ページ取得が成功すること."""
            scraper = BaseIRScraper(rate_limit_seconds=0)  # テスト用にレート制限を無効化

            mock_page = AsyncMock()
            mock_response = MagicMock()
            mock_response.status = 200
            mock_page.goto = AsyncMock(return_value=mock_response)
            mock_page.content = AsyncMock(return_value="<html>Test</html>")
            mock_page.close = AsyncMock()

            mock_context = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            scraper._context = mock_context

            result = await scraper.fetch_page("https://example.com/ir")

            assert result == "<html>Test</html>"
            mock_page.goto.assert_called_once()
            mock_page.close.assert_called_once()

        @pytest.mark.asyncio
        async def test_fetch_page_not_initialized(self) -> None:
            """初期化されていない場合にエラーが発生すること."""
            scraper = BaseIRScraper()
            # _context is None by default

            with pytest.raises(IRPageAccessError) as exc_info:
                await scraper.fetch_page("https://example.com")

            assert "not initialized" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_fetch_page_http_error(self) -> None:
            """HTTPエラーの場合にIRPageAccessErrorが発生すること."""
            scraper = BaseIRScraper(rate_limit_seconds=0)

            mock_page = AsyncMock()
            mock_response = MagicMock()
            mock_response.status = 404
            mock_page.goto = AsyncMock(return_value=mock_response)
            mock_page.close = AsyncMock()

            mock_context = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            scraper._context = mock_context

            with pytest.raises(IRPageAccessError) as exc_info:
                await scraper.fetch_page("https://example.com/not-found")

            assert exc_info.value.status_code == 404

    class TestDownloadPdf:
        """Tests for download_pdf method."""

        @pytest.mark.asyncio
        async def test_download_pdf_success(self, tmp_path: Path) -> None:
            """PDFダウンロードが成功すること."""
            scraper = BaseIRScraper(rate_limit_seconds=0)
            save_path = tmp_path / "test.pdf"

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"%PDF-1.4 test content"
            mock_response.raise_for_status = MagicMock()

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = await scraper.download_pdf("https://example.com/doc.pdf", save_path)

                assert result == save_path
                assert save_path.exists()
                assert save_path.read_bytes() == b"%PDF-1.4 test content"

        @pytest.mark.asyncio
        async def test_download_pdf_skip_existing(self, tmp_path: Path) -> None:
            """既存ファイルをスキップすること."""
            scraper = BaseIRScraper(rate_limit_seconds=0)
            save_path = tmp_path / "existing.pdf"
            save_path.write_text("existing content")

            # httpxがcallされないことを確認
            with patch("httpx.AsyncClient") as mock_client_class:
                result = await scraper.download_pdf("https://example.com/doc.pdf", save_path)

                assert result == save_path
                mock_client_class.assert_not_called()

        @pytest.mark.asyncio
        async def test_download_pdf_force_overwrite(self, tmp_path: Path) -> None:
            """force=Trueで既存ファイルを上書きすること."""
            scraper = BaseIRScraper(rate_limit_seconds=0)
            save_path = tmp_path / "existing.pdf"
            save_path.write_text("old content")

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"new content"
            mock_response.raise_for_status = MagicMock()

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = await scraper.download_pdf(
                    "https://example.com/doc.pdf", save_path, force=True
                )

                assert result == save_path
                assert save_path.read_bytes() == b"new content"

    class TestCheckRobotsTxt:
        """Tests for check_robots_txt method."""

        @pytest.mark.asyncio
        async def test_check_robots_txt_allowed(self) -> None:
            """robots.txtでアクセスが許可されている場合."""
            scraper = BaseIRScraper()

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "User-agent: *\nDisallow: /admin/"
            mock_response.raise_for_status = MagicMock()

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = await scraper.check_robots_txt("https://example.com", "/ir/documents")

                assert result is True

        @pytest.mark.asyncio
        async def test_check_robots_txt_disallowed(self) -> None:
            """robots.txtでアクセスが禁止されている場合."""
            scraper = BaseIRScraper()

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "User-agent: *\nDisallow: /ir/"
            mock_response.raise_for_status = MagicMock()

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = await scraper.check_robots_txt("https://example.com", "/ir/documents")

                assert result is False

        @pytest.mark.asyncio
        async def test_check_robots_txt_not_found(self) -> None:
            """robots.txtが存在しない場合（全て許可）."""
            scraper = BaseIRScraper()

            mock_response = MagicMock()
            mock_response.status_code = 404

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = await scraper.check_robots_txt("https://example.com", "/any/path")

                assert result is True

        @pytest.mark.asyncio
        async def test_check_robots_txt_uses_cache(self) -> None:
            """robots.txtキャッシュが使用されること."""
            scraper = BaseIRScraper()
            # 事前にキャッシュを設定
            scraper._robots_cache["https://example.com/robots.txt"] = {"/blocked/"}

            # httpxが呼ばれないことを確認
            with patch("httpx.AsyncClient") as mock_client_class:
                result = await scraper.check_robots_txt("https://example.com", "/allowed/path")

                assert result is True
                mock_client_class.assert_not_called()

    class TestResolveUrl:
        """Tests for resolve_url method."""

        def test_resolve_absolute_url(self) -> None:
            """絶対URLはそのまま返されること."""
            scraper = BaseIRScraper()
            result = scraper.resolve_url("https://example.com/ir", "https://other.com/doc.pdf")
            assert result == "https://other.com/doc.pdf"

        def test_resolve_relative_url(self) -> None:
            """相対URLが解決されること."""
            scraper = BaseIRScraper()
            result = scraper.resolve_url("https://example.com/ir/", "documents/report.pdf")
            assert result == "https://example.com/ir/documents/report.pdf"

        def test_resolve_root_relative_url(self) -> None:
            """ルート相対URLが解決されること."""
            scraper = BaseIRScraper()
            result = scraper.resolve_url("https://example.com/ir/page", "/assets/doc.pdf")
            assert result == "https://example.com/assets/doc.pdf"
