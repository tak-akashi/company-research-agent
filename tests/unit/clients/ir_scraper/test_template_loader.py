"""Tests for TemplateLoader."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from company_research_agent.clients.ir_scraper.template_loader import TemplateLoader


@pytest.fixture
def temp_templates_dir(tmp_path: Path) -> Path:
    """テスト用のテンプレートディレクトリを作成."""
    templates_dir = tmp_path / "ir_templates"
    templates_dir.mkdir()

    # テスト用YAMLファイルを作成（link_patternはシングルクォートで）
    toyota_yaml = """
company:
  sec_code: "72030"
  name: "トヨタ自動車"

ir_page:
  base_url: "https://global.toyota/jp/ir/"
  sections:
    earnings:
      url: "library/index.html"
      selector: ".ir-list a"
      link_pattern: '.*\\.pdf$'
"""
    (templates_dir / "72030_toyota.yaml").write_text(toyota_yaml)

    sony_yaml = """
company:
  sec_code: "67580"
  name: "ソニーグループ"

ir_page:
  base_url: "https://www.sony.com/ja/SonyInfo/IR/"
  sections:
    earnings:
      url: "library/"
      selector: ".ir-item a"
"""
    (templates_dir / "67580_sony.yaml").write_text(sony_yaml)

    return templates_dir


class TestTemplateLoader:
    """Tests for TemplateLoader class."""

    class TestLoadTemplate:
        """Tests for load_template method."""

        def test_load_existing_template(self, temp_templates_dir: Path) -> None:
            """存在するテンプレートをロードできること."""
            loader = TemplateLoader(temp_templates_dir)
            template = loader.load_template("72030")

            assert template is not None
            assert template.company.sec_code == "72030"
            assert template.company.name == "トヨタ自動車"
            assert "earnings" in template.ir_page.sections

        def test_load_nonexistent_template(self, temp_templates_dir: Path) -> None:
            """存在しないテンプレートの場合Noneを返すこと."""
            loader = TemplateLoader(temp_templates_dir)
            template = loader.load_template("99999")

            assert template is None

        def test_cache_loaded_template(self, temp_templates_dir: Path) -> None:
            """ロードしたテンプレートがキャッシュされること."""
            loader = TemplateLoader(temp_templates_dir)

            # 1回目のロード
            template1 = loader.load_template("72030")
            # 2回目のロード（キャッシュから）
            template2 = loader.load_template("72030")

            assert template1 is template2

    class TestListTemplates:
        """Tests for list_templates method."""

        def test_list_all_templates(self, temp_templates_dir: Path) -> None:
            """全テンプレートの証券コードを取得できること."""
            loader = TemplateLoader(temp_templates_dir)
            sec_codes = loader.list_templates()

            assert "72030" in sec_codes
            assert "67580" in sec_codes
            assert len(sec_codes) == 2

        def test_list_templates_empty_dir(self, tmp_path: Path) -> None:
            """空のディレクトリの場合空リストを返すこと."""
            empty_dir = tmp_path / "empty"
            empty_dir.mkdir()

            loader = TemplateLoader(empty_dir)
            sec_codes = loader.list_templates()

            assert sec_codes == []

        def test_list_templates_nonexistent_dir(self, tmp_path: Path) -> None:
            """存在しないディレクトリの場合空リストを返すこと."""
            loader = TemplateLoader(tmp_path / "nonexistent")
            sec_codes = loader.list_templates()

            assert sec_codes == []

    class TestScrapeWithTemplate:
        """Tests for scrape_with_template method."""

        @pytest.mark.asyncio
        async def test_scrape_extracts_pdf_links(self, temp_templates_dir: Path) -> None:
            """テンプレートに基づいてPDFリンクを抽出できること."""
            loader = TemplateLoader(temp_templates_dir)
            template = loader.load_template("72030")
            assert template is not None

            # モックスクレイパー
            mock_scraper = MagicMock()
            mock_scraper.fetch_page = AsyncMock(
                return_value="""
                <html>
                <body>
                <div class="ir-list">
                    <a href="doc1.pdf">決算説明会資料 2024Q1</a>
                    <a href="doc2.pdf">決算説明会資料 2024Q2</a>
                    <a href="other.html">その他</a>
                </div>
                </body>
                </html>
                """
            )

            docs = await loader.scrape_with_template(mock_scraper, template, category="earnings")

            assert len(docs) == 2
            assert all(doc.category == "earnings" for doc in docs)
            assert all(doc.url.endswith(".pdf") for doc in docs)

        @pytest.mark.asyncio
        async def test_scrape_handles_relative_urls(self, temp_templates_dir: Path) -> None:
            """相対URLを絶対URLに変換できること."""
            loader = TemplateLoader(temp_templates_dir)
            template = loader.load_template("72030")
            assert template is not None

            mock_scraper = MagicMock()
            mock_scraper.fetch_page = AsyncMock(
                return_value="""
                <html>
                <div class="ir-list">
                    <a href="/ir/docs/report.pdf">レポート</a>
                </div>
                </html>
                """
            )

            docs = await loader.scrape_with_template(mock_scraper, template, category="earnings")

            assert len(docs) == 1
            # 絶対URLに変換されていること
            assert docs[0].url.startswith("https://")

        @pytest.mark.asyncio
        async def test_scrape_filters_non_pdf_links(self, temp_templates_dir: Path) -> None:
            """PDF以外のリンクを除外すること."""
            loader = TemplateLoader(temp_templates_dir)
            template = loader.load_template("67580")  # link_patternなし
            assert template is not None

            mock_scraper = MagicMock()
            mock_scraper.fetch_page = AsyncMock(
                return_value="""
                <html>
                <div class="ir-item">
                    <a href="doc.pdf">PDF資料</a>
                    <a href="page.html">HTMLページ</a>
                    <a href="doc.xlsx">Excel</a>
                </div>
                </html>
                """
            )

            docs = await loader.scrape_with_template(mock_scraper, template, category="earnings")

            assert len(docs) == 1
            assert docs[0].url.endswith(".pdf")

    class TestExtractDocumentFromElement:
        """Tests for _extract_document_from_element method."""

        def test_extract_from_anchor_element(self, temp_templates_dir: Path) -> None:
            """アンカー要素から情報を抽出できること."""
            from bs4 import BeautifulSoup

            loader = TemplateLoader(temp_templates_dir)

            html = '<a href="report.pdf">年次報告書</a>'
            soup = BeautifulSoup(html, "html.parser")
            element = soup.find("a")

            doc = loader._extract_document_from_element(
                element=element,
                base_url="https://example.com/ir/",
                category="earnings",
            )

            assert doc is not None
            assert doc.title == "年次報告書"
            assert doc.url == "https://example.com/ir/report.pdf"
            assert doc.category == "earnings"

        def test_extract_returns_none_for_non_pdf(self, temp_templates_dir: Path) -> None:
            """PDF以外のリンクの場合Noneを返すこと."""
            from bs4 import BeautifulSoup

            loader = TemplateLoader(temp_templates_dir)

            html = '<a href="page.html">ページ</a>'
            soup = BeautifulSoup(html, "html.parser")
            element = soup.find("a")

            doc = loader._extract_document_from_element(
                element=element,
                base_url="https://example.com/",
                category="earnings",
            )

            assert doc is None

        def test_extract_with_link_pattern(self, temp_templates_dir: Path) -> None:
            """link_patternでフィルタリングできること."""
            from bs4 import BeautifulSoup

            loader = TemplateLoader(temp_templates_dir)

            html = '<a href="2024_q1.pdf">Q1レポート</a>'
            soup = BeautifulSoup(html, "html.parser")
            element = soup.find("a")

            # マッチするパターン
            doc = loader._extract_document_from_element(
                element=element,
                base_url="https://example.com/",
                category="earnings",
                link_pattern=r"2024.*\.pdf$",
            )
            assert doc is not None

            # マッチしないパターン
            doc = loader._extract_document_from_element(
                element=element,
                base_url="https://example.com/",
                category="earnings",
                link_pattern=r"2025.*\.pdf$",
            )
            assert doc is None
