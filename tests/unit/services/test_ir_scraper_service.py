"""Tests for IRScraperService."""

from datetime import date, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from company_research_agent.schemas.ir_schemas import IRDocument
from company_research_agent.services.ir_scraper_service import IRScraperService


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """テスト用データディレクトリ."""
    data_dir = tmp_path / "data" / "ir"
    data_dir.mkdir(parents=True)
    return data_dir


@pytest.fixture
def temp_templates_dir(tmp_path: Path) -> Path:
    """テスト用テンプレートディレクトリ."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    toyota_yaml = """
company:
  sec_code: "72030"
  name: "トヨタ自動車"

ir_page:
  base_url: "https://global.toyota/jp/ir/"
  sections:
    earnings:
      url: "library/"
      selector: ".ir-list a"
"""
    (templates_dir / "72030_toyota.yaml").write_text(toyota_yaml)
    return templates_dir


class TestIRScraperService:
    """Tests for IRScraperService class."""

    class TestInit:
        """Tests for __init__ method."""

        def test_default_initialization(self) -> None:
            """デフォルト値で初期化できること."""
            service = IRScraperService()
            assert service._template_loader is not None
            assert service._llm_explorer is not None

        def test_custom_directories(self, temp_templates_dir: Path, temp_data_dir: Path) -> None:
            """カスタムディレクトリを指定できること."""
            service = IRScraperService(
                templates_dir=temp_templates_dir,
                data_dir=temp_data_dir,
            )
            assert service._data_dir == temp_data_dir

    class TestShouldSkipDownload:
        """Tests for _should_skip_download method."""

        def test_skip_existing_file(self, temp_data_dir: Path) -> None:
            """既存ファイルの場合スキップすること."""
            service = IRScraperService(data_dir=temp_data_dir)
            existing_file = temp_data_dir / "existing.pdf"
            existing_file.write_text("test")

            result = service._should_skip_download(
                "https://example.com/doc.pdf", existing_file, force=False
            )

            assert result is True

        def test_not_skip_nonexistent_file(self, temp_data_dir: Path) -> None:
            """存在しないファイルの場合スキップしないこと."""
            service = IRScraperService(data_dir=temp_data_dir)
            nonexistent_file = temp_data_dir / "nonexistent.pdf"

            result = service._should_skip_download(
                "https://example.com/doc.pdf", nonexistent_file, force=False
            )

            assert result is False

        def test_not_skip_with_force(self, temp_data_dir: Path) -> None:
            """forceフラグがTrueの場合スキップしないこと."""
            service = IRScraperService(data_dir=temp_data_dir)
            existing_file = temp_data_dir / "existing.pdf"
            existing_file.write_text("test")

            result = service._should_skip_download(
                "https://example.com/doc.pdf", existing_file, force=True
            )

            assert result is False

    class TestFilterByDate:
        """Tests for _filter_by_date method."""

        def test_filter_old_documents(self, temp_data_dir: Path) -> None:
            """古いドキュメントを除外すること."""
            service = IRScraperService(data_dir=temp_data_dir)

            today = date.today()
            old_date = today - timedelta(days=100)
            recent_date = today - timedelta(days=30)

            documents = [
                IRDocument(
                    title="Old Doc",
                    url="https://example.com/old.pdf",
                    category="earnings",
                    published_date=old_date,
                ),
                IRDocument(
                    title="Recent Doc",
                    url="https://example.com/recent.pdf",
                    category="earnings",
                    published_date=recent_date,
                ),
            ]

            since = today - timedelta(days=60)
            filtered = service._filter_by_date(documents, since)

            assert len(filtered) == 1
            assert filtered[0].title == "Recent Doc"

        def test_keep_documents_without_date(self, temp_data_dir: Path) -> None:
            """日付が不明なドキュメントは除外しないこと."""
            service = IRScraperService(data_dir=temp_data_dir)

            documents = [
                IRDocument(
                    title="No Date Doc",
                    url="https://example.com/nodate.pdf",
                    category="earnings",
                    published_date=None,
                ),
            ]

            since = date.today() - timedelta(days=30)
            filtered = service._filter_by_date(documents, since)

            assert len(filtered) == 1

    class TestGetSavePath:
        """Tests for _get_save_path method."""

        def test_generate_save_path(self, temp_data_dir: Path) -> None:
            """保存パスが正しく生成されること."""
            service = IRScraperService(data_dir=temp_data_dir)

            doc = IRDocument(
                title="Test Doc",
                url="https://example.com/ir/reports/annual_report_2024.pdf",
                category="earnings",
            )

            path = service._get_save_path("72030", doc)

            assert path.parent.name == "earnings"
            assert path.parent.parent.name == "ir"
            assert path.parent.parent.parent.name == "72030"
            assert path.name == "annual_report_2024.pdf"

        def test_handle_encoded_filename(self, temp_data_dir: Path) -> None:
            """URLエンコードされたファイル名を処理できること."""
            service = IRScraperService(data_dir=temp_data_dir)

            doc = IRDocument(
                title="Test Doc",
                url="https://example.com/ir/%E5%A0%B1%E5%91%8A%E6%9B%B8.pdf",
                category="earnings",
            )

            path = service._get_save_path("72030", doc)

            assert path.name == "報告書.pdf"

    class TestListRegisteredCompanies:
        """Tests for list_registered_companies method."""

        def test_list_companies(self, temp_templates_dir: Path, temp_data_dir: Path) -> None:
            """登録企業を一覧できること."""
            service = IRScraperService(
                templates_dir=temp_templates_dir,
                data_dir=temp_data_dir,
            )

            companies = service.list_registered_companies()

            assert "72030" in companies

    class TestFetchIrDocuments:
        """Tests for fetch_ir_documents method."""

        @pytest.mark.asyncio
        async def test_fetch_with_template(
            self, temp_templates_dir: Path, temp_data_dir: Path
        ) -> None:
            """テンプレートを使用してIR資料を取得できること."""
            service = IRScraperService(
                templates_dir=temp_templates_dir,
                data_dir=temp_data_dir,
            )

            # モックを設定
            with patch.object(service._template_loader, "scrape_with_template") as mock_scrape:
                mock_scrape.return_value = [
                    IRDocument(
                        title="Test Doc",
                        url="https://example.com/doc.pdf",
                        category="earnings",
                        published_date=date.today(),
                    )
                ]

                with patch(
                    "company_research_agent.services.ir_scraper_service.BaseIRScraper"
                ) as mock_scraper_class:
                    mock_scraper = AsyncMock()
                    mock_scraper.download_pdf = AsyncMock(
                        return_value=temp_data_dir / "72030" / "earnings" / "doc.pdf"
                    )
                    mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
                    mock_scraper.__aexit__ = AsyncMock(return_value=None)
                    mock_scraper_class.return_value = mock_scraper

                    docs = await service.fetch_ir_documents(
                        sec_code="72030",
                        category="earnings",
                        with_summary=False,  # 要約をスキップ
                    )

                    assert len(docs) == 1
                    assert docs[0].title == "Test Doc"

        @pytest.mark.asyncio
        async def test_fetch_with_default_since(
            self, temp_templates_dir: Path, temp_data_dir: Path
        ) -> None:
            """デフォルトのsinceが90日前になること."""
            service = IRScraperService(
                templates_dir=temp_templates_dir,
                data_dir=temp_data_dir,
            )

            with patch.object(service._template_loader, "scrape_with_template") as mock_scrape:
                mock_scrape.return_value = []

                with patch.object(service, "_find_ir_page_for_company") as mock_find:
                    mock_find.return_value = None

                    with patch(
                        "company_research_agent.services.ir_scraper_service.BaseIRScraper"
                    ) as mock_scraper_class:
                        mock_scraper = AsyncMock()
                        mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
                        mock_scraper.__aexit__ = AsyncMock(return_value=None)
                        mock_scraper_class.return_value = mock_scraper

                        # テンプレートなし、IRページなしでエラー
                        from company_research_agent.core.exceptions import (
                            IRTemplateNotFoundError,
                        )

                        with pytest.raises(IRTemplateNotFoundError):
                            await service.fetch_ir_documents(sec_code="99999")

    class TestExploreIrPage:
        """Tests for explore_ir_page method."""

        @pytest.mark.asyncio
        async def test_explore_page(self, temp_data_dir: Path) -> None:
            """IRページを探索できること."""
            service = IRScraperService(data_dir=temp_data_dir)

            with patch.object(service._llm_explorer, "explore_ir_page") as mock_explore:
                mock_explore.return_value = [
                    IRDocument(
                        title="Discovered Doc",
                        url="https://example.com/doc.pdf",
                        category="news",
                        published_date=date.today(),
                    )
                ]

                with patch(
                    "company_research_agent.services.ir_scraper_service.BaseIRScraper"
                ) as mock_scraper_class:
                    mock_scraper = AsyncMock()
                    mock_scraper.download_pdf = AsyncMock(
                        return_value=temp_data_dir / "example" / "news" / "doc.pdf"
                    )
                    mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
                    mock_scraper.__aexit__ = AsyncMock(return_value=None)
                    mock_scraper_class.return_value = mock_scraper

                    docs = await service.explore_ir_page(
                        url="https://example.com/ir/",
                        with_summary=False,
                    )

                    assert len(docs) == 1
                    assert docs[0].title == "Discovered Doc"
