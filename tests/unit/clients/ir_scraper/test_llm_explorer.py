"""Tests for LLMExplorer."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from company_research_agent.clients.ir_scraper.llm_explorer import LLMExplorer
from company_research_agent.schemas.ir_schemas import (
    ExtractedLink,
    ExtractedLinksResponse,
)


class TestLLMExplorer:
    """Tests for LLMExplorer class."""

    class TestInit:
        """Tests for __init__ method."""

        def test_init_without_provider(self) -> None:
            """プロバイダーなしで初期化できること."""
            explorer = LLMExplorer()
            assert explorer._llm_provider is None

        def test_init_with_provider(self) -> None:
            """プロバイダー指定で初期化できること."""
            mock_provider = MagicMock()
            explorer = LLMExplorer(llm_provider=mock_provider)
            assert explorer._llm_provider is mock_provider

    class TestHtmlToMarkdown:
        """Tests for _html_to_markdown method."""

        def test_extracts_pdf_links(self) -> None:
            """PDFリンクを抽出できること."""
            explorer = LLMExplorer()
            html = """
            <html>
            <body>
            <a href="report.pdf">年次報告書</a>
            <a href="page.html">ページ</a>
            </body>
            </html>
            """

            markdown = explorer._html_to_markdown(html, "https://example.com")

            assert "[PDF]" in markdown
            assert "年次報告書" in markdown
            assert "report.pdf" in markdown

        def test_removes_script_and_style(self) -> None:
            """script/style要素を除去すること."""
            explorer = LLMExplorer()
            html = """
            <html>
            <head>
            <script>console.log('test');</script>
            <style>body { color: red; }</style>
            </head>
            <body>
            <p>これは十分に長いコンテンツテキストです</p>
            </body>
            </html>
            """

            markdown = explorer._html_to_markdown(html, "https://example.com")

            assert "console.log" not in markdown
            assert "color: red" not in markdown
            assert "これは十分に長いコンテンツテキストです" in markdown

        def test_extracts_headings(self) -> None:
            """見出しを抽出できること."""
            explorer = LLMExplorer()
            html = """
            <html>
            <body>
            <h1>大見出し</h1>
            <h2>中見出し</h2>
            </body>
            </html>
            """

            markdown = explorer._html_to_markdown(html, "https://example.com")

            assert "# 大見出し" in markdown
            assert "## 中見出し" in markdown

    class TestExploreIrPage:
        """Tests for explore_ir_page method."""

        @pytest.mark.asyncio
        async def test_explore_returns_documents(self) -> None:
            """IRページからドキュメントを抽出できること."""
            mock_provider = MagicMock()
            mock_provider.ainvoke_structured = AsyncMock(
                return_value=ExtractedLinksResponse(
                    links=[
                        ExtractedLink(
                            title="決算説明会資料",
                            url="https://example.com/ir/doc.pdf",
                            category="earnings",
                            published_date="2024-05-15",
                            confidence=0.9,
                        ),
                        ExtractedLink(
                            title="業績予想修正",
                            url="/ir/news.pdf",  # 相対URL
                            category="disclosures",
                            published_date="",
                            confidence=0.85,
                        ),
                    ],
                    page_description="企業のIRページ",
                )
            )

            mock_scraper = MagicMock()
            mock_scraper.fetch_page = AsyncMock(return_value="<html><body>IR Page</body></html>")

            explorer = LLMExplorer(llm_provider=mock_provider)
            docs = await explorer.explore_ir_page(mock_scraper, "https://example.com/ir/")

            assert len(docs) == 2
            assert docs[0].title == "決算説明会資料"
            assert docs[0].category == "earnings"
            assert docs[0].published_date is not None

            # 相対URLが絶対URLに変換されていること
            assert docs[1].url.startswith("https://")

        @pytest.mark.asyncio
        async def test_explore_handles_empty_response(self) -> None:
            """空のレスポンスを処理できること."""
            mock_provider = MagicMock()
            mock_provider.ainvoke_structured = AsyncMock(
                return_value=ExtractedLinksResponse(links=[], page_description="")
            )

            mock_scraper = MagicMock()
            mock_scraper.fetch_page = AsyncMock(return_value="<html></html>")

            explorer = LLMExplorer(llm_provider=mock_provider)
            docs = await explorer.explore_ir_page(mock_scraper, "https://example.com")

            assert docs == []

        @pytest.mark.asyncio
        async def test_explore_handles_scraper_error(self) -> None:
            """スクレイパーエラーを処理できること."""
            mock_scraper = MagicMock()
            mock_scraper.fetch_page = AsyncMock(side_effect=Exception("Network error"))

            explorer = LLMExplorer()
            docs = await explorer.explore_ir_page(mock_scraper, "https://example.com")

            # エラー時は空リストを返す
            assert docs == []

    class TestFindIrPageUrl:
        """Tests for find_ir_page_url method."""

        @pytest.mark.asyncio
        async def test_find_ir_page_by_url_pattern(self) -> None:
            """URLパターンでIRページを見つけられること."""
            mock_scraper = MagicMock()
            mock_scraper.fetch_page = AsyncMock(
                return_value="""
                <html>
                <body>
                <a href="/ir/">IR情報</a>
                </body>
                </html>
                """
            )

            explorer = LLMExplorer()
            url = await explorer.find_ir_page_url(mock_scraper, "https://example.com")

            assert url == "https://example.com/ir/"

        @pytest.mark.asyncio
        async def test_find_ir_page_by_text(self) -> None:
            """テキストでIRページを見つけられること."""
            mock_scraper = MagicMock()
            mock_scraper.fetch_page = AsyncMock(
                return_value="""
                <html>
                <body>
                <a href="/investor-relations/">投資家情報</a>
                </body>
                </html>
                """
            )

            explorer = LLMExplorer()
            url = await explorer.find_ir_page_url(mock_scraper, "https://example.com")

            assert url is not None
            assert "investor-relations" in url

        @pytest.mark.asyncio
        async def test_find_ir_page_not_found(self) -> None:
            """IRページが見つからない場合Noneを返すこと."""
            mock_scraper = MagicMock()
            mock_scraper.fetch_page = AsyncMock(
                return_value="""
                <html>
                <body>
                <a href="/about/">会社概要</a>
                <a href="/products/">製品情報</a>
                </body>
                </html>
                """
            )

            explorer = LLMExplorer()
            url = await explorer.find_ir_page_url(mock_scraper, "https://example.com")

            assert url is None
